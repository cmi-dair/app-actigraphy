"""Tests the switches callbacks.

Due to the custom nature of the callbacks, it is not possible to call them
directly. Instead, we use global manager to get the callback function and then
call it with the appropriate arguments.
"""
from typing import Any, Callable

from pytest_mock import plugin

from actigraphy.core import callback_manager

manager = callback_manager.global_manager
callback_manager.initialize_components()


def get_callback(name: str) -> Callable[..., Any]:
    """Returns the callback with the given name.

    Args:
        name: The name of the callback.

    Returns:
        Callable[[Any], Any]: The callback with the given name.
    """
    for callback in manager._callbacks:  # pylint: disable=protected-access
        if callback.func.__name__ == name:
            return callback.func  # type: ignore[no-any-return]
    raise ValueError(f"Callback {name} not found.")


def test_update_switches(mocker: plugin.MockerFixture) -> None:
    """Test the update_switches function."""
    mocker.patch("actigraphy.io.minor_files.read_vector", return_value=["1"])
    expected = (True, True, True)
    func = get_callback("update_switches")
    file_manager = {
        "multiple_sleeplog_file": "",
        "missing_sleep_file": "",
        "review_night_file": "",
    }

    actual = func(0, file_manager)

    assert actual == expected


def test_toggle_exclude_night(mocker: plugin.MockerFixture) -> None:
    """Test the toggle_exclude_night function."""
    mocker.patch(
        "actigraphy.components.switches._toggle_vector_value", return_value=None
    )
    func = get_callback("toggle_exclude_night")

    actual = func(True, 1, {"missing_sleep_file": ""})

    assert actual is None


def test_toggle_review_night(mocker: plugin.MockerFixture) -> None:
    """Test the toggle_review_night function."""
    mocker.patch(
        "actigraphy.components.switches._toggle_vector_value", return_value=None
    )
    func = get_callback("toggle_review_night")

    actual = func(True, 1, {"review_night_file": ""})

    assert actual is None


def test_toggle_nap(mocker: plugin.MockerFixture) -> None:
    """Test the toggle_nap function."""
    mocker.patch(
        "actigraphy.components.switches._toggle_vector_value", return_value=None
    )
    func = get_callback("toggle_nap")

    actual = func(True, 1, {"multiple_sleeplog_file": ""})

    assert actual is None
