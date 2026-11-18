from __future__ import annotations

import math

from manim import (
    Arrow,
    Circle,
    Dot,
    FadeIn,
    Indicate,
    Text,
    ValueTracker,
    VGroup,
    linear,
)

from ... import theme
from ...ctx import Ctx
from ...registry import Param as P, component


def _speeds_ok(source_speed: float, wave_speed: float) -> str | None:
    if not math.isfinite(float(source_speed)) or not math.isfinite(float(wave_speed)):
        return "speeds must be finite numbers"
    if wave_speed <= 0:
        return "wave_speed must be greater than zero"
    if source_speed < 0:
        return "source_speed must be non-negative"
    if source_speed >= wave_speed:
        return "source_speed must be less than wave_speed"
    return None


def _source_speed_ok(source_speed: float) -> str | None:
    if not math.isfinite(float(source_speed)):
        return "must be a finite number"
    if source_speed < 0:
        return "must be non-negative"
    return None


def _wave_speed_ok(wave_speed: float) -> str | None:
    if not math.isfinite(float(wave_speed)) or wave_speed <= 0:
        return "must be a finite number greater than zero"
    return None


def _frequency_ok(frequency: float) -> str | None:
    if not math.isfinite(float(frequency)) or frequency <= 0:
        return "must be a finite number greater than zero"
    return None

# Return approaching and receding frequencies for stationary observers
def _observed_frequencies(
    frequency: float,
    source_speed: float,
    wave_speed: float,
) -> tuple[float, float]:
    err = _speeds_ok(source_speed, wave_speed)
    if err:
        raise ValueError(err)

    err = _frequency_ok(frequency)
    if err:
        raise ValueError(err)

    approaching = frequency * wave_speed / (wave_speed - source_speed)
    receding = frequency * wave_speed / (wave_speed + source_speed)

    return approaching, receding

#Return wavelengths ahead of and behind the moving source
def _observed_wavelengths(
    frequency: float,
    source_speed: float,
    wave_speed: float,
) -> tuple[float, float]:
    err = _speeds_ok(source_speed, wave_speed)
    if err:
        raise ValueError(err)

    err = _frequency_ok(frequency)
    if err:
        raise ValueError(err)

    period = 1.0 / frequency

    ahead = (wave_speed - source_speed) * period
    behind = (wave_speed + source_speed) * period

    return ahead, behind


#Return (emission_position, radius) for each emitted wavefront
def _wavefronts(
    source_speed: float,
    wave_speed: float,
    elapsed: float,
    period: float,
) -> list[tuple[float, float]]:
    err = _speeds_ok(source_speed, wave_speed)
    if err:
        raise ValueError(err)

    if not math.isfinite(float(elapsed)) or elapsed < 0:
        raise ValueError("elapsed must be a finite non-negative number")

    if not math.isfinite(float(period)) or period <= 0:
        raise ValueError("period must be a finite number greater than zero")

    count = int(elapsed / period) + 1

    return [
        (
            source_speed * i * period,
            wave_speed * (elapsed - i * period),
        )
        for i in range(count)
        if elapsed - i * period > 0
    ]


