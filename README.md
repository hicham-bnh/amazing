_This project has been created as part of the 42 curriculum by tchemin, mobenhab._

# A-Maze-ing — Maze generator

## Table of contents

- [Description](#description)
- [Instructions](#instructions)
  - [Prerequisites](#prerequisites)
  - [Common Makefile commands](#common-makefile-commands)
- [Quick example](#quick-example)
- [Reusable module (mazegen)](#reusable-module-mazegen)
- [Configuration file example](#configuration-file-example)
- [Maze generation algorithm](#maze-generation-algorithm)
- [Maze resolution algorithm](#maze-resolution-algorithm)
- [Reusability details](#reusability-details)
- [Building the package](#building-the-package)
- [Resources](#resources)
- [AI usage](#ai-usage)
- [Team & project management](#team--project-management)
- [Tests and quality checks](#tests-and-quality-checks)

## Description

A-Maze-ing is a small Python project that generates perfect mazes (no cycles, a single path between any two cells) and provides at least one solution path. The generator is delivered as a single reusable module so it can be imported into other projects or packaged for pip distribution (package name: mazegen-\*).

## Instructions

Prerequisites

- Python 3.10+
- make (to use the provided Makefile)

Common Makefile commands

- make setup — create a virtual environment in .venv and install build tools
- make install — install project dependencies (attempts dependencies/requirements.txt)
- make run FILE=path/to/output — run the main script (main.py); optional FILE arg passed to script
- make debug — run main.py under pdb
- make build — build the package (creates dist/ with .tar.gz and .whl)
- make clean / fclean — remove build artifacts and virtualenv

Quick example

- Create environment and install tools:
  - make setup
  - source .venv/bin/activate
- Install dependencies:
  - make install
- Build a package:
  - make build
  - Expected output example: dist/mazegen-1.0.0-py3-none-any.whl (actual filename depends on package metadata)

## Reusable module (mazegen)

The reusable component is provided as a single module intended for packaging as mazegen-\*. The module exposes a MazeGenerator class that encapsulates maze creation, access to the grid, and at least one solution.

If you are using **VSCode** and want access to docstrings and args, try **relaunching** your VSCode or put this in your **settings.json**

```JSON
{
  "python.analysis.useLibraryCodeForTypes": true
}
```

Basic usage example

```python
from mazegen import MazeGenerator

# Instantiate using the real constructor: (height, width, entry_point, exit_point, output_file, perfect)
mg = MazeGenerator(
    height=11,
    width=21,
    entry_point=(0, 1),
    exit_point=(10, 19),
    output_file="maze.txt",
    perfect=True,
)
# Generate the maze (method name in the module)
mg.generate_maze()

# Access the internal representation and the found path
maze_grid = mg.maze        # 2D list of ints (bitmask per cell)
solution_path = mg.path    # list of Point objects from entry to exit
solution_steps = mg.path_str  # list of direction names (strings)

# Convert to hex chars and write to file using provided helpers
hex_grid = mg.convert_to_hex()
mg.set_to_file()
```

**Constructor parameters (actual)**

- height (int): number of rows
- width (int): number of columns
- entry_point (tuple[int, int]): (row, col) for the entry cell
- exit_point (tuple[int, int]): (row, col) for the exit cell
- output_file (str): output filepath for set_to_file()
- perfect (bool): True -> perfect maze (no extra loops)

**Primary methods and attributes (actual)**

- generate_maze(): run the full generation flow (init, place logo, wilson_algo, optional postprocessing)
- maze: internal 2D list of ints representing cell wall bitmasks
- path: list[Point] representing the found path (set by find_path)
- path_str: list[str] of direction names corresponding to the path
- convert_to_hex(): return a 2D list of hex characters for each cell
- set_to_file(): write the hex maze and entry/exit/path info to output_file

**Data formats**

- grid: list of rows, indexable as grid[y][x]. Typical values: 0 => path, 1 => wall.
- solution: ordered list of (x, y) tuples from entrance to exit.

Note: The module exposes the internal grid format which may differ from output formats (text, JSON, image). Use provided exporters if available.

## Configuration file example

An optional txt config accepted by MazeGenerator.from_dict (keys expected by the module):

default_config.txt

```
  HEIGHT=11
  WIDTH=21
  ENTRY=0,1
  EXIT=10,19
  OUTPUT_FILE=maze.txt
  PERFECT=true
```

## Maze generation algorithm

Algorithm: Wilson's algorithm (loop-erased random walk) — produces a uniform spanning tree.

**Overview:**

- Start with a root node (for example the `entry_point`) and treat it as the initial tree. For each remaining cell not yet in the tree, perform an independent random walk until it first hits a cell that is already part of the tree. During the walk, erase any loops (i.e., apply loop-erasure) so the recorded path contains no cycles. Add the resulting loop-erased path to the tree. Repeat until every cell belongs to the tree.

**Characteristics and complexity:**

- Produces a uniformly random spanning tree over the grid graph, which means every possible perfect maze (spanning tree) is equally likely.
- Time/space: performance depends on the graph and random-walk mixing times; for typical maze sizes Wilson's algorithm is practical and fast. Memory usage is O(N) for storing the final tree and transient path buffers.

**Why this algorithm was chosen:**

- Uniform randomness: Wilson guarantees unbiased sampling of spanning trees, desirable when you want every perfect maze to be equally likely.
- Robust and deterministic with a fixed RNG seed: results are reproducible when seeding the RNG.
- Works well with the project's layout and the included `mlx` wheel: it integrates cleanly with post-processing and optional non-perfect variants.

## Maze resolution algorithm

Primary method: Breadth-First Search (BFS) as implemented in `find_path`.

**Overview:**

- The resolver performs a BFS from the `entry_point` to the `exit_point` over the maze graph where vertices are cells and edges exist when there is no wall between two adjacent cells. A `deque` queue is used to explore cells by increasing distance from the start.
- Traversal respects walls by checking the cell bitmask with `check_walls` and bounds with `check_bounds` so only open passages are followed.

**Behavior and outputs:**

- If a path exists, `find_path` reconstructs the shortest path using a `parent` map (child -> (parent, direction)). It sets `self.path` to an ordered list of `Point` objects from entry to exit and `self.path_str` to the corresponding list of direction names (e.g. `['E','S','S',...]`). The method returns the `self.path` list.
- If no path is found, the method returns `None`.

**Complexity and rationale:**

- Time complexity: O(N) where N is the number of cells (each cell visited at most once by BFS).
- Space complexity: O(N) for the `visited`/`parent` structures and the queue.
- BFS was chosen because it finds the shortest path (fewest steps) in an unweighted grid, is simple to implement, and integrates cleanly with the internal bitmask representation of walls.

**Notes:**

- `find_path` also fills `self.path_str` with direction names (used by exporters) and is used during non-perfect post-processing (when `perfect=False`) to create loops safely.

## Reusability details

- The reusable unit is the MazeGenerator class in a single file (e.g., mazegen.py) placed at the repository root and designed to be packaged.
- The package name should follow the mazegen-\_ convention. After building (make build) the distribution files in dist/ can be installed via pip (pip install dist/mazegen-1.0.0-py3-none-any.whl).
- Reusable parts:
  - MazeGenerator (API for generation and access)

## Building the package

1. Create and activate a virtualenv:
   - make setup
   - source .venv/bin/activate
2. Install build tools and dependencies:
   - make install
3. Build the distribution:
   - make build
   - artifacts will be in dist/ (both .tar.gz and .whl as generated by Python build tools)
4. Install locally to test:
   - pip install dist/mazegen-\*.whl
   - Or, to install the built wheels (package wheel plus bundled wheel) from the virtualenv, run:
     - `./.venv/bin/python -m pip install mazegen-1.0.0-py3-none-any.whl path/to/package/mazegen/_wheels/mlx-2.2-py3-none-any.whl`
       This installs both the package wheel and the bundled `mlx` wheel.

## Resources

- Tutorials on maze generation (Recursive Backtracker)
- Algorithm references (generic algorithms textbooks and online articles)
- Wilson, D. B. (1996). Generating random spanning trees more quickly than the cover time.
- Python packaging guide: https://packaging.python.org/
- setuptools docs: https://setuptools.pypa.io/
- mypy docs (module layout): https://mypy.readthedocs.io/

AI usage

- An AI assistant was used to draft the README content. The maze algorithm implementation and validation were done by the project authors.

## Team & project management

- **Contributors:** mobenhab, tchemin
- **Timeline:**
  - Day 1: research and algorithm selection
  - Day 2–3: implementation of MazeGenerator
  - Day 4: tests and packaging
  - Day 5: documentation and final adjustments

**Work distribution:**

- mobenhab:
  - Find path
  - Put maze on screen using MLX
  - Data validation
- tchemin:
  - Maze generation
  - Building package
  - Put maze on screen using MLX

**What went well**

- Clear modular design with a single reusable module.
  Improvements

## Tests and quality checks

- The Makefile includes targets for linting (flake8, mypy) and building. Run make lint to check static quality.
- Add unit tests in tests/ and run with pytest.

---
