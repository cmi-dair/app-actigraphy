"""Module for all plotting functions."""
import bisect
import datetime
import logging
from collections.abc import Sequence

import numpy as np
from plotly import graph_objects

from actigraphy.core import config, exceptions

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME


logger = logging.getLogger(LOGGER_NAME)


def build_sensor_plot(
    timestamps: list[datetime.datetime],
    sensor_angle: Sequence[float | int],
    sensor_acceleration: Sequence[float | int],
    title_day: str,
) -> tuple[graph_objects.Figure, int]:
    """Builds a plot of the sensor's angle and arm movement.

    Args:
        timestamps: The timestamps of the sensor's angle and arm movement.
        sensor_angle: The sensor's angle.
        sensor_acceleration: The arm movement.
        title_day: The title of the plot.
        n_ticks: The number of ticks on the x-axis.

    Returns:
        The plot.

    Notes:
        We assume that the delta time between timestamps is constant.
    """
    logger.debug("Building sensor plot.")
    _validate_timezones(timestamps)
    n_hours = _calculate_number_of_hours(timestamps)
    delta_time = timestamps[1] - timestamps[0]
    max_measurements = int(n_hours * 60 * 60 / delta_time.total_seconds())

    timestamp_values = _get_timestamp_x_values(timestamps, delta_time, max_measurements)
    x_min = 0
    x_max = n_hours * 60 * 60 / delta_time.total_seconds()
    x_tick_values, x_tick_names = _get_x_axis(
        timestamps,
        n_hours,
        delta_time,
        max_measurements,
        x_min,
        x_max,
    )

    figure = _build_figure(
        sensor_angle,
        sensor_acceleration,
        title_day,
        timestamp_values,
        x_min,
        x_max,
        x_tick_values,
        x_tick_names,
    )

    return figure, max_measurements


def add_rectangle(
    figure: graph_objects.Figure,
    limits: list[float],
    color: str,
    label: str,
) -> graph_objects.Figure:
    """Adds a rectangle to the figure.

    Args:
        figure: The figure to add the rectangle to.
        limits: The limits of the rectangle in range [0, 1].
        color: The color of the rectangle.
        label: The label of the rectangle.
    """
    logger.debug("Adding rectangle to figure.")
    figure.add_vrect(
        x0=figure.layout.xaxis.range[1] * limits[0],
        x1=figure.layout.xaxis.range[1] * limits[1],
        fillcolor=color,
        opacity=0.2,
        annotation={"text": label},
    )
    return figure


def _validate_timezones(timestamps: list[datetime.datetime]) -> None:
    """Validates that the timestamps contain no more than two different timezones."""
    logger.debug("Validating timezones.")
    timezones = {ts.tzinfo for ts in timestamps}
    if len(timezones) > 2:
        msg = "More than two timezones in timestamps."
        raise exceptions.InternalError(msg)


def _calculate_number_of_hours(timestamps: list[datetime.datetime]) -> float:
    """Calculates the number of hours in the graph."""
    logger.debug("Calculating number of hours.")
    timezones = list(dict.fromkeys(ts.tzinfo for ts in timestamps))
    max_timezones = 2
    if len(timezones) > max_timezones:
        msg = "More than two timezones in timestamps."
        raise exceptions.InternalError(msg)
    if len(timezones) == 2:  # noqa: PLR2004
        hour_difference = datetime.datetime(
            1,
            1,
            1,
            tzinfo=timezones[1],
        ) - datetime.datetime(1, 1, 1, tzinfo=timezones[0])
    if len(timezones) == 1:
        hour_difference = datetime.timedelta(hours=0)
    if len(timezones) == 0:
        msg = "No timezones in timestamps."
        raise exceptions.InternalError(msg)
    return 36 + (hour_difference.total_seconds() / 60 / 60)


def _get_timestamp_x_values(timestamps, delta_time, n_ticks) -> list[int]:
    """Calculates the x values for the timestamps."""
    x_times = [
        datetime.datetime.combine(
            timestamps[0].date(),
            datetime.time(hour=12),
            tzinfo=timestamps[0].tzinfo,
        )
        + datetime.timedelta(seconds=delta_time.total_seconds() * tick)
        for tick in range(int(n_ticks))
    ]
    first_timestamp_index = min(
        range(len(x_times)),
        key=lambda i: abs(x_times[i] - timestamps[0]),
    )
    return list(
        range(
            first_timestamp_index,
            first_timestamp_index + len(timestamps),
        ),
    )


def _get_x_axis(timestamps, n_hours, delta_time, max_measurements, x_min, x_max):
    timestamps_including_missing = [
        timestamps[0].replace(hour=12, minute=0, second=0, microsecond=0)
        + datetime.timedelta(seconds=delta_time.total_seconds() * tick)
        for tick in range(int(max_measurements))
    ]
    first_timestamp_index = bisect.bisect_left(
        timestamps_including_missing,
        timestamps[0],
    )

    timestamps_timezone_update = [
        timestamps_including_missing[first_timestamp_index + index].astimezone(
            timestamps[index].tzinfo,
        )
        for index in range(
            len(timestamps),
        )
    ]
    timestamps_including_missing[
        first_timestamp_index : first_timestamp_index
        + len(
            timestamps,
        )
    ] = timestamps_timezone_update

    timestamps_including_missing.append(
        timestamps_including_missing[-1].replace(
            day=timestamps_including_missing[-1].day + 1,
            hour=0,
            minute=0,
            second=0,
            microsecond=0,
        ),
    )

    x_tick_values = np.linspace(x_min, x_max, int(n_hours) + 1, dtype=int)

    x_tick_times = [timestamps_including_missing[tick] for tick in x_tick_values]
    x_tick_names = [
        datetime.datetime.strftime(
            time,
            "%H:%M",
        )
        if time.hour % 3 == 0
        else ""
        for time in x_tick_times
    ]
    n_timezones = len(list(dict.fromkeys(ts.tzinfo for ts in timestamps)))
    if n_timezones > 2:  # noqa: PLR2004
        msg = "More than two timezones in timestamps."
        raise exceptions.InternalError(msg)
    if n_timezones == 2:  # noqa: PLR2004
        timezone_format = "%H:%M<br><b>%Z</b>"
        x_tick_names[0] = datetime.datetime.strftime(x_tick_times[0], timezone_format)
        x_tick_names[-1] = datetime.datetime.strftime(x_tick_times[-1], timezone_format)

    return x_tick_values, x_tick_names


def _build_figure(
    sensor_angle,
    sensor_acceleration,
    title_day,
    timestamp_values,
    x_min,
    x_max,
    x_tick_values,
    x_tick_names,
):
    figure = graph_objects.Figure()
    figure.add_trace(
        graph_objects.Scatter(
            x=timestamp_values,
            y=sensor_angle,
            mode="lines",
            name="Angle of sensor's z-axis",
            line_color="blue",
        ),
    )
    figure.add_trace(
        graph_objects.Scatter(
            x=timestamp_values,
            y=sensor_acceleration,
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
                "tickangle": 0,
                "range": [x_min, x_max],
                "tickvals": x_tick_values,
                "ticktext": x_tick_names,
            },
        },
    )

    return figure
