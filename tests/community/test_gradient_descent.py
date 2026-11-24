"""Numerical and validation tests for gradient descent."""
from __future__ import annotations

import math
import pytest

from manimate.components.community.gradient_descent import (
    comparison_trajectories, gradient_descent_steps, loss_gradient, loss_value,
)


def test_bowl_loss_and_gradient():
    assert loss_value(3.0, "bowl") == pytest.approx(4.5)
    assert loss_gradient(3.0, "bowl") == pytest.approx(3.0)


def test_bumpy_loss_and_gradient():
    x = 0.7
    assert loss_value(x, "bumpy") == pytest.approx(0.5*x*x + 0.35*math.sin(3*x))
    assert loss_gradient(x, "bumpy") == pytest.approx(x + 1.05*math.cos(3*x))


@pytest.mark.parametrize("loss", ["bad", "", None])
def test_unknown_loss_rejected(loss):
    with pytest.raises(ValueError):
        loss_value(1.0, loss)
    with pytest.raises(ValueError):
        loss_gradient(1.0, loss)
    with pytest.raises(ValueError):
        gradient_descent_steps(0.5, 1.0, 3, loss)


def test_zero_learning_rate_does_not_move():
    result = gradient_descent_steps(0, 3, 5)
    assert result["status"] == "no_progress"
    assert [p["x"] for p in result["points"]] == [3.0]


def test_small_rate_makes_slow_progress():
    result = gradient_descent_steps(0.1, 3, 3)
    assert [p["x"] for p in result["points"]] == pytest.approx([3, 2.7, 2.43, 2.187])


def test_rate_one_reaches_bowl_minimum():
    result = gradient_descent_steps(1, 3, 8)
    assert result["status"] == "converged"
    assert result["points"][-1]["x"] == pytest.approx(0)


def test_rate_above_one_overshoots_and_converges():
    result = gradient_descent_steps(1.5, 3, 8)
    xs = [p["x"] for p in result["points"]]
    assert xs[1] < 0
    assert abs(xs[-1]) < abs(xs[0])


def test_rate_two_oscillates_without_converging():
    result = gradient_descent_steps(2, 1, 4)
    assert [p["x"] for p in result["points"]] == pytest.approx([1, -1, 1, -1, 1])
    assert result["status"] == "max_steps"


def test_large_rate_shows_overshoots_before_divergence():
    result = gradient_descent_steps(2.5, 1.5, 8)
    xs = [p["x"] for p in result["points"]]
    assert len(xs) >= 3
    assert xs[1] < 0 < xs[2]
    assert result["status"] == "diverged"


def test_start_is_clamped_and_reported():
    result = gradient_descent_steps(0.1, 100, 2)
    assert result["start_clamped"]
    assert result["points"][0]["x"] == pytest.approx(3.5)
    assert "clamped" in result["message"]


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), float("-inf")])
def test_non_finite_start_rejected(bad):
    with pytest.raises(ValueError):
        gradient_descent_steps(0.1, bad, 3)


@pytest.mark.parametrize("bad", [float("nan"), float("inf"), -0.1, 5.1])
def test_invalid_learning_rate_rejected(bad):
    with pytest.raises(ValueError):
        gradient_descent_steps(bad, 1, 3)


@pytest.mark.parametrize("bad", [0, 11, -1, 1.5, True])
def test_invalid_step_count_rejected(bad):
    with pytest.raises(ValueError):
        gradient_descent_steps(0.1, 1, bad)


def test_comparison_uses_three_expected_rates_and_same_start():
    runs = comparison_trajectories(1.5, 8, "bowl")
    assert list(runs) == [0.1, 0.8, 2.5]
    assert all(run["points"][0]["x"] == pytest.approx(1.5) for run in runs.values())


def test_comparison_behaviours_are_distinct():
    runs = comparison_trajectories(1.5, 8, "bowl")
    slow, stable, excessive = (runs[r] for r in (0.1, 0.8, 2.5))
    assert slow["points"][-1]["x"] > 0
    assert stable["points"][-1]["x"] == pytest.approx(0, abs=0.01)
    assert excessive["status"] == "diverged"
    assert excessive["points"][1]["x"] < 0 < excessive["points"][2]["x"]


def test_trajectory_is_deterministic():
    assert gradient_descent_steps(0.25, 2, 5, "bumpy") == gradient_descent_steps(0.25, 2, 5, "bumpy")


def test_all_returned_points_are_finite_and_bounded():
    result = gradient_descent_steps(0.75, 3, 10, "bumpy")
    for point in result["points"]:
        assert -4 <= point["x"] <= 4
        assert math.isfinite(point["loss"])
        assert math.isfinite(point["gradient"])
