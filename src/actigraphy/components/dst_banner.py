"""A warning banner for Daylight savings time."""
from dash import html


def dst_banner(day: int) -> html.Div:
    """A warning banner for daylight savings time.

    Args:
        day: The day of daylight savings time.

    Returns:
        html.Div: A Dash HTML div containing the banner.


    """
    return html.Div(
        children=[
            html.P(
                f"""One or more daylight savings time events were detected in this
participant, with the first one on day {day}. Please be aware there's a known bug
where the data is shifted on data loading of a day with daylight savings time.
When opening these days, please ensure to restore the correct times. Note that if
you accidentally click a DST day, and immediately click on another day, the bug
will still occur.""",
            ),
        ],
        style={
            "backgroundColor": "#ffcc00",
            "color": "#333",
            "borderLeft": "4px solid #ffae42",
            "padding": "10px 20px",
            "margin": "0 auto",
            "fontSize": "16px",
            "fontFamily": "Arial, sans-serif",
            "fontWeight": "bold",
            "textAlign": "center",
            "boxShadow": "0px 4px 6px rgba(0, 0, 0, 0.1)",
            "borderRadius": "5px",
            "maxWidth": "50rem",
        },
    )
