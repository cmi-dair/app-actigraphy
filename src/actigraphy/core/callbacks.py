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


def _toggle_vector_value(new_value: bool, index: int, file_path: str) -> None:
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
    vector[index] = int(new_value)
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
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def refresh_range_slider(
    day: int, file_manager: dict[str, str]
) -> tuple[str, str, str]:
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
    _toggle_vector_value(review_night, day, file_manager["review_night_file"])


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
    dash.State("file_manager", "data"),
)
def create_graph(day: int, file_manager: dict[str, str]):
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

    return sensor_plots.build_sensor_plot(
        timestamp, sensor_angle, arm_movement, title_day
    )


"""
@manager.callback(
    dash.Output("graph", "figure"),
    dash.Output("my-range-slider", "value"),
    dash.Input("day_slider", "value"),
    dash.Input("my-range-slider", "value"),
    dash.State("file_manager", "data"),
)
def update_graph(day: int, position: Any, file_manager: dict[str, str]):
    # Position is intentionally not used.
    logger.debug("Entering update graph callback")
    daycount = data_import.get_daycount(file_manager["base_dir"])

    sleeponset, wakeup = minor_files.read_sleeplog(file_manager["sleeplog_file"])
    vec_sleeponset = utils.time2point(sleeponset[day])
    vec_wake = utils.time2point(wakeup[day])
    axis_range = data_import.get_axis_range(file_manager)
    dates = data_import.get_dates(file_manager)
    n_points_per_day = data_import.get_n_points_per_day(file_manager)

    vec_ang_day_1, vec_acc_day_1, vec_nonwear_day_1 = data_import.create_graph(
        file_manager, day
    )
    vec_ang_day_2, vec_acc_day_2, vec_nonwear_day_2 = data_import.create_graph(
        file_manager, day + 1
    )

    # Patchwork testfix
    vec_ang = np.stack((vec_ang_day_1, vec_ang_day_2))
    vec_acc = np.stack((vec_acc_day_1, vec_acc_day_2))
    vec_nonwear = np.stack((vec_nonwear_day_1, vec_nonwear_day_2))

    title_day = f"Day {day+1}: {dates[day].strftime('%A - %d %B %Y')}"  # Frontend uses 1-indexed days.

    # Getting the timestamp (one minute resolution) and transforming it to dataframe
    # Need to do this to plot the time on the graph hover
    timestamp_day1 = [dates[day] for x in range(n_points_per_day // 2)]
    if day < daycount:
        timestamp_day2 = [dates[day + 1] for x in range(n_points_per_day)]
        timestamp = timestamp_day1 + timestamp_day2
    else:
        curr_date = dates[day]
        list_temp = list(curr_date)
        temp = str(int(curr_date[8:]) + 1).zfill(2)

        list_temp[8:] = temp
        curr_date = "".join(list_temp)
        timestamp_day2 = [curr_date for x in range(n_points_per_day)]

    timestamp = [
        " ".join(
            [
                timestamp[x].strftime("%d/%b/%Y"),
                utils.point2time_timestamp(x, axis_range, n_points_per_day),
            ]
        )
        for x in range(int(n_points_per_day * 1.5))
    ]

    if day < daycount:
        vec_ang = np.concatenate((vec_ang[0, :], vec_ang[1, : n_points_per_day // 2]))
        vec_acc = np.concatenate((vec_acc[0, :], vec_acc[1, : n_points_per_day // 2]))
    else:
        vec_end = [0] * (n_points_per_day // 2)
        vec_end_acc = [-210] * (n_points_per_day // 2)

        vec_ang = np.concatenate((vec_ang[0, :], vec_end))
        vec_acc = np.concatenate((vec_acc[0, :], vec_end_acc))

    figure = graph_objects.Figure()

    figure.add_trace(
        graph_objects.Scatter(
            x=timestamp,
            y=vec_ang,
            mode="lines",
            name="Angle of sensor's z-axis",
            line_color="blue",
        )
    )
    figure.add_trace(
        graph_objects.Scatter(
            x=timestamp,
            y=vec_acc,
            mode="lines",
            name="Arm movement",
            line_color="black",
        )
    )

    figure.update_layout(
        legend={
            "orientation": "h",
            "yanchor": "bottom",
            "y": 1.02,
            "xanchor": "right",
            "x": 1,
        }
    )

    figure.update_layout(title=title_day)

    sleep_split = sleeponset[day].split(":")
    sleep_split[1] = sleep_split[1].zfill(2)
    new_sleep = sleep_split[0] + ":" + sleep_split[1]

    if vec_sleeponset < n_points_per_day // 2 or (
        vec_sleeponset > n_points_per_day // 2 and day == daycount
    ):
        new_sleep = dates[day].strftime("%d/%b/%Y") + " " + new_sleep
    else:
        new_sleep = dates[day + 1].strftime("%d/%b/%Y") + " " + new_sleep

    wake_split = wakeup[day].split(":")
    wake_split[1] = wake_split[1].zfill(2)
    new_wake = wake_split[0] + ":" + wake_split[1]

    import pdb

    pdb.set_trace()
    if vec_wake < n_points_per_day // 2 or (
        vec_wake > n_points_per_day // 2 and day == daycount
    ):
        new_wake = dates[day].strftime("%d/%b/%Y") + " " + new_wake
    else:
        new_wake = dates[day + 1].strftime("%d/%b/%Y") + " " + new_wake

    if (
        new_sleep[-5:] == "03:00" and new_wake[-5:] == "03:00"
    ):  # Getting the last four characters from the string containing day and time
        figure.add_vrect(
            x0=new_sleep, x1=new_wake, line_width=0, fillcolor="red", opacity=0.2
        )
    else:
        figure.add_vrect(
            x0=new_sleep,
            x1=new_wake,
            line_width=0,
            fillcolor="red",
            opacity=0.2,
            annotation_text="sleep window",
            annotation_position="top left",
        )

    # Nonwear
    vec_for_the_day = np.concatenate((vec_nonwear[0, :], vec_nonwear[0, 0:8620]))

    if vec_for_the_day[0] == 0:
        begin_value = np.where(np.diff(vec_nonwear[0]) == 1)[0]
        end_value = np.where(np.diff(vec_nonwear[0]) == -1)[0]
    else:
        first_value = 0
        begin_value = np.where(np.diff(vec_nonwear[0]) == 1)
        begin_value = np.asarray(begin_value)
        begin_value = np.insert(begin_value, 0, first_value)
        begin_value = np.insert(begin_value, 0, first_value)
        end_value = np.where(np.diff(vec_nonwear[0]) == -1)
        end_value = np.insert(end_value, 0, 179)

    rect_data_init = []
    rect_data_final = []

    if len(begin_value) > 0:
        rect_data_init.append(begin_value[0])

        for ii in range(0, len(begin_value) - 1):
            if begin_value[ii + 1] - end_value[ii] > 1:
                rect_data_init.append(begin_value[ii + 1])
                rect_data_final.append(end_value[ii])

        rect_data_final.append(end_value[-1])

    for ii, rect_data in enumerate(rect_data_init):
        if rect_data_final[ii] >= 17280:
            rect_data_final[ii] = 17279
        new_begin_value = utils.point2time_timestamp(
            rect_data, axis_range, n_points_per_day
        )
        new_end_value = utils.point2time_timestamp(
            rect_data_final[ii], axis_range, n_points_per_day
        )

        # need to control for different days (non-wear marker after midnight)
        if rect_data >= 8640:
            figure.add_vrect(
                x0=dates[day].strftime("%d/%b/%Y") + " " + new_begin_value,
                x1=dates[day].strftime("%d/%b/%Y") + " " + new_end_value,
                line_width=0,
                fillcolor="green",
                opacity=0.5,
            )
            figure.add_annotation(
                text="nonwear",
                y=75,
                x=dates[day].strftime("%d/%b/%Y") + " " + new_begin_value,
                xanchor="left",
                showarrow=False,
            )
        else:
            if rect_data_final[ii] >= 8640:
                figure.add_vrect(
                    x0=dates[day - 1].strftime("%d/%b/%Y") + " " + new_begin_value,
                    x1=dates[day].strftime("%d/%b/%Y") + " " + new_end_value,
                    line_width=0,
                    fillcolor="green",
                    opacity=0.5,
                )
                figure.add_annotation(
                    text="nonwear",
                    y=75,
                    x=dates[day - 1].strftime("%d/%b/%Y") + " " + new_begin_value,
                    xanchor="left",
                    showarrow=False,
                )
            else:
                figure.add_vrect(
                    x0=dates[day - 1].strftime("%d/%b/%Y") + " " + new_begin_value,
                    x1=dates[day - 1].strftime("%d/%b/%Y") + " " + new_end_value,
                    line_width=0,
                    fillcolor="green",
                    opacity=0.5,
                )
                figure.add_annotation(
                    text="nonwear",
                    y=75,
                    x=dates[day - 1].strftime("%d/%b/%Y") + " " + new_begin_value,
                    xanchor="left",
                    showarrow=False,
                )

    figure.update_layout(showlegend=True)
    figure.update_yaxes(visible=False, showticklabels=False)

    return figure
"""
