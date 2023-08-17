"""Pytest configuration file."""
import pathlib

import pytest


@pytest.fixture(scope="session")
def data_dir() -> pathlib.Path:
    """Returns the path to the test data directory for this project.

    Returns:
        A pathlib.Path object representing the path to the 'data' directory.
    """
    return pathlib.Path(__file__).parent / "data"
