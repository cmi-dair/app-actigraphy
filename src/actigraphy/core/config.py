"""Contains the app settings."""
import functools
import re

import pydantic


@pydantic.dataclasses.dataclass
class Colors:
    """Represents the colors used in the app."""

    background: str = "#FFFFFF"
    text: str = "#111111"
    title_text: str = "#0060EE"


class Settings(pydantic.BaseModel):
    """Represents the app settings."""

    NAME: str = pydantic.Field("Actigraphy", description="The name of the app.")
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
