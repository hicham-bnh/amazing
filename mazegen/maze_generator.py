"""
Maze generation utilities for the A-Maze_Ing application.

This module implements a Point representation, a PathEnum of directions and
a MazeGenerator that creates mazes using Wilson's algorithm. All public
functions and classes include Google-style docstrings and explicit typing.
"""
from __future__ import annotations
from typing import (
    Tuple,
    Dict,
    List,
    Set,
    Optional,
    Deque,
    Any,
)
from enum import Enum
from random import sample, choice
from collections import deque
from dataclasses import dataclass
from .data_validator import DataValidator


@dataclass(slots=True, frozen=True)
class Point:
    """Immutable 2D point representing a maze cell.

    Attributes:
        row: Row index of the point.
        col: Column index of the point.
    """

    row: int
    col: int

    @classmethod
    def from_tuple(cls, data: Tuple[int, int]) -> "Point":
        """Create a Point from a (row, col) tuple.

        Args:
            data: A 2-tuple containing (row, col).

        Returns:
            A new Point instance.
        """
        p: Point = cls(row=data[0], col=data[1])
        return p

    @staticmethod
    def add_points(p1: "Point", p2: "Point") -> "Point":
        """Return the vector addition of two points.

        Args:
            p1: First point.
            p2: Second point.

        Returns:
            A new Point equal to p1 + p2 component-wise.
        """
        n_p: Point = Point(p1.row + p2.row, p1.col + p2.col)
        return n_p

    def __eq__(self, other: object) -> bool:
        """Compare two points for equality.

        Args:
            other: Object to compare with.

        Returns:
            True if other is a Point with the same coordinates,
            False otherwise.
        """
        if isinstance(other, Point):
            return other.row == self.row and other.col == self.col
        return NotImplemented

    def __hash__(self) -> int:
        """Return a stable hash for the point."""
        return hash((self.row, self.col))

    def __str__(self) -> str:
        """Return a human readable representation of the point."""
        return f"[{self.row},{self.col}]"


