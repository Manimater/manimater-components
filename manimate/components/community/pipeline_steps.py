"""TEMPLATE: copy this file to ``community/<your_component>.py``, rename everything, and edit.

Files whose name starts with an underscore are never loaded, so this one is only a starting point. It is a complete,
working component: a chain of labelled steps that lights up one by one.

The rules every component follows (the full list is in ``docs/WRITING_A_COMPONENT.md``):
  * One idea per component. Few, forgiving params, each with a default or clearly required.
  * The ``example`` must render: it is used as the preview and as a test.
  * Use ``theme`` colours and ``ctx.fit`` so nothing leaves the stage. Fill the time you are given (``ctx.remaining``).
  * No network, no files, no ``eval``/``exec``. Components are pure drawing code.
"""
from __future__ import annotations

from manim import DOWN, RIGHT, Arrow, Circle, FadeIn, Indicate, VGroup

from ...ctx import Ctx, label
from ... import theme
from ...registry import Param as P, component


def _clean_steps(steps: list[str]) -> list[str]:
    """Plain Python, testable without Manim: trim, drop blanks, keep at most 6 short labels."""
    return [s.strip()[:24] for s in steps if s and s.strip()][:6]


@component(
    "pipeline_steps",                                        # snake_case, unique across the whole library
    "A row of 2-6 labelled steps that light up one after another. Good for a process or a sequence of stages.",
    {
        "steps": P("string[]", "The step names, in order (2 to 6 short labels)", required=True,
                   validator=lambda v: None if len(_clean_steps(v)) >= 2 else "needs at least two non-empty steps"),
        "title": P("string", "Optional heading above the chain", default=""),
    },
    {"steps": ["Plan", "Build", "Test", "Ship"], "title": "A release in four steps"},   # must render
    domain="general",                                    # an existing domain, or a new lowercase-hyphenated one
)
def pipeline_steps(ctx: Ctx, steps: list[str], title: str = "") -> None:
    names = _clean_steps(steps)
    nodes = VGroup(*[
        VGroup(Circle(radius=0.55, color=theme.ACCENT, stroke_width=4, fill_color=theme.PANEL, fill_opacity=1),
               label(str(i + 1), 30, theme.FG, weight="BOLD"))
        for i in range(len(names))
    ]).arrange(RIGHT, buff=1.25)
    names_mobs = [label(n, 24, theme.FG, width=14).next_to(node, DOWN, buff=0.3) for n, node in zip(names, nodes)]
    arrows = [Arrow(a.get_right(), b.get_left(), buff=0.1, color=theme.MUTED, stroke_width=4)
              for a, b in zip(nodes[:-1], nodes[1:])]
    parts = [nodes, *names_mobs, *arrows]
    if title:
        parts.insert(0, label(title, 34, theme.ACCENT, width=45))
    group = VGroup(*parts)
    ctx.fit(group)

    ctx.play(FadeIn(group), run_time=1.2)                # the finished picture appears as a whole
    beat = ctx.beat(ctx.remaining, len(names))           # then each step is highlighted, sharing the remaining time
    for node in nodes:
        ctx.play(Indicate(node, color=theme.GOOD, scale_factor=1.15), run_time=beat)
