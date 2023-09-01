# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import datetime
import logging

import dash
import dash_bootstrap_components
import numpy as np
from dash import dcc, html
from plotly import graph_objects

from actigraphy.core import cli, components, config, utils
from actigraphy.io import minor_files
from actigraphy.plotting import graphs

settings = config.get_settings()
APP_NAME = settings.APP_NAME
APP_COLORS = settings.APP_COLORS
LOGGER_NAME = settings.LOGGER_NAME

config.initialize_logger(logging_level=logging.DEBUG)
logger = logging.getLogger(LOGGER_NAME)

app = dash.Dash(
    APP_NAME, external_stylesheets=[dash_bootstrap_components.themes.BOOTSTRAP]
)
args = cli.parse_args()
subject_directories = cli.get_subject_folders(args)

app.layout = html.Div(
    (
        dcc.Store(id="file_manager", storage_type="session"),
        dcc.Store(id="check-done", storage_type="session"),
        dcc.Store(id="annotations-save", storage_type="session"),
        components.header(),
        components.no_evaluator_error(),
        components.file_selection(subject_directories),
        html.Pre(id="annotations-data"),
    ),
    style={"backgroundColor": APP_COLORS.background},  # pylint: disable=no-member
)


@app.callback(
    [
        dash.Output("annotations-data", "children"),
        dash.Output("loading", "children"),
        dash.Output("insert-user", "displayed"),
        dash.Output("file_manager", "data"),
    ],
    dash.State("my-dropdown", "value"),
    dash.State("evaluator_name", "value"),
    dash.Input("load_file_button", "n_clicks"),
    prevent_initial_call=True,
)
def parse_contents(
    filepath: str, evaluator_name: str, n_clicks: int  # pylint: disable=unused-argument
):
    logger.debug("Entering parse contents callback")
    # n_clicks is only used to trigger this function and is intentionally not used.
    global graph_data
    if not evaluator_name:
        return "", "", True, None

    file_manager = utils.FileManager(base_dir=filepath).__dict__
    daycount = graphs.get_daycount(file_manager["base_dir"])
    minor_files.initialize_files(file_manager, evaluator_name)
    graph_data = graphs.create_graphs(file_manager)

    axis_range = graphs.get_axis_range(file_manager)
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


@app.callback(
    dash.Output("multiple_sleep", "on"),
    dash.Input("day_slider", "value"),
    dash.State("file_manager", "data"),
)
def update_nap_switch(day, file_manager: dict[str, str]) -> bool:
    logger.debug("Entering update nap switch callback")
    naps = minor_files.read_vector(
        file_manager["multiple_sleeplog_file"],
    )
    return bool(naps[day - 1])


@app.callback(
    dash.Output("exclude-night", "on"),
    dash.Input("day_slider", "value"),
    dash.State("file_manager", "data"),
)
def update_exclude_switch(day, file_manager: dict[str, str]) -> bool:
    logger.debug("Entering update exclude night callback")
    missing = minor_files.read_vector(
        file_manager["missing_sleep_file"],
    )
    return bool(missing[day - 1])


@app.callback(
    dash.Output("review-night", "on"),
    dash.Input("day_slider", "value"),
    dash.State("file_manager", "data"),
)
def update_review_night(day, file_manager: dict[str, str]) -> bool:
    logger.debug("Entering update review night callback")
    nights = minor_files.read_vector(file_manager["review_night_file"])
    return bool(nights[day - 1])


