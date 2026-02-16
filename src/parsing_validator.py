"""Validation helpers for CLI/config parsing.

This module provides a Pydantic BaseModel used to validate maze configuration
parameters (width, height, entry/exit points, perfect, output file). All
validators include Google-style docstrings and explicit typing.
"""
from typing import Tuple, Optional
from pydantic import BaseModel, field_validator, ValidationInfo


class ParsingValidator(BaseModel):
    """Pydantic model validating maze configuration inputs.

    Attributes:
        width: Maze width in cells.
        height: Maze height in cells.
        entry_point: (row, col) tuple for entry cell.
        exit_point: (row, col) tuple for exit cell.
        perfect: Whether the maze must be perfect (no loops).
        output_file: Path to the output file.
    """

    width: int
    height: int
    entry_point: Tuple[int, int]
    exit_point: Tuple[int, int]
    perfect: bool
    output_file: str

    @field_validator("width", "height")
    @classmethod
    def check_limit_width_height(cls, value: int) -> int:
        """Validate width and height limits.

        Args:
            value: The value provided for width or height.

        Returns:
            The validated value.

        Raises:
            ValueError: If the value is less than 1 or greater than 120.
        """
        if value <= 0:
            raise ValueError("cannot be less than 1")
        if value > 120:
            raise ValueError("cannot be above 120")
        return value

    @field_validator("entry_point", "exit_point")
    @classmethod
    def check_limit_entry_exit_point(
        cls,
        case: Tuple[int, int],
        validation: ValidationInfo,
    ) -> Tuple[int, int]:
        """Validate entry/exit coordinates are non-negative and in bounds.

        Args:
            case: Tuple of (row, col) for entry or exit.
            validation: Pydantic ValidationInfo providing access to
            other fields.

        Returns:
            The validated (row, col) tuple.

        Raises:
            ValueError: If coordinates are negative or out of
            configured bounds.
        """
        if case[0] < 0 or case[1] < 0:
            raise ValueError("entry/exit cannot be negative")
        width: Optional[int] = validation.data.get("width")
        height: Optional[int] = validation.data.get("height")
        if (width is not None and case[0] >= width) or (
            height is not None and case[1] >= height
        ):
            raise ValueError("entry/exit ERROR")
        return case

    @field_validator("exit_point")
    @classmethod
    def check_dif_entry_exit(
        cls,
        value: Tuple[int, int],
        validation: ValidationInfo,
    ) -> Tuple[int, int]:
        """Ensure the exit point is not identical to the entry point.

        Args:
            value: The exit point (row, col).
            validation: Pydantic ValidationInfo providing access to
            other fields.

        Returns:
            The validated exit point.

        Raises:
            ValueError: If the exit equals the entry.
        """
        entry: Optional[Tuple[int, int]] = validation.data.get("entry_point")
        if value and entry is not None and value == entry:
            raise ValueError("the entry cannot be the exit")
        return value

    @field_validator("perfect")
    @classmethod
    def check_perfect(cls, maze: bool) -> bool:
        """Validate that 'perfect' is a boolean.

        Args:
            maze: The provided perfect flag.

        Returns:
            The validated boolean value.

        Raises:
            ValueError: If the provided value is not a boolean.
        """
        if not isinstance(maze, bool):
            raise ValueError("Error for perfect : True or False")
        return maze

    @field_validator("output_file")
    @classmethod
    def check_output(cls, file: str) -> str:
        """Validate output file is a string.

        Args:
            file: The provided output file path.

        Returns:
            The validated file path string.

        Raises:
            ValueError: If the provided value is not a string.
        """
        if not isinstance(file, str):
            raise ValueError("file output ERROR")
        return file
