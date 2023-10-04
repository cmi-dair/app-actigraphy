"""Entrypoint for the Actigraphy app."""
from actigraphy import app


def __main__() -> None:
    dash_app = app.create_app()
    dash_app.run_server(port=8051, host="0.0.0.0")


if __name__ == "__main__":
    __main__()
