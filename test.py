from mlx import Mlx
import os


def handle_keypress(keysym, param):
    mlx_ptr, win_ptr = param
    m = Mlx()
    if keysym == 97:
        m.mlx_destroy_window(mlx_ptr, win_ptr)
        os._exit(0)

if __name__ == "__main__":
    m = Mlx()
    mlx_ptr = m.mlx_init()
    win_ptr = m.mlx_new_window(mlx_ptr,1200, 1200, "A-Maze-ing")
    m.mlx_key_hook(win_ptr, handle_keypress, (mlx_ptr, win_ptr))
    m.mlx_pixel_put(mlx_ptr, win_ptr, 1200//2, 1200//2, 0xFFFFFF)
    m.mlx_loop(mlx_ptr)