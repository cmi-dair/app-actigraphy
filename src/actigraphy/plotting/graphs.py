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
    axis_range: int
    daycount: int
    vec_acc: np.ndarray
    vec_ang: np.ndarray
    vec_sleeponset: np.ndarray
    vec_wake: np.ndarray
    vec_line: np.ndarray
    npointsperday: int
    excl_night: np.ndarray
    vec_nonwear: np.ndarray
    ddate_new: pd.Index


@functools.lru_cache()
def get_metadata(base_dir: str) -> metadata.MetaData:
    logger.debug("Getting metadata from %s", "base_dir")
    metadata_file = _get_data_file(pathlib.Path(base_dir) / "meta" / "basic")
    return metadata.MetaData.from_file(metadata_file)


@functools.lru_cache()
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


def create_graphs(file_manager: dict[str, str]):
    metadata_data = get_metadata(file_manager["base_dir"])
    ms4_data = get_ms4_data(file_manager["base_dir"])

    timestamps = [
        datetime.datetime.strptime(time, "%Y-%m-%dT%H:%M:%S%z")
        for time in metadata_data.m.metashort.timestamp
    ]

    passed_midnight = get_midnights(file_manager["base_dir"])

    ddate = [time.strftime("%Y-%m-%d") for time in timestamps]
    ddates_of_interest = [ddate[index] for index in passed_midnight]
    ddate_new = pd.Index(ddates_of_interest)

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

    npointsperday = int((60 / metadata_data.m.windowsizes[0]) * 1440)

    # Creating auxiliary vectors to store the data
    vec_acc = np.zeros((len(passed_midnight) + 1, npointsperday))
    vec_ang = np.zeros((len(passed_midnight) + 1, npointsperday))
    vec_sleeponset = np.zeros(len(passed_midnight) + 1)
    vec_wake = np.zeros(len(passed_midnight) + 1)
    vec_nonwear = np.zeros((len(passed_midnight) + 1, npointsperday))

    if len(passed_midnight) > 0:
        nplots = np.size(passed_midnight) + 1
        daycount = 1

        for n_graph in range(nplots):
            logger.debug("Creating graph %s.", n_graph)

            check_date = 1
            change_date = 0

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
            extension = range(0, (npointsperday - (t1 - t0)) - 1, 1)
            extra_extension = range(0, 1)

            # check to see if there are any sleep onset or wake annotations on this day
            sleeponset_loc = 0
            wake_loc = 0
            sw_coefs = [12, 36]

            # Index 0=day; 1=month; 2=year
            sleep_dates = [
                datetime.datetime.strptime(row.calendar_date, "%d/%m/%Y")
                for row in ms4_data
            ]

            new_sleep_date = [date.strftime("%Y-%m-%d") for date in sleep_dates]

            # check for sleeponset & wake time that is logged on this day before midnight
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

                if daycount == 1:
                    # Updating the all days variable to include the day before (without act data) on the first position
                    ddate_new = pd.concat([pd.Series(curr_date), pd.Series(ddate_new)])
                    ddate_new = ddate_new.reset_index()
                    ddate_new = ddate_new[0]
                    change_date = 1

            if curr_date in str(new_sleep_date):
                check_date = 0
                idx = list(new_sleep_date).index(curr_date)

            if check_date is False:
                # Get sleeponset
                sleep_onset_time_all = [row.sleeponset for row in ms4_data]
                sleeponset_time = sleep_onset_time_all[idx + 1]

                if (sleeponset_time >= sw_coefs[0]) & (sleeponset_time < sw_coefs[1]):
                    sleeponset_hour = int(sleeponset_time)
                    sleeponset_hour %= 24

                    sleeponset_min = (sleeponset_time - int(sleeponset_time)) * 60
                    sleeponset_min %= 60

                    hour = [time.hour for time in timestamps]
                    minute = [time.minute for time in timestamps]
                    sleeponset_locations = (
                        ((pd.to_numeric(hour[t0:t1])) == sleeponset_hour)
                        & ((pd.to_numeric(minute[t0:t1])) == int(sleeponset_min))
                    ).which()
                    sleeponset_locations = list(pd.to_numeric(sleeponset_locations) + 2)

                    if len(sleeponset_locations) == 0:
                        sleeponset_loc = 0
                    else:
                        sleeponset_loc = sleeponset_locations[0]

                # Get wakeup
                wake_time_all = [row.wakeup for row in ms4_data]
                wake_time = wake_time_all[idx + 1]

                if (wake_time >= sw_coefs[0]) & (wake_time < sw_coefs[1]):
                    wake_hour = int(wake_time) % 24

                    wake_min = ((wake_time - int(wake_time)) * 60) % 60

                    wake_locations = (
                        ((pd.to_numeric(hour[t0:t1])) == wake_hour)
                        & ((pd.to_numeric(minute[t0:t1])) == int(wake_min))
                    ).which()
                    wake_locations = list(pd.to_numeric(wake_locations) + 2)

                    # Need to change this line to work with boolean
                    # if(wake_locations[0] == True):
                    if len(wake_locations) == 0:
                        wake_loc = 0
                    else:
                        wake_loc = wake_locations[0]

            if (((t1 - t0) + 1) != npointsperday) & (t0 == 1):
                extension = [0] * ((npointsperday - (t1 - t0)) - 1)
                acc = extension + list(acc)
                ang = extension + list(ang)
                non_wear = extension + list(non_wear)
                t1 = len(acc)

                if len(non_wear) < 17280:
                    non_wear = list(extra_extension) + list(non_wear)

                if len(acc) == npointsperday + 1:
                    extension = extension[1 : (len(extension))]
                    acc = acc[1 : (len(acc))]
                    ang = ang[1 : (len(ang))]
                    non_wear = non_wear[1 : (len(non_wear))]

                # adjust any sleeponset / wake annotations if they exist:
                if sleeponset_loc != 0:
                    sleeponset_loc = sleeponset_loc + len(extension)

                if wake_loc != 0:
                    wake_loc = wake_loc + len(extension)

            elif ((t1 - t0) + 1) != npointsperday & (t1 == len(timestamps)):
                extension = [0] * ((npointsperday - (t1 - t0)))
                acc = list(acc) + extension
                ang = list(ang) + extension
                non_wear = list(non_wear) + extension

                if len(non_wear) < 17280:
                    non_wear = list(non_wear) + extension

                if len(acc) == npointsperday + 1:
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

        vec_line = []
        # Setting nnights = 70 because GGIR version 2.0-0 need a value for the nnights variable.
        vec_line = [0 for i in range((70) * 2)]

        excl_night = [0 for i in range(daycount)]

    ddate_temp = ddate_new[0]
    new_sleep_date_temp = new_sleep_date[1]
    if (
        (ddate_new[0] != new_sleep_date[1])
        and (change_date == 0)
        and (ddate_temp[8:] > new_sleep_date_temp[8:])
    ):
        ddate_new = pd.concat([pd.Series(new_sleep_date[1]), pd.Series(ddate_new)])
        ddate_new = ddate_new.reset_index()
        ddate_new = ddate_new[0]

    if len(new_sleep_date) != daycount - 1:
        new_sleep_date = pd.concat([pd.Series(new_sleep_date), pd.Series(curr_date)])
        new_sleep_date = new_sleep_date.reset_index()
        new_sleep_date = new_sleep_date[0]

    axis_range = int((2 * (60 / metadata_data.m.windowsizes[0]) * 60))

    return GraphOutput(
        axis_range,
        daycount,
        vec_acc,
        vec_ang,
        vec_sleeponset,
        vec_wake,
        vec_line,
        npointsperday,
        excl_night,
        vec_nonwear,
        ddate_new,
    )
