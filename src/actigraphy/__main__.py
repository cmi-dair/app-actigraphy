"""Entrypoint for the Actigraphy app."""
from actigraphy import app

dash_app = app.create_app()
dash_app.run_server(port=8051, host="0.0.0.0")
