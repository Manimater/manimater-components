"""Plain-Python helpers behind function_plot's tick labels (no Manim render needed)."""
from __future__ import annotations

from manimate.components.general import axis_ticks, format_tick


def test_axis_ticks_cover_the_range_without_float_drift():
    assert axis_ticks(-1.5, 1.5, 0.5) == [-1.5, -1.0, -0.5, 0.0, 0.5, 1.0, 1.5]
    assert axis_ticks(0.1, 0.3, 0.1) == [0.1, 0.2, 0.3]


def test_axis_ticks_reject_an_empty_or_backwards_range():
    assert axis_ticks(2, 1, 1) == []
    assert axis_ticks(0, 1, 0) == []


def test_format_tick_uses_the_step_precision():
    assert format_tick(1.0, 0.5) == "1"
    assert format_tick(0.5, 0.5) == "0.5"
    assert format_tick(-2.0, 2) == "-2"
    assert format_tick(0.25, 0.05) == "0.25"
