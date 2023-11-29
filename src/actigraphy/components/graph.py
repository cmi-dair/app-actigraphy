"""Defines the graph component of the Actigraphy app.

The graph component contains a graph and range slider for use in the Actigraphy
app. The graph displays the sensor angle and arm movement data for a given day.
The range slider is used to select a sleep window for the given day.
"""
import datetime
import logging
from collections.abc import Iterable

import dash
from dash import dcc, html
from plotly import graph_objects

from actigraphy.core import callback_manager, config, utils
from actigraphy.database import crud, database, models
from actigraphy.io import ggir_files
from actigraphy.plotting import sensor_plots

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME
TIME_FORMATTING = settings.TIME_FORMATTING
N_SLIDER_STEPS = settings.N_SLIDER_STEPS

logger = logging.getLogger(LOGGER_NAME)


def graph() -> html.Div:
    """Builds the graph component of the Actigraphy app.

    Returns:
        html.Div: A Dash HTML div containing a graph and range slider
        components.
    """
    return html.Div(
        children=[
            dcc.Graph(id="graph"),
            html.Div(
                children=[
                    dcc.RangeSlider(
                        min=0,
                        max=N_SLIDER_STEPS,
                        step=1,
                        marks=None,
                        id="my-range-slider",
                        updatemode="mouseup",
                    ),
                    html.Pre(id="annotations-slider"),
                ],
                style={"margin-left": "55px", "margin-right": "55px"},
            ),
            html.Div(
                children=[
                    html.B(id="sleep-onset"),
                    html.B(id="sleep-offset"),
                    html.B(id="sleep-duration"),
                ],
                style={"margin-left": "80px", "margin-right": "55px"},
            ),
        ],
    )


