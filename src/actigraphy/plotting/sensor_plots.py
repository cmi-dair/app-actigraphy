"""Module for all plotting functions."""
import datetime

from plotly import graph_objects


def build_sensor_plot(
    timestamps: list[datetime.datetime],
    sensor_angle: list[float],
    arm_movement: list[float],
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
    if len(sensor_angle) != len(arm_movement) != len(timestamps):
        raise ValueError(
            "The lengths of the timestamps, sensor angle and arm movement must be equal."
        )

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
        )
    )
    figure.add_trace(
        graph_objects.Scatter(
            x=x_values,
            y=arm_movement,
            mode="lines",
            name="Arm movement",
            line_color="black",
        )
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
        }
    )
    return figure
