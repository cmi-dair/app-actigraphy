"""Contains the file selection component of the Actigraphy app.

The file selection component contains an input box for the evaluator's name, and
dropdown menu for selecting a subject.
"""
import logging

import dash
import dash_bootstrap_components
from dash import dcc, html

from actigraphy.components import day_slider, finished_checkbox, graph, switches
from actigraphy.core import callback_manager, config, utils
from actigraphy.io import data_import, minor_files

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def file_selection(dropdown_choices: list[str]) -> html.Div:
    """Returns a Dash HTML div containing an input box for the evaluator's name,
    a dropdown menu for selecting a subject, and a spinner for indicating loading.

    Args:
        dropdown_choices: A list of choices for the dropdown menu.

    Returns:
        html.Div: A Dash HTML div containing the input box, dropdown menu, and
            spinner.
    """
    input_box_evaluator = dcc.Input(
        id="evaluator_name",
        type="text",
        placeholder="Insert evaluator's name",
        size="40",
    )
    drop_down = dcc.Dropdown(
        dropdown_choices,
        dropdown_choices[0],
        id="my-dropdown",
    )
    spinner = html.Div(
        [
            dash_bootstrap_components.Spinner(html.Div(id="loading")),
        ],
        style={"margin": "40px 0"},
    )

    confirmation_button = html.Button(
        "Load Files",
        id="load_file_button",
        n_clicks=0,
        style={"margin": 10},
    )

    no_evaluator_error = dcc.ConfirmDialog(
        id="insert-user",
        message="Insert the evaluator's name before continuing.",
    )

    return html.Div(
        [
            input_box_evaluator,
            drop_down,
            confirmation_button,
            spinner,
            no_evaluator_error,
        ],
        style={"padding": 10},
    )


@callback_manager.global_manager.callback(
    [
        dash.Output("annotations-data", "children"),
        dash.Output("loading", "children"),
        dash.Output("insert-user", "displayed"),
        dash.Output("file_manager", "data"),
    ],
    dash.Input("load_file_button", "n_clicks"),
    dash.State("my-dropdown", "value"),
    dash.State("evaluator_name", "value"),
    prevent_initial_call=True,
)
def parse_files(
    n_clicks: int,  # pylint: disable=unused-argument n_clicks intentionallty unused.
    filepath: str,
    evaluator_name: str,
):
    """
    Parses the contents of the selected files and returns the UI components to be displayed.

    Args:
        n_clicks: The number of times the parse button has been clicked. Used to trigger
            the callback.
        filepath: The path to the selected file.
        evaluator_name: The name of the evaluator.

    Returns:
        tuple: A tuple containing the UI components to be displayed, an empty
        string, a boolean indicating whether parsing was successful, and the
        file manager object.
    """
    logger.debug("Parsing files...")
    if not evaluator_name:
        return "", "", True, None

    file_manager = utils.FileManager(base_dir=filepath).__dict__
    n_midnights = len(data_import.get_midnights(file_manager["base_dir"]))
    minor_files.initialize_files(file_manager, evaluator_name)

    ui_components = [
        day_slider.day_slider(file_manager["identifier"], n_midnights),
        finished_checkbox.finished_checkbox(),
        switches.switches(),
        graph.graph(),
    ]
    return (
        ui_components,
        "",
        False,
        file_manager,
    )
