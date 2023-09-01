"""Contains the Dash HTML components used in the actigraphy app."""
import dash_bootstrap_components
import dash_daq
from dash import dcc, html

from actigraphy.core import utils


def header() -> html.Div:
    """Returns an HTML div containing an image of the CMI logo.

    Returns:
        html.Div: An HTML div containing an image of the CMI logo.
    """
    return html.Img(
        src="/assets/CMI_Logo_title.png", style={"height": "60%", "width": "60%"}
    )


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
        disabled=False,
        size="40",
    )
    drop_down = dcc.Dropdown(
        dropdown_choices,
        dropdown_choices[0],
        id="my-dropdown",
    )
    spinner = dash_bootstrap_components.Spinner(html.Div(id="loading"))

    confirmation_button = html.Button(
        "Load Files",
        id="load_file_button",
        n_clicks=0,
        style={"margin": 10},
    )

    return html.Div(
        [
            input_box_evaluator,
            drop_down,
            spinner,
            confirmation_button,
        ],
        style={"padding": 10},
    )


def no_evaluator_error() -> html.Div:
    """Returns a Div containing a ConfirmDialog component that prompts the user
    to insert the evaluator's name before continuing.
    """
    return html.Div(
        [
            dcc.ConfirmDialog(
                id="insert-user",
                message="Insert the evaluator's name before continue",
            )
        ]
    )


def finished_checkbox() -> dcc.Checklist:
    return dcc.Checklist(
        [" I'm done and I would like to proceed to the next participant. "],
        id="are-you-done",
        style={"margin-left": "50px"},
    )


def day_slider(participant_name: str, max_count: int) -> html.Div:
    return html.Div(
        children=[
            html.B(
                "* All changes will be automatically saved\n\n",
                style={"color": "red"},
            ),
            html.B(f"Select day for participant {participant_name}:"),
            dcc.Slider(
                1,
                max_count,
                1,
                value=1,
                id="day_slider",
            ),
        ],
        style={"margin-left": "20px", "padding": 10},
    )


def graph(axis_range: int) -> html.Div:
    return html.Div(
        children=[
            dcc.Graph(id="graph"),
            html.Div(
                children=[
                    html.B(id="sleep-onset"),
                    html.B(id="sleep-offset"),
                    html.B(id="sleep-duration"),
                ],
                style={"margin-left": "80px", "margin-right": "55px"},
            ),
            html.Div(
                children=[
                    dcc.RangeSlider(
                        min=0,
                        max=25920,
                        step=1,
                        marks={
                            i * (axis_range // 2): utils.hour_to_time_string(i)
                            for i in range(37)
                        },
                        id="my-range-slider",
                    ),
                    html.Pre(id="annotations-slider"),
                ],
                # html.Pre(id="annotations-nap"),
                style={"margin-left": "55px", "margin-right": "55px"},
            ),
        ],
    )


def switches() -> html.Div:
    # pylint: disable=not-callable because dash_daq.BooleanSwitch is callable
    return html.Div(
        children=[
            dash_daq.BooleanSwitch(
                id="multiple_sleep",
                on=False,
                label=" Does this participant have multiple sleep periods in this 24h period?",
            ),
            html.Pre(id="checklist-items"),
            dash_daq.BooleanSwitch(
                id="exclude-night",
                on=False,
                label=" Does this participant have more than 2 hours of missing sleep data from 8PM to 8AM?",
            ),
            html.Pre(id="checklist-items2"),
            dash_daq.BooleanSwitch(
                id="review-night",
                on=False,
                label=" Do you need to review this night?",
            ),
        ]
    )


def app_license() -> html.P:
    return html.P(
        """
This software is licensed under the GNU Lesser General Public License v3.0
Permissions of this copyleft license are conditioned on making available
complete source code of licensed works and modifications under the same license
or the GNU GPLv3. Copyright and license notices must be preserved. Contributors
provide an express grant of patent rights. However, a larger work using the
licensed work through interfaces provided by the licensed work may be
distributed under different terms and without source code for the larger work.",
""",
        style={"color": "gray"},
    )
