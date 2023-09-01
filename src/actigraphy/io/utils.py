"""Utility functions for the actigraphy.io module."""
import csv
import enum
import itertools
import pathlib
import re
from typing import Any

import rdata


class Weekdays(str, enum.Enum):
    """Enum for weekdays."""

    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


def rdata_to_datadict(filepath: str | pathlib.Path) -> dict[str, Any]:
    """Converts an Rdata file to a pandas dataframe.

    Args:
        filepath: The path to the Rdata file.

    Returns:
        np.ndarray: The numpy array.
    """
    data = rdata.parser.parse_file(filepath)
    return rdata.conversion.convert(data)


def snakecase(string: str) -> str:
    """Converts a string to snake case. Consecutive uppercase letters
    do not receive underscores between them.

    Args:
        string: The string to convert.

    Returns:
        The converted string.
    """
    return re.sub(r"(?<=[A-Z])(?!$)(?!_)(?![A-Z])", "_", string[::-1]).lower()[::-1]


def flatten(list_of_lists: list[Any]) -> list[Any]:
    """Recursively flattens a list of lists into a single list.

    Args:
        list_of_lists: The list of lists to flatten.

    Returns:
        list[any]: The flattened list.
    """
    new_list = []
    for item in list_of_lists:
        if isinstance(item, list):
            new_list.extend(flatten(item))
        else:
            new_list.append(item)
    return new_list


def read_one_line_from_csv_file(filepath: str, line_number: int) -> list[str]:
    """Reads one line from a .csv file in a memory efficient way.

    Args:
        line_number: The line number to read from the file.

    Returns:
        list[str]: A list of strings representing the contents of the line read
            from the file.

    Notes:
        Is using itertools for memory-efficient access overkill? Yes. But
        separating this functionality into its own function makes other
        functions easier to read.
    """
    with open(filepath, "r", encoding="utf-8") as file_buffer:
        reader = csv.reader(file_buffer)
        return next(itertools.islice(reader, line_number, None))
