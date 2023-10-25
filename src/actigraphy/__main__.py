"""Entrypoint for the Actigraphy app."""
from actigraphy import app


def main() -> None:
    """Creates the Dash app and runs the server."""
    dash_app = app.create_app()
    dash_app.run_server(port=8051, host="0.0.0.0")  # noqa: S104


if __name__ == "__main__":
    main()
