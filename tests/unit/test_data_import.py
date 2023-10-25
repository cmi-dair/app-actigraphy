"""Unit tests for the data_import module."""
# pylint: disable=protected-access
# pylint: disable=redefined-outer-name
import datetime
import pathlib
from typing import Any

import pytest
from pytest_mock import plugin

from actigraphy.io import data_import, metadata


def test_get_data_file_one_file(tmp_path: pathlib.Path) -> None:
    """Test that the function returns the correct file when there is only one file."""
    tmp_file = tmp_path / "test.RData"
    tmp_file.touch()

    actual = data_import._get_data_file(tmp_path)

    assert actual == tmp_file


def test_get_data_file_multiple_files(tmp_path: pathlib.Path) -> None:
    """Test that the function raises an error when there are multiple files."""
    tmp_file = tmp_path / "test.RData"
    tmp_file.touch()
    extra_file = tmp_path / "extra.RData"
    extra_file.touch()
    with pytest.raises(ValueError, match="Expected one data file"):
        data_import._get_data_file(tmp_path)


def test_get_data_file_no_files(tmp_path: pathlib.Path) -> None:
    """Test that the function raises an error when there are no files."""
    with pytest.raises(ValueError, match="Expected one data file"):
        data_import._get_data_file(tmp_path)


def test_get_metadata(mocker: plugin.MockerFixture, tmp_path: pathlib.Path) -> None:
    """Test that get_metadata reads from the correct file."""
    meta_dir = tmp_path / "meta" / "basic"
    meta_dir.mkdir(parents=True)
    meta_file = meta_dir / "metadata.RData"
    meta_file.touch()
    mock_metadata = mocker.Mock(spec=metadata.MetaData)
    mocker.patch(
        "actigraphy.io.metadata.MetaData.from_file",
        return_value=mock_metadata,
    )

    actual = data_import.get_metadata(tmp_path)

    # pylint: disable=no-member
    metadata.MetaData.from_file.assert_called_once_with(meta_file)  # type: ignore[attr-defined]
    assert actual == mock_metadata


def test_get_metadata_no_file(tmp_path: pathlib.Path) -> None:
    """Test that get_metadata raises an error when the metadata file is missing."""
    with pytest.raises(ValueError, match="Expected one data file"):
        data_import.get_metadata(tmp_path)


def test_get_time() -> None:
    """Test that get_time correctly parses time strings."""
    times = ("2020-01-01T12:00:00+0000", "2020-01-01T13:00:00+0000")
    expected = [
        datetime.datetime(2020, 1, 1, 12, 0, tzinfo=datetime.UTC),
        datetime.datetime(2020, 1, 1, 13, 0, tzinfo=datetime.UTC),
    ]

    actual = data_import.get_time(times)

    assert actual == expected


def test_get_midnights(mocker: plugin.MockerFixture) -> None:
    """Test get_midnights with mocked metadata and time data."""
    mock_metadata = mocker.Mock(spec=metadata.MetaData)
    mock_metadata.m = mocker.Mock()
    mock_metadata.m.metashort = mocker.Mock()
    mock_metadata.m.metashort.timestamp = [
        "2022-10-15T23:59:59+0000",
        "2022-10-16T00:00:00+0000",
    ]
    mocker.patch("actigraphy.io.data_import.get_metadata", return_value=mock_metadata)
    mocked_times = [
        datetime.datetime(2022, 10, 15, 23, 59, 59, tzinfo=datetime.UTC),
        datetime.datetime(2022, 10, 16, 0, 0, 0, tzinfo=datetime.UTC),
        datetime.datetime(2022, 10, 16, 0, 0, 1, tzinfo=datetime.UTC),
    ]
    mocker.patch("actigraphy.io.data_import.get_time", return_value=mocked_times)

    actual = data_import.get_midnights("base_dir")

    data_import.get_metadata.assert_called_once_with("base_dir")  # type: ignore[attr-defined]
    assert actual == [2]


def test_get_daycount(mocker: plugin.MockerFixture) -> None:
    """Test get_daycount with mocked get_midnights data."""
    mocker.patch("actigraphy.io.data_import.get_midnights", return_value=[1, 2, 3])
    expected_days = 4

    actual = data_import.get_daycount("base_dir")

    data_import.get_midnights.assert_called_once_with("base_dir")  # type: ignore[attr-defined]
    assert actual == expected_days


def test_get_n_points_per_day(mocker: plugin.MockerFixture) -> None:
    """Test get_n_points_per_day with mocked metadata."""
    mock_metadata = mocker.Mock(spec=metadata.MetaData)
    mock_metadata.m = mocker.Mock()
    mock_metadata.m.windowsizes = [30]
    mocker.patch("actigraphy.io.data_import.get_metadata", return_value=mock_metadata)
    file_manager = {"base_dir": "base_dir"}
    expected_points = 2880

    actual = data_import.get_n_points_per_day(file_manager)

    data_import.get_metadata.assert_called_once_with("base_dir")  # type: ignore[attr-defined]
    assert actual == expected_points


