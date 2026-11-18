"""Gradient-descent visualization with comparison and exploration modes."""
from __future__ import annotations

import math

from manim import (
    DOWN, LEFT, RIGHT, Arrow, Axes, Create, Dot, FadeIn, FadeOut, FadeTransform,
    Line, VGroup, Write,
)

from ... import theme
from ...ctx import Ctx, label
from ...registry import Param as P, component


_X_MIN, _X_MAX = -4.0, 4.0
_START_MIN, _START_MAX = -3.5, 3.5
_MAX_STEPS = 10
_MAX_LEARNING_RATE = 5.0
_LOSSES = ("bowl", "bumpy")
_COMPARISON_RATES = (0.1, 0.8, 2.5)
_COMPARISON_COLORS = (theme.YELLOW, theme.GOOD, theme.DANGER)


def loss_value(x: float, loss: str = "bowl") -> float:
    """Evaluate a supported one-dimensional loss function."""
    x = float(x)
    if not math.isfinite(x):
        raise ValueError("x must be finite")
    if loss == "bowl":
        return 0.5 * x * x
    if loss == "bumpy":
        return 0.5 * x * x + 0.35 * math.sin(3.0 * x)
    raise ValueError("loss must be 'bowl' or 'bumpy'")


def loss_gradient(x: float, loss: str = "bowl") -> float:
    """Return the analytical derivative of a supported loss function."""
    x = float(x)
    if not math.isfinite(x):
        raise ValueError("x must be finite")
    if loss == "bowl":
        return x
    if loss == "bumpy":
        return x + 1.05 * math.cos(3.0 * x)
    raise ValueError("loss must be 'bowl' or 'bumpy'")


def gradient_descent_steps(
    learning_rate: float, start_x: float, steps: int, loss: str = "bowl"
) -> dict:
    """Return a deterministic bounded trajectory; points includes the initial point."""
    try:
        learning_rate, start_x = float(learning_rate), float(start_x)
    except (TypeError, ValueError, OverflowError) as exc:
        raise ValueError("learning_rate and start_x must be finite numbers") from exc
    if not math.isfinite(learning_rate) or not 0.0 <= learning_rate <= _MAX_LEARNING_RATE:
        raise ValueError(f"learning_rate must be between 0 and {_MAX_LEARNING_RATE:g}")
    if not math.isfinite(start_x):
        raise ValueError("start_x must be finite")
    if isinstance(steps, bool) or not isinstance(steps, int) or not 1 <= steps <= _MAX_STEPS:
        raise ValueError(f"steps must be an integer from 1 to {_MAX_STEPS}")
    if loss not in _LOSSES:
        raise ValueError("loss must be 'bowl' or 'bumpy'")

    x = max(_START_MIN, min(_START_MAX, start_x))
    clamped = x != start_x
    points = [{
        "step": 0, "x": x, "loss": loss_value(x, loss),
        "gradient": loss_gradient(x, loss),
    }]
    status, message = "max_steps", f"Completed {steps} updates."
    if learning_rate == 0:
        status, message = "no_progress", "Learning rate is zero: the parameter does not move."
    else:
        for step in range(1, steps + 1):
            previous = points[-1]
            next_x = x - learning_rate * previous["gradient"]
            if not math.isfinite(next_x) or not _X_MIN <= next_x <= _X_MAX:
                status, message = "diverged", "Divergence: the next update leaves the plotted range."
                break
            next_loss = loss_value(next_x, loss)
            if not math.isfinite(next_loss):
                status, message = "diverged", "Divergence: the loss became non-finite."
                break
            points.append({
                "step": step, "x": next_x, "loss": next_loss,
                "gradient": loss_gradient(next_x, loss),
            })
            x = next_x
            if abs(points[-1]["gradient"]) < 1e-7:
                status, message = "converged", "Converged: the gradient is approximately zero."
                break
    if clamped:
        message = "Start value was clamped to the visible range. " + message
    return {"points": points, "status": status, "message": message, "start_clamped": clamped}


