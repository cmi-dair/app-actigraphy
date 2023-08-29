# Run this app with `python app.py` and
# visit http://127.0.0.1:8050/ in your web browser.

import argparse
import calendar
import datetime
import logging
import pathlib
from os import path

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
subjects = [str(x) for x in sorted(input_datapath.glob("output_*"))]

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
                dcc.Dropdown(
                    subjects, id="my-dropdown", placeholder="Select subject..."
                ),
                dbc.Spinner(html.Div(id="loading")),
            ],
            style={"padding": 10},
        ),
        html.Pre(id="annotations-data"),
        html.Pre(id="file_manager"),
    ],
)


@app.callback(
    [
        Output("annotations-data", "children"),
        Output("loading", "children"),
        Output("insert-user", "displayed"),
        Output("input_name", "disabled"),
        Output("file_manager", "data"),
    ],
    Input("my-dropdown", "value"),
    Input("input_name", "value"),
    suppress_callback_exceptions=True,
    prevent_initial_call=True,
)
def parse_contents(filepath: str, name: str):
    global graph_data
    if not name:
        return "", "", True, False, None

    if not filepath or not "output_" in filepath:
        return

    file_manager = utils.FileManager(base_dir=filepath)
    graph_data = graphs.create_graphs(pathlib.Path(filepath))
    tmp_axis = int(graph_data.axis_range / 2)

    hour_vector = []
    for onset, wake in zip(graph_data.vec_sleeponset, graph_data.vec_wake):
        onset_time = utils.point2time(
            onset, graph_data.axis_range, graph_data.npointsperday
        )
        wake_time = utils.point2time(
            wake, graph_data.axis_range, graph_data.npointsperday
        )
        hour_vector.extend([onset_time, wake_time])

    if not path.exists(file_manager.sleeplog_file):
        minor_files.write_ggir(hour_vector, file_manager.sleeplog_file)

    vector_files = [
        "review_night_file",
        "multiple_sleeplog_file",
        "data_cleaning_file",
        "missing_sleep_file",
    ]
    for vector_file in vector_files:
        filepath = getattr(file_manager, vector_file)
        if not path.exists(filepath):
            minor_files.write_vector(filepath, [0] * graph_data.daycount)

    minor_files.write_log_file(name, file_manager.log_file, graph_data.identifier)

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
        file_manager.__dict__,
    )


@app.callback(
    Output("multiple_sleep", "on"),
    Input("day_slider", "value"),
    Input("file_manager", "data"),
)
def update_nap_switch(file_manager: dict[str, str], day) -> bool:
    naps = minor_files.read_vector(
        file_manager["multiple_sleeplog_file"], graph_data.daycount
    )
    return bool(naps[day - 1])


@app.callback(
    Output("exclude-night", "on"),
    Input("day_slider", "value"),
    Input("file_manager", "data"),
)
def update_exclude_switch(day, file_manager: dict[str, str]) -> bool:
    missing = minor_files.read_vector(
        file_manager["missing_sleep_file"], graph_data.daycount
    )
    return bool(missing[day - 1])


@app.callback(
    Output("review-night", "on"),
    Input("day_slider", "value"),
    Input("file_manager", "data"),
)
def update_review_night(day, file_manager: dict[str, str]) -> bool:
    nights = minor_files.read_vector(file_manager["review_night_file"], day)
    return bool(nights[day - 1])


@app.callback(
    Output("graph", "figure"),
    Output("my-range-slider", "value"),
    Input("day_slider", "value"),
    Input("exclude-night", "on"),
    Input("review-night", "on"),
    Input("multiple_sleep", "on"),
    Input("my-range-slider", "value"),
    Input("file_manager", "data"),
    suppress_callback_exceptions=True,
)
def update_graph(day, exclude_button, review_night, nap, position, file_manager):
    night_to_review = minor_files.read_vector(
        file_manager["review_night_file"], graph_data.daycount
    )
    nap_times = minor_files.read_vector(
        file_manager["multiple_sleeplog_file"], graph_data.daycount
    )
    night_to_exclude = minor_files.read_vector(
        file_manager["data_cleaning_file"], graph_data.daycount
    )

    sleeponset, wakeup = minor_files.read_sleeplog(file_manager["sleeplog_file"])
    vec_sleeponset = utils.time2point(sleeponset[day - 1])
    vec_wake = utils.time2point(wakeup[day - 1])

    month_1 = calendar.month_abbr[int(graph_data.ddate_new[day - 1][5:7])]
    day_of_week_1 = datetime.datetime.fromisoformat(graph_data.ddate_new[day - 1])
    day_of_week_1 = day_of_week_1.strftime("%A")

    if day < graph_data.daycount - 1:
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

    minor_files.write_excluded_night(
        graph_data.identifier, night_to_exclude, file_manager["data_cleaning_file"]
    )
    minor_files.write_vector(file_manager["missing_sleep_file"], night_to_exclude)
    minor_files.write_vector(file_manager["review_night_file"], night_to_review)
    minor_files.write_vector(file_manager["multiple_sleeplog_file"], nap_times)

    return fig, [int(vec_sleeponset), int(vec_wake)]


@app.callback(
    Output("check-done", "children"),
    Input("are-you-done", "value"),
    Input("file_manager", "data"),
)
def write_log_done(value, file_manager):
    if not value:
        print("Sleep log analysis not completed yet.")
    else:
        minor_files.write_log_analysis_completed(
            graph_data.identifier, file_manager["completed_analysis_file"]
        )


@app.callback(
    Output("annotations-save", "children"),
    Output("sleep-onset", "children"),
    Output("sleep-offset", "children"),
    Output("sleep-duration", "children"),
    Input("my-range-slider", "drag_value"),
    Input("file_manager", "data"),
    State("day_slider", "value"),
)
def write_info(drag_value, file_manager, day):
    if not drag_value:
        return "", "", "", ""

    minor_files.write_sleeplog(
        file_manager["sleeplog_file"], graph_data, day, drag_value[0], drag_value[1]
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
    app.run_server(debug=True, port=8051, dev_tools_hot_reload=True)
