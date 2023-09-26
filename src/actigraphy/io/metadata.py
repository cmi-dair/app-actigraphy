"""Metadata class for actigraphy data import."""
import pathlib
import re
from typing import Any, Literal

import pandas as pd
import pydantic
import rdata


class MetaData_C(pydantic.BaseModel):
    cal_error_end: float
    cal_error_start: float
    scale: list[float]
    offset: list[float]
    tempoffset: list[float]
    qc_message: str
    npoints: int
    nhoursused: float
    use_temp: bool


class MetaData_I(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)
    header: pd.DataFrame
    monc: float
    monn: str
    dformc: float
    dformn: str
    sf: int
    filename: str


class MetaData_M(pydantic.BaseModel):
    model_config = pydantic.ConfigDict(arbitrary_types_allowed=True)
    filecorrupt: bool
    filetooshort: bool
    nfile_pages_skipped: int
    metalong: pd.DataFrame
    metashort: pd.DataFrame
    wday: int
    wdayname: Literal[
        "Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"
    ]
    windowsizes: list[int]
    bsc_qc: pd.DataFrame


class MetaData(pydantic.BaseModel):
    c: MetaData_C
    i: MetaData_I
    m: MetaData_M
    filefoldername: str
    filename_dir: pathlib.Path

    @classmethod
    def from_file(cls, filepath: str | pathlib.Path) -> "MetaData":
        """Reads a metadata file from disk and returns a Metadata object.

        Args:
            filepath: The path to the metadata file.

        Returns:
            A Metadata object.
        """
        metadata = _rdata_to_datadict(filepath)
        metadata["C"]["qc_message"] = metadata["C"]["QCmessage"]
        del metadata["C"]["QCmessage"]
        metadata = _recursive_clean_rdata(metadata)
        return cls(**metadata)


def _clean_key(key: str) -> str:
    """Replaces strings with snakecase characters and legal attribute names.

    Args:
        key: The key name to clean.

    Returns:
        A cleaned key.

    """
    key = key.replace(".", "_")
    key = _snakecase(key)
    return key


def _clean_value(value: Any) -> Any:
    """Cleans a value."""
    if isinstance(value, list) and len(value) == 1:
        return value[0]
    return value


def _recursive_clean_rdata(r_data: dict[str, Any]) -> dict[str, Any]:
    """Replaces dictionary keys with snakecase characters and legal attribute names.
    Replaces single length lists in dictionary values with their first element.

    Args:
        rdata: The dictionary to clean.

    Returns:
        A dictionary with cleaned keys.

    Notes:
        - This function acts recursively on nested dictionaries.
        - Replaces `.` in keys with `_`.
        - Sets all attributes to snakecase.
    """
    cleaned_rdata = {}
    for key, value in r_data.items():
        key = _clean_key(key)
        value = _clean_value(value)
        if isinstance(value, dict):
            value = _recursive_clean_rdata(value)
        cleaned_rdata[key] = value
    return cleaned_rdata


def _rdata_to_datadict(filepath: str | pathlib.Path) -> dict[str, Any]:
    """Converts an Rdata file to a pandas dataframe.

    Args:
        filepath: The path to the Rdata file.

    Returns:
        np.ndarray: The numpy array.
    """
    data = rdata.parser.parse_file(filepath)
    return rdata.conversion.convert(data)


def _snakecase(string: str) -> str:
    """Converts a string to snake case. Consecutive uppercase letters
    do not receive underscores between them.

    Args:
        string: The string to convert.

    Returns:
        The converted string.
    """
    return re.sub(r"(?<=[A-Z])(?!$)(?!_)(?![A-Z])", "_", string[::-1]).lower()[::-1]
