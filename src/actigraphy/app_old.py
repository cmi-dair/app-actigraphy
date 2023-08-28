# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import argparse
import calendar
import csv
import datetime
import logging
import pathlib

import dash
import dash_bootstrap_components as dbc
import dash_daq as daq
import numpy as np
import pandas as pd
import plotly.graph_objects as go
from dash import Input, Output, State, dcc, html

from actigraphy.core import config, utils
from actigraphy.io import minor_files
from actigraphy.plotting import graphs

settings = config.get_settings()
APP_NAME = settings.APP_NAME
APP_COLORS = settings.APP_COLORS
LOGGER_NAME = settings.LOGGER_NAME

config.initialize_logger()
logger = logging.getLogger(LOGGER_NAME)

app = dash.Dash(APP_NAME, external_stylesheets=[dbc.themes.BOOTSTRAP])

parser = argparse.ArgumentParser(
    description="""Actigraphy APP to manually correct annotations for the sleep log diary. """,
    epilog="""APP developed by Child Mind Institute.""",
)
parser.add_argument("input_folder", help="GGIR output folder", type=pathlib.Path)
args = parser.parse_args()

input_datapath = args.input_folder
files = [str(x) for x in sorted(input_datapath.glob("output_*"))]

log_path = input_datapath / "logs"
log_path.mkdir(exist_ok=True)


