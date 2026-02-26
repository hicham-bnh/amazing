from functools import wraps
from mlx import Mlx
from .maze_generator import MazeGenerator, PathEnum, Point
from typing import Dict, Union, Tuple, Callable, Any, Optional, List


class XVar:
    """Container for mlx and image/window related mutable state.

    Attributes:
        mlx: The mlx binding instance.
        mlx_ptr: Pointer/handle to the mlx instance.
        win_ptr: Pointer/handle to the created window.
        win_width: Window width in pixels.
        win_height: Window height in pixels.
        img_ptr: Pointer/handle to the created image.
        img_width: Image width in pixels.
        img_height: Image height in pixels.
        bpp: Bytes per pixel.
        line_len: Length of a line (in bytes) of the image buffer.
        maze_img: The raw image bytearray/buffer returned by mlx_get_data_addr.
        pixel_d: Logical pixel size for maze cell rendering.
        wall_thickness: Thickness of drawn walls.
    """

    def __init__(self) -> None:
        """Initialize default values for mlx/image/window state."""
        self.mlx: Optional[Mlx] = None
        self.mlx_ptr: Optional[Any] = None

        self.win_ptr: Optional[Any] = None
        self.win_width: int = 0
        self.win_height: int = 0

        self.img_ptr: Optional[Any] = None
        self.img_width: int = 0
        self.img_height: int = 0
        self.bpp: int = 0
        self.line_len: int = 0
        self.maze_img: Optional[bytearray] = None

        self.pixel_d: int = 12
        self.wall_thickness: int = 3


