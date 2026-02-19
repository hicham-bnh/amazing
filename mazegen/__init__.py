try:
    from .display_maze import MazeRepresentation
    HAVE_MLX = True
except Exception:
    MazeRepresentation = None  # type: ignore
    HAVE_MLX = False
from .parsing import get_config, transform_data, get_entry_or_exit
from .data_validator import DataValidator
from .maze_generator import MazeGenerator, Point, PathEnum

__all__ = [
    "get_config",
    "transform_data",
    "get_entry_or_exit",
    "DataValidator",
    "MazeGenerator",
    "Point",
    "PathEnum",
]
if HAVE_MLX:
    __all__.insert(0, "MazeRepresentation")

__author__ = "tchemin, mobenhab"
__version__ = "1.0.0"
