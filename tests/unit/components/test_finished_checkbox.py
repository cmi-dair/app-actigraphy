"""Unit tests for the finished_checkbox module."""
from pytest_mock import plugin

from . import callback_test_manager


def test_write_log_done(mocker: plugin.MockerFixture) -> None:
    """Test the write_log_done function."""
    mocker.patch("actigraphy.io.minor_files.write_log_analysis_completed")
    func = callback_test_manager.get_callback("write_log_done")
    file_manager = {
        "identifier": "identifier",
        "completed_analysis_file": "completed_analysis_file",
    }

    actual = func(True, file_manager)

    assert actual is True
