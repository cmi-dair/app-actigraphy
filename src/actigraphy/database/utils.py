"""Standard CRUD operations for the database."""
import datetime
import logging
import pathlib
from collections.abc import Iterable
from typing import TypeVar

import numpy as np
from sqlalchemy import orm

from actigraphy.core import config
from actigraphy.database import models
from actigraphy.io import metadata

T = TypeVar("T")

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME
DEFAULT_SLEEP_TIME = settings.DEFAULT_SLEEP_TIME

logger = logging.getLogger(LOGGER_NAME)


def initialize_datapoints(
    metadata_obj: metadata.MetaData,
) -> list[models.DataPoint]:
    """Initialize the data points for the given subject.

    Args:
        metadata_obj: The path to the metadata file for the subject.
        days: The days for the subject.

    Returns:
        list[models.DataPoint]: The initialized data points.

    """
    logger.debug("Initializing data points.")
    data_points = []
    window_size_ratio = (
        metadata_obj.m.windowsizes[1] // metadata_obj.m.windowsizes[0] - 1
    )
    non_wear_elements = np.where(metadata_obj.m.metalong.nonwearscore > 1)[0]
    non_wear_indices = np.concatenate(
        [np.arange(index, index + window_size_ratio) for index in non_wear_elements],
    )
    for index, row in metadata_obj.m.metashort.iterrows():
        is_non_wear = index in non_wear_indices
        date = datetime.datetime.strptime(row["timestamp"], "%Y-%m-%dT%H:%M:%S%z")

        data_points.append(
            models.DataPoint(
                timestamp=date.astimezone(datetime.UTC),
                timestamp_utc_offset=date.utcoffset().total_seconds(),
                sensor_angle=row["anglez"],
                sensor_acceleration=row["ENMO"],
                non_wear=is_non_wear,
            ),
        )
    return data_points


def initialize_days(
    metadata_obj: metadata.MetaData,
) -> list[models.Day]:
    """Initialize the days for the given subject.

    Args:
        metadata_obj: The path to the metadata file for the subject.

    Returns:
        list[models.Day]: The initialized days.

    """
    logger.debug("Initializing days.")
    raw_dates = [
        datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
        for date in metadata_obj.m.metashort.timestamp
    ]
    dates = sorted(_keep_last_unique_date(raw_dates))

    day_models = []
    for day_index in range(len(dates)):
        day = dates[day_index]
        day_model = models.Day(date=day.date())
        utc_offset = day.utcoffset() or datetime.timedelta()
        default_sleep_datetime = datetime.datetime.combine(
            day,
            DEFAULT_SLEEP_TIME,
            tzinfo=datetime.timezone(utc_offset),
        )

        day_model.sleep_times = [
            models.SleepTime(
                onset=default_sleep_datetime.astimezone(datetime.UTC),
                onset_utc_offset=day.utcoffset().total_seconds(),  # type: ignore[union-attr]
                wakeup=default_sleep_datetime.astimezone(datetime.UTC),
                wakeup_utc_offset=day.utcoffset().total_seconds(),  # type: ignore[union-attr]
            ),
        ]
        day_models.append(day_model)
    return day_models


def initialize_subject(
    identifier: str,
    metadata_file: str | pathlib.Path,
    session: orm.Session,
) -> models.Subject:
    """Initializes a new subject with the given identifier and metadata file.

    Args:
        identifier: The identifier for the new subject.
        metadata_file: The path to the metadata file for the new subject.
        session: The database session.

    Returns:
        models.Subject: The initialized subject object.

    Notes:
        Default sleep times are set to 03:00 the next day.
        Last day is not included as it doesn't include a night.
    """
    logger.debug("Initializing subject %s", identifier)
    metadata_obj = metadata.MetaData.from_file(metadata_file)
    day_models = initialize_days(metadata_obj)
    data_points = initialize_datapoints(metadata_obj)

    n_points_per_day = 86400 // metadata_obj.m.windowsizes[0]
    subject = models.Subject(
        name=identifier,
        days=day_models,
        n_points_per_day=n_points_per_day,
        data_points=data_points,
    )
    session.add_all([subject, *data_points])
    session.commit()
    return subject


def _keep_last_unique_date(
    datetimes: Iterable[datetime.datetime],
) -> list[datetime.datetime]:
    """Fetch unique dates.

    Args:
        datetimes: A list of datetime objects.

    Returns:
        list[datetime.datetime]: A list of datetime objects with unique dates
            The last occurence of the sorted dates is retained.
    """
    unique_dates = set()
    result = []

    sorted_dates = sorted(datetimes)
    for dt in sorted_dates[::-1]:
        dt_date = dt.date()
        if dt_date not in unique_dates:
            unique_dates.add(dt_date)
            result.append(dt)

    return result