def create_datacleaning(identifier):
    filename = "missing_sleep_" + identifier + ".csv"
    filename_path = log_path / filename

    data = ["0" for ii in range(0, graph_data.daycount - 1)]

    with open(filename_path, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(data)


def save_datacleaning(identifier, datacleaning_log):
    filename = "missing_sleep_" + identifier + ".csv"
    filename_path = log_path / filename

    with open(filename_path, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(datacleaning_log)


def open_datacleaning(identifier):
    filename = "missing_sleep_" + identifier + ".csv"
    filename_path = log_path / filename

    df = pd.read_csv(filename_path, header=None)
    datacleaning = [df.iloc[0, idx] for idx in range(0, graph_data.daycount - 1)]

    return datacleaning


def create_multiple_sleeplog(identifier):
    filename = "multiple_sleeplog_" + identifier + ".csv"
    filename_path = log_path / filename

    data = ["0" for ii in range(0, graph_data.daycount - 1)]

    with open(filename_path, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(data)


def save_multiple_sleeplog(identifier, multiple_log):
    filename = "multiple_sleeplog_" + identifier + ".csv"
    filename_path = log_path / filename

    data = multiple_log

    with open(filename_path, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(data)


def open_multiple_sleeplog(identifier):
    filename = "multiple_sleeplog_" + identifier + ".csv"
    filename_path = log_path / filename

    df = pd.read_csv(filename_path, header=None)
    multiple_sleep = [df.iloc[0, idx] for idx in range(0, graph_data.daycount - 1)]

    return multiple_sleep


def create_review_night_file(identifier):
    filename = "review_night_" + identifier + ".csv"
    filename_path = log_path / filename

    dataline = ["0" for ii in range(1, graph_data.daycount)]

    with open(filename_path, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(dataline)


def save_review_night(identifier, review_night):
    filename = "review_night_" + identifier + ".csv"
    filename_path = log_path / filename

    data = review_night

    with open(filename_path, "w", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(data)


def open_review_night(identifier):
    filename = "review_night_" + identifier + ".csv"
    filename_path = log_path / filename

    df = pd.read_csv(filename_path, header=None)
    vec_nights = [df.iloc[0, idx] for idx in range(0, graph_data.daycount - 1)]

    return vec_nights


def store_sleep_diary(day, sleep, wake):
    if sleep == 0 and wake == 0:
        graph_data.vec_line[(day * 2) - 2] = 0
        graph_data.vec_line[day * 2 - 1] = 0
    else:
        sleeptime = utils.point2time(
            sleep, graph_data.axis_range, graph_data.npointsperday
        )
        waketime = utils.point2time(
            wake, graph_data.axis_range, graph_data.npointsperday
        )
        graph_data.vec_line[(day * 2) - 2] = sleeptime
        graph_data.vec_line[day * 2 - 1] = waketime

    return graph_data.vec_line


def store_excluded_night(day):
    excl_night = graph_data.excl_night
    excl_night[day - 1] = 1

    return excl_night


app.layout = html.Div(
    style={"backgroundColor": APP_COLORS.background},  # pylint: disable=no-member
    children=[
        html.Img(
            src="/assets/CMI_Logo_title.png", style={"height": "60%", "width": "60%"}
        ),
        html.Div(
            [
                dcc.ConfirmDialog(
                    id="insert-user",
                    message="Insert the evaluator's name before continue",
                )
            ]
        ),
        html.Div(
            [
                dcc.Input(
                    id="input_name",
                    type="text",
                    placeholder="Insert evaluator's name",
                    disabled=False,
                    size="40",
                ),
                dcc.Dropdown(files, id="my-dropdown", placeholder="Select subject..."),
                dbc.Spinner(html.Div(id="loading")),
            ],
            style={"padding": 10},
        ),
        html.Pre(id="annotations-data"),
    ],
)


@app.callback(
    [
        Output("annotations-data", "children"),
        Output("loading", "children"),
        Output("insert-user", "displayed"),
        Output("input_name", "disabled"),
    ],
    Input("my-dropdown", "value"),
    Input("input_name", "value"),
    suppress_callback_exceptions=True,
    prevent_initial_call=True,
)
def parse_contents(filename, name):
    global graph_data
    if not name:
        return "", "", True, False

    if not filename:
        return

    if "output_" in filename:
        print("Loading data ...")
        graph_data = graphs.create_graphs(pathlib.Path(filename))
        hour_vector = []
        sleep_tmp = []
        wake_tmp = []
        tmp_axis = int(graph_data.axis_range / 2)

        for ii in range(0, len(graph_data.vec_sleeponset)):
            sleep_tmp.append(
                utils.point2time(
                    graph_data.vec_sleeponset[ii],
                    graph_data.axis_range,
                    graph_data.npointsperday,
                )
            )
            wake_tmp.append(
                utils.point2time(
                    graph_data.vec_wake[ii],
                    graph_data.axis_range,
                    graph_data.npointsperday,
                )
            )

        for jj in range(0, graph_data.daycount - 1):
            hour_vector.append(sleep_tmp[jj])
            hour_vector.append(wake_tmp[jj])

        # Checking for a previous sleeplog file
        if (
            input_datapath / ("logs/sleeplog_" + graph_data.identifier + ".csv")
        ).exists():
            print(
                "Participant ",
                graph_data.identifier,
                "has a sleeplog. Loading existing file",
            )
        else:
            print(
                "Participant ",
                graph_data.identifier,
                "does not have a sleeplog. Loading sleepdata from GGIR",
            )
            minor_files.save_ggir(hour_vector, log_path / filename)

        # Checking for a previous nights do review file
        if (
            input_datapath / ("logs/review_night_" + graph_data.identifier + ".csv")
        ).exists():
            print(
                "Participant ",
                graph_data.identifier,
                "have a night review file. Loading existing file",
            )
        else:
            print(
                "Participant ",
                graph_data.identifier,
                "does not have a night review file. Creating a new one.",
            )
            create_review_night_file(graph_data.identifier)

        # Checking for a multiple sleeplog (nap times) file
        if (
            input_datapath
            / ("logs/multiple_sleeplog_" + graph_data.identifier + ".csv")
        ).exists():
            print(
                "Participant ",
                graph_data.identifier,
                "have a multiple sleeplog file. Loading existing file",
            )
        else:
            print(
                "Participant ",
                graph_data.identifier,
                "does not have a multiple sleeplog file. Creating a new one.",
            )
            create_multiple_sleeplog(graph_data.identifier)

        # Checking for data cleaning file
        if (
            input_datapath / ("logs/missing_sleep_" + graph_data.identifier + ".csv")
        ).exists():
            print(
                "Participant ",
                graph_data.identifier,
                "have a data cleaning file. Loading existing file",
            )
        else:
            print(
                "Participant ",
                graph_data.identifier,
                "does not have a data cleaning file. Creating a new one.",
            )
            create_datacleaning(graph_data.identifier)

        minor_files.save_log_file(
            name, log_path / "log_file.csv", graph_data.identifier
        )

        return (
            [
                html.Div(
                    [
                        html.B(
                            "* All changes will be automatically saved\n\n",
                            style={"color": "red"},
                        ),
                        html.B(
                            "Select day for participant " + graph_data.identifier + ": "
                        ),
                        dcc.Slider(
                            1,
                            graph_data.daycount - 1,
                            1,
                            value=1,
                            id="day_slider",
                        ),
                    ],
                    style={"margin-left": "20px", "padding": 10},
                ),
                dcc.Checklist(
                    [" I'm done and I would like to proceed to the next participant. "],
                    id="are-you-done",
                    style={"margin-left": "50px"},
                ),
                html.Pre(id="check-done"),
                daq.BooleanSwitch(
                    id="multiple_sleep",
                    on=False,
                    label=" Does this participant have multiple sleep periods in this 24h period?",
                ),
                html.Pre(id="checklist-items"),
                daq.BooleanSwitch(
                    id="exclude-night",
                    on=False,
                    label=" Does this participant have more than 2 hours of missing sleep data from 8PM to 8AM?",
                ),
                html.Pre(id="checklist-items2"),
                daq.BooleanSwitch(
                    id="review-night",
                    on=False,
                    label=" Do you need to review this night?",
                ),
                dcc.Graph(id="graph"),
                html.Div(
                    [
                        html.B(id="sleep-onset"),
                        html.B(id="sleep-offset"),
                        html.B(id="sleep-duration"),
                    ],
                    style={"margin-left": "80px", "margin-right": "55px"},
                ),
                html.Div(
                    [
                        dcc.RangeSlider(
                            min=0,
                            max=25920,
                            step=1,
                            marks={
                                i * tmp_axis: utils.hour_to_time_string(i)
                                for i in range(37)
                            },
                            id="my-range-slider",
                        ),
                        html.Pre(id="annotations-slider"),
                    ],
                    # html.Pre(id="annotations-nap"),
                    style={"margin-left": "55px", "margin-right": "55px"},
                ),
                # html.Button('Refresh graph', id='btn_clear', style={"margin-left": "15px"}),
                html.Pre(id="annotations-save"),
                html.P(
                    "\n\n     This software is licensed under the GNU Lesser General Public License v3.0\n     Permissions of this copyleft license are conditioned on making available complete source code of licensed works and modifications under the same license or\n     the GNU GPLv3. Copyright and license notices must be preserved.\n     Contributors provide an express grant of patent rights.\n     However, a larger work using the licensed work through interfaces provided by the licensed work may be distributed under different terms\n     and without source code for the larger work.",
                    style={"color": "gray"},
                ),
            ],
            "",
            False,
            True,
        )


@app.callback(Output("multiple_sleep", "on"), Input("day_slider", "value"))
def update_nap_switch(day):
    filename = "multiple_sleeplog_" + graph_data.identifier + ".csv"
    naps = open_multiple_sleeplog(graph_data.identifier)

    return naps[day - 1] != 0


@app.callback(Output("exclude-night", "on"), Input("day_slider", "value"))
def update_exclude_switch(day):
    missing = open_datacleaning(graph_data.identifier)

    return missing[day - 1] != 0


@app.callback(Output("review-night", "on"), Input("day_slider", "value"))
def update_review_night(day):
    nights = open_review_night(graph_data.identifier)

    return nights[day - 1] != 0


@app.callback(
    Output("graph", "figure"),
    Output("my-range-slider", "value"),
    Input("day_slider", "value"),
    Input("exclude-night", "on"),
    Input("review-night", "on"),
    Input("multiple_sleep", "on"),
    Input("my-range-slider", "value"),
    suppress_callback_exceptions=True,
)
def update_graph(day, exclude_button, review_night, nap, position):
    night_to_review = open_review_night(graph_data.identifier)
    nap_times = open_multiple_sleeplog(graph_data.identifier)
    night_to_exclude = open_datacleaning(graph_data.identifier)

    sleeplog_file = log_path / ("sleeplog_" + graph_data.identifier + ".csv")
    sleeponset, wakeup = minor_files.read_sleeplog(sleeplog_file)
    vec_sleeponset = utils.time2point(sleeponset[day - 1])
    vec_wake = utils.time2point(wakeup[day - 1])

    end_value = []
    begin_value = []

    month_1 = calendar.month_abbr[int(graph_data.ddate_new[day - 1][5:7])]
    day_of_week_1 = datetime.datetime.fromisoformat(graph_data.ddate_new[day - 1])
    day_of_week_1 = day_of_week_1.strftime("%A")

    if day < graph_data.daycount - 1:
        month_2 = calendar.month_abbr[int(graph_data.ddate_new[day][5:7])]
        day_of_week_2 = datetime.datetime.fromisoformat(graph_data.ddate_new[day])
        day_of_week_2 = day_of_week_2.strftime("%A")

    title_day = f"Day {day}: {day_of_week_1} - {graph_data.ddate_new[day - 1][8:]} {month_1} {graph_data.ddate_new[day - 1][0:4]}"

    # Getting the timestamp (one minute resolution) and transforming it to dataframe
    # Need to do this to plot the time on the graph hover
    if day < graph_data.daycount - 1:
        timestamp_day1 = [
            graph_data.ddate_new[day - 1]
            for x in range(int(graph_data.npointsperday / 2))
        ]
        timestamp_day2 = [
            graph_data.ddate_new[day] for x in range(graph_data.npointsperday)
        ]
        timestamp = timestamp_day1 + timestamp_day2

        timestamp = [
            (
                timestamp[x]
                + utils.point2time_timestamp(
                    x, graph_data.axis_range, graph_data.npointsperday
                )
            )
            for x in range(
                0, graph_data.npointsperday + int(graph_data.npointsperday / 2)
            )
        ]

        df = pd.DataFrame(index=timestamp)
        df["vec_ang"] = np.concatenate(
            (
                graph_data.vec_ang[day - 1, :],
                graph_data.vec_ang[day, 0 : int(graph_data.npointsperday / 2)],
            )
        )
        df["vec_acc"] = np.concatenate(
            (
                graph_data.vec_acc[day - 1, :],
                graph_data.vec_acc[day, 0 : int(graph_data.npointsperday / 2)],
            )
        )
        df["non_wear"] = np.concatenate(
            (
                graph_data.vec_nonwear[day - 1, :],
                graph_data.vec_nonwear[day, 0 : int(graph_data.npointsperday / 2)],
            )
        )
    else:  # in case this is the last day
        # Adding one more day to the day vector
        curr_date = graph_data.ddate_new[day - 1]
        list_temp = list(curr_date)
        temp = int(curr_date[8:]) + 1

        if len(str(temp)) == 1:
            temp = "0" + str(temp)
        else:
            temp = str(temp)

        list_temp[8:] = temp
        curr_date = "".join(list_temp)

        timestamp_day1 = [
            graph_data.ddate_new[day - 1]
            for x in range(int(graph_data.npointsperday / 2))
        ]
        timestamp_day2 = [curr_date for x in range(graph_data.npointsperday)]
        timestamp = timestamp_day1 + timestamp_day2

        timestamp = [
            (
                timestamp[x]
                + utils.point2time_timestamp(
                    x, graph_data.axis_range, graph_data.npointsperday
                )
            )
            for x in range(
                0, graph_data.npointsperday + int(graph_data.npointsperday / 2)
            )
        ]

        vec_end = [0 for x in range(int(graph_data.npointsperday / 2))]
        vec_end_acc = [-210 for x in range(int(graph_data.npointsperday / 2))]

        df = pd.DataFrame(index=timestamp)
        df["vec_ang"] = np.concatenate((graph_data.vec_ang[day - 1, :], vec_end))
        df["vec_acc"] = np.concatenate((graph_data.vec_acc[day - 1, :], vec_end_acc))
        df["non_wear"] = np.concatenate((graph_data.vec_nonwear[day - 1, :], vec_end))

    fig = go.Figure()
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df.vec_ang,
            mode="lines",
            name="Angle of sensor's z-axis",
            line_color="blue",
        )
    )
    fig.add_trace(
        go.Scatter(
            x=df.index,
            y=df.vec_acc,
            mode="lines",
            name="Arm movement",
            line_color="black",
        )
    )

    fig.update_layout(
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    fig.update_layout(title=title_day)

    sleep_split = sleeponset[day - 1].split(":")
    if int(sleep_split[1]) < 10:
        sleep_split[1] = "0" + sleep_split[1]
    new_sleep = sleep_split[0] + ":" + sleep_split[1]

    if vec_sleeponset < int(graph_data.npointsperday / 2):
        new_sleep = graph_data.ddate_new[day - 1] + new_sleep
    elif vec_sleeponset > int(graph_data.npointsperday / 2) and (
        day == graph_data.daycount - 1
    ):
        new_sleep = graph_data.ddate_new[day - 1] + new_sleep
    else:
        new_sleep = graph_data.ddate_new[day] + new_sleep

    wake_split = wakeup[day - 1].split(":")
    if int(wake_split[1]) < 10:
        wake_split[1] = "0" + wake_split[1]
    new_wake = wake_split[0] + ":" + wake_split[1]

    if vec_wake < int(graph_data.npointsperday / 2):
        new_wake = graph_data.ddate_new[day - 1] + new_wake
    elif vec_wake > int(graph_data.npointsperday / 2) and (
        day == graph_data.daycount - 1
    ):
        new_wake = graph_data.ddate_new[day - 1] + new_wake
    elif vec_wake > int(graph_data.npointsperday):
        new_wake = graph_data.ddate_new[day] + new_wake
    else:
        new_wake = graph_data.ddate_new[day] + new_wake

    if (
        new_sleep[-4:] == "3:00" and new_wake[-4:] == "3:00"
    ):  # Getting the last four characters from the string containing day and time
        fig.add_vrect(
            x0=new_sleep, x1=new_wake, line_width=0, fillcolor="red", opacity=0.2
        )
    else:
        fig.add_vrect(
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
        begin_value = np.where(np.diff(graph_data.vec_nonwear[day - 1]) == 1)
        begin_value = begin_value[0] + 180
        end_value = np.where(np.diff(graph_data.vec_nonwear[day - 1]) == -1)
        end_value = end_value[0] + 180
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

    new_end_value = []
    new_begin_value = []
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
            rect_data, graph_data.axis_range, graph_data.npointsperday
        )
        new_end_value = utils.point2time_timestamp(
            rect_data_final[ii], graph_data.axis_range, graph_data.npointsperday
        )

        # need to control for different days (non-wear marker after midnight)
        if rect_data >= 8640:
            fig.add_vrect(
                x0=graph_data.ddate_new[day] + new_begin_value,
                x1=graph_data.ddate_new[day] + new_end_value,
                line_width=0,
                fillcolor="green",
                opacity=0.5,
            )
            fig.add_annotation(
                text="nonwear",
                y=75,
                x=graph_data.ddate_new[day] + new_begin_value,
                xanchor="left",
                showarrow=False,
            )
        else:
            if rect_data_final[ii] >= 8640:
                fig.add_vrect(
                    x0=graph_data.ddate_new[day - 1] + new_begin_value,
                    x1=graph_data.ddate_new[day] + new_end_value,
                    line_width=0,
                    fillcolor="green",
                    opacity=0.5,
                )
                fig.add_annotation(
                    text="nonwear",
                    y=75,
                    x=graph_data.ddate_new[day - 1] + new_begin_value,
                    xanchor="left",
                    showarrow=False,
                )
            else:
                fig.add_vrect(
                    x0=graph_data.ddate_new[day - 1] + new_begin_value,
                    x1=graph_data.ddate_new[day - 1] + new_end_value,
                    line_width=0,
                    fillcolor="green",
                    opacity=0.5,
                )
                fig.add_annotation(
                    text="nonwear",
                    y=75,
                    x=graph_data.ddate_new[day - 1] + new_begin_value,
                    xanchor="left",
                    showarrow=False,
                )

    fig.update_xaxes(
        ticktext=[utils.hour_to_time_string(time) for time in range(0, 37)],
    )

    fig.update_layout(showlegend=True)
    fig.update_yaxes(visible=False, showticklabels=False)

    night_to_exclude[day - 1] = 1 if exclude_button else 0
    night_to_review[day - 1] = 1 if review_night else 0
    nap_times[day - 1] = 1 if nap else 0

    excluded_night_file = log_path / (
        "data_cleaning_file_" + graph_data.identifier + ".csv"
    )
    minor_files.save_excluded_night(
        graph_data.identifier, night_to_exclude, excluded_night_file
    )
    save_datacleaning(graph_data.identifier, night_to_exclude)
    print("Nights to exclude: ", night_to_exclude)

    save_review_night(graph_data.identifier, night_to_review)
    print("Nights to review: ", night_to_review)

    save_multiple_sleeplog(graph_data.identifier, nap_times)
    print("Nap times: ", nap_times)

    return fig, [int(vec_sleeponset), int(vec_wake)]


@app.callback(Output("check-done", "children"), Input("are-you-done", "value"))
def save_log_done(value):
    if not value:
        print("Sleep log analysis not completed yet.")
    else:
        minor_files.save_log_analysis_completed(
            graph_data.identifier,
            log_path / "participants_with_completed_analysis.csv",
        )


@app.callback(
    Output("annotations-save", "children"),
    Output("sleep-onset", "children"),
    Output("sleep-offset", "children"),
    Output("sleep-duration", "children"),
    Input("my-range-slider", "drag_value"),
    State("day_slider", "value"),
)
def save_info(drag_value, day):
    if not drag_value:
        return "", "", "", ""

    sleeplog_file = log_path / ("sleeplog_" + graph_data.identifier + ".csv")

    minor_files.save_sleeplog(
        graph_data, day, drag_value[0], drag_value[1], sleeplog_file
    )
    sleep_time = utils.point2time(
        drag_value[0], graph_data.axis_range, graph_data.npointsperday
    )
    wake_time = utils.point2time(
        drag_value[1], graph_data.axis_range, graph_data.npointsperday
    )
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
    app.run_server(debug=False, port=8051)
