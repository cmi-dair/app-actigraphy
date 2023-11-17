"""Unit tests for the graph component."""
# pylint: disable=protected-access

from pytest_mock import plugin

from actigraphy.components import graph

from .callback_test_manager import get_callback


def test_refresh_range_slider(file_manager: dict[str, str]) -> None:
    """Test the refresh_range_slider function."""
    expected = [0, 60]
    func = get_callback("refresh_range_slider")

    actual = func(0, file_manager)

    assert actual == expected


def test_adjust_range_slider(
    mocker: plugin.MockerFixture,
    file_manager: dict[str, str],
) -> None:
    """Test the adjust_range_slider function."""
    mocker.patch("actigraphy.io.ggir_files.write_sleeplog")

    expected = (
        "Sleep onset: Thursday - 26 August 1993 12:00\n",
        "Sleep offset: Thursday - 26 August 1993 13:00\n",
        "Sleep duration: 01:00\n",
    )
    func = get_callback("adjust_range_slider")

    actual = func([0, 60], file_manager, 0)

    assert actual == expected


def test__get_day_data_in_range(
    mocker: plugin.MockerFixture,
    file_manager: dict[str, str],
) -> None:
    """Test the _get_day_data function with data in range."""
    expected = "data"
    mocker.patch("actigraphy.io.data_import.get_graph_data", return_value=expected)

    actual = graph._get_day_data(file_manager, 0, 10)

    assert actual == expected  # type: ignore[comparison-overlap]


def test__get_day_data_out_range(
    mocker: plugin.MockerFixture,
    file_manager: dict[str, str],
) -> None:
    """Test the _get_day_data function with data out of range."""
    mocker.patch("actigraphy.io.data_import.get_graph_data", return_value="data")
    expected = ([0] * 10, [-210] * 10, [0] * 10)

    actual = graph._get_day_data(file_manager, 2, 10)

    assert actual == expected


def test__get_nonwear_changes_no_start_change() -> None:
    """Test the _get_nonwear_changes function with no start change."""
    expected = [3, 5]

    actual = graph._get_nonwear_changes([0, 0, 0, 1, 1, 0])

    assert actual == expected


def test__get_nonwear_changes_with_end_change() -> None:
    """Test the _get_nonwear_changes function with an end change."""
    expected = [0, 1, 3, 5]

    actual = graph._get_nonwear_changes([1, 0, 0, 1, 1, 1])

    assert actual == expected


def test__get_nonwear_changes_with_start_change() -> None:
    """Test the _get_nonwear_changes function with a start change."""
    expected = [0, 1, 3, 5]

    actual = graph._get_nonwear_changes([1, 0, 0, 1, 1, 0])

    assert actual == expected
