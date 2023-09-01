"""This module contains functions for reading and writing minor files."""
import csv
import datetime
from os import path
from typing import Any

from actigraphy.core import utils as core_utils
from actigraphy.io import utils as io_utils
from actigraphy.plotting import graphs


def read_sleeplog(filepath: str) -> tuple[list[str], list[str]]:
    """Reads sleep log data from a CSV file and returns two lists containing the
    sleep and wake times.

    Args:
        filepath: The path to the CSV file containing the sleep log data.

    Returns:
        list[str]: A list of the sleep times.
        list[str]: A list of the wake times.
    """
    sleep_hours = io_utils.read_one_line_from_csv_file(filepath, 1)[1:]

    wake = [sleep_hours[index] for index in range(len(sleep_hours)) if index % 2 == 1]
    sleep = [sleep_hours[index] for index in range(len(sleep_hours)) if index % 2 != 1]

    return sleep, wake


def write_sleeplog(file_manager, graph_data, day, sleep, wake) -> None:
    with open(file_manager["sleeplog_file"], "r", encoding="utf-8") as file_buffer:
        reader = csv.reader(file_buffer)
        sleeplog: list[list[str]] = list(reader)

    sleeplog[1][0] = file_manager["identifier"]

    sleep_time = core_utils.point2time(
        sleep, graph_data.axis_range, graph_data.npointsperday
    )

    wake_time = core_utils.point2time(
        wake, graph_data.axis_range, graph_data.npointsperday
    )

    sleeplog[1][(day * 2) - 1] = sleep_time
    sleeplog[1][(day * 2)] = wake_time

    with open(file_manager["sleeplog_file"], "w", encoding="utf-8") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerows(sleeplog)


def write_ggir(hour_vector: list[datetime.datetime], filepath: str) -> None:
    """Save the given hour vector to a CSV file in GGIR format.

    Args:
        hour_vector: A 1D array-like object containing hourly activity counts.
        filepath: The path to the output file.

    """
    data_line = ["identifier"]
    data_line.extend([str(date) for date in hour_vector])
    data_line = [data if data else "NA" for data in data_line]

    header = ["ID"] + io_utils.flatten(
        [
            [f"onset_N{day+1}", f"wakeup_N{day+1}"]
            for day in range(len(hour_vector) // 2)
        ]
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
    """Write a list of values to a CSV file.

    Args:
        filepath: The path to the CSV file.
        vector: The list of values to write to the CSV file.

    """
    with open(filepath, "w", encoding="utf-8") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerow(vector)


def read_vector(filepath: str, up_to_column: int | None = None) -> list[Any]:
    """Reads a vector of data from a CSV file.

    Args:
        filepath: The path to the CSV file.
        up_to_column: The index of the last column to read. If not specified,
            reads all columns.

    Returns:
        list[Any]: A list of values read from the CSV file.
    """
    data = io_utils.read_one_line_from_csv_file(filepath, 0)
    if up_to_column is not None:
        return data[:up_to_column]
    return data


def initialize_files(
    file_manager: dict[str, str],
    hour_vector: list[datetime.datetime | None],
    evaluator_name: str,
) -> None:
    """
    Initializes the files required for actigraphy analysis.

    Args:
        file_manager: A dictionary containing file paths for various files.
        hour_vector: A list of datetime objects representing hours and minutes.
        evaluator_name: The name of the evaluator.

    Returns:
        None
    """
    if not path.exists(file_manager["sleeplog_file"]):
        write_ggir(hour_vector, file_manager["sleeplog_file"])

    daycount = graphs.get_daycount(file_manager["base_dir"])
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
