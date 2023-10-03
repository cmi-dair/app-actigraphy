import datetime

from actigraphy.core import utils


def test_datetime_delta_as_hh_mm() -> None:
    """Test the datetime_delta_as_hh_mm function."""
    delta = datetime.timedelta(hours=4, minutes=30)
    expected = "04:30"

    actual = utils.datetime_delta_as_hh_mm(delta)

    assert actual == expected