def comparison_trajectories(start_x: float, steps: int, loss: str = "bowl") -> dict:
    """Compute the three fixed learning-rate trajectories using the shared engine."""
    return {
        rate: gradient_descent_steps(rate, start_x, steps, loss)
        for rate in _COMPARISON_RATES
    }


def _finite_number(value) -> bool:
    try:
        return math.isfinite(float(value))
    except (TypeError, ValueError, OverflowError):
        return False


def _learning_rate_ok(value) -> str | None:
    if not _finite_number(value) or not 0 <= float(value) <= _MAX_LEARNING_RATE:
        return f"must be a finite number from 0 to {_MAX_LEARNING_RATE:g}"
    return None


def _start_x_ok(value) -> str | None:
    return None if _finite_number(value) else "must be a finite number"


def _steps_ok(value) -> str | None:
    if isinstance(value, bool) or not isinstance(value, int) or not 1 <= value <= _MAX_STEPS:
        return f"must be a whole number from 1 to {_MAX_STEPS}"
    return None


def _loss_ok(value) -> str | None:
    return None if value in _LOSSES else "must be 'bowl' or 'bumpy'"


def _mode_ok(value) -> str | None:
    return None if value in ("comparison", "exploration") else "must be 'comparison' or 'exploration'"


def _draw_axes(ctx: Ctx, loss: str):
    """Draw a larger shared plot while reserving room for labels and summaries."""
    axes = Axes(
        x_range=[_X_MIN, _X_MAX, 1],
        y_range=[-1.0, 9.0, 2],
        x_length=10.4,
        y_length=3.0,
        axis_config={
            "color": theme.MUTED,
            "include_numbers": True,
            "font_size": 20,
            "stroke_width": 2,
        },
    ).move_to((0.0, -0.10, 0.0))
    curve = axes.plot(
        lambda value: loss_value(value, loss),
        x_range=[_X_MIN, _X_MAX, 0.04],
        color=theme.ACCENT,
        stroke_width=4,
        use_smoothing=False,
    )
    ctx.play(Create(axes), Create(curve), run_time=0.65)
    return axes


def _status_title(result: dict) -> str:
    status = result["status"]
    if status == "converged":
        return "CONVERGED"
    if status == "diverged":
        return "DIVERGED"
    if status == "no_progress":
        return "NO MOVEMENT"
    if status == "max_steps":
        return "STILL DESCENDING"
    return status.replace("_", " ").upper()


