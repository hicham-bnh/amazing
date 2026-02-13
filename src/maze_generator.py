from __future__ import annotations
from typing import Tuple, Dict, Union, List
from enum import Enum
from random import choice


class Point:
    def __init__(self, row: int, col: int):
        self.row: int = row
        self.col: int = col

    @classmethod
    def from_tuple(cls, data) -> Point:
        p: Point = cls(
            row=data[0],
            col=data[1]
        )
        return p

    @staticmethod
    def add_points(p1: Point, p2: Point) -> Point:
        n_p: Point = (p1.row + p2.row, p1.col + p2.col)
        return n_p

    def __eq__(self, _) -> int:
        return (self.row + self.col)

    def __hash__(self):
        return hash(self.row * self.col)


class PathEnum(Enum):
    N = (1, 0)
    E = (2, 1)
    S = (4, 2)
    W = (8, 3)

    @staticmethod
    def oppose_bit(bit: int) -> int:
        pass


class MazeGenerator:

    dir: Dict[PathEnum, Point] = {
        PathEnum.N: Point(-1, 0),
        PathEnum.E: Point(0, 1),
        PathEnum.S: Point(1, 0),
        PathEnum.W: Point(0, -1),
    }

    def __init__(
        self,
        height: int,
        width: int,
        entry_point: Tuple[int, int],
        exit_point: Tuple[int, int],
        output_file: str,
        perfect: bool
    ) -> None:
        self.height: int = height
        self.width: int = width
        self.entry_point: Point = Point.from_tuple(entry_point)
        self.exit_point: Point = Point.from_tuple(exit_point)
        self.output_file: str = output_file
        self.perfect: bool = perfect
        self.path_str: str = ""
        self.path: List[Point] = [entry_point, exit_point]
        self.maze: List[List[int]] = self.init_maze()

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Union[Tuple[int, int], int, str, bool]]
    ) -> MazeGenerator:
        maze: MazeGenerator = cls(
            height=data["HEIGHT"],
            width=data["WIDTH"],
            entry_point=data["ENTRY"],
            exit_point=data["EXIT"],
            output_file=data["OUTPUT_FILE"],
            perfect=data["PERFECT"]
        )
        return maze

    def init_maze(self) -> List[List[int]]:
        maze: List[List[int]] = [
            [15 for _ in range(self.width)]
            for _ in range(self.height)
        ]
        return maze

    def check_bounds(self, p: Point) -> bool:
        return (
            self.height < p.row and self.width < p.col
            and p.col >= 0 and p.row >= 0
        )

    def check_walls(self, p: Point, path_enum: PathEnum) -> bool:
        return (self.maze[p.row][p.col] >> path_enum.value[1]) & 1 == 1

    def place_logo(self) -> None:
        pass

    def generate_maze(self) -> None:
        self.place_logo()
        self.wilson_algo()
        if not self.perfect:
            self.break_walls()

    def wilson_algo(self) -> None:
        unvisited: List[Point] = [
            Point(row, col)
            for col in range(self.width)
            for row in range(self.height)
        ]
        unvisited.remove(self.entry_point)
        visited: List[Point] = [self.entry_point]

        tree: List[Point] = self.random_walk(visited, unvisited)

    def random_walk(
        self,
        visited: List[Point],
        unvisited: List[Point]
    ) -> List[Point]:
        tree: List[Point] = []

        r_p: Point = choice(unvisited)

        for k, v in self.dir.items():
            n_p: Point = Point.add_points(r_p, v)

        return tree

    def break_walls(self) -> None:
        pass
