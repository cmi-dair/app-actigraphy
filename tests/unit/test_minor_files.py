"""Test the ggir_files module."""
import pathlib

from actigraphy.io import ggir_files


def test_write_sleeplog(tmp_path: pathlib.Path, file_manager: dict[str, str]) -> None:
    """Test write_ggir function."""
    filepath = tmp_path / "test_ggir.csv"

    file_manager["sleeplog_file"] = str(filepath)
    ggir_files.write_sleeplog(file_manager)
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    assert lines[0] == "ID,onset_N1,wakeup_N1\n"
    assert (
        lines[1] == "identifier,1993-08-26 12:00:00+00:00,1993-08-26 13:00:00+00:00\n"
    )


def test_write_vector(tmp_path: pathlib.Path) -> None:
    """Test the write_vector function."""
    sample_vector = [1, 2, 3, 4, 5]
    expected = "1,2,3,4,5\n"
    vector_path = tmp_path / "test_vector.csv"

    ggir_files.write_vector(str(vector_path), sample_vector)
    with open(vector_path, encoding="utf-8") as file_buffer:
        actual = file_buffer.read()

    assert actual == expected


def test_flatten() -> None:
    """Test the flatten function."""
    expected = [1, 2, "abc", b"abc", 5, 6]

    actual = ggir_files._flatten([[1, 2], [["abc", b"abc"], [5, 6]]])

    assert actual == expected
