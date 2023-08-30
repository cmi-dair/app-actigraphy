"""Contains the Dash HTML components used in the actigraphy app."""
import dash_bootstrap_components
from dash import dcc, html


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
