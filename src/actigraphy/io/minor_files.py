import csv
import datetime
from os import path
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

from actigraphy.core import utils
from actigraphy.plotting import graphs


def _flatten(list_of_lists: list[Any]) -> list[Any]:
    """Recursively flattens a list of lists into a single list.

    Args:
        list_of_lists: The list of lists to flatten.

    Returns:
        list[any]: The flattened list.
    """
    new_list = []
    for item in list_of_lists:
        if isinstance(item, list):
            new_list.extend(_flatten(item))
        else:
            new_list.append(item)
    return new_list


def read_sleeplog(filepath: str) -> tuple[list[str], list[str]]:
    sleeplog_file = pd.read_csv(filepath, index_col=0)
    sleeplog_file = sleeplog_file.iloc[0]
    wake = [sleeplog_file[idx] for idx in range(len(sleeplog_file)) if idx % 2 == 1]
    sleep = [sleeplog_file[idx] for idx in range(len(sleeplog_file)) if idx % 2 != 1]

    return sleep, wake


def write_sleeplog(file_manager, graph_data, day, sleep, wake) -> None:
    df = pd.read_csv(file_manager["sleeplog_file"])
    df.iloc[0, 0] = file_manager["identifier"]
    sleep_time = utils.point2time(
        sleep, graph_data.axis_range, graph_data.npointsperday
    )
    wake_time = utils.point2time(wake, graph_data.axis_range, graph_data.npointsperday)
    df.iloc[0, ((day) * 2) - 1] = sleep_time
    df.iloc[0, ((day) * 2)] = wake_time

    df.to_csv(file_manager["sleeplog_file"], index=False)


def write_ggir(hour_vector: npt.ArrayLike, filepath: str) -> None:
    """Save the given hour vector to a CSV file in GGIR format.

    Args:
        hour_vector: A 1D array-like object containing hourly activity counts.
        filepath: The path to the output file.

    """
    data_line = ["identifier"] + np.array(hour_vector).tolist()
    data_line = [data if data else "NA" for data in data_line]

    header = ["ID"] + _flatten(
        [[f"onset_N{day+1}", f"wakeup_N{day+1}"] for day in range(len(data_line))]
    )

    with open(filepath, "w", encoding="utf-8") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerow(header)
        writer.writerow(data_line)


def write_log_file(name: str, filepath: str, identifier: str) -> None:
    filename = "sleeplog_" + identifier + ".csv"

    log_info = [name, identifier, datetime.date.today(), filename]

    if not path.exists(filepath):
        with open(filepath, "w", encoding="utf-8") as file_buffer:
            writer = csv.writer(file_buffer)
            writer.writerow(["Username", "Participant", "Date", "Filename"])

    with open(filepath, "a", encoding="utf-8") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerow(log_info)


def write_log_analysis_completed(identifier: str, filepath: str) -> None:
    log_info = [identifier, "Yes", datetime.datetime.now()]

    if not path.exists(filepath):
        header = [
            "Participant",
            "Is the sleep log analysis completed?",
            "Last modified",
        ]
        with open(filepath, "w", encoding="utf-8") as file_buffer:
            writer = csv.writer(file_buffer)
            writer.writerow(header)

    with open(filepath, "a", encoding="utf-8") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerow(log_info)


def write_vector(filepath: str, vector: list[Any]) -> None:
    with open(filepath, "w", encoding="utf-8") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerow(vector)


def read_vector(filepath: str, up_to_column=None) -> list[Any]:
    df = pd.read_csv(filepath, header=None)
    if up_to_column is None:
        up_to_column = len(df.columns)
    return [df.iloc[0, idx] for idx in range(up_to_column)]


def initialize_files(
    file_manager: dict[str, str],
    hour_vector: list[int],
    evaluator_name: str,
) -> None:
    if not path.exists(file_manager["sleeplog_file"]):
        write_ggir(hour_vector, file_manager["sleeplog_file"])

    daycount = graphs.get_daycount(file_manager)
    vector_files = [
        "review_night_file",
        "multiple_sleeplog_file",
        "data_cleaning_file",
        "missing_sleep_file",
    ]
    for vector_file in vector_files:
        filepath = file_manager[vector_file]
        if not path.exists(filepath):
            write_vector(filepath, [0] * daycount)

    write_log_file(evaluator_name, file_manager["log_file"], file_manager["identifier"])
