"""Standard CRUD operations for the database."""
import datetime
import logging
import pathlib
from collections.abc import Iterable

from actigraphy.core import config
from actigraphy.database import models
from actigraphy.io import metadata

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME
DEFAULT_SLEEP_TIME = settings.DEFAULT_SLEEP_TIME

logger = logging.getLogger(LOGGER_NAME)


def initialize_subject(
    identifier: str,
    metadata_file: str | pathlib.Path,
) -> models.Subject:
    """Initializes a new subject with the given identifier and metadata file.

    Args:
        identifier: The identifier for the new subject.
        metadata_file: The path to the metadata file for the new subject.

    Returns:
        models.Subject: The initialized subject object.

    Notes:
        Default sleep times are set to 03:00 the next day.
        Last day is not included as it doesn't include a night.
    """
    logger.debug("Initializing subject %s", identifier)
    metadata_obj = metadata.MetaData.from_file(metadata_file)
    raw_dates = [
        datetime.datetime.strptime(date, "%Y-%m-%dT%H:%M:%S%z")
        for date in metadata_obj.m.metashort.timestamp
    ]
    dates = sorted(_keep_first_unique_dates(raw_dates))

    day_models = []
    for day_index in range(len(dates) - 1):
        day = dates[day_index]
        day_model = models.Day(date=day.date())
        utc_offset = (dates[day_index + 1]).utcoffset() or datetime.timedelta()
        default_sleep_datetime = (
            datetime.datetime.combine(
                day + datetime.timedelta(days=1),
                DEFAULT_SLEEP_TIME,
                tzinfo=datetime.UTC,
            )
            + utc_offset
        )

        day_model.sleep_times = [
            models.SleepTime(
                onset=default_sleep_datetime,
                onset_utc_offset=dates[day_index + 1].utcoffset().total_seconds(),  # type: ignore[union-attr]
                wakeup=default_sleep_datetime,
                wakeup_utc_offset=dates[day_index + 1].utcoffset().total_seconds(),  # type: ignore[union-attr]
            ),
        ]
        day_models.append(day_model)

    n_points_per_day = 86400 // metadata_obj.m.windowsizes[0]
    return models.Subject(
        name=identifier,
        days=day_models[:-1],
        n_points_per_day=n_points_per_day,
    )


def _keep_first_unique_dates(
    datetimes: Iterable[datetime.datetime],
) -> list[datetime.datetime]:
    """Fetch unique dates.

    Args:
        datetimes: A list of datetime objects.

    Returns:
        list[datetime.datetime]: A list of datetime objects with unique dates
            The first occurence of the date is retained.
    """
    unique_dates = set()
    result = []

    for dt in datetimes:
        dt_date = dt.date()
        if dt_date not in unique_dates:
            unique_dates.add(dt_date)
            result.append(dt)

    return result
