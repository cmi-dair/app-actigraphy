"""Functions for reading and writing minor files to a format accepted by GGIR."""
import csv
import logging
from collections import abc
from typing import Any

from actigraphy.core import config
from actigraphy.database import crud, database

settings = config.get_settings()

LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def write_sleeplog(file_manager: dict[str, str]) -> None:
    """Save the given hour vector to a CSV file.

    Args:
        file_manager: A dictionary containing file paths for the sleep log file.

    Notes:
        The last day is discarded as each frontend "day" displays two days.

    """
    logger.debug("Writing sleep log file.")
    session = next(database.session_generator(file_manager["database"]))
    subject = crud.read_subject(session, file_manager["identifier"])
    onset_times = [day.sleep_times[0].onset_with_tz for day in subject.days]
    wakeup_times = [day.sleep_times[0].wakeup_with_tz for day in subject.days]
    dates = _flatten(zip(onset_times, wakeup_times, strict=True))

    data_line = ["identifier"]
    data_line.extend([str(date) for date in dates])

    sleep_times = _flatten(
        [[f"onset_N{day + 1}", f"wakeup_N{day + 1}"] for day in range(len(dates) // 2)],
    )
    header = ["ID", *sleep_times]

    with open(file_manager["sleeplog_file"], "w") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerow(header)
        writer.writerow(data_line)


def write_vector(filepath: str, vector: list[Any]) -> None:
    """Write a list of values to a CSV file.

    Args:
        filepath: The path to the CSV file.
        vector: The list of values to write to the CSV file.

    """
    with open(filepath, "w") as file_buffer:
        writer = csv.writer(file_buffer)
        writer.writerow(vector)


def _flatten(iterable_of_iterables: abc.Iterable[Any]) -> list[Any]:
    """Recursively flattens an iterable of iterables into a single list.

    Args:
        iterable_of_iterables: The list of lists to flatten.

    Returns:
        list[any]: The flattened list.
    """
    new_list = []
    for item in iterable_of_iterables:
        if isinstance(item, abc.Iterable) and not isinstance(item, str | bytes):
            new_list.extend(_flatten(item))
        else:
            new_list.append(item)
    return new_list
