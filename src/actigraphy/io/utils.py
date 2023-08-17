"""Utility functions for the actigraphy.io module."""
import enum
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


def snakecase(s: str) -> str:
    """Converts a string to snake case. If the input is all uppercase,
    it is converted to all lowercase.

    Args:
        s: The string to convert.

    Returns:
        The converted string.
    """
    if all(character.isupper() for character in s if character.isalpha()):
        return s.lower()
    return re.sub(r"(?<!^)(?<!_)(?=[A-Z])", "_", s).lower()
