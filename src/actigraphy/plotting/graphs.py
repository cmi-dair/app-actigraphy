import dataclasses
import datetime
import functools
import logging
import pathlib

import numpy as np
import pandas as pd

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
    vec_sleeponset: np.ndarray
    vec_wake: np.ndarray
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
    nonwear = np.zeros(np.size(metadata_data.m.metashort.ENMO))

    # take instances where nonwear was detected (on ws2 time vector) and map results onto a ws3 lenght vector for plotting purposes
    nonwear_elements = np.where(metadata_data.m.metalong.nonwearscore > 1)[0]

    for j in range(np.size(nonwear_elements) - 1):
        # The next if deals with the cases in which the first point is a nowwear data
        # When this happens, the data takes a minute to load on the APP
        # TO-DO: find a better way to treat the nonwear cases in the first datapoint
        if nonwear_elements[j] == 0:
            nonwear_elements[j] = 1

        match_loc = np.where(
            metadata_data.m.metalong.timestamp[nonwear_elements[j]] == time
            for time in timestamps
        )[0]

        nonwear[
            int(match_loc) : int(
                (
                    int(match_loc)
                    + (metadata_data.m.windowsizes[1] / metadata_data.m.windowsizes[0])
                    - 1
                )
            )
        ] = 1

    n_points_per_day = get_n_points_per_day(file_manager)

    # Creating auxiliary vectors to store the data
    vec_acc = np.zeros((len(passed_midnight) + 1, n_points_per_day))
    vec_ang = np.zeros((len(passed_midnight) + 1, n_points_per_day))
    vec_sleeponset = np.zeros(len(passed_midnight) + 1)
    vec_wake = np.zeros(len(passed_midnight) + 1)
    vec_nonwear = np.zeros((len(passed_midnight) + 1, n_points_per_day))

    if len(passed_midnight) == 0:
        raise ValueError("No midnight found in the data.")
    nplots = np.size(passed_midnight) + 1
    daycount = 1

    for n_graph in range(nplots):
        logger.debug("Creating graph %s.", n_graph)

        if daycount == 1:
            t0 = 1
            t1 = passed_midnight[daycount - 1]
            non_wear = nonwear[range(t0, t1 + 1)]
        if daycount > 1 and daycount < nplots:
            t0 = passed_midnight[daycount - 2] + 1
            t1 = passed_midnight[daycount - 1]
            non_wear = nonwear[range(t0, t1 + 1)]
        if daycount == nplots:
            t0 = passed_midnight[daycount - 2]
            t1 = np.size(timestamps)
            non_wear = nonwear[range(t0, t1)]

        # Day with 25 hours, just pretend that 25th hour did not happen
        if ((t1 - t0) + 1) / (60 * 60 / metadata_data.m.windowsizes[0]) == 25:
            t1 = t1 - (60 * 60 / metadata_data.m.windowsizes[0])
            t1 = int(t1)

        # Day with 23 hours, just extend timeline with 1 hour
        if ((t1 - t0) + 1) / (60 * 60 / metadata_data.m.windowsizes[0]) == 23:
            t1 = t1 + (60 * 60 / metadata_data.m.windowsizes[0])
            t1 = int(t1)

        # Initialize daily "what we think you did" vectors
        acc = abs((metadata_data.m.metashort.ENMO * 1000)[range(t0, t1 + 1)])
        ang = metadata_data.m.metashort.anglez[range(t0, t1 + 1)]
        non_wear = nonwear[range(t0, t1)]
        extension = range(0, (n_points_per_day - (t1 - t0)) - 1, 1)
        extra_extension = range(0, 1)

        # check to see if there are any sleep onset or wake annotations on this day
        sleeponset_loc = 0
        wake_loc = 0

        # Index 0=day; 1=month; 2=year
        sleep_dates = [
            datetime.datetime.strptime(row.calendar_date, "%d/%m/%Y").date()
            for row in ms4_data
        ]

        new_sleep_date = [date.strftime("%Y-%m-%d") for date in sleep_dates]

        # check for sleeponset & wake time that is logged on this day before midnight
        ddate = [time.strftime("%Y-%m-%d") for time in timestamps]
        curr_date = ddate[t0]

        # check to see if it is the first day that has less than 24 and starts after midnight
        if (t1 - t0) < (
            (60 * 60 * 12) / metadata_data.m.windowsizes[0]
        ):  # if there is less than half a days worth of data
            list_temp = list(curr_date)
            temp = int(curr_date[8:]) - 1
            temp = str(temp).zfill(2)

            list_temp[8:] = temp
            curr_date = "".join(list_temp)

            new_sleep_date = pd.concat(
                [pd.Series(curr_date), pd.Series(new_sleep_date)]
            )

        if (((t1 - t0) + 1) != n_points_per_day) & (t0 == 1):
            extension = [0] * ((n_points_per_day - (t1 - t0)) - 1)
            acc = extension + list(acc)
            ang = extension + list(ang)
            non_wear = extension + list(non_wear)
            t1 = len(acc)

            if len(non_wear) < 17280:
                non_wear = list(extra_extension) + list(non_wear)

            if len(acc) == n_points_per_day + 1:
                extension = extension[1 : (len(extension))]
                acc = acc[1 : (len(acc))]
                ang = ang[1 : (len(ang))]
                non_wear = non_wear[1 : (len(non_wear))]

            # adjust any sleeponset / wake annotations if they exist:
            if sleeponset_loc != 0:
                sleeponset_loc = sleeponset_loc + len(extension)

            if wake_loc != 0:
                wake_loc = wake_loc + len(extension)

        elif ((t1 - t0) + 1) != n_points_per_day & (t1 == len(timestamps)):
            extension = [0] * ((n_points_per_day - (t1 - t0)))
            acc = list(acc) + extension
            ang = list(ang) + extension
            non_wear = list(non_wear) + extension

            if len(non_wear) < 17280:
                non_wear = list(non_wear) + extension

            if len(acc) == n_points_per_day + 1:
                extension = extension[1 : (len(extension))]
                acc = acc[1 : (len(acc))]
                ang = ang[1 : (len(ang))]
                non_wear = non_wear[1 : (len(non_wear))] + list(extra_extension)

        # Comment the next line if the app will create two different graphs: one for the arm movement and one for the z-angle
        acc = (np.array(acc) / 14) - 210

        # storing important variables in vectors to be accessed later
        vec_acc[n_graph] = acc
        vec_ang[n_graph] = ang
        vec_sleeponset[n_graph] = sleeponset_loc
        vec_wake[n_graph] = wake_loc
        vec_nonwear[n_graph] = non_wear

        daycount = daycount + 1

    return GraphOutput(
        vec_acc,
        vec_ang,
        vec_sleeponset,
        vec_wake,
        vec_nonwear,
    )
