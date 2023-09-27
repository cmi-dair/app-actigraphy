"""Entrypoint for the Actigraphy app."""
from actigraphy import app

app.app.run_server(port=8051, host="0.0.0.0")
