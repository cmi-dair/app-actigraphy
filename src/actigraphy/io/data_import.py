""" Graph preparation functions. """
import datetime
import functools
import itertools
import logging
import pathlib

import numpy as np

from actigraphy.core import config
from actigraphy.io import metadata

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


def _get_data_file(data_sub_dir: pathlib.Path) -> pathlib.Path:
    data_files = list(data_sub_dir.glob("*.RData"))
    if len(data_files) == 1:
        return data_files[0]
    raise ValueError(
        f"Expected one data file in {data_sub_dir}, found {len(data_files)}"
    )


@functools.lru_cache(maxsize=None)
def get_metadata(base_dir: str) -> metadata.MetaData:
    logger.debug("Getting metadata from %s", "base_dir")
    metadata_file = _get_data_file(pathlib.Path(base_dir) / "meta" / "basic")
    return metadata.MetaData.from_file(metadata_file)


@functools.lru_cache()
def get_time(times: list[str]) -> list[datetime.datetime]:
    """Source data is shifted by negative twelve hours. This function returns a
    list of datetime objects that represent the standard time.

    Args:
        meta: The metadata object.

    Returns:
        A list of datetime objects that represent the standard time.

    """
    logger.debug("Getting standard time from metadata.")
    return [datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S%z") for time in times]


@functools.lru_cache()
def get_midnights(base_dir: str) -> list[int]:
    """Returns a list of indices of midnight timestamps in the metadata file.

    Args:
        base_dir: The base directory containing the metadata file.

    Returns:
        list[int]: A list of indices of midnight timestamps in the metadata file.
    """
    logger.debug("Getting midnights from %s", base_dir)
    metadata_data = get_metadata(base_dir)
    timestamps = get_time(tuple(metadata_data.m.metashort.timestamp))
    midnight_indices = []
    for date_pairs in itertools.pairwise(timestamps):
        if date_pairs[0].day != date_pairs[1].day:
            midnight_indices.append(timestamps.index(date_pairs[1]) + 1)
    logger.debug("Found %s midnights.", len(midnight_indices))
    return midnight_indices


@functools.lru_cache()
def get_daycount(base_dir: str) -> int:
    """Returns the number of days in the subject's data.

    Args:
        base_dir: The path to the subject's data.

    Returns:
        int: The number of days in the subject's data.

    """
    logger.debug("Getting daycount from %s", base_dir)
    return len(get_midnights(base_dir)) + 1


def get_n_points_per_day(file_manager: dict[str, str]) -> int:
    """Calculates the number of data points per day based on the metadata file.

    Args:
        file_manager: A dictionary containing the base directory of the metadata file.

    Returns:
        int: The number of data points per day.
    """
    logger.debug("Getting n points per day from %s", file_manager["base_dir"])
    metadata_data = get_metadata(file_manager["base_dir"])
    return 86400 // metadata_data.m.windowsizes[0]


def get_dates(file_manager: dict[str, str]) -> list[datetime.date]:
    """Returns a list of unique dates from the metadata.

    Args:
        file_manager: A dictionary containing the base directory of the metadata.

    Returns:
        list[datetime.date]: A sorted list of unique dates extracted from the metadata.

    """
    logger.debug("Getting dates from %s", file_manager["base_dir"])
    metadata_data = get_metadata(file_manager["base_dir"])
    timestamps = get_time(tuple(metadata_data.m.metashort.timestamp))
    dates = {time.date() for time in timestamps}
    return sorted(dates)


def create_graph(
    file_manager: dict[str, str], day: int
) -> tuple[list[float], list[float], list[float]]:
    """Loads data for a given day and prepares it for plotting.

    Args:
        file_manager: A dictionary containing file paths.
        day: The day for which to load data.

    Returns:
        tuple[list[float], list[float], list[float]]: A tuple containing three lists:
            - A list of acceleration values.
            - A list of angle values.
            - A list of non-wear values.
    """
    # TODO: This function does a lot of type conversions. It should be refactored
    logger.debug("Loading data for day %s.", day)
    metadata_data = get_metadata(file_manager["base_dir"])
    passed_midnight = get_midnights(file_manager["base_dir"])

    # Prepare nonwear information for plotting
    enmo = metadata_data.m.metashort.ENMO.reset_index(drop=True)
    anglez = metadata_data.m.metashort.anglez.reset_index(drop=True)
    nonwear = np.zeros(len(enmo))

    # take instances where nonwear was detected (on ws2 time vector) and map results onto a ws3 lenght vector for plotting purposes
    nonwear_elements = np.where(metadata_data.m.metalong.nonwearscore > 1)[0]

    for index in nonwear_elements:
        nonwear[
            index : (
                index
                + metadata_data.m.windowsizes[1] // metadata_data.m.windowsizes[0]
                - 1
            )
        ] = 1

    n_points_per_day = get_n_points_per_day(file_manager)

    if len(passed_midnight) == 0:
        raise ValueError("No midnight found in the data.")

    time_day_starts, time_day_ends = _day_start_and_end_time_points(
        file_manager, day, metadata_data.m.windowsizes[0]
    )

    acc = abs(enmo[time_day_starts:time_day_ends] * 1000)
    ang = anglez[time_day_starts:time_day_ends]
    non_wear = nonwear[time_day_starts:time_day_ends]

    extension = [0] * (n_points_per_day - len(acc))
    if time_day_starts == 0:
        acc = extension + list(acc)
        ang = extension + list(ang)
        non_wear_list = extension + list(non_wear)
    elif time_day_ends is None:
        acc = list(acc) + extension
        ang = list(ang) + extension
        non_wear_list = list(non_wear) + extension
    else:
        non_wear_list = list(non_wear)

    acc = (np.array(acc) / 14) - 210

    return list(acc), list(ang), non_wear_list


def _day_start_and_end_time_points(
    file_manager: dict[str, str], day: int, window_size: int
) -> tuple[int, int | None]:
    """Given a file manager, a day index, and a window size, returns the start
    and end time points for the given day.

    Args:
        file_manager: A dictionary containing file paths.
        day : The index of the day for which to retrieve the start and end time points.
        window_size: The size of the window in minutes.

    Returns:
        tuple[int, int | None]: A tuple containing the start and end time points for the given day.
    """
    target_timepoints = [0] + get_midnights(file_manager["base_dir"]) + [None]

    start, end = list(itertools.pairwise(target_timepoints))[day]
    if start is None:
        raise ValueError(f"No start time found for day {day}.")

    if end:
        time_day_ends: int | None = _adjust_timepoint_for_daylight_savings(
            start, end, window_size
        )
    else:
        time_day_ends = end
    return start, time_day_ends


def _adjust_timepoint_for_daylight_savings(
    start: int, end: int, window_size: int
) -> int:
    """
    Adjusts the end timepoint for daylight savings time.

    Args:
        start: The start timepoint.
        end: The end timepoint.
        window_size: The size of the time window.

    Returns:
        int: The adjusted end timepoint.
    """
    day_length = end - start
    if (day_length + 1) // (3600 / window_size) == 25:
        end = end - int(60 * 60 / window_size)
    if (day_length + 1) // (3600 / window_size) == 23:
        end = end + int(60 * 60 / window_size)
    return end
