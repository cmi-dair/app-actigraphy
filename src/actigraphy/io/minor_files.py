import csv
import pathlib
from datetime import datetime
from typing import Any

import numpy as np
import numpy.typing as npt
import pandas as pd

from actigraphy.core import utils
from actigraphy.plotting.graphs import GraphOutput


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


def read_sleeplog(filepath: str | pathlib.Path) -> tuple[list[str], list[str]]:
    sleeplog_file = pd.read_csv(filepath, index_col=0)
    sleeplog_file = sleeplog_file.iloc[0]
    wake = [sleeplog_file[idx] for idx in range(len(sleeplog_file)) if idx % 2 == 1]
    sleep = [sleeplog_file[idx] for idx in range(len(sleeplog_file)) if idx % 2 != 1]

    return sleep, wake


def save_sleeplog(
    graph_data: GraphOutput, day, sleep, wake, filepath: pathlib.Path
) -> None:
    df = pd.read_csv(filepath)
    df.iloc[0, 0] = graph_data.identifier
    sleep_time = utils.point2time(
        sleep, graph_data.axis_range, graph_data.npointsperday
    )
    wake_time = utils.point2time(wake, graph_data.axis_range, graph_data.npointsperday)
    df.iloc[0, ((day) * 2) - 1] = sleep_time
    df.iloc[0, ((day) * 2)] = wake_time

    df.to_csv(filepath, index=False)


def save_excluded_night(
    identifier: str, excl_night: np.ndarray, filepath: pathlib.Path
):
    header = ["ID", "day_part5", "relyonguider_part4", "night_part4"]
    nights_excluded = " ".join((np.where(excl_night == 1)[0] + 1).astype(str))
    data_night = [identifier, "", "", nights_excluded]

    with open(filepath, "w", encoding="utf-8") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerow(header)
        writer.writerow(data_night)

    print("Excluded nights formated: ", nights_excluded)


def save_ggir(hour_vector: npt.ArrayLike, filepath: pathlib.Path) -> None:
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


def save_log_file(name: str, filepath: pathlib.Path, identifier: str) -> None:
    filename = "sleeplog_" + identifier + ".csv"

    log_info = [name, identifier, datetime.date.today(), filename]

    if not filepath.exists():
        with open(filepath, "w", encoding="utf-8") as file_buffer:
            writer = csv.writer(file_buffer)
            writer.writerow(["Username", "Participant", "Date", "Filename"])

    with open(filepath, "a", encoding="utf-8") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerow(log_info)


def save_log_analysis_completed(identifier: str, filepath: pathlib.Path) -> None:
    log_info = [identifier, "Yes", datetime.datetime.now()]

    if not filepath.exists():
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
