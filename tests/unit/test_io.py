"""Unit tests for the io module."""

import pathlib

from actigraphy import io


def test_ms4(data_dir: pathlib.Path) -> None:
    """Test the MS4 class."""
    ms4 = io.MS4.from_file(data_dir / "ms4.RData")

    assert ms4[0].night == 1
