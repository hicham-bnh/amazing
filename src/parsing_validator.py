from typing import Tuple, Optional
from pydantic import BaseModel, field_validator, ValidationInfo


class ParsingValidator(BaseModel):
    width: int
    height: int
    entry_point: Tuple[int, int]
    exit_point: Tuple[int, int]
    perfect: bool
    output_file: str

    @field_validator("width", "height")
    @classmethod
    def check_limit_width_height(cls, value: int) -> int:
        if value <= 0:
            raise ValueError("cannot be less than 1")
        elif value > 120:
            raise ValueError("cannot be above 120")
        return value

    @field_validator("entry_point", "exit_point")
    @classmethod
    def check_limit_entry_exit_point(
        cls,
        case: Tuple[int, int],
        validation: ValidationInfo
    ) -> Tuple[int, int]:
        if case[0] < 0 or case[1] < 0:
            raise ValueError("entry/exit cannot be negative")
        width: Optional[int] = validation.data.get("width")
        height: Optional[int] = validation.data.get("height")
        if (width and case[0] >= width) or (height and case[1] >= height):
            raise ValueError("entry/exit ERROR")
        return case

    @field_validator("exit_point")
    @classmethod
    def check_dif_entry_exit(
        cls,
        value: Tuple[int, int],
        validation: ValidationInfo
    ):
        entry: Optional[Tuple[int, int]] = validation.data.get("entry_point")
        if value and value == entry:
            raise ValueError("the entry cannot be the exit")
        return value

    @field_validator("perfect")
    @classmethod
    def check_perfect(cls, maze: bool) -> bool:
        if not isinstance(maze, bool):
            raise ValueError("Error for perfect : True or False")
        return maze

    @field_validator("output_file")
    @classmethod
    def check_output(cls, file: str) -> str:
        if not isinstance(file, str):
            raise ValueError("file output ERROR")
        return file
