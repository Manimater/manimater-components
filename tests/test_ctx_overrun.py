from unittest.mock import Mock

import pytest

from manimate.ctx import Ctx


@pytest.mark.parametrize("elapsed,expected", [
    (0.0, 0.0),
    (5.0, 0.0),
    (10.0, 0.0),
    (12.5, 2.5),
])
def test_overrun_property(elapsed, expected):
    ctx = Ctx(Mock(), 10.0)
    ctx.elapsed = elapsed
    assert ctx.overrun == pytest.approx(expected)


def test_play_overrun():
    ctx = Ctx(Mock(), 2.0)
    ctx.play(Mock(), run_time=3.0)
    assert ctx.overrun == pytest.approx(1.0)
    assert ctx.remaining == 0.0


def test_wait_overrun():
    ctx = Ctx(Mock(), 2.0)
    ctx.wait(3.0)
    assert ctx.overrun == pytest.approx(1.0)


def test_finish_does_not_increase_overrun():
    ctx = Ctx(Mock(), 2.0)
    ctx.wait(3.0)
    ctx.finish()
    assert ctx.overrun == pytest.approx(1.0)


def test_finish_within_budget():
    ctx = Ctx(Mock(), 5.0)
    ctx.wait(2.0)
    ctx.finish()
    assert ctx.elapsed == pytest.approx(5.0)
    assert ctx.overrun == 0.0
