"""Parse maze configuration from a 'config.txt' file.

Provides:
    get_entry_or_exit: Parse a coordinate string "x,y" -> (x, y).
    transform_data: Convert raw string values to proper types.
    get_config: Read and parse the config file into a typed dict.
"""

from typing import Any, Dict, List, Optional, Tuple

from src.parsing_validator import ParsingValidator


def get_entry_or_exit(path: str) -> Tuple[int, int]:
    """Parse a coordinate string "x,y" and return a tuple of ints.

    Args:
        path: Coordinate as a string using a comma separator, e.g. "3,4".

    Returns:
        A tuple (x, y) where both are integers.

    Raises:
        ValueError: If the coordinate does not contain exactly two parts.
        TypeError: If either coordinate part is not an integer string.
    """
    parts: List[str] = [p.strip() for p in path.split(",")]
    if len(parts) != 2:
        raise ValueError(
            "EXIT and/or ENTRY must be like '<int>,<int>' "
            f"received {parts}"
        )

    return int(parts[0]), int(parts[1])


def transform_data(data: Dict[str, Any]) -> None:
    """Transform string values in the config dict to proper Python types.

    This mutates the provided dictionary in place converting:
        - ENTRY and EXIT from 'x,y' strings to (int, int) tuples
        - WIDTH and HEIGHT to ints
        - PERFECT to a boolean (True if value equals "true" ignoring case)

    Args:
        data: Configuration dictionary with raw string values.

    Raises:
        ValueError: If validation fails on the transformed data.
    """
    data["ENTRY"] = get_entry_or_exit(str(data["ENTRY"]))
    data["EXIT"] = get_entry_or_exit(str(data["EXIT"]))
    data["WIDTH"] = int(data["WIDTH"])
    data["HEIGHT"] = int(data["HEIGHT"])
    perfect_raw: str = str(data.get("PERFECT", "")).lower()
    data["PERFECT"] = perfect_raw == "true"

    exit_point: Tuple[int, int] = data["EXIT"]
    data["EXIT"] = (exit_point[1], exit_point[0])
    entry_point: Tuple[int, int] = data["ENTRY"]
    data["ENTRY"] = (entry_point[1], entry_point[0])

    try:
        ParsingValidator(
            width=data["WIDTH"],
            height=data["HEIGHT"],
            entry_point=data["ENTRY"],
            exit_point=data["EXIT"],
            perfect=data["PERFECT"],
            output_file=data["OUTPUT_FILE"]
        )

    except Exception as e:
        raise ValueError(f"transform_data validation error: {e}")


def get_config(file_name: Optional[str] = None) -> Dict[str, Any]:
    """Read and parse 'config.txt' into a typed configuration dictionary.

    The config file must contain lines in the form KEY=VALUE. Lines that
    start with '#' or are empty are ignored.

    Args:
        file_name: Path to the configuration file. Defaults to
            "default_config.txt" if None.

    Returns:
        A dictionary with keys ENTRY, EXIT, WIDTH, HEIGHT, PERFECT (and any
        other keys present) with converted types.

    Raises:
        FileNotFoundError: If the config file does not exist.
        PermissionError: If the file cannot be opened due to permissions.
        IndexError: If a non-comment line does not contain a '=' separator.
        ValueError: If integer conversion for WIDTH/HEIGHT fails.
    """
    if file_name is None:
        file_name = "default_config.txt"
    with open(file_name, "r", encoding="utf-8") as fd:
        content: str = fd.read()

        data: Dict[str, Any] = {}
        for line in content.splitlines():
            line_stripped: str = line.strip()
            if not line_stripped or line_stripped.startswith("#"):
                continue
            if "=" not in line_stripped:
                raise IndexError(
                    f"get_config can't access to value: {line_stripped}")
            key: str
            val: str
            key, val = line_stripped.split("=", 1)
            data[key.strip()] = val.strip()

        transform_data(data)
        return data
