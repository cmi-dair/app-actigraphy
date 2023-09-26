"""Defines the callbacks for the Actigraphy app."""
import datetime
import logging

import dash

from actigraphy.core import callback_manager, components, config, utils
from actigraphy.io import data_import, minor_files
from actigraphy.plotting import sensor_plots

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

manager = callback_manager.CallbackManager()


def _toggle_vector_value(new_value: int, index: int, file_path: str) -> None:
    """Toggles the value of a vector at a given index in a file.

    Args:
        new_value: The new value to set at the given index.
        index: The index of the vector to toggle.
        file_path: The path to the file containing the vector.

    """
    logger.debug(
        "Setting index %s to value %s for file %s", index, new_value, file_path
    )
    vector = minor_files.read_vector(file_path)
    vector[index] = new_value
    minor_files.write_vector(file_path, vector)


@manager.callback(
    [
        dash.Output("annotations-data", "children"),
        dash.Output("loading", "children"),
        dash.Output("insert-user", "displayed"),
        dash.Output("file_manager", "data"),
    ],
    dash.Input("load_file_button", "n_clicks"),
    dash.State("my-dropdown", "value"),
    dash.State("evaluator_name", "value"),
    prevent_initial_call=True,
)
def parse_files(
    n_clicks: int,  # pylint: disable=unused-argument n_clicks intentionallty unused.
    filepath: str,
    evaluator_name: str,
):
    """
    Parses the contents of the selected files and returns the UI components to be displayed.

    Args:
        n_clicks: The number of times the parse button has been clicked. Used to trigger
            the callback.
        filepath: The path to the selected file.
        evaluator_name: The name of the evaluator.

    Returns:
        tuple: A tuple containing the UI components to be displayed, an empty
        string, a boolean indicating whether parsing was successful, and the
        file manager object.
    """
    logger.debug("Parsing files...")
    if not evaluator_name:
        return "", "", True, None

    file_manager = utils.FileManager(base_dir=filepath).__dict__
    n_midnights = len(data_import.get_midnights(file_manager["base_dir"]))
    minor_files.initialize_files(file_manager, evaluator_name)

    ui_components = [
        components.day_slider(file_manager["identifier"], n_midnights),
        components.finished_checkbox(),
        components.switches(),
        components.graph(),
        components.app_license(),
    ]
    return (
        ui_components,
        "",
        False,
        file_manager,
    )


@manager.callback(
    dash.Output("multiple_sleep", "on"),
    dash.Output("exclude-night", "on"),
    dash.Output("review-night", "on"),
    dash.Input("day_slider", "value"),
    dash.State("file_manager", "data"),
)
def update_switches(day: int, file_manager: dict[str, str]) -> tuple[bool, bool, bool]:
    """Reads the sleep logs for the given day from the file manager and returns a
    tuple of boolean values indicating whether there are naps, missing sleep,
    and reviewed nights for that day.

    Args:
        day: The day for which to retrieve the sleep logs.
        file_manager: A dictionary containing file paths for various sleep log
            files.

    Returns:
        tuple[bool, bool, bool]: A tuple of boolean values indicating whether
            there are naps, missing sleep, and reviewed nights for the given
            day.
    """
    logger.debug("Entering update switches callback")
    naps = minor_files.read_vector(file_manager["multiple_sleeplog_file"])
    missing = minor_files.read_vector(file_manager["missing_sleep_file"])
    nights = minor_files.read_vector(file_manager["review_night_file"])
    return bool(naps[day]), bool(missing[day]), bool(nights[day])


