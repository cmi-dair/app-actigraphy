# pylint: disable=protected-access
from pytest_mock import plugin

from actigraphy.components import graph


def test__get_day_data_in_range(mocker: plugin.MockerFixture) -> None:
    """Test the _get_day_data function with data in range."""
    expected = "data"
    mocker.patch("actigraphy.io.data_import.get_dates", return_value=["1", "2"])
    mocker.patch("actigraphy.io.data_import.get_graph_data", return_value=expected)

    actual = graph._get_day_data({"data_file": ""}, 0, 10)

    assert actual == expected  # type: ignore[comparison-overlap]


def test__get_day_data_out_range(mocker: plugin.MockerFixture) -> None:
    """Test the _get_day_data function with data out of range."""
    mocker.patch("actigraphy.io.data_import.get_dates", return_value=["1", "2"])
    mocker.patch("actigraphy.io.data_import.get_graph_data", return_value="data")
    expected = ([0] * 10, [-210] * 10, [0] * 10)

    actual = graph._get_day_data({"data_file": ""}, 2, 10)

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
