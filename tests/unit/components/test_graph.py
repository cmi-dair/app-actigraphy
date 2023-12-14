"""Unit tests for the graph component."""
# pylint: disable=protected-access

from pytest_mock import plugin

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
