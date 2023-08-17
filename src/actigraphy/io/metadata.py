import pathlib
from typing import Any

import pandas as pd
import pydantic

from actigraphy.io import utils


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
    n_file_pages_skipped: int
    metalong: pd.DataFrame
    metashort: pd.DataFrame
    wday: int
    wdayname: utils.Weekdays
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
        metadata = utils.rdata_to_datadict(filepath)
        metadata["C"]["qc_message"] = metadata["C"]["QCmessage"]
        del metadata["C"]["QCmessage"]
        metadata = _recursive_remove_single_length_lists(metadata)
        metadata = _recursive_clean_dict_keys(metadata)
        return cls(**metadata)


def _recursive_remove_single_length_lists(rdata: dict[str, Any]) -> dict[str, Any]:
    """Replaces single length lists with their first element.

    Args:
        rdata: The dictionary to clean.

    Returns:
        A dictionary with cleaned keys.

    Notes:
        - This function acts recursively on nested dictionaries.
    """

    def clean_value(value: Any) -> Any:
        """Cleans a value."""
        if isinstance(value, dict):
            return _recursive_remove_single_length_lists(value)
        if isinstance(value, list) and len(value) == 1:
            return value[0]
        return value

    return {key: clean_value(value) for key, value in rdata.items()}


def _recursive_clean_dict_keys(rdata: dict[str, Any]) -> dict[str, Any]:
    """Replaces dictionary keys with snakecase characters and legal attribute names.

    Args:
        rdata: The dictionary to clean.

    Returns:
        A dictionary with cleaned keys.

    Notes:
        - This function acts recursively on nested dictionaries.
        - Replaces `.` in keys with `_`.
        - Sets all attributes to snakecase.
    """

    def clean_key(key: str) -> str:
        """Cleans a key."""
        key = key.replace(".", "_")
        key = utils.snakecase(key)
        return key

    def clean_value(value: Any) -> Any:
        """Cleans a value."""
        if isinstance(value, dict):
            return _recursive_clean_dict_keys(value)
        return value

    return {clean_key(key): clean_value(value) for key, value in rdata.items()}
