"""Module for all plotting functions."""
from collections.abc import Sequence

from plotly import graph_objects


def build_sensor_plot(
    timestamps: list[str],
    sensor_angle: Sequence[float | int],
    arm_movement: Sequence[float | int],
    title_day: str,
    n_ticks: int = 36,
) -> graph_objects.Figure:
    """Builds a plot of the sensor's angle and arm movement.

    Args:
        timestamps: The timestamps of the sensor's angle and arm movement.
        sensor_angle: The sensor's angle.
        arm_movement: The arm movement.
        title_day: The title of the plot.
        n_ticks: The number of ticks on the x-axis.

    Returns:
        The plot.
    """
    if len(sensor_angle) != len(arm_movement) or len(sensor_angle) != len(timestamps):
        msg = (
            "The lengths of the timestamps, sensor angle "
            "and arm movement must be equal."
        )
        raise ValueError(msg)

    x_values = list(range(len(timestamps)))
    x_tick_values = list(range(0, len(timestamps), len(timestamps) // n_ticks))
    x_tick_text = [timestamps[i] for i in x_tick_values]

    figure = graph_objects.Figure()
    figure.add_trace(
        graph_objects.Scatter(
            x=x_values,
            y=sensor_angle,
            mode="lines",
            name="Angle of sensor's z-axis",
            line_color="blue",
        ),
    )
    figure.add_trace(
        graph_objects.Scatter(
            x=x_values,
            y=arm_movement,
            mode="lines",
            name="Arm movement",
            line_color="black",
        ),
    )
    figure.update_layout(
        {
            "title": title_day,
            "legend": {
                "orientation": "h",
                "yanchor": "bottom",
                "y": 1.02,
                "xanchor": "right",
                "x": 1,
            },
            "xaxis": {
                "tickmode": "array",
                "tickvals": x_tick_values,
                "ticktext": x_tick_text,
                "tickangle": 90,
            },
        },
    )
    return figure


def add_rectangle(
    figure: graph_objects.Figure,
    limits: list[int],
    color: str,
    label: str,
) -> graph_objects.Figure:
    """Adds a rectangle to the figure.

    Args:
        figure: The figure to add the rectangle to.
        limits: The limits of the rectangle.
        color: The color of the rectangle.
        label: The label of the rectangle.
    """
    figure.add_vrect(
        x0=limits[0],
        x1=limits[1],
        fillcolor=color,
        opacity=0.2,
        annotation={"text": label},
    )
    return figure