@callback_manager.global_manager.callback(
    dash.Output("graph", "figure"),
    dash.Input("day_slider", "value"),
    dash.Input("my-range-slider", "value"),
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def create_graph(
    day_index: int,
    drag_value: list[int],
    file_manager: dict[str, str],
) -> graph_objects.Figure:
    """Creates a graph for a given day using data from the file manager."""
    logger.debug("Creating graph.")
    session = next(database.session_generator(file_manager["database"]))
    subject = crud.read_subject(session, file_manager["identifier"])
    dates = [day.date for day in subject.days]

    logger.debug("Getting day data.")
    data_points = _get_day_data(
        file_manager,
        day_index,
    )
    included_data_points = [
        point
        for point in data_points
        if (
            point.timestamp_with_tz.date() == dates[day_index]
            and point.timestamp_with_tz.hour >= 12
        )
        or point.timestamp_with_tz.date()
        == dates[day_index] + datetime.timedelta(days=1)
    ]

    logger.debug("Getting non-wear data.")
    timestamps = [point.timestamp_with_tz for point in included_data_points]
    sensor_angle = [point.sensor_angle for point in included_data_points]
    arm_movement = [point.sensor_acceleration for point in included_data_points]
    non_wear = [point.non_wear for point in included_data_points]

    title_day = (
        f"Day {day_index+1}: {dates[day_index].strftime('%A, %d %B %Y')}"
    )  # Frontend uses 1-indexed days.

    return _build_figure(
        timestamps,
        sensor_angle,
        arm_movement,
        title_day,
        drag_value,
        non_wear,
    )


@callback_manager.global_manager.callback(
    dash.Output("my-range-slider", "value"),
    dash.Input("day_slider", "value"),
    dash.Input("file_manager", "data"),
    prevent_initial_call=True,
)
def refresh_range_slider(
    day_index: int,
    file_manager: dict[str, str],
) -> list[int]:
    """Reads the sleep logs for the given day.

    Args:
        day_index: The day for which to retrieve the sleep logs.
        file_manager: A dictionary containing file paths for various sleep log
            files.

    Returns:
        list[int]: A list containing the sleep onset and sleep offset points.
    """
    session = next(database.session_generator(file_manager["database"]))
    day = crud.read_day_by_subject(session, day_index, file_manager["identifier"])
    sleep_time = day.sleep_times[0].onset_with_tz
    wake_time = day.sleep_times[0].wakeup_with_tz

    sleep_point = utils.time2point(sleep_time, day.date)
    wake_point = utils.time2point(wake_time, day.date)

    return [sleep_point, wake_point]


@callback_manager.global_manager.callback(
    dash.Output("sleep-onset", "children", allow_duplicate=True),
    dash.Output("sleep-offset", "children", allow_duplicate=True),
    dash.Output("sleep-duration", "children", allow_duplicate=True),
    dash.Input("my-range-slider", "value"),
    dash.State("file_manager", "data"),
    dash.State("day_slider", "value"),
    prevent_initial_call=True,
)
def adjust_range_slider(
    drag_value: list[int],
    file_manager: dict[str, str],
    day_index: int,
) -> tuple[str, str, str]:
    """Adjusts the text labels for a given day and writes the sleep log to a file.

    Args:
        drag_value: The drag values of the range slider.
        file_manager: The file manager containing the sleep log.
        day_index: The day for which to adjust the range slider.

    Returns:
        Tuple[str, str, str, str]: A tuple containing the sleep onset, sleep
            offset, and sleep duration.
    """
    session = next(database.session_generator(file_manager["database"]))
    day = crud.read_day_by_subject(session, day_index, file_manager["identifier"])

    sleep_time = utils.point2time(
        drag_value[0],
        day.date,
        day.sleep_times[0].onset_utc_offset,
    )
    wake_time = utils.point2time(
        drag_value[1],
        day.date,
        day.sleep_times[0].wakeup_utc_offset,
    )

    day.sleep_times[0].onset = sleep_time.astimezone(datetime.UTC)
    day.sleep_times[0].wakeup = wake_time.astimezone(datetime.UTC)

    session.commit()
    ggir_files.write_sleeplog(file_manager)

    onset_string = sleep_time.strftime(TIME_FORMATTING)
    offset_string = wake_time.strftime(TIME_FORMATTING)
    duration_string = utils.datetime_delta_as_hh_mm(wake_time - sleep_time)
    return (
        f"Sleep onset: {onset_string}\n",
        f"Sleep offset: {offset_string}\n",
        f"Sleep duration: {duration_string}\n",
    )


def _get_day_data(
    file_manager: dict[str, str],
    day_index: int,
) -> list[models.DataPoint]:
    """Get data for a given day.

    Args:
        file_manager: A dictionary containing file paths.
        day_index: The index of the day for which to retrieve the data.

    Returns:
        list[models.DataPoint]: A list of data points for the given day.

    """
    logger.debug("Getting data for day %s", day_index)
    session = next(database.session_generator(file_manager["database"]))
    subject = crud.read_subject(session, file_manager["identifier"])
    day = crud.read_day_by_subject(session, day_index, file_manager["identifier"])
    return session.query(models.DataPoint).filter(
        models.DataPoint.subject_id == subject.id,
        models.DataPoint.timestamp
        >= datetime.datetime.combine(
            day.date - datetime.timedelta(days=1),
            datetime.time(hour=11),
        ),
        models.DataPoint.timestamp
        <= datetime.datetime.combine(
            day.date + datetime.timedelta(days=3),
            datetime.time(hour=1),
        ),
    )


def _build_figure(  # noqa: PLR0913
    timestamps: list[datetime.datetime],
    sensor_angle: list[float],
    arm_movement: list[float],
    title_day: str,
    drag_value: list[int],
    nonwear_changes: list[int],
) -> graph_objects.Figure:
    """Build the graph figure."""
    logger.debug("Building figure.")
    logger.debug("Length of timestamps: %s", len(timestamps))
    rescale_arm_movement = [value * 50 - 210 for value in arm_movement]
    figure, max_measurements = sensor_plots.build_sensor_plot(
        timestamps,
        sensor_angle,
        rescale_arm_movement,
        title_day,
    )

    drag_fraction = [value / N_SLIDER_STEPS for value in drag_value]
    sensor_plots.add_rectangle(figure, drag_fraction, "red", "sleep window")

    continuous_non_wear_blocks = _find_continuous_blocks(nonwear_changes)
    non_wear_fractions = [
        value / max_measurements for value in continuous_non_wear_blocks
    ]

    for index in range(0, len(non_wear_fractions), 2):
        sensor_plots.add_rectangle(
            figure,
            [
                non_wear_fractions[index],
                non_wear_fractions[index + 1],
            ],
            "green",
            "non-wear",
        )
    return figure


def _find_continuous_blocks(vector: Iterable[bool]) -> list[int]:
    """Finds the indices of continuous blocks of True values in a vector.

    Args:
        vector: The vector to search.

    Returns:
        list[int]: A list of indices of continuous blocks of True values in the
            vector.
    """
    return [
        index
        for index, value in enumerate(vector)
        if value
        and (
            index == 0
            or index == len(vector)
            or not vector[index - 1]
            or not vector[index + 1]
        )
    ]
