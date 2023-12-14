"""Unit tests for the data_import module."""
# pylint: disable=protected-access
# pylint: disable=redefined-outer-name
import datetime
import pathlib

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
