"""Test the minor_files module."""
import csv
import datetime
import os
import pathlib

import pytest
from pytest_mock import plugin

from actigraphy.io import minor_files


def test_read_sleeplog(mocker: plugin.MockerFixture) -> None:
    """Mock the utility function."""
    mocker.patch(
        "actigraphy.io.utils.read_one_line_from_csv_file",
        return_value=["Identifier", "23:00", "07:00", "23:30", "07:30"],
    )

    sleep, wake = minor_files.read_sleeplog("dummy_filepath.csv")

    assert sleep == ["23:00", "23:30"]
    assert wake == ["07:00", "07:30"]


def test_read_sleeplog_empty_file(mocker: plugin.MockerFixture) -> None:
    """Mock the utility function for an empty file."""
    mocker.patch("actigraphy.io.utils.read_one_line_from_csv_file", return_value=[])

    with pytest.raises(ValueError, match="The sleep log file is empty."):
        minor_files.read_sleeplog("dummy_filepath.csv")


def test_read_sleeplog_odd_entries(mocker: plugin.MockerFixture) -> None:
    """Mock the utility function with an odd number of entries."""
    mocker.patch(
        "actigraphy.io.utils.read_one_line_from_csv_file",
        return_value=["Identifier", "23:00", "07:00", "23:30"],
    )

    with pytest.raises(
        ValueError,
        match="The sleep log file has an odd number of entries.",
    ):
        minor_files.read_sleeplog("dummy_filepath.csv")


def test_modify_sleeplog(tmp_path: pathlib.Path, mocker: plugin.MockerFixture) -> None:
    """Test modify_sleeplog function."""
    file_manager = {
        "sleeplog_file": str(tmp_path / "test_sleeplog.csv"),
        "identifier": "test_identifier",
    }
    mocker.patch("actigraphy.io.data_import.get_dates", return_value=["2023-10-10"])
    mocker.patch("actigraphy.core.utils.point2time", side_effect=["23:00", "07:00"])
    mocker.patch(
        "actigraphy.io.data_import.get_timezone",
        return_value=datetime.UTC,
    )
    # Initialize file
    with open(file_manager["sleeplog_file"], "w", encoding="utf-8") as file_buffer:
        file_buffer.write("Dummy, first, line\n")
        file_buffer.write("Dummy, second, line\n")

    minor_files.modify_sleeplog(file_manager, 0, 23.0, 7.0)

    with open(file_manager["sleeplog_file"], encoding="utf-8") as f:
        lines = f.readlines()
        assert "test_identifier" in lines[1]
        assert "23:00" in lines[1]
        assert "07:00" in lines[1]


def test_write_sleeplog(tmp_path: pathlib.Path) -> None:
    """Test write_ggir function."""
    date_vector = [
        datetime.datetime(2023, 10, 10, 23, 0),
        datetime.datetime(2023, 10, 11, 7, 0),
        datetime.datetime(2023, 10, 11, 23, 0),
        datetime.datetime(2023, 10, 12, 7, 0),
    ]
    filepath = tmp_path / "test_ggir.csv"

    minor_files.write_sleeplog(date_vector, str(filepath))
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    assert lines[0] == "ID,onset_N1,wakeup_N1\n"
    assert lines[1] == "identifier,2023-10-10 23:00:00,2023-10-11 07:00:00\n"


def test_write_log_file(tmp_path: pathlib.Path) -> None:
    """Test write_log_file function."""
    today = datetime.date.today()
    filepath = tmp_path / "test_log.csv"

    minor_files.write_log_file("JohnDoe", str(filepath), "test_identifier")
    with open(filepath, encoding="utf-8") as f:
        lines = f.readlines()

    assert lines[0] == "Username,Participant,Date,Filename\n"
    assert lines[1] == f"JohnDoe,test_identifier,{today},sleeplog_test_identifier.csv\n"


def test_write_vector(tmp_path: pathlib.Path) -> None:
    """Test the write_vector function."""
    sample_vector = [1, 2, 3, 4, 5]
    expected = "1,2,3,4,5\n"
    vector_path = tmp_path / "test_vector.csv"

    minor_files.write_vector(str(vector_path), sample_vector)
    with open(vector_path, encoding="utf-8") as file_buffer:
        actual = file_buffer.read()

    assert actual == expected


def test_read_vector(tmp_path: pathlib.Path) -> None:
    """Test the read_vector function."""
    vector_path = tmp_path / "test_vector.csv"
    expected = ["1", "2", "3", "4", "5"]
    with open(vector_path, "w", encoding="utf-8") as file_buffer:
        file_buffer.write(",".join(expected))

    read_result = minor_files.read_vector(str(vector_path))

    assert read_result == expected


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


def test_write_log_analysis_completed(
    tmp_path: pathlib.Path,
    patch_datetime_now: datetime.datetime,  # pylint: disable=redefined-outer-name
) -> None:
    """Test the write_log_analysis_completed function."""
    identifier = "test_participant"
    is_completed = True
    test_file = tmp_path / "test_log.csv"
    expected_header = [
        "Participant",
        "Is the sleep log analysis completed?",
        "Last modified",
    ]
    expected_data = [identifier, "Yes", str(patch_datetime_now)]

    minor_files.write_log_analysis_completed(is_completed, identifier, str(test_file))

    with open(test_file, encoding="utf-8") as file_buffer:
        reader = csv.reader(file_buffer)
        header_row = next(reader)
        data_row = next(reader)

    assert header_row == expected_header
    assert data_row == expected_data


def test_initialize_files(tmp_path: pathlib.Path, mocker: plugin.MockerFixture) -> None:
    """Test the initialize_files function."""
    mocker.patch("actigraphy.io.data_import.get_dates", return_value=[None, None])
    mocker.patch(
        "actigraphy.core.utils.point2time",
        return_value=[str(datetime.datetime.now())],
    )
    mocker.patch("actigraphy.io.data_import.get_daycount", return_value=1)
    mocker.patch(
        "actigraphy.io.data_import.get_timezone",
        return_value=datetime.UTC,
    )
    file_manager = {
        "base_dir": str(tmp_path),
        "sleeplog_file": os.path.join(str(tmp_path), "sleeplog.csv"),
        "review_night_file": os.path.join(str(tmp_path), "review_night.csv"),
        "multiple_sleeplog_file": os.path.join(str(tmp_path), "multiple_sleeplog.csv"),
        "data_cleaning_file": os.path.join(str(tmp_path), "data_cleaning.csv"),
        "missing_sleep_file": os.path.join(str(tmp_path), "missing_sleep.csv"),
        "log_file": os.path.join(str(tmp_path), "log.csv"),
        "identifier": "test_identifier",
    }
    evaluator_name = "test_evaluator"

    minor_files.initialize_files(file_manager, evaluator_name)

    for key, filepath in file_manager.items():
        if key != "identifier":
            assert os.path.exists(filepath)
    with open(file_manager["sleeplog_file"], encoding="utf-8") as file_buffer:
        content = file_buffer.read()
        assert "ID,onset_N1,wakeup_N1\nidentifier," in content
    with open(file_manager["log_file"], encoding="utf-8") as file_buffer:
        content = file_buffer.read()
        assert evaluator_name in content