class MazeRepresentation:
    """Render and manage display interactions for a generated maze.

    The class wraps an instance of MazeGenerator and provides methods to
    create an mlx window/image, draw the maze, update the display and react
    to key events.

    Args:
        config: Configuration dictionary used by MazeGenerator.from_dict.
    """

    def __init__(
        self,
        config: Dict[str, Union[str, int, bool, Tuple[int, ...]]]
    ) -> None:
        """Initialize MazeRepresentation and its dependent objects.

        Args:
            config: Configuration dictionary forwarded to MazeGenerator.
        """
        self.xvar: XVar = XVar()
        self.maze_gen: MazeGenerator = MazeGenerator.from_dict(config)
        self.txt_color: int = 0xFFFFFFFF
        self.wall_color: int = 0xFFFFFFFF
        self.wall_color2: int = 0xFFBDFF99
        self.logo_color: int = 0xFFFF0000
        self.path_color: int = 0xFF5050FF
        self.path_printed: int = 0
        self.logo_printed: int = 0
        self.wall_colored: int = 0

    @staticmethod
    def display_img(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator that pushes the current image to the window after func.

        Args:
            func: The function to wrap.

        Returns:
            A wrapped function that posts the image to the window.
        """

        @wraps(func)
        def wrapper(self: "MazeRepresentation",
                    *args: Any, **kwargs: Any) -> None:
            func(self, *args, **kwargs)
            m_ptr: Any = self.xvar.mlx_ptr
            w_ptr: Any = self.xvar.win_ptr
            i_ptr: Any = self.xvar.img_ptr
            mlx = self.xvar.mlx
            assert mlx is not None, "mlx must be initialized before " \
                "displaying image"
            mlx.mlx_put_image_to_window(m_ptr, w_ptr, i_ptr, 0, 0)
            return

        return wrapper

    @staticmethod
    def clear_window(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator that clears the window before calling func.

        Args:
            func: The function to wrap.

        Returns:
            A wrapped function that clears the window first.
        """

        @wraps(func)
        def wrapper(self: "MazeRepresentation",
                    *args: Any, **kwargs: Any) -> None:
            m_ptr: Any = self.xvar.mlx_ptr
            w_ptr: Any = self.xvar.win_ptr
            mlx = self.xvar.mlx
            assert mlx is not None, "mlx must be initialized before " \
                "clearing window"
            mlx.mlx_clear_window(m_ptr, w_ptr)
            func(self, *args, **kwargs)
            return

        return wrapper

    @staticmethod
    def new_img(func: Callable[..., Any]) -> Callable[..., Any]:
        """Decorator that recreates the image buffer before calling func.

        The decorator destroys the previous image, creates a new one, obtains
        its data pointer and clears the buffer.

        Args:
            func: The function to wrap.

        Returns:
            A wrapped function that ensures a fresh image buffer.
        """

        @wraps(func)
        def wrapper(self: "MazeRepresentation",
                    *args: Any, **kwargs: Any) -> None:
            m_ptr: Any = self.xvar.mlx_ptr
            mlx = self.xvar.mlx
            assert mlx is not None, "mlx must be initialized before " \
                "destroying image"
            mlx.mlx_destroy_image(m_ptr, self.xvar.img_ptr)
            self.create_img()
            self.get_img_data()
            mv = self.xvar.maze_img
            if mv is not None:
                try:
                    mv[:] = b'\x00' * len(mv)
                except Exception:
                    pass
            func(self, *args, **kwargs)
            return

        return wrapper

    @display_img
    def launch(self) -> None:
        """Initialize window/image and render the initial maze.

        This performs all initialization required to show the maze on screen.
        """
        self.init_window_dimension()
        self.init_img_dimension()
        self.display_win()
        self.create_img()
        self.get_img_data()
        self.display_txt()
        self.display_maze(self.wall_color)

    def init_mlx(self) -> None:
        """Initialize the mlx binding and store the returned pointer.

        Raises:
            Exception: If mlx_init fails and returns a falsy pointer.
        """
        self.xvar.mlx = Mlx()
        self.xvar.mlx_ptr = self.xvar.mlx.mlx_init()
        if not self.xvar.mlx_ptr:
            raise Exception("Can't create a Mlx instance.")

    def init_window_dimension(self) -> None:
        """Compute and set the window width and height based on maze size."""
        self.xvar.win_height = max(
            (self.maze_gen.height * self.xvar.pixel_d) + 150, 850)
        self.xvar.win_width = max(
            (self.maze_gen.width * self.xvar.pixel_d) + 150, 850)

    def init_img_dimension(self) -> None:
        """Compute and set the internal image width/height used for drawing."""
        self.xvar.img_height = max(
            self.maze_gen.height * self.xvar.pixel_d * 2, 700)
        self.xvar.img_width = max(
            self.maze_gen.width * self.xvar.pixel_d * 2, 700)

    @display_img
    def fill_case(self, color: int, points: List[Point]) -> None:
        """Fill given maze cell points with the provided color.

        Args:
            color: Integer ARGB color to write.
            points: List of Point objects to fill.
        """
        pixel_d: int = self.xvar.pixel_d
        line_len: int = self.xvar.line_len
        bpp: int = self.xvar.bpp
        mv = self.xvar.maze_img
        assert mv is not None, "maze_img must be initialized before drawing"
        for p in points:
            pixel: int = (p.row * self.xvar.line_len * self.xvar.pixel_d +
                          p.col * self.xvar.pixel_d * self.xvar.bpp)
            for x in range(self.xvar.wall_thickness, pixel_d):
                for y in range(self.xvar.wall_thickness, pixel_d):
                    pos: int = pixel + x * line_len + y * bpp
                    for c in range(bpp):
                        mv[pos + c] = (color >> (8 * c)) & 0xFF

    def display_wall_north(self, pixel: int, color: int) -> None:
        """Draw the northern wall segment for a cell at buffer offset pixel."""
        bpp: int = self.xvar.bpp
        pixel_d: int = self.xvar.pixel_d
        wall_thickness: int = self.xvar.wall_thickness
        line_len: int = self.xvar.line_len
        mv = self.xvar.maze_img
        assert mv is not None, "maze_img must be initialized before drawing"
        for x in range(wall_thickness):
            for y in range(pixel_d):
                pos: int = pixel + x * line_len + y * bpp
                for c in range(bpp):
                    mv[pos + c] = (color >> (8 * c)) & 0xFF

    def display_wall_south(self, pixel: int, color: int) -> None:
        """Draw the southern wall segment for a cell at buffer offset pixel."""
        bpp: int = self.xvar.bpp
        pixel_d: int = self.xvar.pixel_d
        wall_thickness: int = self.xvar.wall_thickness
        line_len: int = self.xvar.line_len

        mv = self.xvar.maze_img
        assert mv is not None, "maze_img must be initialized before drawing"
        for x in range(wall_thickness):
            for y in range(pixel_d):
                pos: int = pixel + ((x + pixel_d) * line_len) + y * bpp
                for c in range(bpp):
                    mv[pos + c] = (color >> (8 * c)) & 0xFF

    def display_wall_east(self, pixel: int, color: int) -> None:
        """Draw the eastern wall segment for a cell at buffer offset pixel."""
        bpp: int = self.xvar.bpp
        pixel_d: int = self.xvar.pixel_d
        wall_thickness: int = self.xvar.wall_thickness
        line_len: int = self.xvar.line_len

        mv = self.xvar.maze_img
        assert mv is not None, "maze_img must be initialized before drawing"
        for x in range(pixel_d + 3):
            for y in range(wall_thickness):
                pos: int = pixel + x * line_len + ((y + pixel_d) * bpp)
                for c in range(bpp):
                    mv[pos + c] = (color >> (8 * c)) & 0xFF

    def display_wall_west(self, pixel: int, color: int) -> None:
        """Draw the western wall segment for a cell at buffer offset pixel."""
        bpp: int = self.xvar.bpp
        pixel_d: int = self.xvar.pixel_d
        wall_thickness: int = self.xvar.wall_thickness
        line_len: int = self.xvar.line_len

        mv = self.xvar.maze_img
        assert mv is not None, "maze_img must be initialized before drawing"
        for x in range(pixel_d + 3):
            for y in range(wall_thickness):
                pos: int = pixel + x * line_len + y * bpp
                for c in range(bpp):
                    mv[pos + c] = (color >> (8 * c)) & 0xFF

    def put_pixel(self, pixel: int, value: int, color: int) -> None:
        """Plot a cell's walls according to the value bitmask.

        Args:
            pixel: The byte offset into the image buffer for the cell.
            value: Bitmask value encoding which walls exist.
            color: Color to use when drawing walls.
        """
        if value >> PathEnum.N.value[1] & 1:
            self.display_wall_north(pixel, color)
        if value >> PathEnum.S.value[1] & 1:
            self.display_wall_south(pixel, color)
        if value >> PathEnum.E.value[1] & 1:
            self.display_wall_east(pixel, color)
        if value >> PathEnum.W.value[1] & 1:
            self.display_wall_west(pixel, color)
        return

    @display_img
    def display_maze(self, color: int) -> None:
        """Draw the entire maze using the specified wall color.

        Args:
            color: ARGB integer color to use for walls.
        """
        for row, height in enumerate(self.maze_gen.maze):
            for col, value in enumerate(height):
                pixel: int = (row * self.xvar.line_len * self.xvar.pixel_d +
                              col * self.xvar.pixel_d * self.xvar.bpp)
                self.put_pixel(pixel, value, color)

    @clear_window
    @new_img
    @display_img
    def redisplay_maze(self) -> None:
        """Re-generate the maze, find a path, write to file and redraw."""
        self.maze_gen.generate_maze()
        self.maze_gen.find_path()
        self.maze_gen.set_to_file()
        self.display_maze(self.wall_color)
        self.display_txt()
        self.wall_colored = 0
        self.path_printed = 0
        self.logo_printed = 0

    def display_win(self) -> None:
        """Create the application window using mlx and store its handle.

        Raises:
            Exception: If opening the window fails.
        """
        m_ptr: Any = self.xvar.mlx_ptr
        width: int = self.xvar.win_width
        height: int = self.xvar.win_height
        mlx = self.xvar.mlx
        assert mlx is not None, "mlx must be initialized before " \
            "creating window"
        self.xvar.win_ptr = mlx.mlx_new_window(
            m_ptr, width, height, "A-Maze_Ing")
        if not self.xvar.win_ptr:
            raise Exception("Can't create a window.")

    def create_img(self) -> None:
        """Create a new image via mlx and store its handle.

        Raises:
            Exception: If creating the image returns None.
        """
        m_ptr: Any = self.xvar.mlx_ptr
        width: int = self.xvar.img_width
        height: int = self.xvar.img_height
        mlx = self.xvar.mlx
        assert mlx is not None, "mlx must be initialized before creating image"
        self.xvar.img_ptr = mlx.mlx_new_image(m_ptr, width, height)

        if self.xvar.img_ptr is None:
            raise Exception("mlx_new_image returned None")

    def get_img_data(self) -> None:
        """Obtain image data pointer and metadata from mlx.

        Raises:
            Exception: If the returned maze image buffer is None.
        """
        i_ptr: Any = self.xvar.img_ptr
        mlx = self.xvar.mlx
        assert mlx is not None, "mlx must be initialized before " \
            "getting image data"
        self.xvar.maze_img, self.xvar.bpp, self.xvar.line_len, _ = (
            mlx.mlx_get_data_addr(i_ptr)
        )
        self.xvar.bpp //= 8

        if self.xvar.maze_img is None:
            raise Exception("maze_img is None")

    def display_txt(self) -> None:
        """Render menu/help text at the bottom of the window."""
        m_ptr: Any = self.xvar.mlx_ptr
        w_ptr: Any = self.xvar.win_ptr
        mlx = self.xvar.mlx
        assert mlx is not None, "mlx must be initialized before drawing text"
        height: int = self.xvar.win_height
        strings: List[str] = [
            "=== A_Maze_Ing ===",
            "1. Re-generate maze",
            "2. Show/Hide path",
            "3. Rotate maze color",
            "4. Show logo" if len(self.maze_gen.logo) >= 1 else "4. Quit",
            "5. Quit" if len(self.maze_gen.logo) >= 1 else ""
        ]
        dif: int = 120 if len(self.maze_gen.logo) else 100
        for s in strings:
            if s != "":
                mlx.mlx_string_put(m_ptr, w_ptr, 0, height -
                                   dif, self.txt_color, s)
                dif -= 20

    def quit_mlx(self, params: Optional[Any] = None) -> None:
        """Exit the mlx main loop.

        Args:
            params: Optional parameter for compatibility with hook signature.
        """
        m_ptr: Any = self.xvar.mlx_ptr
        mlx = self.xvar.mlx
        assert mlx is not None, "mlx must be initialized before exiting loop"
        mlx.mlx_loop_exit(m_ptr)

    def key_hook(self, key: int, params: Optional[Any] = None) -> None:
        """Handle keyboard events mapped to application actions.

        Args:
            key: Integer keycode received from the event system.
            params: Optional parameter for compatibility with hook signature.
        """
        if key == 49:  # 1
            self.redisplay_maze()
            return
        if key == 50:  # 2
            if self.path_printed == 0:
                self.fill_case(self.path_color, self.maze_gen.path)
                self.path_printed = 1
            else:
                self.fill_case(0xFF000000, self.maze_gen.path)
                self.path_printed = 0
            return
        if key == 51:
            if self.wall_colored == 0:  # 3
                self.display_maze(self.wall_color2)
                self.wall_colored = 1
            else:
                self.display_maze(self.wall_color)
                self.wall_colored = 0
            return
        if len(self.maze_gen.logo) >= 1:
            if key == 52:  # 4
                if self.logo_printed == 0:
                    self.fill_case(self.logo_color, self.maze_gen.logo)
                    self.logo_printed = 1
                else:
                    self.fill_case(0xFF000000, self.maze_gen.logo)
                    self.logo_printed = 0
                return
            if key == 53:  # 5
                self.quit_mlx()
                return
        else:
            if key == 52:  # 4
                self.quit_mlx()
                return
        return
