""" Unit tests for the plotting module. """
import pytest
from plotly import graph_objects

from actigraphy.plotting import sensor_plots


def test_build_sensor_plot() -> None:
    """Test the build_sensor_plot function."""
    timestamps = ["2022-01-01 00:00", "2022-01-01 00:01", "2022-01-01 00:02"]
    sensor_angle = [30, 45, 60]
    arm_movement = [5, 10, 15]
    title_day = "Day 1"
    n_ticks = 1

    figure = sensor_plots.build_sensor_plot(
        timestamps, sensor_angle, arm_movement, title_day, n_ticks
    )

    assert isinstance(figure, graph_objects.Figure)
    assert len(figure.data) == 2
    assert figure.data[0].name == "Angle of sensor's z-axis"
    assert figure.data[1].name == "Arm movement"
    assert figure.layout.title.text == title_day


def test_add_rectangle() -> None:
    """Test the add_rectangle function."""
    figure = graph_objects.Figure()
    figure.add_trace(graph_objects.Scatter(x=[1, 2, 3], y=[1, 2, 3]))
    limits = [1, 2]
    color = "blue"
    label = "Test"

    new_figure = sensor_plots.add_rectangle(figure, limits, color, label)

    assert isinstance(new_figure, graph_objects.Figure)
    assert len(new_figure.layout.shapes) == 1
    assert new_figure.layout.shapes[0].x0 == limits[0]
    assert new_figure.layout.shapes[0].x1 == limits[1]
    assert new_figure.layout.shapes[0].fillcolor == color
    assert new_figure.layout.shapes[0].opacity == 0.2


def test_build_sensor_plot_unequal_lengths() -> None:
    """Test that build_sensor_plot raises a ValueError when input sequences have unequal lengths."""
    timestamps = ["2022-01-01 00:00", "2022-01-01 00:01", "2022-01-01 00:02"]
    sensor_angle = [30, 45]
    arm_movement = [5, 10, 15]

    with pytest.raises(ValueError):
        sensor_plots.build_sensor_plot(timestamps, sensor_angle, arm_movement, "Day 1")
