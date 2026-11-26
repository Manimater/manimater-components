"""Normal distribution and the empirical 68-95-99.7 rule."""
from __future__ import annotations

import math

from manim import (
    DOWN, Axes, Create, FadeIn, Polygon,
    Transform, VGroup, VMobject,
)

from ... import theme
from ...ctx import Ctx, label
from ...registry import Param as P, component


def _valid_mean(value: float) -> str | None:
    if not math.isfinite(value):
        return "mean must be finite"
    return None


def _valid_std(value: float) -> str | None:
    if not math.isfinite(value) or value <= 0:
        return "standard deviation must be finite and positive"
    return None


def normal_density(
    x: float, mean: float, std_dev: float
) -> float:
    """Calculate the normal probability density."""
    error = _valid_std(std_dev) or _valid_mean(mean)
    if error:
        raise ValueError(error)

    z = (x - mean) / std_dev
    return math.exp(-0.5 * z * z) / math.sqrt(
        2 * math.pi
    ) / std_dev


def band_probability(k: float) -> float:
    """Probability within k standard deviations of the mean."""
    if not math.isfinite(k) or k < 0:
        raise ValueError("band width must be finite and non-negative")
    return math.erf(k / math.sqrt(2))


def _curve(axes, ratio, height, color):
    points = [
        axes.c2p(
            ratio * (i / 20 - 4),
            height * math.exp(-0.5 * (i / 20 - 4) ** 2),
        )
        for i in range(161)
    ]
    curve = VMobject(color=color, stroke_width=4)
    curve.set_points_as_corners(points)
    return curve


def _band(axes, ratio, height, k):
    points = [axes.c2p(-k * ratio, 0)]
    points += [
        axes.c2p(
            ratio * z,
            height * math.exp(-0.5 * z * z),
        )
        for z in [
            -k + 2 * k * i / 120
            for i in range(121)
        ]
    ]
    points.append(axes.c2p(k * ratio, 0))

    return Polygon(
        *points,
        stroke_width=0,
        fill_color=theme.ACCENT,
        fill_opacity=0.35,
    )


@component(
    "normal_distribution",
    "Normal distribution, standard deviation bands and comparison of spread.",
    {
        "mean": P(
            "number", "Mean of the distribution",
            default=0, validator=_valid_mean,
        ),
        "std_dev": P(
            "number", "Positive standard deviation",
            default=1, validator=_valid_std,
        ),
        "compare_std_dev": P(
            "number", "Optional positive comparison deviation",
            validator=_valid_std,
        ),
        "bands": P(
            "string", "Probability bands to display",
            default="three",
            choices=["none", "one", "three"],
        ),
    },
    {
        "mean": 0,
        "std_dev": 1,
        "bands": "three",
    },
    domain="statistics",
)
def normal_distribution(
    ctx: Ctx,
    mean: float = 0,
    std_dev: float = 1,
    compare_std_dev: float | None = None,
    bands: str = "three",
) -> None:
    error = _valid_mean(mean) or _valid_std(std_dev)
    if error:
        raise ValueError(error)

    if compare_std_dev is not None:
        error = _valid_std(compare_std_dev)
        if error:
            raise ValueError(error)

    # Normalize coordinates to avoid overflowing axes for
    # very large means or very small deviations.
    other = (
        std_dev if compare_std_dev is None
        else compare_std_dev
    )
    scale = max(std_dev, other)
    smallest = min(std_dev, other)

    ratio = std_dev / scale
    height = smallest / std_dev

    axes = Axes(
        x_range=[-4, 4, 1],
        y_range=[0, 1.2, 0.4],
        x_length=9.5,
        y_length=2.8,
        tips=False,
        axis_config={"color": theme.MUTED},
    ).move_to((0, 0.45, 0))

    head = ctx.heading("Normal distribution")

    subtitle = label(
        f"Mean = {mean:.4g}    Standard deviation = {std_dev:.4g}",
        23, theme.FG,
    ).next_to(head, DOWN, buff=0.15)

    ticks = VGroup(*[
        label(
            "μ" if k == 0 else f"{k:+d}σ",
            20, theme.MUTED,
        ).next_to(
            axes.c2p(k * ratio, 0),
            DOWN, buff=0.12,
        )
        for k in (
            range(-3, 4) if ratio >= 0.2 else [0]
        )
    ])

    axis_note = label(
        "Density (scaled) · Distance from mean",
        18, theme.MUTED,
    ).next_to(ticks, DOWN, buff=0.18)

    curve = _curve(
        axes, ratio, height, theme.ACCENT
    )

    levels = {
        "none": [],
        "one": [1],
        "three": [1, 2, 3],
    }[bands]

    areas = [
        _band(axes, ratio, height, k)
        for k in levels
    ]

    captions = [
        label(
            f"Within ±{k}σ: {band_probability(k):.1%}",
            28, theme.GOOD,
        ).move_to((0, -2.45, 0))
        for k in levels
    ]

    comparison = None
    comparison_note = None

    if compare_std_dev is not None:
        comparison = _curve(
            axes,
            other / scale,
            smallest / other,
            theme.YELLOW,
        )
        comparison_note = label(
            f"Yellow: σ = {other:.4g} (same mean)",
            20, theme.YELLOW,
        ).move_to((0, -2.95, 0))

    group = VGroup(
        head, subtitle, axes, ticks, axis_note,
        curve, *areas, *captions,
    )

    if comparison is not None:
        group.add(comparison, comparison_note)

    ctx.fit(group)

    steps = 1 + len(levels) + int(comparison is not None)
    beat = ctx.remaining * 0.85 / steps

    ctx.play(
        FadeIn(head), FadeIn(subtitle),
        Create(axes), FadeIn(ticks),
        FadeIn(axis_note), Create(curve),
        run_time=beat,
    )

    if areas:
        active_area = areas[0]
        active_caption = captions[0]

        ctx.play(
            FadeIn(active_area),
            FadeIn(active_caption),
            run_time=beat,
        )

        for area, caption in zip(
            areas[1:], captions[1:]
        ):
            ctx.play(
                Transform(active_area, area),
                Transform(active_caption, caption),
                run_time=beat,
            )

    if comparison is not None:
        ctx.play(
            Create(comparison),
            FadeIn(comparison_note),
            run_time=beat,
        )

    ctx.finish()