def _comparison(ctx: Ctx, start_x: float, steps: int, loss: str) -> None:
    results = comparison_trajectories(start_x, steps, loss)
    axes = _draw_axes(ctx, loss)

    heading = ctx.heading("Gradient descent: learning-rate comparison")
    subtitle = label(
        "Same starting point and loss curve  |  compare the update sizes",
        23,
        theme.YELLOW,
    ).move_to((0.0, 2.55, 0.0))
    ctx.play(Write(heading), FadeIn(subtitle), run_time=0.35)

    # Horizontal legend occupies its own band above the plot.
    legend_items = [
        label("η = 0.1  SLOW", 21, _COMPARISON_COLORS[0]),
        label("η = 0.8  STABLE", 21, _COMPARISON_COLORS[1]),
        label("η = 2.5  EXCESSIVE", 21, _COMPARISON_COLORS[2]),
    ]
    legend = VGroup(*legend_items).arrange(RIGHT, buff=0.42)
    legend.move_to((0.0, 1.88, 0))
    direction_note = label(
        "White: +gradient direction    Colored: -η × gradient update",
        16,
        theme.FG,
    )
    direction_note.move_to((0.0, 1.53, 0))
    ctx.play(FadeIn(legend), FadeIn(direction_note), run_time=0.22)

    dots = []
    for rate, color in zip(_COMPARISON_RATES, _COMPARISON_COLORS):
        first = results[rate]["points"][0]
        dot = Dot(axes.c2p(first["x"], first["loss"]), radius=0.09, color=color)
        dots.append(dot)
    ctx.play(*(FadeIn(dot) for dot in dots), run_time=0.2)

    update_count = max(len(result["points"]) - 1 for result in results.values())
    available = max(1.0, ctx.remaining - 1.0)
    per_update = max(0.14, min(0.32, available / max(1, update_count * 1.15)))

    for index in range(1, update_count + 1):
        animations = []
        transient = []
        for rate, color, dot in zip(_COMPARISON_RATES, _COMPARISON_COLORS, dots):
            points = results[rate]["points"]
            if index >= len(points):
                continue
            previous, current = points[index - 1], points[index]
            start_point = axes.c2p(previous["x"], previous["loss"])
            end_point = axes.c2p(current["x"], current["loss"])
            segment = Line(start_point, end_point, color=color, stroke_width=4)
            update_arrow = Arrow(
                start_point, end_point, buff=0.06, color=color, stroke_width=2.8,
                max_tip_length_to_length_ratio=0.18,
            )
            animations.extend([
                Create(segment),
                dot.animate.move_to(end_point),
                FadeIn(update_arrow),
            ])
            transient.append(update_arrow)

        # White arrows show the positive gradient direction.
        # Colored arrows show the actual gradient-descent update (-eta * gradient).
        for rate, color, dot in zip(
            _COMPARISON_RATES, _COMPARISON_COLORS, dots
        ):
            points = results[rate]["points"]

            if index - 1 >= len(points):
                continue

            point = points[index - 1]
            px, py = point["x"], point["loss"]
            slope = point["gradient"]

            if abs(slope) < 1e-5:
                continue

            # Positive gradient points towards increasing loss.
            dx = 0.48 if slope > 0 else -0.48
            end_x = max(_X_MIN, min(_X_MAX, px + dx))

            if abs(end_x - px) < 0.05:
                continue

            gradient_arrow = Arrow(
                axes.c2p(px, py + 0.25),
                axes.c2p(end_x, py + 0.25),
                buff=0.03,
                color=theme.FG,
                stroke_width=2.8,
                max_tip_length_to_length_ratio=0.25,
            )

            animations.append(FadeIn(gradient_arrow))
            transient.append(gradient_arrow)



        if not animations:
            break
        ctx.play(*animations, run_time=per_update)
        if transient:
            ctx.play(*(FadeOut(item) for item in transient), run_time=0.08)

    # Three result columns are separated from the graph and each other.
    summary_x = (-3.55, 0.0, 3.55)
    summaries = []
    for rate, color, x_pos in zip(_COMPARISON_RATES, _COMPARISON_COLORS, summary_x):
        result = results[rate]
        last = result["points"][-1]
        if result["status"] == "diverged":
            final_value = "DIVERGED"
        else:
            final_value = f"x = {last['x']:.2f}"
        summary_text = (
            f"η = {rate:g}  {_status_title(result)}\n"
            f"{final_value}    loss = {last['loss']:.2f}"
        )
        item = label(summary_text, 19, color, width=27).move_to((x_pos, -2.48, 0))
        summaries.append(item)
    ctx.play(*(FadeIn(item) for item in summaries), run_time=0.25)
    ctx.wait(min(ctx.remaining, 1.25))


