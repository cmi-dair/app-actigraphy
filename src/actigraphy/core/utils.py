"""Utility functions for the actigraphy package."""
import datetime
import logging
import os
from os import path

from actigraphy.core import config

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)


class FileManager:
    """A class for managing file paths and directories.

    Attributes:
        base_dir (str): The base directory for the file manager.
        log_dir (str): The directory for log files.
        identifier (str): The identifier for the file manager.
        log_file (str): The path to the log file.
        sleeplog_file (str): The path to the sleep log file.
        multiple_sleeplog_file (str): The path to the multiple sleep log file.
        data_cleaning_file (str): The path to the data cleaning file.
        missing_sleep_file (str): The path to the missing sleep file.
        review_night_file (str): The path to the review night file.
        completed_analysis_file (str): The path to the completed analysis file.

    Notes:
        Files are kept as strings because Dash cannot serialize pathlib.Path.
    """

    def __init__(self, base_dir: str) -> None:
        self.base_dir = base_dir
        self.log_dir = path.join(self.base_dir, "logs")
        self.identifier = self.base_dir.rsplit("_", maxsplit=1)[-1]

        self.log_file = path.join(self.log_dir, "log_file.csv")
        self.sleeplog_file = path.join(self.log_dir, f"sleeplog_{self.identifier}.csv")
        self.multiple_sleeplog_file = path.join(
            self.log_dir, f"multiple_sleeplog_{self.identifier}.csv"
        )
        self.data_cleaning_file = path.join(
            self.log_dir, f"data_cleaning_{self.identifier}.csv"
        )
        self.missing_sleep_file = path.join(
            self.log_dir, f"missing_sleep_{self.identifier}.csv"
        )
        self.review_night_file = path.join(
            self.log_dir, f"review_night_{self.identifier}.csv"
        )
        self.completed_analysis_file = path.join(
            self.log_dir, "participants_with_completed_analysis.csv"
        )

        os.makedirs(self.log_dir, exist_ok=True)


def datetime_delta_as_hh_mm(delta: datetime.timedelta) -> str:
    """Calculates the difference between two datetime objects and returns the
    result as a string in the format "HH:MM".

    Args:
        delta: The difference between two datetime objects.

    Returns:
        str: The difference between the two datetime objects as a string in the
        format "HH:MM".
    """
    logger.debug("Calculating datetime delta as HH:MM: %s", delta)
    total_minutes = delta.total_seconds() // 60
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    return f"{hours:02}:{minutes:02}"


def time2point(time: datetime.datetime, date: datetime.date) -> int:
    """Converts a datetime object to a float representing the number of minutes
    since midnight on the given date.

    Args:
        time: The datetime object to convert.
        date: The date preceding midnight as reference.

    Returns:
        float: The number of minutes since midnight on the given date.
    """
    logger.debug("Converting time to point: %s.", time)
    reference = datetime.datetime.combine(date, datetime.time(hour=12))
    delta = time - reference
    return delta.total_seconds() // 60


def point2time(point: float | None, date: datetime.date) -> datetime.datetime:
    logger.debug("Converting point to time: %s.", point)
    if point is None:
        delta = datetime.timedelta(
            days=1, hours=3, minutes=0
        )  # Default to 03:00AM the next day
    else:
        days = point // 1440
        hour = (point - 1440 * days) // 60
        minute = (point - 1440 * days - 60 * hour) % 60
        offset = datetime.timedelta(hours=12)
        delta = datetime.timedelta(days=days, hours=hour, minutes=minute) + offset
    return datetime.datetime.combine(date, datetime.time(0)) + delta


def point2time_timestamp(point: int, npointsperday: int, offset: int = 0):
    """Converts a point to a time string in the format of 'hour:minute'.

    Args:
        point: The point to convert to a time string.
        npointsperday: The number of points per day.
        offset: The offset to apply to the point in hours.

    Returns:
        The time string.
    """
    offset_in_points = offset * npointsperday / 24
    scaled_point = (point + offset_in_points) * 24 / npointsperday
    hour = scaled_point % 24
    minute = (scaled_point - int(scaled_point)) * 60
    return f"{int(hour):02d}:{int(minute):02d}"


def slider_values_to_graph_values(
    values: list[int], n_points_per_day: int
) -> list[int]:
    """Converts the values of the slider to the values of the graph.

    Args:
        values: The values of the slider.
        n_points_per_day: The number of points per day.

    Returns:
        The values of the graph.

    Notes:
        The slider has one point per minute.
    """
    return [int(value * n_points_per_day / 24 / 60) for value in values]
