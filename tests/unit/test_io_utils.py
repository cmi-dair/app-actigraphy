"""Tests for the io utilities module."""
import os
import tempfile

from pytest import mark

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


@mark.skipif(is_windows(), reason="Not supported on Windows.")  # type: ignore[misc]
def test_read_one_line_from_csv_file() -> None:
    """Test the read_one_line_from_csv_file function."""
    expected = ["1", "2", "3"]
    with tempfile.NamedTemporaryFile() as file_buffer:
        file_buffer.write(b"a,b,c\n1,2,3")
        file_buffer.seek(0)

        actual = utils.read_one_line_from_csv_file(file_buffer.name, 1)

    assert actual == expected
