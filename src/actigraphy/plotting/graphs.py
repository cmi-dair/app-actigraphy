import dataclasses
import datetime
import functools
import logging
import pathlib

import numpy as np

from actigraphy.core import config
from actigraphy.io import metadata, ms4

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


@dataclasses.dataclass
class GraphOutput:
    vec_acc: np.ndarray
    vec_ang: np.ndarray
    vec_nonwear: np.ndarray


@functools.lru_cache(maxsize=None)
def get_metadata(base_dir: str) -> metadata.MetaData:
    logger.debug("Getting metadata from %s", "base_dir")
    metadata_file = _get_data_file(pathlib.Path(base_dir) / "meta" / "basic")
    return metadata.MetaData.from_file(metadata_file)


@functools.lru_cache(maxsize=None)
def get_ms4_data(base_dir: str) -> ms4.MS4:
    logger.debug("Getting MS4 data from %s", base_dir)
    ms4_file = _get_data_file(pathlib.Path(base_dir) / "meta" / "ms4.out")
    return ms4.MS4.from_file(ms4_file)


@functools.lru_cache()
def get_midnights(base_dir: str) -> list[int]:
    logger.debug("Getting midnights from %s", base_dir)
    metadata_data = get_metadata(base_dir)
    timestamps = [
        datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S%z")
        for time in metadata_data.m.metashort.timestamp
    ]

    return [
        index + 1
        for index, time in enumerate(timestamps)
        if time.second == 0
        and time.minute == 0
        and time.hour == 12
        and index != len(timestamps) - 1
    ]


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


def get_axis_range(file_manager: dict[str, str]) -> int:
    logger.debug("Getting axis range from %s", file_manager["base_dir"])
    metadata_data = get_metadata(file_manager["base_dir"])
    return 7200 / metadata_data.m.windowsizes[0]


def get_n_points_per_day(file_manager: dict[str, str]) -> int:
    logger.debug("Getting n points per day from %s", file_manager["base_dir"])
    metadata_data = get_metadata(file_manager["base_dir"])
    return 86400 // metadata_data.m.windowsizes[0]


def get_dates(file_manager: dict[str, str]) -> list[datetime.date]:
    """Returns a list of unique dates from the metadata.

    Args:
        file_manager (d: A dictionary containing the base directory of the metadata.

    Returns:
        list[datetime.date]: A sorted list of unique dates extracted from the metadata.

    Notes:
        The first date is removed because it is not a full day.
    """
    logger.debug("Getting dates from %s", file_manager["base_dir"])
    metadata_data = get_metadata(file_manager["base_dir"])
    timestamps = [
        datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S%z")
        for time in metadata_data.m.metashort.timestamp
    ]
    dates = {time.date() for time in timestamps}

    return sorted(dates)[1:]


def create_graphs(file_manager: dict[str, str]) -> GraphOutput:
    metadata_data = get_metadata(file_manager["base_dir"])
    ms4_data = get_ms4_data(file_manager["base_dir"])

    timestamps = [
        datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S%z")
        for time in metadata_data.m.metashort.timestamp
    ]

    passed_midnight = get_midnights(file_manager["base_dir"])

    # Prepare nonwear information for plotting
    enmo = metadata_data.m.metashort.ENMO.reset_index(drop=True)
    anglez = metadata_data.m.metashort.anglez.reset_index(drop=True)
    nonwear = np.zeros(len(enmo))
\
    # take instances where nonwear was detected (on ws2 time vector) and map results onto a ws3 lenght vector for plotting purposes
    nonwear_elements = np.where(metadata_data.m.metalong.nonwearscore > 1)[0]
\
    for index in nonwear_elements:
        nonwear[
            index : (
                    index
                    + metadata_data.m.windowsizes[1] // metadata_data.m.windowsizes[0]
                    - 1
                )
        ] = 1

    n_points_per_day = get_n_points_per_day(file_manager)

    # Creating auxiliary vectors to store the data
    vec_acc = np.zeros((len(passed_midnight) + 1, n_points_per_day))
    vec_ang = np.zeros((len(passed_midnight) + 1, n_points_per_day))
    vec_nonwear = np.zeros((len(passed_midnight) + 1, n_points_per_day))

    if len(passed_midnight) == 0:
        raise ValueError("No midnight found in the data.")
    n_plots = len(passed_midnight) + 1

    for n_graph in range(n_plots):
        logger.debug("Creating graph %s.", n_graph)

        if n_graph == 0:
            time_day_starts = 0
            time_day_ends = passed_midnight[n_graph]
        elif n_graph < n_plots - 1:
            time_day_starts = passed_midnight[n_graph-1]
            time_day_ends = passed_midnight[n_graph]
        else:
            time_day_starts = passed_midnight[n_graph-1]
            time_day_ends = len(timestamps)

        # Day with 25 hours, just pretend that 25th hour did not happen
        if ((time_day_ends - time_day_starts) + 1) // (3600 / metadata_data.m.windowsizes[0]) == 25:
            time_day_ends = time_day_ends - (60 * 60 / metadata_data.m.windowsizes[0])
            time_day_ends = int(time_day_ends)

        # Day with 23 hours, just extend timeline with 1 hour
        if ((time_day_ends - time_day_starts) + 1) // (3600 / metadata_data.m.windowsizes[0]) == 23:
            time_day_ends = time_day_ends + (60 * 60 / metadata_data.m.windowsizes[0])
            time_day_ends = int(time_day_ends)

        acc = abs((enmo * 1000)[range(time_day_starts, time_day_ends)])
        ang = anglez[range(time_day_starts, time_day_ends)]
        non_wear = nonwear[range(time_day_starts, time_day_ends)]

        extension = [0] * (n_points_per_day - len(acc))
        if time_day_starts == 0:
            acc = extension + list(acc)
            ang = extension + list(ang)
            non_wear = extension + list(non_wear)
        elif time_day_ends == len(timestamps):
            acc = list(acc) + extension
            ang = list(ang) + extension
            non_wear = list(non_wear) + extension

        acc = (np.array(acc) / 14) - 210

        vec_acc[n_graph] = acc
        vec_ang[n_graph] = ang
        vec_nonwear[n_graph] = non_wear

    return GraphOutput(
        vec_acc,
        vec_ang,
        vec_nonwear,
    )
