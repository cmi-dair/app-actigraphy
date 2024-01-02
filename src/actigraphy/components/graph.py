"""Defines the graph component of the Actigraphy app.

The graph component contains a graph range sliders for use in the Actigraphy
app. The graph displays the sensor angle and arm movement data for a given day.
The range slider is used to select a sleep window for the given day.
"""
import datetime
import logging
import statistics
from collections.abc import Sequence

import dash
from dash import dcc, html
from plotly import graph_objects

from actigraphy.components import utils as components_utils
from actigraphy.core import callback_manager, config
from actigraphy.core import utils as core_utils
from actigraphy.database import crud, database
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
                    html.Button(
                        "+",
                        id="add_slider",
                    ),
                    html.Button(
                        "-",
                        id="remove_slider",
                    ),
                ],
                style={
                    "marginLeft": "55px",
                    "marginRight": "55px",
                    "display": "flex",
                },
            ),
            html.Div(
                children=[],
                id="slider_div",
                style={"marginLeft": "55px", "marginRight": "55px"},
            ),
        ],
    )


@callback_manager.global_manager.callback(
    dash.Output("graph", "figure"),
    dash.Input("trigger_day_load", "value"),
    dash.Input({"type": "range_slider", "index": dash.ALL}, "value"),
    dash.State("day_slider", "value"),
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def create_graph(
    _trigger_load: str,
    drag_values: tuple[list[int]],
    day_index: int,
    file_manager: dict[str, str],
) -> graph_objects.Figure:
    """Creates a graph for a given day using data from the file manager."""
    logger.debug("Creating graph.")
    session = next(database.session_generator(file_manager["database"]))
    subject = crud.read_subject(session, file_manager["identifier"])
    dates = [day.date for day in subject.days]

    logger.debug("Getting day data.")
    data_points = components_utils.get_day_data(
        day_index,
        file_manager["database"],
        file_manager["identifier"],
    )
    included_data_points = [
        point
        for point in data_points
        if (
            point.timestamp_with_tz.date() == dates[day_index]
            and point.timestamp_with_tz.hour >= 12  # noqa: PLR2004
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
        f"Day {day_index+1}:"
        f"{included_data_points[0].timestamp.strftime('%A, %d %B %Y')}"
    )  # Frontend uses 1-indexed days.

    return _build_figure(
        timestamps,
        sensor_angle,
        arm_movement,
        title_day,
        drag_values,
        non_wear,
    )


@callback_manager.global_manager.callback(
    dash.Output("slider_div", "children", allow_duplicate=True),
    dash.Input("trigger_day_load", "value"),
    dash.State("day_slider", "value"),
    dash.State("file_manager", "data"),
    dash.State("daylight_savings_shift", "value"),
    prevent_initial_call=True,
)
def refresh_range_slider(
    _trigger_load: str,
    day_index: int,
    file_manager: dict[str, str],
    daylight_savings_shift: int | None,
    slider_index: int = 0,
) -> list[int]:
    """Reads the sleep logs for the given day.

    Args:
        _trigger_load: A trigger for the callback.
        day_index: The day for which to retrieve the sleep logs.
        file_manager: A dictionary containing file paths for various sleep log
            files.
        daylight_savings_shift: The seconds offset due to daylight savings.
        slider_index: The index of the slider to refresh.

    Returns:
        list[int]: A list containing the sleep onset and sleep offset points.
    """
    session = next(database.session_generator(file_manager["database"]))
    day = crud.read_day_by_subject(session, day_index, file_manager["identifier"])
    if len(day.sleep_times) < slider_index:
        return [0, 0]
    sleep_time = day.sleep_times[slider_index].onset_with_tz
    wake_time = day.sleep_times[slider_index].wakeup_with_tz

    sleep_point = core_utils.time2point(
        sleep_time,
        day.date,
        daylight_savings_shift,
    )
    wake_point = core_utils.time2point(
        wake_time,
        day.date,
        daylight_savings_shift,
    )

    return [sleep_point, wake_point]


@callback_manager.global_manager.callback(
    dash.Output(
        {"type": "range_slider", "index": dash.MATCH},
        "value",
        allow_duplicate=True,
    ),
    dash.Input({"type": "range_slider", "index": dash.MATCH}, "value"),
    dash.State("file_manager", "data"),
    dash.State("day_slider", "value"),
    dash.State("daylight_savings_timepoint", "value"),
    dash.State("daylight_savings_shift", "value"),
    dash.State(
        {
            "type": "range_slider",
            "index": dash.ALL,
        },
        "value",
    ),
    prevent_initial_call=True,
)
def adjust_range_slider(
    drag_values: list[int],
    file_manager: dict[str, str],
    day_index: int,
    daylight_savings_timepoint: str | None,
    daylight_savings_shift: int | None,
    all_drag_values: list[list[int]],
) -> tuple[str, str, str]:
    """Checks if the new position is valid and writes the sleep log to a file.

    If the new position is not valid, the callback will return the state to
    the previous position.

    Args:
        drag_values: The drag values of the range slider.
        file_manager: The file manager containing the sleep log.
        day_index: The day for which to adjust the range slider.
        daylight_savings_timepoint: The index of the first data point that is
            affected by daylight savings time.
        daylight_savings_shift: The seconds offset due to daylight savings.
        other_drag_values: The drag values of the other range sliders.

    Notes:
        This assumes only one side of the slider is being dragged at a time.
        It could break if the second side is dragged before the first side is
        processed.
    """
    logger.debug("Adjusting range slider.")

    other_drag_values = [values for values in all_drag_values if values != drag_values]
    new_values = _adjust_range_slider_values(drag_values, other_drag_values)

    session = next(database.session_generator(file_manager["database"]))
    day = crud.read_day_by_subject(session, day_index, file_manager["identifier"])
    first_data_point = components_utils.get_day_data(
        day_index,
        file_manager["database"],
        file_manager["identifier"],
    )[0]
    base_timezone = first_data_point.timestamp_utc_offset

    sleep_time = core_utils.point2time(
        new_values[0],
        day.date,
        base_timezone,
        daylight_savings_timepoint,
        daylight_savings_shift,
    )
    wake_time = core_utils.point2time(
        new_values[1],
        day.date,
        base_timezone,
        daylight_savings_timepoint,
        daylight_savings_shift,
    )

    day.sleep_times[0].onset = sleep_time.astimezone(datetime.UTC)
    day.sleep_times[0].onset_utc_offset = sleep_time.utcoffset().total_seconds()  # type: ignore [union-attr]
    day.sleep_times[0].wakeup = wake_time.astimezone(datetime.UTC)
    day.sleep_times[0].wakeup_utc_offset = wake_time.utcoffset().total_seconds()  # type: ignore [union-attr]

    session.commit()
    ggir_files.write_sleeplog(file_manager)

    return new_values


@callback_manager.global_manager.callback(
    dash.Output("slider_div", "children", allow_duplicate=True),
    dash.Input("add_slider", "n_clicks"),
    prevent_initial_call=True,
)
def add_sliders(
    n_clicks: int,
) -> dash.Patch:
    """Adds sliders from the graph.

    Args:
        n_clicks: The number of times the add button has been clicked.

    Returns:
        dash.Patch: A patch to add a slider.
    """
    logger.debug("Adding slider %s.", n_clicks)
    patch = dash.Patch()
    slider = _create_slider(index=n_clicks)
    patch.append(slider)
    return patch


@callback_manager.global_manager.callback(
    dash.Output("slider_div", "children", allow_duplicate=True),
    dash.Input("remove_slider", "n_clicks"),
    prevent_initial_call=True,
)
def remove_sliders(
    remove_clicks: int,  # noqa: ARG001
) -> dash.Patch:
    """Removes sliders from the graph.

    Args:
        remove_clicks: The number of times the remove button has been clicked.
        sliders: The sliders.

    Returns:
        dash.Patch: A patch to remove the last slider.

    """
    logger.debug("Removing slider.")
    patch = dash.Patch()
    del patch[-1]
    return patch


def _build_figure(  # noqa: PLR0913
    timestamps: list[datetime.datetime],
    sensor_angle: list[float],
    arm_movement: list[float],
    title_day: str,
    drag_values: tuple[list[int]],
    nonwear_changes: list[bool],
) -> graph_objects.Figure:
    """Build the graph figure."""
    logger.debug("Building figure.")
    rescale_arm_movement = [value * 50 - 210 for value in arm_movement]
    figure, max_measurements = sensor_plots.build_sensor_plot(
        timestamps,
        sensor_angle,
        rescale_arm_movement,
        title_day,
    )

    for values in drag_values:
        if not values:
            continue
        drag_fraction = [value / N_SLIDER_STEPS for value in values]
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


def _find_continuous_blocks(vector: Sequence[bool]) -> list[int]:
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


def _create_slider(index: int) -> dcc.RangeSlider:
    """Creates slider components for selecting sleep windows.

    Args:
        index: The index of the slider.

    Returns:
        A list of slider components.
    """
    return dcc.RangeSlider(
        min=0,
        max=N_SLIDER_STEPS,
        step=1,
        marks=None,
        id={"type": "range_slider", "index": index},
        updatemode="mouseup",
    )


def _adjust_range_slider_values(
    drag_values: list[int],
    other_drag_values: list[list[int]],
) -> list[int]:
    """Adjusts the range slider values to ensure validity.

    Slider ranges are not allowed to intersect with each other.

    Args:
        drag_values: The drag values of the range slider.
        other_drag_values: The drag values of the other range sliders.

    Returns:
        list[int]: The adjusted range slider values.
    """
    if not drag_values:
        return drag_values

    new_values = [drag_values[0], drag_values[1]]
    n_loops = 0
    max_loops = 10
    start_values = [None, None]

    while new_values != start_values:
        n_loops += 1
        start_values = [new_values[0], new_values[1]]
        for other in other_drag_values:
            if not other:
                continue
            this_on_right_of_other = statistics.mean(drag_values) > statistics.mean(
                other,
            )
            if other[0] <= new_values[0] <= other[1]:
                if this_on_right_of_other:
                    new_values[0] = other[1] + 1
                else:
                    new_values[0] = other[0] - 1

            if other[0] <= new_values[1] <= other[1]:
                if this_on_right_of_other:
                    new_values[1] = other[1] + 1
                else:
                    new_values[1] = other[0] - 1

            if new_values[0] <= other[0] and new_values[1] >= other[1]:
                if this_on_right_of_other:
                    new_values[0] = other[1] + 1
                else:
                    new_values[1] = other[0] - 1

        if n_loops > max_loops:
            msg = "Infinite loop detected in range slider callback."
            raise RuntimeError(msg)
    return new_values
