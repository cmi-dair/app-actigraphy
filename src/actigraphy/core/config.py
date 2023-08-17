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

    @pydantic.validator("*", pre=True)
    def _validate_color(self, value: str) -> str:
        """Validates that a color is a valid hex color.

        Args:
            value: The color to validate.

        Returns:
            The validated color.

        Raises:
            ValueError: If the color is invalid.
        """
        if re.match(r"^#(?:[0-9a-fA-F]{3}){1,2}$", value):
            return value
        raise ValueError(f"{value} is not a valid hex color.")


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
