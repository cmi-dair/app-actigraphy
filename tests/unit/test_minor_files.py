"""Test the minor_files module."""
import datetime
import pathlib

import pytest

from actigraphy.core import utils
from actigraphy.io import minor_files


def test_write_sleeplog(tmp_path: pathlib.Path) -> None:
    """Test write_ggir function."""
    filepath = tmp_path / "test_ggir.csv"
    file_manager = utils.FileManager(str(tmp_path))

    minor_files.write_sleeplog(file_manager.__dict__)
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    assert lines[0] == "ID,onset_N1,wakeup_N1\n"
    assert lines[1] == "identifier,2023-10-10 23:00:00,2023-10-11 07:00:00\n"


def test_write_vector(tmp_path: pathlib.Path) -> None:
    """Test the write_vector function."""
    sample_vector = [1, 2, 3, 4, 5]
    expected = "1,2,3,4,5\n"
    vector_path = tmp_path / "test_vector.csv"

    minor_files.write_vector(str(vector_path), sample_vector)
    with open(vector_path, encoding="utf-8") as file_buffer:
        actual = file_buffer.read()

    assert actual == expected


@pytest.fixture()
def patch_datetime_now(monkeypatch: pytest.MonkeyPatch) -> datetime.datetime:
    """Patch `datetime.now()` return a fixed datetime object.

    Args:
        monkeypatch: A pytest monkeypatch fixture object.

    Returns:
        datetime.datetime: A datetime object representing the fixed datetime
            value that `datetime.now()` will return after patching.

    Example usage:
        def test_something(monkeypatch):
            fixed_datetime = patch_datetime_now(monkeypatch)
            # ... test code that uses datetime.now() ...
    """

    class MyDateTime(datetime.datetime):
        @classmethod
        # type: ignore[override] # Intentional override without args
        def now(cls) -> datetime.datetime:  # pylint: disable=arguments-differ
            return datetime.datetime(2021, 1, 1)

    monkeypatch.setattr(datetime, "datetime", MyDateTime)
    return datetime.datetime(2021, 1, 1)


def test_flatten() -> None:
    """Test the flatten function."""
    expected = [1, 2, "abc", b"abc", 5, 6]

    actual = minor_files._flatten([[1, 2], [["abc", b"abc"], [5, 6]]])

    assert actual == expected
