"""Entry point for the A-Maze_Ing application.

This module parses configuration, prepares the maze representation and
starts the graphical loop using the mlx wrapper. The main() function
initializes required resources and handles top-level errors.
"""
from mazegen.display_maze import MazeRepresentation
from mazegen.parsing import get_config

from typing import Dict, Any, Optional
import sys


def main() -> None:
    """Initialize the application and run the graphical loop.

    The function retrieves configuration via get_config(), creates the maze
    representation, generates the maze and its path, writes output to file,
    initializes the mlx instance and starts the UI event loop. Top-level
    errors are caught and cause a graceful exit with a printed message.

    Raises:
        SystemExit: Exits the process on unrecoverable errors.
    """
    try:
        file_name: Optional[str] = None
        if len(sys.argv) != 1:
            file_name = sys.argv[1]
        config: Dict[str, Any] = get_config(file_name)
        rpr: MazeRepresentation = MazeRepresentation(config)
        rpr.maze_gen.generate_maze()
        rpr.maze_gen.find_path()
        rpr.maze_gen.set_to_file()
        rpr.init_mlx()
    except KeyError as e:
        print(f"Error, can't instantiate maze: KEY NOT FOUND -> {e}")
        sys.exit()
    except Exception as e:
        print(f"Error, can't instantiate maze: {e}")
        sys.exit()

    try:
        rpr.launch()
        mlx = rpr.xvar.mlx
        assert mlx is not None, "mlx must be initialized before exiting loop"

        mlx.mlx_key_hook(rpr.xvar.win_ptr, rpr.key_hook, None)
        mlx.mlx_hook(rpr.xvar.win_ptr, 33, 0, rpr.quit_mlx, None)

        mlx.mlx_loop(rpr.xvar.mlx_ptr)
    except Exception as e:
        print(f"Error main: {e}")
        sys.exit()


if __name__ == "__main__":
    main()
