"""Utility functions for the actigraphy package."""
import datetime
import logging
import os
import pathlib
from os import path

from actigraphy.core import config

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)


class FileManager:
    """A class for managing file paths and directories.

    Attributes:
        base_dir (str): The base directory for the file manager.
        database (str): The path to the database file.
        log_dir (str): The directory for log files.
        identifier (str): The identifier for the file manager.
        log_file (str): The path to the log file.
        sleeplog_file (str): The path to the sleep log file.
        data_cleaning_file (str): The path to the data cleaning file.
        metadata_file (str): The path to the metadata file.

    Notes:
        Files are kept as strings because Dash cannot serialize pathlib.Path.
    """

    def __init__(self, base_dir: str) -> None:
        """Initializes the FileManager class."""
        self.base_dir = base_dir
        self.database = path.join(base_dir, "actigraphy.sqlite")
        self.log_dir = path.join(self.base_dir, "logs")
        self.identifier = self.base_dir.rsplit("_", maxsplit=1)[-1]

        self.log_file = path.join(self.log_dir, "log_file.csv")
        self.sleeplog_file = path.join(self.log_dir, f"sleeplog_{self.identifier}.csv")
        self.data_cleaning_file = path.join(
            self.log_dir,
            f"data_cleaning_{self.identifier}.csv",
        )
        metadata_dir = path.join(self.base_dir, "meta", "basic")
        self.metadata_file = str(next(pathlib.Path(metadata_dir).glob("meta_*")))

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
) -> int:
    """Converts a datetime to the number of minutes since the given day's midnight.

    Args:
        time: The datetime object to convert.
        date: The date preceding midnight as reference.

    Returns:
        float: The number of minutes since midnight on the given date.
    """
    logger.debug("Converting time to point: %s.", time)
    reference = datetime.datetime.combine(
        date,
        datetime.time(hour=12),
        tzinfo=time.tzinfo,
    )

    delta = time - reference
    return int(delta.total_seconds() // 60)


def point2time(
    point: float,
    date: datetime.date,
    timezone_offset: int,
) -> datetime.datetime:
    """Converts a point value to a datetime object.

    Args:
        point: The point value to convert.
        date: The date to combine with the converted time.
        timezone_offset: Timezone offset in seconds.

    Returns:
        datetime.datetime: The resulting datetime object.

    """
    logger.debug("Converting point to time: %s.", point)

    days, remainder_minutes = divmod(point, 1440)
    hours, minutes = divmod(remainder_minutes, 60)

    slider_offset = datetime.timedelta(hours=12)
    timezone_delta = datetime.timedelta(seconds=timezone_offset)

    delta = datetime.timedelta(days=days, hours=hours, minutes=minutes) + slider_offset
    adjusted_time = datetime.datetime.combine(date, datetime.time(0)) + delta

    tz_info = datetime.timezone(timezone_delta)
    return adjusted_time.replace(tzinfo=tz_info)


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
