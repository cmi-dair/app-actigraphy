"""Defines a Dash checklist component that allows the user to indicate whether
they are done with the current participant and would like to proceed to the next
one.
"""
import logging

import dash
from dash import dcc

from actigraphy.core import callback_manager, config
from actigraphy.io import minor_files

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def finished_checkbox() -> dcc.Checklist:
    """Returns a Dash checklist component that allows the user to indicate
    whether they are done with the current participant and would like to proceed
    to the next one.

    Returns:
        dcc.Checklist: A Dash checklist component with a single checkbox option.
    """
    return dcc.Checklist(
        [" I'm done and I would like to proceed to the next participant. "],
        id="are-you-done",
        style={"margin-left": "50px"},
    )


@callback_manager.global_manager.callback(
    dash.Output("check-done", "children"),
    dash.Input("are-you-done", "value"),
    dash.State("file_manager", "data"),
)
def write_log_done(is_user_done: bool, file_manager: dict[str, str]) -> bool:
    """Writes a log message indicating that the analysis has been completed.

    Args:
        is_user_done: Whether the user has completed the analysis.
        file_manager: A dictionary containing information about the file being analyzed.
    """
    minor_files.write_log_analysis_completed(
        is_user_done,
        file_manager["identifier"],
        file_manager["completed_analysis_file"],
    )
    return is_user_done
