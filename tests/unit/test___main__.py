"""Unit tests for the __main__ module."""
from pytest_mock import plugin

from actigraphy import __main__  # assuming this is the module name


def test___main__(mocker: plugin.MockerFixture) -> None:
    """Tests that the __main__ function calls the create_app function and runs the
    server."""
    mock_dash_app = mocker.MagicMock()
    mock_create_app = mocker.patch(
        "actigraphy.__main__.app.create_app", return_value=mock_dash_app
    )

    __main__.__main__()

    mock_create_app.assert_called_once()
    mock_dash_app.run_server.assert_called_once_with(port=8051, host="0.0.0.0")
