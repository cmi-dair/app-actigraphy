""" Entrypoint for the Actigraphy app. """
import logging

import dash
import dash_bootstrap_components

from actigraphy.core import callbacks, cli, components, config

settings = config.get_settings()
APP_NAME = settings.APP_NAME
LOGGER_NAME = settings.LOGGER_NAME

config.initialize_logger(logging_level=logging.DEBUG)
logger = logging.getLogger(LOGGER_NAME)

logger.info("Starting Actigraphy app")
app = dash.Dash(
    APP_NAME, external_stylesheets=[dash_bootstrap_components.themes.BOOTSTRAP]
)
app.title = APP_NAME

logger.debug("Attaching callbacks to app")
callbacks.manager.attach_to_app(app)

logger.debug("Parsing command line arguments")
args = cli.parse_args()
subject_directories = cli.get_subject_folders(args)

logger.debug("Creating app layout")
app.layout = components.layout(subject_directories)

if __name__ == "__main__":
    logger.debug("Running app")
    app.run_server(debug=True, port=8051, dev_tools_hot_reload=True)