@component(
    "doppler_effect",
    "Shows how a moving source compresses wavefronts ahead and spreads them behind, changing observed pitch.",
    {
        "source_speed": P(
            "number",
            "Source speed, non-negative and below wave_speed",
            default=0.4,
            validator=_source_speed_ok,
        ),
        "wave_speed": P(
            "number",
            "Wave propagation speed, greater than zero",
            default=1.0,
            validator=_wave_speed_ok,
        ),
        "frequency": P(
            "number",
            "Frequency emitted by the source, greater than zero",
            default=1.0,
            validator=_frequency_ok,
        ),
        "show_formula": P(
            "boolean",
            "Whether to display the Doppler frequency equations",
            default=True,
        ),
    },
    {
        "source_speed": 0.4,
        "wave_speed": 1.0,
        "frequency": 1.0,
        "show_formula": True,
    },
    domain="physics",
)
def doppler_effect(
    ctx: Ctx,
    source_speed: float = 0.4,
    wave_speed: float = 1.0,
    frequency: float = 1.0,
    show_formula: bool = True,
) -> None:

    err = _speeds_ok(source_speed, wave_speed)
    if err:
        raise ValueError(err)

    err = _frequency_ok(frequency)
    if err:
        raise ValueError(err)

    approaching, receding = _observed_frequencies(
        frequency,
        source_speed,
        wave_speed,
    )

    ahead_wavelength, behind_wavelength = _observed_wavelengths(
        frequency,
        source_speed,
        wave_speed,
    )

    total_periods = 5
    period = 1.0 / frequency
    scale = 2.0 / (wave_speed * total_periods * period)
    start_x = 0.0
    axis_y = 0.45

    def source_x(tau: float) -> float:
        return (
            start_x
            + source_speed * tau * period * scale
        )

    heading = ctx.heading("The Doppler Effect")

    direction = Arrow(
        [-0.8, 2.85, 0],
        [0.9, 2.85, 0],
        buff=0,
        color=theme.YELLOW,
        stroke_width=3,
        max_tip_length_to_length_ratio=0.15,
    )

    direction_label = Text(
        "DIRECTION OF MOTION",
        font_size=17,
        color=theme.YELLOW,
    ).move_to([0.05, 3.12, 0])

    clock = ValueTracker(0.0)


    # Moving source
    source = Dot(
        radius=0.14,
        color=theme.YELLOW,
    ).move_to([start_x, axis_y, 0])

    source.add_updater(
        lambda mob: mob.move_to(
            [source_x(clock.get_value()), axis_y, 0]
        )
    )

    source_label = Text(
        "SOURCE",
        font_size=19,
        color=theme.YELLOW,
    )

    source_label.add_updater(
        lambda mob: mob.next_to(
            source,
            [0, 1, 0],
            buff=0.16,
        )
    )

    # Expanding wavefronts
    rings = VGroup()

    for emission_index in range(total_periods):
        emission_time = float(emission_index)

        emission_x = source_x(emission_time)

        ring = Circle(
            radius=0.01,
            color=theme.ACCENT,
            stroke_width=2.5,
            fill_opacity=0,
        ).move_to([emission_x, axis_y, 0])

        ring.set_stroke(opacity=0)

        def update_ring(
            mob,
            dt=0,
            emission_time=emission_time,
            emission_x=emission_x,
        ):
            tau = clock.get_value()
            age = tau - emission_time

            if age <= 0:
                mob.set_stroke(opacity=0)
                mob.set_fill(opacity=0)
                return

            radius = wave_speed * period * age * scale

            updated_ring = Circle(
                radius=max(radius, 0.001),
                color=theme.ACCENT,
                stroke_width=2.5,
                fill_opacity=0,
            ).move_to([emission_x, axis_y, 0])

            updated_ring.set_fill(opacity=0)
            updated_ring.set_stroke(opacity=0.85)

            mob.become(updated_ring)

        ring.add_updater(update_ring)
        rings.add(ring)


    # Stationary observers
    observer_x = 2.0

    behind = Dot(
        radius=0.14,
        color=theme.PURPLE,
    ).move_to([-observer_x, axis_y, 0])

    ahead = Dot(
        radius=0.14,
        color=theme.GOOD,
    ).move_to([observer_x, axis_y, 0])

    # Observer labels
    behind_label = Text(
        "RECEDING OBSERVER",
        font_size=18,
        color=theme.PURPLE,
    ).move_to([-observer_x, -1.95, 0])

    ahead_label = Text(
        "APPROACHING OBSERVER",
        font_size=18,
        color=theme.GOOD,
    ).move_to([observer_x, -1.95, 0])

    # Observed frequencies
    behind_frequency = Text(
        f"f' = {receding:.2f} f",
        font_size=24,
        color=theme.PURPLE,
    ).move_to([-observer_x, -2.35, 0])

    ahead_frequency = Text(
        f"f' = {approaching:.2f} f",
        font_size=24,
        color=theme.GOOD,
    ).move_to([observer_x, -2.35, 0])

    # Observed wavelengths
    behind_wavelength_text = Text(
        f"lambda = {behind_wavelength:.2f}",
        font_size=18,
        color=theme.PURPLE,
    ).move_to([-observer_x, -2.78, 0])

    ahead_wavelength_text = Text(
        f"lambda = {ahead_wavelength:.2f}",
        font_size=18,
        color=theme.GOOD,
    ).move_to([observer_x, -2.78, 0])

    parts = [
        heading,
        direction,
        direction_label,
        rings,
        source,
        source_label,
        behind,
        ahead,
        behind_label,
        ahead_label,
        behind_frequency,
        ahead_frequency,
        behind_wavelength_text,
        ahead_wavelength_text,
    ]

    if show_formula:
        formula_1 = Text(
            "Approaching:  f' = f x v / (v - vs)",
            font_size=19,
            color=theme.GOOD,
        ).move_to([0, -3.28, 0])

        formula_2 = Text(
            "Receding:  f' = f x v / (v + vs)",
            font_size=19,
            color=theme.PURPLE,
        ).move_to([0, -3.66, 0])

        parts.extend([
            formula_1,
            formula_2,
        ])

    board = VGroup(*parts)


    ctx.play(
        FadeIn(board),
        run_time=1.0,
    )

    ctx.play(
        clock.animate.set_value(float(total_periods)),
        run_time=6.0,
        rate_func=linear,
    )

    ctx.play(
        Indicate(ahead, color=theme.GOOD),
        run_time=0.7,
    )

    ctx.play(
        Indicate(behind, color=theme.PURPLE),
        run_time=0.7,
    )

    ctx.wait(ctx.remaining)
