"""This module provides a class for managing Dash callbacks.

The CallbackManager class allows registering Dash callbacks and attaching them
to a Dash app. This is useful for defining callbacks in a separate file from
the Dash app itself.
"""
import dataclasses
import logging
from typing import Any, Callable

import dash
from dash import dependencies

from actigraphy.core import config

settings = config.get_settings()
LOGGER_NAME = settings.LOGGER_NAME

logger = logging.getLogger(LOGGER_NAME)


@dataclasses.dataclass
class Callback:
    """A class representing a Dash callback.

    Attributes:
        func (Callable): The function to be called when the callback is triggered.
        outputs (dash.Output | list[dash.Output]): The output(s) of the callback.
        inputs (dash.Input | list[dash.Input]): The input(s) of the callback.
        states (dash.State | list[dash.State]): The state(s) of the callback.
        kwargs (dict): Additional keyword arguments to be passed to the callback.
    """

    func: Callable
    outputs: dash.Output | list[dash.Output]
    inputs: dash.Input | list[dash.Input]
    states: dash.State | list[dash.State] = dataclasses.field(default_factory=list)
    kwargs: dict = dataclasses.field(
        default_factory=lambda: {"prevent_initial_call": False}
    )


class CallbackManager:
    """
    A class for managing Dash callbacks.

    Attributes:
        _callbacks (list[Callback]): A list of Callback objects.
    """

    def __init__(self) -> None:
        self._callbacks: list[Callback] = []

    def callback(self, *args: Any, **kwargs: Any) -> Callable:
        """A decorator for registering a Dash callback.

        Args:
            *args: The arguments of the callback.
            **kwargs: The keyword arguments of the callback.

        Returns:
            Callable: The decorated function.
        """
        output, inputs, state, prevent_initial_call = dependencies.handle_callback_args(
            args, kwargs
        )

        def wrapper(func: Callable) -> None:
            self._callbacks.append(
                Callback(
                    func,
                    output,
                    inputs,
                    state,
                    {"prevent_initial_call": prevent_initial_call},
                )
            )

        return wrapper

    def attach_to_app(self, app: dash.Dash) -> None:
        """Attaches all registered callbacks to a Dash app.

        Args:
            app: The Dash app to attach the callbacks to.
        """
        for callback in self._callbacks:
            logger.debug("Attaching callback: %s.", callback.func.__name__)
            app.callback(
                callback.outputs, callback.inputs, callback.states, **callback.kwargs
            )(callback.func)


# Allow a single manager to be used across multiple files.
global_manager = CallbackManager()


def initialize_components():
    """Initializes the components of the Actigraphy app.

    Notes:
        This is a workaround to allow callbacks to be placed across multiple
        files. All these files use the global_manager object defined in this
        file. As such, a side-effect of importing these files is that all the
        callbacks are registered.
    """
    # pylint: disable=import-outside-toplevel
    from actigraphy.components import (
        app_license,
        day_slider,
        file_selection,
        finished_checkbox,
        graph,
        switches,
    )