class PathEnum(Enum):
    """Enumeration of maze wall directions with bit and index metadata.

    Each enum value is a tuple (bitmask, shift_index) used to read/write
    wall bits in the internal integer cell representation.
    """

    N = (1, 0)
    E = (2, 1)
    S = (4, 2)
    W = (8, 3)

    @staticmethod
    def oppose_bit(bit: int) -> int:
        """Return the opposite direction bit for a given direction bit.

        Args:
            bit: Direction bit value (1, 2, 4, or 8).

        Returns:
            The opposite direction bit.

        Raises:
            ValueError: If the provided bit is not a valid direction bit.
        """
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
    """Generate and export mazes using Wilson's algorithm.

    The maze stores cell wall information as integers where bits correspond
    to walls. The class supports placing a fixed logo, generating mazes,
    converting the maze to hexadecimal characters and writing to a file.
    """

    directions: Dict[PathEnum, Point] = {
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
        perfect: bool,
    ) -> None:
        """Initialize a MazeGenerator.

        Args:
            height: Number of rows in the maze.
            width: Number of columns in the maze.
            entry_point: (row, col) of the entry cell.
            exit_point: (row, col) of the exit cell.
            output_file: Path to the file where the maze will be written.
            perfect: If True, produce a perfect maze (no loops).
        """
        try:
            DataValidator(
                width=width,
                height=height,
                entry_point=entry_point,
                exit_point=exit_point,
                perfect=perfect,
                output_file=output_file
            )
        except Exception as e:
            raise ValueError(f"Error configurating maze: {e}")
        self.height: int = height
        self.width: int = width
        self.entry_point: Point = Point.from_tuple(entry_point)
        self.exit_point: Point = Point.from_tuple(exit_point)
        self.output_file: str = output_file
        self.perfect: bool = perfect
        self.path_str: List[str] = []
        self.path: List[Point] = [Point.from_tuple(
            entry_point), Point.from_tuple(exit_point)]
        self.maze: List[List[int]] = []
        self.logo: Set[Point] = set()

    @classmethod
    def from_dict(
        cls,
        data: Dict[str, Any],
    ) -> "MazeGenerator":
        """Create a MazeGenerator from a configuration dictionary.

        Args:
            data: Configuration containing keys HEIGHT, WIDTH, ENTRY, EXIT,
                OUTPUT_FILE and PERFECT.

        Returns:
            A configured MazeGenerator instance.
        """

        maze: MazeGenerator = cls(
            height=data["HEIGHT"],
            width=data["WIDTH"],
            entry_point=data["ENTRY"],
            exit_point=data["EXIT"],
            output_file=data["OUTPUT_FILE"],
            perfect=data["PERFECT"],
        )
        return maze

    def init_maze(self) -> List[List[int]]:
        """Create the default filled maze representation.

        Every cell is initialized to 15 (all walls present).

        Returns:
            A 2D list representing the maze cells.
        """

        maze: List[List[int]] = [
            [15 for _ in range(self.width)] for _ in range(self.height)]
        self.path = []
        self.path_str = []
        return maze

    def check_bounds(self, p: Point) -> bool:
        """Return True if a point lies within maze bounds.

        Args:
            p: Point to check.

        Returns:
            True when 0 <= p.row < height and 0 <= p.col < width.
        """

        return (
            self.height > p.row
            and self.width > p.col
            and p.col >= 0
            and p.row >= 0
        )

    def check_walls(self, p: Point, path_enum: PathEnum) -> bool:
        """Check whether a given wall bit is set on a cell.

        Args:
            p: Cell coordinate to inspect.
            path_enum: Direction enum specifying which wall to test.

        Returns:
            True if the wall bit is set (wall present), False otherwise.
        """

        return (self.maze[p.row][p.col] >> path_enum.value[1]) & 1 == 1

    def place_logo(self) -> None:
        """Try to place a predefined '42' logo at the maze center.

        If the maze is too small the logo is not placed. Cells used by the
        logo are forced to have all walls present.
        """

        if not (self.width >= 9 and self.height >= 7):
            print("Error, can't place 42. Maze too small.")
            return
        h: int = self.height // 2
        w: int = self.width // 2
        self.logo.add(Point(h, w - 1))
        self.logo.add(Point(h, w - 2))
        self.logo.add(Point(h, w - 3))
        self.logo.add(Point(h - 1, w - 3))
        self.logo.add(Point(h - 2, w - 3))
        self.logo.add(Point(h + 1, w - 1))
        self.logo.add(Point(h + 2, w - 1))
        self.logo.add(Point(h, w + 1))
        self.logo.add(Point(h, w + 2))
        self.logo.add(Point(h, w + 3))
        self.logo.add(Point(h - 1, w + 3))
        self.logo.add(Point(h - 2, w + 3))
        self.logo.add(Point(h - 2, w + 2))
        self.logo.add(Point(h - 2, w + 1))
        self.logo.add(Point(h + 1, w + 1))
        self.logo.add(Point(h + 2, w + 1))
        self.logo.add(Point(h + 2, w + 2))
        self.logo.add(Point(h + 2, w + 3))
        if self.entry_point in self.logo or self.exit_point in self.logo:
            print("you can't begin from the 42 symbol")
            self.logo.clear()
            return
        for p in self.logo:
            self.maze[p.row][p.col] = 15

    def generate_maze(self) -> None:
        """Create a new maze and optionally post-process it.

        The core generation is Wilson's algorithm. If the maze is not
        requested to be perfect, a path is found and extra walls are broken
        to introduce loops.
        """

        self.maze = self.init_maze()
        self.place_logo()
        self.wilson_algo()
        if not self.perfect:
            self.find_path()
            self.remove_walls_non_perfect()
            self.path = []
            self.path_str = []

    def break_wall(self, p1: Point, p2: Point, path_enum: PathEnum) -> None:
        """Toggle the wall bits between two adjacent cells.

        Args:
            p1: First cell.
            p2: Second cell.
            path_enum: Direction from p1 to p2.
        """

        bit: int = path_enum.value[0]
        op_bit: int = PathEnum.oppose_bit(bit)
        self.maze[p1.row][p1.col] ^= bit
        self.maze[p2.row][p2.col] ^= op_bit

    def remove_walls_non_perfect(self) -> None:
        """Break a small number of walls on the solution path to
        create loops."""

        valid_points: Set[Point] = set()
        for row in range(self.height):
            for col in range(self.width):
                p: Point = Point(row, col)
                if p not in self.logo:
                    valid_points.add(p)

        n_to_break: int = int(max(5 * (self.width * self.height) // 100, 1))
        for _ in range(n_to_break):
            random_point: Point = sample(tuple(valid_points), 1)[0]

            neighbors: Set[Tuple[PathEnum, Point]] = set()
            for k, v in self.directions.items():
                neighbor: Point = Point.add_points(random_point, v)
                if (
                    self.check_bounds(neighbor)
                    and neighbor not in self.logo
                    and self.check_walls(random_point, k)
                    and self.check_3_by_3(random_point, k, v)
                ):
                    neighbors.add((k, neighbor))

            if len(neighbors) == 0:
                random_point = sample(tuple(valid_points), 1)[0]
                continue

            random_neighbor: Tuple[PathEnum, Point] = sample(tuple(neighbors),
                                                             1)[0]
            self.break_wall(
                random_point, random_neighbor[1], random_neighbor[0])
            try:
                valid_points.remove(random_point)
            except ValueError:
                pass

    def wilson_algo(self) -> None:
        """Generate the maze using Wilson's algorithm
        (loop-erased random walks)."""

        unvisited: Set[Point] = {
            Point(row, col)
            for col in range(self.width)
            for row in range(self.height)
        }
        unvisited.remove(self.entry_point)
        for p in self.logo:
            unvisited.remove(p)
        visited: Set[Point] = {self.entry_point}

        while len(unvisited) >= 1:
            tree: List[Point]
            walls: List[PathEnum]
            tree, walls = self.random_walk(visited, unvisited)

            if not len(tree):
                continue

            for i in range(len(walls)):
                n_point = tree[i + 1]
                self.break_wall(tree[i], n_point, walls[i])
                visited.add(tree[i])
                if tree[i] in unvisited:
                    unvisited.remove(tree[i])

    def random_walk(
        self,
        visited: Set[Point],
        unvisited: Set[Point],
    ) -> Tuple[List[Point], List[PathEnum]]:
        """Perform a loop-erased random walk until it reaches visited set.

        Args:
            visited: Set of already visited points in the maze.
            unvisited: Set of points not yet part of the spanning tree.

        Returns:
            A tuple (tree, walls) where tree is the ordered list of points
            visited during the walk and walls is the list of directions
            taken between consecutive points.
        """

        new_point: Point = sample(tuple(unvisited), 1)[0]
        tree: List[Point] = [new_point]
        tree_index: Dict[Point, int] = {new_point: 0}
        walls: List[PathEnum] = []

        while True:
            neighbors: List[Tuple[PathEnum, Point]] = []
            for k, v in self.directions.items():
                neighbor: Point = Point.add_points(new_point, v)
                if self.check_bounds(neighbor) and neighbor not in self.logo:
                    neighbors.append((k, neighbor))

            if not len(neighbors):
                new_point = sample(tuple(unvisited), 1)[0]
                tree = [new_point]
                tree_index = {new_point: 0}
                assert tree_index.keys() == set(tree)
                continue

            dir_random: Tuple[PathEnum, Point] = choice(neighbors)
            path_enum: PathEnum = dir_random[0]
            new_point = dir_random[1]

            if new_point in tree_index:
                i: int = tree_index[new_point] + 1
                end: int = len(tree)
                tree_to_remove: List[Point] = tree[i:end]
                tree = tree[:i]
                walls = walls[: i - 1]
                assert len(walls) == max(0, len(tree) - 1)
                for p in tree_to_remove:
                    tree_index.pop(p)
                if len(tree) <= 0:
                    return tree, walls
                new_point = tree[-1]
            else:
                tree.append(new_point)
                tree_index.update({new_point: len(tree) - 1})
                walls.append(path_enum)

            if new_point in visited:
                return tree, walls

    def find_path(self) -> Optional[List[Point]]:
        """Find the shortest path between entry and exit using BFS.

        Returns:
            The ordered list of Points forming the path from entry to exit,
            or None if no path exists. The generator's self.path and
            self.path_str are updated when a path is found.
        """

        start: Point = self.entry_point
        end: Point = self.exit_point
        visited: Dict[Point, int] = {start: 0}
        parent: Dict[Point, Tuple[Point, PathEnum]] = {}
        queue: Deque[Point] = deque([start])
        while queue:
            current: Point = queue.popleft()
            if current == end:
                break
            for direction, point in self.directions.items():
                voisin: Point = Point.add_points(current, point)
                if (self.check_walls(current, direction)
                        or not self.check_bounds(voisin)):
                    continue
                if voisin not in visited:
                    visited[voisin] = visited[current] + 1
                    parent[voisin] = (current, direction)
                    queue.append(voisin)
        if end not in visited:
            return None
        current = end
        while current != start:
            self.path.append(current)
            prev_point, move = parent[current]
            self.path_str.append(move.name)
            current = prev_point
        self.path.append(start)
        self.path.reverse()
        self.path_str.reverse()
        return self.path

    def convert_to_hex(self) -> List[List[str]]:
        """Convert the integer maze representation to hexadecimal characters.

        Returns:
            A 2D list where each cell is a single hexadecimal character string
            representing the wall bits for that cell.
        """
        char_hex: str = "0123456789ABCDEF"
        maze: List[List[str]] = [
            [char_hex[value] for value in row] for row in self.maze
        ]
        return maze

    def set_to_file(self) -> None:
        """Write the maze, entry/exit and path string to the output file.

        The maze is written as hexadecimal characters line by line followed
        by the coordinates for entry and exit and the path string.
        """

        path_str: str = "".join(self.path_str)
        maze: List[List[str]] = self.convert_to_hex()
        with open(self.output_file, "w") as fd:
            for row in maze:
                for value in row:
                    fd.write(value)
                fd.write("\n")

            fd.write(f"\n{self.entry_point.row},{self.entry_point.col}")
            fd.write(f"\n{self.exit_point.row},{self.exit_point.col}")
            fd.write(f'\n{"".join(path_str)}')

    def check_north_east(self, p: Point) -> bool:
        """Check the 2x2 area to the north-east of point p for walls.

        Args:
            p: The bottom-left point of the 2x2 area to check.

        Returns:
            True if the 2x2 area has at least one wall, False otherwise.
        """

        all_points: List[Point] = []

        for row in range(2):
            for col in range(2):
                n_p: Point = Point.add_points(p, Point(-row, col))
                if self.check_bounds(n_p):
                    all_points.append(n_p)
                else:
                    return False

        for point in all_points:
            for k, _ in self.directions.items():
                if self.check_walls(point, k):
                    return True

        return False

    def check_north_west(self, p: Point) -> bool:
        """Check that the 2x2 area north-west of point p has at least one wall.

        Args:
            p: The bottom-right point of the 2x2 area to check.

        Returns:
            True if the 2x2 area has at least one wall, False otherwise.
        """

        all_points: List[Point] = []

        for row in range(2):
            for col in range(2):
                n_p: Point = Point.add_points(p, Point(-row, -col))
                if self.check_bounds(n_p):
                    all_points.append(n_p)
                else:
                    return False

        for point in all_points:
            for k, _ in self.directions.items():
                if self.check_walls(point, k):
                    return True

        return False

    def check_south_east(self, p: Point) -> bool:
        """Check the 2x2 area to the south-east of point p for walls.

        Args:
            p: The top-left point of the 2x2 area to check.

        Returns:
            True if the 2x2 area has at least one wall, False otherwise.
        """

        all_points: List[Point] = []

        for row in range(2):
            for col in range(2):
                n_p: Point = Point.add_points(p, Point(row, col))
                if self.check_bounds(n_p):
                    all_points.append(n_p)
                else:
                    return False

        for point in all_points:
            for k, _ in self.directions.items():
                if self.check_walls(point, k):
                    return True

        return False

    def check_south_west(self, p: Point) -> bool:
        """Check that the 2x2 area south-west of point p has at least one wall.

        Args:
            p: The top-right point of the 2x2 area to check.

        Returns:
            True if the 2x2 area has at least one wall, False otherwise.
        """

        all_points: List[Point] = []

        for row in range(2):
            for col in range(2):
                n_p: Point = Point.add_points(p, Point(row, -col))
                if self.check_bounds(n_p):
                    all_points.append(n_p)
                else:
                    return False

        for point in all_points:
            for k, _ in self.directions.items():
                if self.check_walls(point, k):
                    return True

        return False

    def check_3_by_3(self, p: Point, path: PathEnum, dir_point: Point) -> bool:
        """Check that breaking a wall in the given direction from point p does
        not create a 2x2 open area.

        Args:
            p: The point from which the wall would be broken.
            path: The direction in which the wall would be broken.
            dir_point: The point representing the direction vector.

        Returns:
            True if breaking the wall does not create a 2x2 open area,
            False otherwise.
        """

        tmp_maze = [row.copy() for row in self.maze]

        if not self.check_walls(p, path):
            return True

        n_p = Point.add_points(p, dir_point)
        if n_p in self.logo:
            return False

        if (n_p.row >= self.height
            or n_p.col >= self.width
            or n_p.row < 0
                or n_p.col < 0):
            return False

        self.break_wall(p, n_p, path)

        if (
            self.check_north_east(p) and
            self.check_north_west(p) and
            self.check_south_east(p) and
            self.check_south_west(p)
        ):
            self.maze = tmp_maze
            return True

        self.maze = tmp_maze
        return False