def test_get_dates(mocker: plugin.MockerFixture) -> None:
    """Test get_dates with mocked metadata and time data."""
    mock_metadata = mocker.Mock(spec=metadata.MetaData)
    mock_metadata.m = mocker.Mock()
    mock_metadata.m.metashort = mocker.Mock()
    mock_metadata.m.metashort.timestamp = [
        "2022-10-15T12:34:56+0000",
        "2022-10-16T12:34:56+0000",
    ]
    mocker.patch("actigraphy.io.data_import.get_metadata", return_value=mock_metadata)
    mocked_times = [
        datetime.datetime(2022, 10, 15, 12, 34, 56, tzinfo=datetime.UTC),
        datetime.datetime(2022, 10, 16, 12, 34, 56, tzinfo=datetime.UTC),
    ]
    mocker.patch("actigraphy.io.data_import.get_time", return_value=mocked_times)
    file_manager = {"base_dir": "base_dir"}

    actual = data_import.get_dates(file_manager)

    data_import.get_metadata.assert_called_once_with("base_dir")  # type: ignore[attr-defined]
    assert actual == [datetime.date(2022, 10, 15), datetime.date(2022, 10, 16)]


def test_extend_data_prepend() -> None:
    """Test _extend_data with action set to 'prepend'."""
    data = [1, 2, 3]
    extension = [4, 5, 6]

    actual = data_import._extend_data(data, extension, "prepend")

    assert actual == [4, 5, 6, 1, 2, 3]


def test_extend_data_append() -> None:
    """Test _extend_data with action set to 'append'."""
    data = [1, 2, 3]
    extension = [4, 5, 6]

    actual = data_import._extend_data(data, extension, "append")

    assert actual == [1, 2, 3, 4, 5, 6]


def test_extend_data_no_action() -> None:
    """Test _extend_data with no action specified."""
    data = [1, 2, 3]
    extension = [4, 5, 6]

    actual = data_import._extend_data(data, extension)

    assert actual == [1, 2, 3]


def test_extend_data_invalid_action() -> None:
    """Test _extend_data with an invalid action specified."""
    data = [1, 2, 3]
    extension = [4, 5, 6]

    with pytest.raises(ValueError, match="Invalid action"):
        data_import._extend_data(data, extension, "invalid")


@pytest.mark.parametrize(
    ("data", "extension", "expected"),
    [
        ([], [7, 8, 9], [7, 8, 9]),
        ([1, 2, 3], [], [1, 2, 3]),
        ([], [], []),
    ],
)
def test_extend_data_edge_cases(
    data: list[Any],
    extension: list[Any],
    expected: list[Any],
) -> None:
    """Test _extend_data with various edge cases."""
    actual = data_import._extend_data(data, extension, "prepend")

    assert actual == expected


def test_adjust_for_daylight_savings_no_change() -> None:
    """Test _adjust_timepoint_for_daylight_savings when no adjustment is needed."""
    start = 0
    end = 24 * 3600 - 1
    window_size = 1

    actual = data_import._adjust_timepoint_for_daylight_savings(start, end, window_size)

    assert actual == end


def test_adjust_for_daylight_savings_add_hour() -> None:
    """Test _adjust_timepoint_for_daylight_savings when an hour needs to be added."""
    start = 0
    end = 23 * 3600 - 1
    window_size = 1
    expected = end + 3600

    actual = data_import._adjust_timepoint_for_daylight_savings(start, end, window_size)

    assert actual == expected


def test_adjust_for_daylight_savings_subtract_hour() -> None:
    """Test functioning when an hour needs to be subtracted."""
    start = 0
    end = 25 * 3600 - 1
    window_size = 1
    expected = end - 3600

    actual = data_import._adjust_timepoint_for_daylight_savings(start, end, window_size)

    assert actual == expected


def test_adjust_for_daylight_savings_invalid_window_size() -> None:
    """Test _adjust_timepoint_for_daylight_savings with an invalid window size."""
    start = 0
    end = 24 * 3600 - 1
    window_size = 0

    with pytest.raises(ZeroDivisionError):
        data_import._adjust_timepoint_for_daylight_savings(start, end, window_size)


def test_day_start_and_end_time_points_first_day(mocker: plugin.MockerFixture) -> None:
    """Test the _day_start_and_end_time_points function for the first day."""
    mock_get_midnights = mocker.patch(
        "actigraphy.io.data_import.get_midnights",
        autospec=True,
    )
    mock_adjust_timepoint_for_daylight_savings = mocker.patch(
        "actigraphy.io.data_import._adjust_timepoint_for_daylight_savings",
        autospec=True,
    )
    mock_get_midnights.return_value = [
        3600,
        7200,
    ]
    mock_adjust_timepoint_for_daylight_savings.return_value = 3600
    file_manager = {"base_dir": "dummy_directory"}
    day = 0
    window_size = 1
    expected_end = mock_adjust_timepoint_for_daylight_savings.return_value

    start, end = data_import._day_start_and_end_time_points(
        file_manager,
        day,
        window_size,
    )

    assert start == 0
    assert end == expected_end


def test_day_start_and_end_time_points_no_end(mocker: plugin.MockerFixture) -> None:
    """Test the _day_start_and_end_time_points function for a day with no end."""
    mock_get_midnights = mocker.patch(
        "actigraphy.io.data_import.get_midnights",
        autospec=True,
    )
    mock_adjust_timepoint_for_daylight_savings = mocker.patch(
        "actigraphy.io.data_import._adjust_timepoint_for_daylight_savings",
        autospec=True,
    )
    mock_get_midnights.return_value = [3600]
    mock_adjust_timepoint_for_daylight_savings.return_value = None

    file_manager = {"base_dir": "dummy_directory"}
    day = 1
    window_size = 1
    expected_start = mock_get_midnights.return_value[0]

    start, end = data_import._day_start_and_end_time_points(
        file_manager,
        day,
        window_size,
    )

    assert start == expected_start
    assert end is None
