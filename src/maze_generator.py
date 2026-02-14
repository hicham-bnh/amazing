from __future__ import annotations
from typing import Tuple, Dict, Union, List
from enum import Enum
from random import choice
from collections import deque


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
        n_p: Point = Point(p1.row + p2.row, p1.col + p2.col)
        return n_p

    def __eq__(self, p: Point) -> bool:
        if isinstance(p, Point):
            return p.row == self.row and p.col == self.col
        return NotImplemented

    def __hash__(self):
        return hash((self.row, self.col))

    def __str__(self) -> str:
        return f"[{self.row},{self.col}]"


class PathEnum(Enum):
    N = (1, 0)
    E = (2, 1)
    S = (4, 2)
    W = (8, 3)

    @staticmethod
    def oppose_bit(bit: int) -> int:
        if bit == PathEnum.N.value[0]:
            return PathEnum.S.value[0]
        if bit == PathEnum.E.value[0]:
            return PathEnum.W.value[0]
        if bit == PathEnum.S.value[0]:
            return PathEnum.N.value[0]
        if bit == PathEnum.W.value[0]:
            return PathEnum.E.value[0]
        raise ValueError("Error, bit can't get opposite bit")


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
        return self.height > p.row and self.width > p.col \
            and p.col >= 0 and p.row >= 0

    def check_walls(self, p: Point, path_enum: PathEnum) -> bool:
        return (self.maze[p.row][p.col] >> path_enum.value[1]) & 1 == 1

    def place_logo(self) -> None:
        pass

    def generate_maze(self) -> None:
        self.maze = self.init_maze()
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

        while len(unvisited) >= 1:
            tree: List[Tuple[Dict[PathEnum, Point], Point]
                       ] = self.random_walk(visited, unvisited)

            if not len(tree):
                continue

            for dir, point in tree:
                dir_p: Point = dir[1]
                path: PathEnum = dir[0]
                n_point = Point.add_points(point, dir_p)

                bit: int = path.value[0]
                op_bit: int = PathEnum.oppose_bit(bit)
                self.maze[point.row][point.col] ^= bit
                self.maze[n_point.row][n_point.col] ^= op_bit

                visited.append(point)
                if point in unvisited:
                    unvisited.remove(point)

    def random_walk(
        self,
        visited: List[Point],
        unvisited: List[Point]
    ) -> List[Tuple[Dict[PathEnum, Point], Point]]:
        tree: List[Point] = [choice(unvisited)]
        paths: List[Tuple[Dict[PathEnum, Point], Point]] = []

        while (1):
            dir: Dict[PathEnum, Point] = choice(list(self.dir.items()))
            r_d: Point = dir[1]
            n_p: Point = Point.add_points(tree[-1], r_d)

            if n_p in tree:
                index: int = tree.index(n_p)
                tree = tree[:index]
                paths = paths[:index]
                if len(tree) <= 0:
                    return paths
            elif (self.check_bounds(n_p)):
                paths.append((dir, tree[-1]))
                tree.append(n_p)
            if n_p in visited:
                return paths

    def break_walls(self) -> None:
        pass

    def convert_to_hex(self) -> List[List[str | int]]:
        char_hex: str = "0123456789ABCDEF"
        maze: List[List[str | int]] = self.init_maze()
        for row, height in enumerate(self.maze):
            for col, value in enumerate(height):
                maze[row][col] = char_hex[value]

        return maze

    def set_to_file(self) -> None:
        maze: List[List[str | int]] = self.convert_to_hex()
        with open(self.output_file, "w") as fd:
            for row in maze:
                for value in row:
                    fd.write(value)
                fd.write("\n")

    def rout(self):
        start = self.entry_point
        end = self.exit_point
        visited: Dict[Point, int] = {start: 0}
        parent: Dict[Point, Point] = {}
        queue = deque([start])
        while queue:
            current = queue.popleft()
            if current == end:
                break
            for direction, point in self.dir.items():
                voisin = Point.add_points(current, point)
                if self.check_walls(current, direction) or not self.check_bounds(voisin):
                    continue
                if voisin not in visited:
                    visited[voisin] = visited[current] + 1
                    parent[voisin] = current
                    queue.append(voisin)
        if end not in parent:
            return None
        self.path = []
        current = end
        while current != start:
            self.path.append(current)
            current = parent[current]
        self.path.append(start)
        self.path.reverse()
        return self.path
