from unittest.mock import Mock

import pytest
from manim import Rectangle

from manimate.ctx import Ctx, STAGE_CENTER, label, wrap


@pytest.mark.parametrize(
    "text,width,expected",
    [
        ("line one\nline two", 40, "line one\nline two"),
        ("alpha beta\ngamma delta", 6, "alpha\nbeta\ngamma\ndelta"),
        ("one\n\ntwo", 40, "one\n\ntwo"),
        ("\none\n", 40, "\none\n"),
        ("", 40, ""),
        ("\n", 40, "\n"),
        ("one two three", 7, "one two\nthree"),
        ("short", 40, "short"),
    ],
)
def test_wrap_preserves_explicit_lines(text, width, expected):
    assert wrap(text, width) == expected


def test_label_keeps_explicit_lines_when_width_is_given():
    result = label("one\ntwo", width=40)
    assert [line.text for line in result] == ["one", "two"]


@pytest.mark.parametrize(
    "remaining,n,cap,floor,expected",
    [(4, 0, 1, 0.3, 1), (4, -1, 2, 0.3, 2),
     (0, 4, 1, 0.3, 0.3), (1, 9, 1, 0.3, 0.3),
     (100, 2, 1, 0.3, 1), (2, 3, 1, 0.3, 0.5)],
)
def test_beat_respects_floor_and_cap(remaining, n, cap, floor, expected):
    assert Ctx.beat(remaining, n, cap=cap, floor=floor) == expected


@pytest.mark.parametrize("run_time,expected", [(-1, 0.1), (0, 0.1), (0.05, 0.1), (0.5, 0.5)])
def test_play_tracks_the_runtime_sent_to_the_scene(run_time, expected):
    scene = Mock()
    ctx = Ctx(scene, duration=0.2)
    animation = object()
    ctx.play(animation, run_time=run_time, rate_func=None)
    scene.play.assert_called_once_with(animation, run_time=expected, rate_func=None)
    assert ctx.elapsed == expected
    assert ctx.remaining == max(0, 0.2 - expected)


def test_finish_uses_only_the_remaining_budget():
    scene = Mock()
    ctx = Ctx(scene, duration=2)
    ctx.play(run_time=0.5)
    ctx.finish()
    scene.wait.assert_called_once_with(1.5)
    assert ctx.remaining == 0
    ctx.finish()
    scene.wait.assert_called_once()


@pytest.mark.parametrize("seconds", [-1, 0, 0.01])
def test_wait_ignores_nonpositive_and_tiny_durations(seconds):
    scene = Mock()
    ctx = Ctx(scene, duration=2)
    ctx.wait(seconds)
    scene.wait.assert_not_called()
    assert ctx.elapsed == 0


@pytest.mark.parametrize("width,height", [(20, 2), (2, 20), (2, 1)])
def test_fit_shrinks_only_as_needed_and_centers(width, height):
    ctx = Ctx(Mock(), duration=1)
    rectangle = Rectangle(width=width, height=height).shift([1, -1, 0])
    assert ctx.fit(rectangle, max_w=4, max_h=3) is rectangle
    factor = min(1, 4 / width, 3 / height)
    assert rectangle.width == pytest.approx(width * factor)
    assert rectangle.height == pytest.approx(height * factor)
    assert rectangle.get_center() == pytest.approx(STAGE_CENTER)
