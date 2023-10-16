"""Tests the core utilities."""
import datetime

from actigraphy.core import utils


def test_time2point() -> None:
    """Test that time2point returns the time difference in minutes."""
    time = datetime.datetime.fromisoformat("1993-08-26T15:00:00.000000")
    date = datetime.date.fromisoformat("1993-08-26")
    expected = 180

    actual = utils.time2point(time, date)

    assert actual == expected


def test_point2time() -> None:
    """Test that point2time returns the new time."""
    point = 180
    date = datetime.date.fromisoformat("1993-08-26")
    expected = datetime.datetime.fromisoformat("1993-08-26T15:00:00.000000")

    actual = utils.point2time(point, date)

    assert actual == expected


def test_point2time_timestamp() -> None:
    """Test that a correct HH:MM string is returned."""
    point = 180
    n_points_per_day = 1440
    offset = 12
    expected = "15:00"

    actual = utils.point2time_timestamp(point, n_points_per_day, offset)

    assert actual == expected


def test_slider_values_to_graph_values() -> None:
    """Tests the conversion from slider values to graph values."""
    n_points_per_day = 2880
    values = [0, 60]
    expected = [0, 120]

    actual = utils.slider_values_to_graph_values(values, n_points_per_day)

    assert actual == expected
