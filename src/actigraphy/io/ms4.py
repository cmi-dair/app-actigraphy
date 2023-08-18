"""Module for reading and writing data from and to files."""
import dataclasses
import datetime
import pathlib
from typing import Iterator

import pydantic

from actigraphy.io import utils


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
    weekday: utils.Weekdays
    filename: str
    cleaningcode: int
    sleeplog_used: bool
    acc_available: bool
    guider: str
    sleep_regularity_index: float | None
    sri_fraction_valid: float | None
    longitudinal_axis: float | None
    calendar_date: str


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
        dataframe = utils.rdata_to_datadict(filepath)
        data_dicts = dataframe["nightsummary"].to_dict(orient="records")
        ms4_rows = []
        for row in data_dicts:
            row_snake_case = {utils.snakecase(key): value for key, value in row.items()}
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
