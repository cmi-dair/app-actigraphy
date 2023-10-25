"""This module contains the switches component for the Actigraphy app.

The switches component contains three BooleanSwitch components for use in the
Actigraphy app. The first switch is used to indicate whether the participant
has multiple sleep periods in a 24-hour period. The second switch is used to
indicate whether the participant has more than 2 hours of missing sleep data.
The third switch is used to indicate whether the user needs to review the sleep
data for a particular night.
"""
import logging

import dash
import dash_daq
from dash import html

from actigraphy.core import callback_manager, config
from actigraphy.io import minor_files

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def switches() -> html.Div:
    """Returns a Dash HTML div containing three BooleanSwitch components.

    - The first switch is used to indicate whether the participant has multiple
        sleep periods in a 24-hour period.
    - The second switch is used to indicate whether the participant has more
        than 2 hours of missing sleep data from 8PM to 8AM.
    - The third switch is used to indicate whether the user needs to
        review the sleep data for a particular night.

    Returns:
        html.Div: A Dash HTML div containing three BooleanSwitch components.
    """
    # pylint: disable=not-callable because dash_daq.BooleanSwitch is callable
    return html.Div(
        children=[
            dash_daq.BooleanSwitch(
                id="multiple_sleep",
                on=False,
                label=(
                    " Does this participant have multiple sleep "
                    "periods in this 24h period?",
                ),
            ),
            dash_daq.BooleanSwitch(
                id="exclude_night",
                on=False,
                label=(
                    " Does this participant have more than 2 hours of "
                    "missing sleep data from 8PM to 8AM?",
                ),
            ),
            dash_daq.BooleanSwitch(
                id="review_night",
                on=False,
                label=" Do you need to review this night?",
            ),
            html.Div(id="null-data-sleep"),
            html.Div(id="null-data-night"),
            html.Div(id="null-data-review"),
        ],
    )


@callback_manager.global_manager.callback(
    dash.Output("multiple_sleep", "on"),
    dash.Output("exclude_night", "on"),
    dash.Output("review_night", "on"),
    dash.Input("day_slider", "value"),
    dash.State("file_manager", "data"),
)
def update_switches(day: int, file_manager: dict[str, str]) -> tuple[bool, bool, bool]:
    """Reads the sleep logs for the given day.

    Args:
        day: The day for which to retrieve the sleep logs.
        file_manager: A dictionary containing file paths for various sleep log
            files.

    Returns:
        tuple[bool, bool, bool]: A tuple of boolean values indicating whether
            there are naps, missing sleep, and reviewed nights for the given
            day.
    """
    logger.debug("Entering update switches callback")
    naps = minor_files.read_vector(file_manager["multiple_sleeplog_file"])
    missing = minor_files.read_vector(file_manager["missing_sleep_file"])
    nights = minor_files.read_vector(file_manager["review_night_file"])
    return naps[day] == "1", missing[day] == "1", nights[day] == "1"


@callback_manager.global_manager.callback(
    dash.Output("null-data-night", "children"),
    dash.Input("exclude_night", "on"),
    dash.State("day_slider", "value"),
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def toggle_exclude_night(
    exclude_button: bool,  # noqa: FBT001
    day: int,
    file_manager: dict[str, str],
) -> None:
    """Toggles the exclusion of a night in the missing sleep file.

    Args:
        exclude_button: Whether to exclude the night or not.
        day : The day to toggle the exclusion for.
        file_manager: A dictionary containing file paths for the missing sleep file.
    """
    _toggle_vector_value(exclude_button, day, file_manager["missing_sleep_file"])


@callback_manager.global_manager.callback(
    dash.Output("null-data-review", "children"),
    dash.Input("review_night", "on"),
    dash.State("day_slider", "value"),
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def toggle_review_night(
    review_night: bool,  # noqa: FBT001
    day: int,
    file_manager: dict[str, str],
) -> None:
    """Toggles the review night flag for a given day in the review night file.

    Args:
        review_night: The new review night flag value (0 or 1).
        day: The day index to toggle the flag for.
        file_manager: A dictionary containing file paths for the review night file.
    """
    _toggle_vector_value(review_night, day, file_manager["review_night_file"])


@callback_manager.global_manager.callback(
    dash.Output("null-data-sleep", "children"),
    dash.Input("multiple_sleep", "on"),
    dash.State("day_slider", "value"),
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def toggle_nap(multiple_sleep: bool, day: int, file_manager: dict[str, str]) -> None:  # noqa: FBT001
    """Toggles the nap status for a given day in the multiple sleep log file.

    Args:
        multiple_sleep:: The new nap status for the given day.
        day: The day to toggle the nap status for.
        file_manager: A dictionary containing file paths for various files.
    """
    _toggle_vector_value(multiple_sleep, day, file_manager["multiple_sleeplog_file"])


def _toggle_vector_value(new_value: int | bool, index: int, file_path: str) -> None:
    """Toggles the value of a vector at a given index in a file.

    Args:
        new_value: The new value to set at the given index.
        index: The index of the vector to toggle.
        file_path: The path to the file containing the vector.

    """
    logger.debug(
        "Setting index %s to value %s for file %s",
        index,
        int(new_value),
        file_path,
    )
    vector = minor_files.read_vector(file_path)
    vector[index] = int(new_value)
    minor_files.write_vector(file_path, vector)
