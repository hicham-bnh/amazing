from src.maze_generator import MazeGenerator
from src.parsing import get_config

from typing import Dict, Tuple, Union
import sys



def main() -> None:
    try:
        config: Dict[str, Union[Tuple[int, int],
                                int, str, bool]] = get_config()
        maze_gen: MazeGenerator = MazeGenerator.from_dict(config)
    except KeyError as e:
        print(f"Error, can't instantiate maze: KEY NOT FOUND -> {e}")
        sys.exit()
    except Exception as e:
        print(f"Error, can't instantiate maze: {e}")
        sys.exit()

    maze_gen.generate_maze()
    maze_gen.set_to_file()
    chemin = maze_gen.rout()
    print(chemin)

if __name__ == "__main__":
    main()
