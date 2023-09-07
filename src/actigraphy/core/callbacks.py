import datetime
import logging

import dash
import numpy as np
from plotly import graph_objects

from actigraphy.core import callback_manager, components, config, utils
from actigraphy.io import data_import, minor_files

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)

manager = callback_manager.CallbackManager()


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
def parse_contents(
    n_clicks: int,  # pylint: disable=unused-argument n_clicks intentionallty unused.
    filepath: str,
    evaluator_name: str,
):
    logger.debug("Entering parse contents callback")
    if not evaluator_name:
        return "", "", True, None

    file_manager = utils.FileManager(base_dir=filepath).__dict__
    daycount = data_import.get_daycount(file_manager["base_dir"])
    minor_files.initialize_files(file_manager, evaluator_name)

    axis_range = data_import.get_axis_range(file_manager)
    ui_components = [
        components.day_slider(file_manager["identifier"], daycount),
        components.finished_checkbox(),
        components.switches(),
        components.graph(axis_range // 2),
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
    dash.Input("day_slider", "value"),
    dash.State("file_manager", "data"),
)
def update_nap_switch(day, file_manager: dict[str, str]) -> bool:
    logger.debug("Entering update nap switch callback")
    naps = minor_files.read_vector(
        file_manager["multiple_sleeplog_file"],
    )
    return bool(naps[day])


@manager.callback(
    dash.Output("exclude-night", "on"),
    dash.Input("day_slider", "value"),
    dash.State("file_manager", "data"),
)
def update_exclude_switch(day, file_manager: dict[str, str]) -> bool:
    logger.debug("Entering update exclude night callback")
    missing = minor_files.read_vector(
        file_manager["missing_sleep_file"],
    )
    return bool(missing[day])


@manager.callback(
    dash.Output("review-night", "on"),
    dash.Input("day_slider", "value"),
    dash.State("file_manager", "data"),
)
def update_review_night(day, file_manager: dict[str, str]) -> bool:
    logger.debug("Entering update review night callback")
    nights = minor_files.read_vector(file_manager["review_night_file"])
    return bool(nights[day])


@manager.callback(
    dash.Output("null-data", "children", allow_duplicate=True),
    dash.Input("my-range-slider", "drag_value"),
    dash.State("file_manager", "data"),
    dash.State("day_slider", "value"),
    prevent_initial_call=True,
)
def adjust_range_slider(drag_value, file_manager, day):
    logger.debug("Entering write info callback")
    if not drag_value:
        return "", "", "", ""

    axis_range = data_import.get_axis_range(file_manager)
    n_points_per_day = data_import.get_n_points_per_day(file_manager)

    minor_files.write_sleeplog(file_manager, day, drag_value[0], drag_value[1])

    sleep_time = utils.point2time(drag_value[0], axis_range, n_points_per_day)
    wake_time = utils.point2time(drag_value[1], axis_range, n_points_per_day)
    sleep_datetime = datetime.datetime.combine(datetime.date.today(), sleep_time)
    if wake_time < sleep_time:
        wake_datetime = datetime.datetime.combine(
            datetime.date.today() + datetime.timedelta(days=1), wake_time
        )
    else:
        wake_datetime = datetime.datetime.combine(datetime.date.today(), wake_time)
    delta = wake_datetime - sleep_datetime
    sleep_duration = utils.datetime_delta_as_hh_mm(delta)

    return (
        "",
        "Sleep onset: " + sleep_datetime.strftime("%H:%M") + "\n",
        "Sleep offset: " + wake_datetime.strftime("%H:%M") + "\n",
        "Sleep duration: " + sleep_duration,
    )


@manager.callback(
    dash.Output("check-done", "children"),
    dash.Input("are-you-done", "value"),
    dash.State("file_manager", "data"),
)
def write_log_done(is_user_done, file_manager):
    logger.debug("Entering write log done callback")
    if is_user_done:
        minor_files.write_log_analysis_completed(
            file_manager["identifier"], file_manager["completed_analysis_file"]
        )


@manager.callback(
    dash.Output("null-data", "children", allow_duplicate=True),
    dash.Input("exclude-night", "on"),
    dash.State("day_slider", "value"),
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def toggle_exclude_night(exclude_button, day, file_manager):
    logger.debug("Setting day %s to exclude: %s", day, exclude_button)
    night_to_exclude = minor_files.read_vector(file_manager["missing_sleep_file"])
    night_to_exclude[day] = int(exclude_button)
    minor_files.write_vector(file_manager["missing_sleep_file"], night_to_exclude)
    return None


@manager.callback(
    dash.Output("null-data", "children", allow_duplicate=True),
    dash.Input("review-night", "on"),
    dash.State("day_slider", "value"),
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def toggle_review_night(review_night, day, file_manager):
    logger.debug("Setting day %s to review: %s", day, review_night)
    night_to_review = minor_files.read_vector(file_manager["review_night_file"])
    night_to_review[day] = int(review_night)
    minor_files.write_vector(file_manager["review_night_file"], night_to_review)
    return None


@manager.callback(
    dash.Output("null-data", "children", allow_duplicate=True),
    dash.Input("multiple_sleep", "on"),
    dash.State("day_slider", "value"),
    dash.State("file_manager", "data"),
    prevent_initial_call=True,
)
def toggle_nap(multiple_sleep, day, file_manager):
    logger.debug("Setting day %s to nap: %s", day, multiple_sleep)
    nap_times = minor_files.read_vector(file_manager["multiple_sleeplog_file"])
    nap_times[day] = int(multiple_sleep)
    minor_files.write_vector(file_manager["multiple_sleeplog_file"], nap_times)
    return None


@manager.callback(
    dash.Output("graph", "figure"),
    dash.Output("my-range-slider", "value"),
    dash.Input("day_slider", "value"),
    dash.Input("my-range-slider", "value"),
    dash.State("file_manager", "data"),
)
def update_graph(day, position, file_manager):
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

        timestamp = [
            " ".join(
                [
                    timestamp[x].strftime("%d/%b/%Y"),
                    utils.point2time_timestamp(x, axis_range, n_points_per_day),
                ]
            )
            for x in range(int(n_points_per_day * 1.5))
        ]

        vec_ang = np.concatenate((vec_ang[0, :], vec_ang[1, : n_points_per_day // 2]))
        vec_acc = np.concatenate((vec_acc[0, :], vec_acc[1, : n_points_per_day // 2]))
    else:  # in case this is the last day
        # Adding one more day to the day vector
        curr_date = dates[day]
        list_temp = list(curr_date)
        temp = str(int(curr_date[8:]) + 1).zfill(2)

        list_temp[8:] = temp
        curr_date = "".join(list_temp)

        timestamp_day2 = [curr_date for x in range(n_points_per_day)]
        timestamp = timestamp_day1 + timestamp_day2

        timestamp = [
            " ".join(
                [
                    timestamp[x].strftime("%d/%b/%Y"),
                    utils.point2time_timestamp(x, axis_range, n_points_per_day),
                ]
            )
            for x in range(0, int(n_points_per_day * 1.5))
        ]

        vec_end = [0 for x in range(n_points_per_day // 2)]
        vec_end_acc = [-210 for x in range(n_points_per_day // 2)]

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
    if int(wake_split[1]) < 10:
        wake_split[1] = "0" + wake_split[1]
    new_wake = wake_split[0] + ":" + wake_split[1]

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

    if int(vec_for_the_day[0]) == 0:
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
    idx = 0

    if len(begin_value > 0):
        rect_data_init.append(begin_value[0])

        for ii in range(0, len(begin_value) - 1):
            if begin_value[ii + 1] - end_value[ii] > 1:
                idx = idx + 1
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

    return figure, [int(vec_sleeponset), int(vec_wake)]