@app.callback(
    dash.Output("graph", "figure"),
    dash.Output("my-range-slider", "value"),
    dash.Input("day_slider", "value"),
    dash.Input("exclude-night", "on"),
    dash.Input("review-night", "on"),
    dash.Input("multiple_sleep", "on"),
    dash.Input("my-range-slider", "value"),
    dash.State("file_manager", "data"),
)
def update_graph(day, exclude_button, review_night, nap, position, file_manager):
    # Position is intentionally not used.
    logger.debug("Entering update graph callback")
    daycount = graphs.get_daycount(file_manager["base_dir"])
    night_to_review = minor_files.read_vector(file_manager["review_night_file"])
    nap_times = minor_files.read_vector(file_manager["multiple_sleeplog_file"])
    night_to_exclude = minor_files.read_vector(file_manager["data_cleaning_file"])

    sleeponset, wakeup = minor_files.read_sleeplog(file_manager["sleeplog_file"])
    vec_sleeponset = utils.time2point(sleeponset[day - 1])
    vec_wake = utils.time2point(wakeup[day - 1])
    axis_range = graphs.get_axis_range(file_manager)
    dates = graphs.get_dates(file_manager)
    n_points_per_day = graphs.get_n_points_per_day(file_manager)

    title_day = f"Day {day}: {dates[day-1].strftime('%A - %d %B %Y')}"

    # Getting the timestamp (one minute resolution) and transforming it to dataframe
    # Need to do this to plot the time on the graph hover
    if day < daycount:
        timestamp_day1 = [dates[day - 1] for x in range(n_points_per_day // 2)]
        timestamp_day2 = [dates[day] for x in range(n_points_per_day)]
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

        vec_ang = np.concatenate(
            (
                graph_data.vec_ang[day - 1, :],
                graph_data.vec_ang[day, : n_points_per_day // 2],
            )
        )
        vec_acc = np.concatenate(
            (
                graph_data.vec_acc[day - 1, :],
                graph_data.vec_acc[day, : n_points_per_day // 2],
            )
        )
    else:  # in case this is the last day
        # Adding one more day to the day vector
        curr_date = dates[day - 1]
        list_temp = list(curr_date)
        temp = int(curr_date[8:]) + 1

        if len(str(temp)) == 1:
            temp = "0" + str(temp)
        else:
            temp = str(temp)

        list_temp[8:] = temp
        curr_date = "".join(list_temp)

        timestamp_day1 = [dates[day - 1] for x in range(n_points_per_day // 2)]
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

        vec_ang = np.concatenate((graph_data.vec_ang[day - 1, :], vec_end))
        vec_acc = np.concatenate((graph_data.vec_acc[day - 1, :], vec_end_acc))

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

    sleep_split = sleeponset[day - 1].split(":")
    if int(sleep_split[1]) < 10:
        sleep_split[1] = "0" + sleep_split[1]
    new_sleep = sleep_split[0] + ":" + sleep_split[1]

    if vec_sleeponset < n_points_per_day // 2:
        new_sleep = dates[day - 1].strftime("%d/%b/%Y") + " " + new_sleep
    elif vec_sleeponset > n_points_per_day // 2 and day == daycount:
        new_sleep = dates[day - 1].strftime("%d/%b/%Y") + " " + new_sleep
    else:
        new_sleep = dates[day].strftime("%d/%b/%Y") + " " + new_sleep

    wake_split = wakeup[day - 1].split(":")
    if int(wake_split[1]) < 10:
        wake_split[1] = "0" + wake_split[1]
    new_wake = wake_split[0] + ":" + wake_split[1]

    if vec_wake < n_points_per_day // 2:
        new_wake = dates[day - 1].strftime("%d/%b/%Y") + " " + new_wake
    elif vec_wake > n_points_per_day // 2 and day == daycount:
        new_wake = dates[day - 1].strftime("%d/%b/%Y") + " " + new_wake
    else:
        new_wake = dates[day].strftime("%d/%b/%Y") + " " + new_wake

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
    vec_for_the_day = np.concatenate(
        (graph_data.vec_nonwear[day - 1, :], graph_data.vec_nonwear[day - 1, 0:8620])
    )

    if int(vec_for_the_day[0]) == 0:
        begin_value = np.where(np.diff(graph_data.vec_nonwear[day - 1]) == 1)[0] + 180
        end_value = np.where(np.diff(graph_data.vec_nonwear[day - 1]) == -1)[0] + 180
    else:
        first_value = 0
        begin_value = np.where(np.diff(graph_data.vec_nonwear[day - 1]) == 1)
        begin_value = np.asarray(begin_value)
        begin_value = np.insert(begin_value, 0, first_value)
        begin_value = begin_value + 180
        begin_value = np.insert(begin_value, 0, first_value)
        end_value = np.where(np.diff(graph_data.vec_nonwear[day - 1]) == -1)
        end_value = end_value[0] + 180
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

    night_to_exclude[day - 1] = 1 if exclude_button else 0
    night_to_review[day - 1] = 1 if review_night else 0
    nap_times[day - 1] = 1 if nap else 0

    minor_files.write_vector(file_manager["missing_sleep_file"], night_to_exclude)
    minor_files.write_vector(file_manager["review_night_file"], night_to_review)
    minor_files.write_vector(file_manager["multiple_sleeplog_file"], nap_times)

    return figure, [int(vec_sleeponset), int(vec_wake)]


@app.callback(
    dash.Output("check-done", "children"),
    dash.Input("are-you-done", "value"),
    dash.State("file_manager", "data"),
)
def write_log_done(is_user_done, file_manager):
    logger.debug("Entering write log done callback")
    if not is_user_done:
        print("Sleep log analysis not completed yet.")
    else:
        minor_files.write_log_analysis_completed(
            file_manager["identifier"], file_manager["completed_analysis_file"]
        )


@app.callback(
    dash.Output("annotations-save", "children"),
    dash.Output("sleep-onset", "children"),
    dash.Output("sleep-offset", "children"),
    dash.Output("sleep-duration", "children"),
    dash.Input("my-range-slider", "drag_value"),
    dash.State("file_manager", "data"),
    dash.State("day_slider", "value"),
)
def write_info(drag_value, file_manager, day):
    logger.debug("Entering write info callback")
    if not drag_value:
        return "", "", "", ""

    axis_range = graphs.get_axis_range(file_manager)
    n_points_per_day = graphs.get_n_points_per_day(file_manager)
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


if __name__ == "__main__":
    app.run_server(debug=True, port=8051, dev_tools_hot_reload=True)
