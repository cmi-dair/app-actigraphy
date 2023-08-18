"""Contains the app settings."""
import functools
import logging

import pydantic


@pydantic.dataclasses.dataclass
class Colors:
    """Represents the colors used in the app."""

    background: str = "#FFFFFF"
    text: str = "#111111"
    title_text: str = "#0060EE"


class Settings(pydantic.BaseModel):
    """Represents the app settings."""

    APP_NAME: str = pydantic.Field("Actigraphy", description="The name of the app.")
    LOGGER_NAME: str = pydantic.Field(
        "Actigraphy", description="The name of the logger."
    )
    APP_COLORS: Colors = pydantic.Field(
        Colors(),
        description="The colors used in the app.",
    )


@functools.lru_cache()
def get_settings() -> Settings:
    """Cached function to get the app settings.

    Returns:
        The app settings.
    """
    return Settings()


def initialize_logger() -> None:
    """Initializes the logger."""
    settings = get_settings()
    logger = logging.getLogger(settings.LOGGER_NAME)
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )

    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    logger.addHandler(ch)
