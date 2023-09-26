"""Dash HTML div containing a slider component for selecting a day for a
participant.
"""
from dash import dcc, html


def day_slider(participant_name: str, max_count: int) -> html.Div:
    """Returns a Dash HTML div containing a slider component for selecting a day
    for a participant.

    Args:
        participant_name : The name of the participant.
        max_count: The maximum number of days available for selection.

    Returns:
        html.Div: A Dash HTML div containing a slider component for selecting a
            day for a participant.

    Notes:
        The frontend shows 1-indexed days, but the backend uses 0-indexed days.
    """
    return html.Div(
        children=[
            html.B(
                "* All changes will be automatically saved\n\n",
                style={"color": "red"},
            ),
            html.B(f"Select day for participant {participant_name}:"),
            dcc.Slider(
                0,
                max_count - 1,
                1,
                marks={f"{i}": f"{i+1}" for i in range(max_count)},
                value=0,
                id="day_slider",
            ),
        ],
        style={"margin-left": "20px", "padding": 10},
    )