@manager.callback(
    dash.Output("sleep-onset", "children", allow_duplicate=True),
    dash.Output("sleep-offset", "children", allow_duplicate=True),
    dash.Output("sleep-duration", "children", allow_duplicate=True),
    dash.Output("my-range-slider", "value"),
    dash.Input("day_slider", "value"),
    dash.Input("file_manager", "data"),
    prevent_initial_call=True,
)
def refresh_range_slider(
    day: int, file_manager: dict[str, str]
) -> tuple[str, str, str, list[int]]:
    """Reads the sleep logs for the given day from the file manager and returns
    the sleep onset, sleep offset, and sleep duration as strings.

    Args:
        day: The day for which to retrieve the sleep logs.
        file_manager: A dictionary containing file paths for various sleep log
            files.

    Returns:
        tuple[str, str, str]: A tuple of strings containing the sleep onset,
            sleep offset, and sleep duration.
    """
    logger.debug("Entering refresh range slider callback")
    dates = data_import.get_dates(file_manager)

    sleep_onset, wake_up = minor_files.read_sleeplog(file_manager["sleeplog_file"])
    sleep_time = datetime.datetime.fromisoformat(sleep_onset[day])
    wake_time = datetime.datetime.fromisoformat(wake_up[day])

    sleep_point = utils.time2point(sleep_time, dates[day])
    wake_point = utils.time2point(wake_time, dates[day])

    return (
        f"Sleep onset: {sleep_time.strftime('%A - %d %B %Y %H:%M')}\n",
        f"Sleep offset: {wake_time.strftime('%A - %d %B %Y %H:%M')}\n",
        f"Sleep duration: {utils.datetime_delta_as_hh_mm(wake_time - sleep_time)}\n",
        [sleep_point, wake_point],
    )


@manager.callback(
    dash.Output("annotations-save", "children"),
    dash.Output("sleep-onset", "children", allow_duplicate=True),
    dash.Output("sleep-offset", "children", allow_duplicate=True),
    dash.Output("sleep-duration", "children", allow_duplicate=True),
    dash.Input("my-range-slider", "value"),
    dash.State("file_manager", "data"),
    dash.State("day_slider", "value"),
    prevent_initial_call=True,
)
def adjust_range_slider(drag_value: list[int], file_manager: dict[str, str], day: int):
    """Adjusts the text labels fora  given day and writes the sleep log to a file.

    Args:
        drag_value: The drag values of the range slider.
        file_manager: The file manager containing the sleep log.
        day: The day for which to adjust the range slider.

    Returns:
        Tuple[str, str, str, str]: A tuple containing the sleep onset, sleep offset, and sleep duration.
    """
    logger.debug("Entering write info callback")
    dates = data_import.get_dates(file_manager)
    minor_files.write_sleeplog(file_manager, day, drag_value[0], drag_value[1])

    sleep_time = utils.point2time(drag_value[0], dates[day])
    wake_time = utils.point2time(drag_value[1], dates[day])

    return (
        "",
        f"Sleep onset: {sleep_time.strftime('%A - %d %B %Y %H:%M')}\n",
        f"Sleep offset: {wake_time.strftime('%A - %d %B %Y %H:%M')}\n",
        f"Sleep duration: {utils.datetime_delta_as_hh_mm(wake_time - sleep_time)}\n",
    )


@manager.callback(
    dash.Output("check-done", "children"),
    dash.Input("are-you-done", "value"),
    dash.State("file_manager", "data"),
)
def write_log_done(is_user_done: bool, file_manager: dict[str, str]) -> bool:
    """Writes a log message indicating that the analysis has been completed.

    Args:
        is_user_done: Whether the user has completed the analysis.
        file_manager: A dictionary containing information about the file being analyzed.
    """
    logger.debug("Entering write log done callback")
    if is_user_done:
        minor_files.write_log_analysis_completed(
            file_manager["identifier"], file_manager["completed_analysis_file"]
        )
    return is_user_done


