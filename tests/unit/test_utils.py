import datetime

from actigraphy.core import utils


def test_calculate_sleep_duration() -> None:
    """Test the datetime_delta_as_hh_mm function."""
    delta = datetime.timedelta(hours=4, minutes=30)
    expected = "04:30"

    actual = utils.datetime_delta_as_hh_mm(delta)

    assert actual == expected


def test_point2time() -> None:
    """Test the point2time function."""
    point = 11
    expected = datetime.time(23, 0, 0)

    actual = utils.point2time(point)

    assert actual == expected
