"""Defines the graph component of the Actigraphy app.

The graph component contains a graph and range slider for use in the Actigraphy
app. The graph displays the sensor angle and arm movement data for a given day.
The range slider is used to select a sleep window for the given day.
"""
import datetime
import logging

import dash
from dash import dcc, html
from plotly import graph_objects

from actigraphy.core import callback_manager, config, utils
from actigraphy.database import crud, database
from actigraphy.io import data_import, ggir_files
from actigraphy.plotting import sensor_plots

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME
TIME_FORMATTING = settings.TIME_FORMATTING

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
                        max=36 * 60,  # 36 hours in minutes
                        step=1,
                        marks={
                            hour * 60: f"{(hour + 12) % 24:02d}:00"
                            for hour in range(0, 37, 2)
                        },
                        id="my-range-slider",
                        updatemode="mouseup",
                    ),
                    html.Pre(id="annotations-slider"),
                ],
                style={"margin-left": "55px", "margin-right": "55px"},
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
    day: int,
    drag_value: list[int],
    file_manager: dict[str, str],
) -> graph_objects.Figure:
    """Creates a graph for a given day using data from the file manager."""
    session = next(database.session_generator(file_manager["database"]))
    subject = crud.read_subject(session, file_manager["identifier"])
    dates = [day.date for day in subject.days]
    n_points_per_day = subject.n_points_per_day

    day_1_sensor_angles, day_1_arm_movement, day_1_non_wear = _get_day_data(
        file_manager,
        day,
        n_points_per_day,
    )
    day_2_sensor_angles, day_2_arm_movement, day_2_non_wear = _get_day_data(
        file_manager,
        day + 1,
        n_points_per_day,
    )

    sensor_angle = day_1_sensor_angles[n_points_per_day // 2 :] + day_2_sensor_angles
    arm_movement = day_1_arm_movement[n_points_per_day // 2 :] + day_2_arm_movement
    nonwear = day_1_non_wear[n_points_per_day // 2 :] + day_2_non_wear

    title_day = (
        f"Day {day+1}: {dates[day].strftime('%A - %d %B %Y')}"
    )  # Frontend uses 1-indexed days.
    day_timestamps = [dates[day]] * (n_points_per_day // 2) + (
        [dates[day] + datetime.timedelta(days=1)]
    ) * n_points_per_day

    timestamps = [
        " ".join(
            [
                day_timestamps[point].strftime("%d/%b/%Y"),
                utils.point2time_timestamp(point, n_points_per_day, offset=12),
            ],
        )
        for point in range(len(day_timestamps))
    ]

    nonwear_changes = _get_nonwear_changes(nonwear)
    return _build_figure(
        timestamps,
        sensor_angle,
        arm_movement,
        title_day,
        drag_value,
        n_points_per_day,
        nonwear_changes,
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
    n_points_per_day: int,
) -> tuple[list[float], list[float], list[int]]:
    """Get data for a given day."""
    session = next(database.session_generator(file_manager["database"]))
    subject = crud.read_subject(session, file_manager["identifier"])
    if day_index < len(subject.days):
        return data_import.get_graph_data(file_manager, day_index)
    return (
        [0] * n_points_per_day,
        [-210] * n_points_per_day,
        [0] * n_points_per_day,
    )


def _get_nonwear_changes(nonwear: list[int]) -> list[int]:
    """Get indices where non-wear data changes."""
    changes = [
        index
        for index in range(1, len(nonwear))
        if nonwear[index] != nonwear[index - 1]
    ]
    if nonwear[0]:
        changes.insert(0, 0)
    if len(changes) % 2 != 0:
        # If the number of changes is odd, then insert the end of the day
        # as the last change.
        changes.append(len(nonwear) - 1)
    return changes


def _build_figure(  # noqa: PLR0913
    timestamps: list[str],
    sensor_angle: list[float],
    arm_movement: list[float],
    title_day: str,
    drag_value: list[int],
    n_points_per_day: int,
    nonwear_changes: list[int],
) -> graph_objects.Figure:
    """Build the graph figure."""
    figure = sensor_plots.build_sensor_plot(
        timestamps,
        sensor_angle,
        arm_movement,
        title_day,
    )
    sleep_timepoints = utils.slider_values_to_graph_values(drag_value, n_points_per_day)

    if sleep_timepoints[0] != sleep_timepoints[1]:
        sensor_plots.add_rectangle(figure, sleep_timepoints, "red", "sleep window")

    for index in range(0, len(nonwear_changes), 2):
        sensor_plots.add_rectangle(
            figure,
            [nonwear_changes[index], nonwear_changes[index + 1]],
            "green",
            "non-wear",
        )
    return figure
