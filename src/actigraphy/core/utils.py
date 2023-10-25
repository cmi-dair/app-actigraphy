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
        """Initializes the FileManager class."""
        self.base_dir = base_dir
        self.log_dir = path.join(self.base_dir, "logs")
        self.identifier = self.base_dir.rsplit("_", maxsplit=1)[-1]

        self.log_file = path.join(self.log_dir, "log_file.csv")
        self.sleeplog_file = path.join(self.log_dir, f"sleeplog_{self.identifier}.csv")
        self.multiple_sleeplog_file = path.join(
            self.log_dir,
            f"multiple_sleeplog_{self.identifier}.csv",
        )
        self.data_cleaning_file = path.join(
            self.log_dir,
            f"data_cleaning_{self.identifier}.csv",
        )
        self.missing_sleep_file = path.join(
            self.log_dir,
            f"missing_sleep_{self.identifier}.csv",
        )
        self.review_night_file = path.join(
            self.log_dir,
            f"review_night_{self.identifier}.csv",
        )
        self.completed_analysis_file = path.join(
            self.log_dir,
            "participants_with_completed_analysis.csv",
        )

        os.makedirs(self.log_dir, exist_ok=True)


def datetime_delta_as_hh_mm(delta: datetime.timedelta) -> str:
    """Calculates the difference between two datetime objects.

    Args:
        delta: The difference between two datetime objects.

    Returns:
        str: The difference between the two datetime objects as a string in the
        format "HH:MM".
    """
    logger.debug("Calculating datetime delta as HH:MM: %s", delta)
    hours, remainder = divmod(delta.total_seconds(), 3600)
    minutes = remainder // 60
    return f"{int(hours):02}:{int(minutes):02}"


def time2point(
    time: datetime.datetime,
    date: datetime.date,
    *,
    ignore_timezone: bool = True,
) -> int:
    """Converts a datetime to the number of minutes since the given day's midnight.

    Args:
        time: The datetime object to convert.
        date: The date preceding midnight as reference.
        ignore_timezone: Whether to ignore the timezone of the datetime object.

    Returns:
        float: The number of minutes since midnight on the given date.
    """
    logger.debug("Converting time to point: %s.", time)
    reference = datetime.datetime.combine(date, datetime.time(hour=12))
    if ignore_timezone:
        delta = time.replace(tzinfo=None) - reference.replace(tzinfo=None)
    else:
        delta = time - reference
    return int(delta.total_seconds() // 60)


def point2time(
    point: float | None,
    date: datetime.date,
    timezone: datetime.tzinfo | None = None,
) -> datetime.datetime:
    """Converts a point value to a datetime object.

    Args:
        point: The point value to convert.
        date: The date to combine with the converted time.
        timezone: The timezone to use for the resulting datetime object.

    Returns:
        datetime.datetime: The resulting datetime object.
    """
    logger.debug("Converting point to time: %s.", point)
    if point is None:
        # Default to 03:00AM the next day
        default_date = datetime.datetime.combine(
            date,
            datetime.time(0),
        ) + datetime.timedelta(days=1, hours=3, minutes=0)
        if timezone:
            return default_date.astimezone(timezone)
        return default_date

    days, remainder_minutes = divmod(point, 1440)
    hours, minutes = divmod(remainder_minutes, 60)
    offset = datetime.timedelta(hours=12)
    delta = datetime.timedelta(days=days, hours=hours, minutes=minutes) + offset
    adjusted_time = datetime.datetime.combine(date, datetime.time(0)) + delta
    if timezone:
        return adjusted_time.astimezone(timezone)
    return adjusted_time


def point2time_timestamp(point: int, npointsperday: int, offset: int = 0) -> str:
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
    values: list[int],
    n_points_per_day: int,
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
