import datetime
import logging

from actigraphy.core import config

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME
logger = logging.getLogger(LOGGER_NAME)


def datetime_delta_as_hh_mm(delta: datetime.timedelta) -> str:
    """Calculates the difference between two datetime objects and returns the
    result as a string in the format "HH:MM".

    Args:
        delta: The difference between two datetime objects.

    Returns:
        str: The difference between the two datetime objects as a string in the
        format "HH:MM".
    """
    logger.debug(f"Calculating datetime delta as HH:MM: {delta}")
    total_minutes = delta.total_seconds() // 60
    hours = int(total_minutes // 60)
    minutes = int(total_minutes % 60)
    return f"{hours:02}:{minutes:02}"


def point2time(point: float, axis_range: float, npointsperday: int) -> datetime.time:
    logger.debug(f"Converting point to time: {point}, {axis_range}, {npointsperday}")
    if int(point) == 0:
        return datetime.time(3, 0, 0)

    if point > 6 * axis_range:
        temp_sleep = (point * 24) / npointsperday - 12
    else:
        temp_sleep = (point * 24) / npointsperday + 12

    temp_sleep_hour = int(temp_sleep)
    temp_sleep_min = (temp_sleep - int(temp_sleep)) * 60
    if int(temp_sleep_min) == 60:
        temp_sleep_min = 0

    return datetime.time(temp_sleep_hour, int(temp_sleep_min), 0)


def time2point(sleep, axis_range=None, npointsperday=None, all_dates=None, day=None):
    # TODO: many of the input variables were clearly intended to be used here
    # but are not.
    logger.debug(f"Converting time to point: {sleep}, {axis_range}, {npointsperday}")

    if sleep == 0:
        return 0
    sleep_split = sleep.split(":")
    # Get sleep time and transform to timepoints
    sleep_time_hour = int(sleep_split[0])
    sleep_time_min = int(sleep_split[1])
    # hour
    if sleep_time_hour >= 0 and sleep_time_hour < 12:
        sleep_time_hour = ((sleep_time_hour + 12) * 8640) / 12
    else:
        sleep_time_hour = ((sleep_time_hour - 12) * 8640) / 12

    sleep_time_min *= 12

    return sleep_time_hour + sleep_time_min


def point2time_timestamp(point, axis_range, npointsperday):
    if point > 6 * axis_range:
        temp_point = ((point * 24) / npointsperday) - 12
    else:
        temp_point = (point * 24) / npointsperday + 12
    temp_point_hour = int(temp_point)

    temp_point_min = (temp_point - int(temp_point)) * 60
    if int(temp_point_min) == 60:
        temp_point_min = 00

    if int(temp_point_min) < 10:
        temp_point_min = "0" + str(int(temp_point_min))
        point_new = str(temp_point_hour) + ":" + temp_point_min
    else:
        point_new = str(temp_point_hour) + ":" + str(int(temp_point_min))

    return point_new


def hour_to_time_string(hour: int) -> str:
    """Converts an hour integer to a time string in the format of 'hour am/pm'.
    If the hour is 0 or 24, returns 'noon'. If the hour is 12, returns
    'midnight'.

    Args:
        hour: The hour to convert to a time string.

    Returns:
        The time string.
    """
    hour %= 24

    if hour == 0:
        return "noon"
    if hour == 12:
        return "midnight"

    clock_hour = hour % 12
    am_pm = "pm" if hour >= 12 else "am"

    return f"{clock_hour}{am_pm}"
