"""Utility functions for the actigraphy.io module."""
import csv
import itertools
from collections import abc
from typing import Any, Iterable


def flatten(iterable_of_iterables: Iterable[Any]) -> list[Any]:
    """Recursively flattens an iterable of iterables into a single list.

    Args:
        iterable_of_iterables: The list of lists to flatten.

    Returns:
        list[any]: The flattened list.
    """
    new_list = []
    for item in iterable_of_iterables:
        if isinstance(item, abc.Iterable) and not isinstance(item, (str, bytes)):
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
