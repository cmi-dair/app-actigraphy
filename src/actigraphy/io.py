"""Module for reading and writing data from and to files."""
import dataclasses
import datetime
import enum
import pathlib
import re
from typing import Iterator

import pandas as pd
import pydantic
import rdata


class Weekdays(str, enum.Enum):
    """Enum for weekdays."""

    MONDAY = "Monday"
    TUESDAY = "Tuesday"
    WEDNESDAY = "Wednesday"
    THURSDAY = "Thursday"
    FRIDAY = "Friday"
    SATURDAY = "Saturday"
    SUNDAY = "Sunday"


class MS4Entry(pydantic.BaseModel):
    """Model for an entry of MS4 data."""

    id: str
    night: int
    sleeponset: float
    wakeup: float
    spt_duration: float
    sleepparam: str
    guider_onset: float
    guider_wakeup: float
    guider_spt_duration: float
    error_onset: float
    error_wake: float
    error_dur: float
    fraction_night_invalid: float
    sleep_duration_in_spt: float
    waso: float
    duration_sib_wakinghours: float
    number_sib_sleepperiod: int
    number_of_awakenings: int
    number_sib_wakinghours: int
    duration_sib_wakinghours_atleast15min: float
    sleeponset_ts: datetime.time
    wakeup_ts: datetime.time
    guider_onset_ts: datetime.time
    guider_wakeup_ts: datetime.time
    page: int
    daysleeper: bool
    weekday: Weekdays
    filename: str
    cleaningcode: int
    sleeplog_used: bool
    acc_available: bool
    guider: str
    sleep_regularity_index: float | None
    sri_fraction_valid: float | None
    longitudinal_axis: float | None


@dataclasses.dataclass
class MS4:
    """Represents an MS4 file containing actigraphy data.

    Attributes:
        rows: A list of MS4Row objects representing the actigraphy data.
    """

    rows: list[MS4Entry]

    @classmethod
    def from_file(cls, filepath: str | pathlib.Path) -> "MS4":
        """Reads an MS4 file from disk and returns an MS4 object.

        Args:
            filepath: The path to the MS4 file.

        Returns:
            An MS4 object containing the data from the file.
        """
        dataframe = _rdata_to_dataframe(filepath)
        data_dicts = dataframe.to_dict(orient="records")
        ms4_rows = []
        for row in data_dicts:
            row_snake_case = {_snakecase(key): value for key, value in row.items()}
            ms4_rows.append(MS4Entry(**row_snake_case))

        return cls(rows=ms4_rows)

    def __iter__(self) -> Iterator[MS4Entry]:
        """Returns an iterator over the rows of the ActigraphyData object.

        Returns:
            iterator: An iterator over the rows of the ActigraphyData object.
        """
        return iter(self.rows)

    def __getitem__(self, key: int) -> MS4Entry:
        """Get the row at the specified index.

        Args:
            key: The index of the row to retrieve.

        Returns:
            list: The row at the specified index.
        """
        return self.rows[key]


def _rdata_to_dataframe(filepath: str | pathlib.Path) -> pd.DataFrame:
    """Converts an Rdata file to a pandas dataframe.

    Args:
        filepath: The path to the Rdata file.

    Returns:
        np.ndarray: The numpy array.
    """
    data = rdata.parser.parse_file(filepath)
    datadict = rdata.conversion.convert(data)
    keys = list(datadict.keys())
    if len(keys) == 1:
        return datadict[keys[0]]
    raise ValueError(f"Expected one key, got {len(keys)}.")


def _snakecase(s: str) -> str:
    """Converts a string to snake case. If the input is all uppercase,
    it is converted to all lowercase.

    Args:
        s: The string to convert.

    Returns:
        The converted string.
    """
    if all(c.isupper() for c in s):
        return s.lower()
    return re.sub(r"(?<!^)(?<!_)(?=[A-Z])", "_", s).lower()