def _exploration(ctx: Ctx, learning_rate: float, start_x: float, steps: int, loss: str) -> None:
    result = gradient_descent_steps(learning_rate, start_x, steps, loss)
    points = result["points"]
    axes = _draw_axes(ctx, loss)

    heading = ctx.heading("Gradient descent: explore a learning rate")
    subtitle = label(
        f"{loss} loss  |  learning rate η = {learning_rate:.2f}",
        23,
        theme.YELLOW,
    ).move_to((0.0, 2.55, 0.0))
    ctx.play(Write(heading), FadeIn(subtitle), run_time=0.35)

    dot = Dot(axes.c2p(points[0]["x"], points[0]["loss"]), radius=0.09, color=theme.GOOD)
    readout = label(
        f"STEP 0/{steps}    x = {points[0]['x']:.2f}    loss = {points[0]['loss']:.2f}",
        22,
        theme.FG,
    ).move_to((0.0, -2.35, 0.0))
    ctx.play(FadeIn(dot), FadeIn(readout), run_time=0.25)

    update_count = max(1, len(points) - 1)
    per_update = max(0.14, min(0.30, max(0.8, ctx.remaining - 0.9) / update_count))
    for previous, current in zip(points, points[1:]):
        start = axes.c2p(previous["x"], previous["loss"])
        end = axes.c2p(current["x"], current["loss"])
        tangent_dx = 0.32
        left_x = max(_X_MIN, previous["x"] - tangent_dx)
        right_x = min(_X_MAX, previous["x"] + tangent_dx)
        tangent = Line(
            axes.c2p(left_x, previous["loss"] + previous["gradient"] * (left_x - previous["x"])),
            axes.c2p(right_x, previous["loss"] + previous["gradient"] * (right_x - previous["x"])),
            color=theme.FG,
            stroke_width=2.8,
        )
        gradient_arrow = Arrow(
            tangent.get_start(),
            tangent.get_end(),
            buff=0.02,
            color=theme.FG,
            stroke_width=2,
        )
        update_arrow = Arrow(
            start,
            end,
            buff=0.06,
            color=theme.GOOD if current["loss"] <= previous["loss"] else theme.DANGER,
            stroke_width=3.2,
        )
        segment = Line(start, end, color=theme.PURPLE, stroke_width=2.5).set_opacity(0.75)
        new_readout = label(
            f"STEP {current['step']}/{steps}    x = {current['x']:.2f}    loss = {current['loss']:.2f}",
            22,
            theme.FG,
        ).move_to(readout)
        ctx.play(
            FadeIn(tangent), FadeIn(gradient_arrow), Create(update_arrow),
            FadeIn(segment), dot.animate.move_to(end),
            FadeTransform(readout, new_readout),
            run_time=per_update,
        )
        ctx.play(
            FadeOut(tangent), FadeOut(gradient_arrow), FadeOut(update_arrow),
            run_time=0.08,
        )
        readout = new_readout

    status_color = {
        "converged": theme.GOOD,
        "no_progress": theme.WARN,
        "diverged": theme.DANGER,
        "max_steps": theme.FG,
    }[result["status"]]
    status = label(result["message"], 20, status_color, width=76).move_to((0.0, -2.9, 0.0))
    ctx.play(FadeIn(status), run_time=0.2)
    ctx.wait(min(ctx.remaining, 1.25))


@component(
    "gradient_descent",
    "Compares learning-rate behaviour or lets you explore a custom one-dimensional gradient-descent run.",
    {
        "mode": P("string", "comparison or exploration", default="comparison",
                  choices=["comparison", "exploration"], validator=_mode_ok),
        "learning_rate": P("number", "custom step size, used in exploration mode", default=0.5,
                           validator=_learning_rate_ok),
        "start_x": P("number", "initial parameter value; clamped to the visible range", default=1.5,
                     validator=_start_x_ok),
        "steps": P("integer", "number of updates, 1-10", default=8, validator=_steps_ok),
        "loss": P("string", "loss curve: bowl or bumpy", default="bowl",
                  choices=["bowl", "bumpy"], validator=_loss_ok),
    },
    {"mode": "comparison", "learning_rate": 0.5, "start_x": 1.5, "steps": 8, "loss": "bowl"},
    domain="machine-learning",
)
def gradient_descent(
    ctx: Ctx, mode: str = "comparison", learning_rate: float = 0.5,
    start_x: float = 1.5, steps: int = 8, loss: str = "bowl",
) -> None:
    """Render a learning-rate comparison or a single custom trajectory."""
    if mode == "comparison":
        _comparison(ctx, start_x, steps, loss)
    else:
        _exploration(ctx, learning_rate, start_x, steps, loss)