@manager.callback(
    dash.Output("null-data", "children", allow_duplicate=True),
    dash.Input("exclude-night", "on"),
    dash.State("day_slider", "value"),
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def toggle_exclude_night(
    exclude_button: bool, day: int, file_manager: dict[str, str]
) -> None:
    """Toggles the exclusion of a night in the missing sleep file.

    Args:
        exclude_button: Whether to exclude the night or not.
        day : The day to toggle the exclusion for.
        file_manager: A dictionary containing file paths for the missing sleep file.
    """
    _toggle_vector_value(exclude_button, day, file_manager["missing_sleep_file"])


@manager.callback(
    dash.Output("null-data", "children", allow_duplicate=True),
    dash.Input("review-night", "on"),
    dash.State("day_slider", "value"),
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def toggle_review_night(
    review_night: int, day: int, file_manager: dict[str, str]
) -> None:
    """
    Toggles the review night flag for a given day in the review night file.

    Args:
        review_night: The new review night flag value (0 or 1).
        day: The day index to toggle the flag for.
        file_manager: A dictionary containing file paths for the review night file.
    """
    _toggle_vector_value(bool(review_night), day, file_manager["review_night_file"])


@manager.callback(
    dash.Output("null-data", "children", allow_duplicate=True),
    dash.Input("multiple_sleep", "on"),
    dash.State("day_slider", "value"),
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def toggle_nap(multiple_sleep: bool, day: int, file_manager: dict[str, str]):
    """
    Toggles the nap status for a given day in the multiple sleep log file.

    Args:
        multiple_sleep:: The new nap status for the given day.
        day: The day to toggle the nap status for.
        file_manager: A dictionary containing file paths for various files.
    """
    _toggle_vector_value(multiple_sleep, day, file_manager["multiple_sleeplog_file"])


@manager.callback(
    dash.Output("graph", "figure"),
    dash.Input("day_slider", "value"),
    dash.Input("my-range-slider", "value"),
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def create_graph(day: int, drag_value: list[int], file_manager: dict[str, str]) -> dict:
    """Creates a graph for a given day using data from the file manager.

    Args:
        day: The day for which to create the graph (0-indexed).
        drag_value: The drag value for the slider.
        file_manager: The file manager containing the data.

    Returns:
        dict: The figure object representing the graph.
    """
    logger.debug("Entering create graph callback")

    dates = data_import.get_dates(file_manager)
    n_points_per_day = data_import.get_n_points_per_day(file_manager)

    day_1_sensor_angles, day_1_arm_movement, day_1_non_wear = data_import.create_graph(
        file_manager, day
    )
    if day < len(dates):
        (
            day_2_sensor_angles,
            day_2_arm_movement,
            day_2_non_wear,
        ) = data_import.create_graph(file_manager, day + 1)
    else:
        day_2_sensor_angles = [0] * n_points_per_day
        day_2_arm_movement = [-210] * n_points_per_day
        day_2_non_wear = [0] * n_points_per_day

    sensor_angle = day_1_sensor_angles[n_points_per_day // 2 :] + day_2_sensor_angles
    arm_movement = day_1_arm_movement[n_points_per_day // 2 :] + day_2_arm_movement
    nonwear = day_1_non_wear[n_points_per_day // 2 :] + day_2_non_wear

    title_day = f"Day {day+1}: {dates[day].strftime('%A - %d %B %Y')}"  # Frontend uses 1-indexed days.
    day_timestamps = [dates[day]] * (n_points_per_day // 2) + (
        [dates[day] + datetime.timedelta(days=1)]
    ) * n_points_per_day

    timestamp = [
        " ".join(
            [
                day_timestamps[point].strftime("%d/%b/%Y"),
                utils.point2time_timestamp(point, n_points_per_day, offset=12),
            ]
        )
        for point in range(len(day_timestamps))
    ]

    nonwear_changes = []
    for index in range(1, len(nonwear)):
        if nonwear[index] != nonwear[index - 1]:
            nonwear_changes += [index]
    if nonwear[0]:
        nonwear_changes.insert(0, 0)
    if len(nonwear_changes) % 2 != 0:
        nonwear_changes.append(len(timestamp) - 1)

    figure = sensor_plots.build_sensor_plot(
        timestamp, sensor_angle, arm_movement, title_day
    )

    rectangle_timepoints = utils.slider_values_to_graph_values(
        drag_value, n_points_per_day
    )

    if rectangle_timepoints[0] != rectangle_timepoints[1]:
        sensor_plots.add_rectangle(figure, rectangle_timepoints, "red", "sleep window")
    for index in range(0, len(nonwear_changes), 2):
        sensor_plots.add_rectangle(
            figure,
            [nonwear_changes[index], nonwear_changes[index + 1]],
            "green",
            "non-wear",
        )
    return figure
