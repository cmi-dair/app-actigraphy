"""Tests for the io utilities module."""
import os
import pathlib

from actigraphy.io import utils


def is_windows() -> bool:
    """Returns True if the current operating system is Windows, False
    otherwise."""
    return os.name == "nt"


def test_flatten() -> None:
    """Test the flatten function."""
    expected = [1, 2, "abc", b"abc", 5, 6]

    actual = utils.flatten([[1, 2], [["abc", b"abc"], [5, 6]]])

    assert actual == expected


def test_read_one_line_from_csv_file(tmp_path: pathlib.Path) -> None:
    """Test the read_one_line_from_csv_file function."""
    expected = ["1", "2", "3"]

    test_file = tmp_path / "test.csv"
    test_file.write_text("a,b,c\n1,2,3")

    actual = utils.read_one_line_from_csv_file(str(test_file), 1)

    assert actual == expected
