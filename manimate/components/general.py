"""General-purpose components usable in any domain."""
from __future__ import annotations

import math

from manim import (
    DOWN, LEFT, RIGHT, UP, Arrow, Axes, Create, FadeIn, Group, LaggedStart, Line, MathTex, ORIGIN,
    Rectangle, RoundedRectangle, Text, VGroup, Write, Dot, GrowFromEdge, FadeOut, Indicate,
)

from .. import theme
from ..ctx import HAS_LATEX, Ctx, label, wrap
from ..tex import normalize_tex, tex_to_plain
from ..registry import Param as P, component
from ..safe_expr import compile_expr, validate_expr


def _nice_step(span: float, target: int) -> float:
    raw = span / target
    mag = 10 ** math.floor(math.log10(raw))
    return next(m * mag for m in (1, 2, 5, 10) if raw <= m * mag)


@component(
    "title_card", "Opening or section title with an optional subtitle. Use as the first scene.",
    {"title": P("string", "Main title", required=True), "subtitle": P("string", "Short subtitle", default="")},
    {"title": "How a Synchronous Motor Works", "subtitle": "Rotating fields and locked rotors"},
)
def title_card(ctx: Ctx, title: str, subtitle: str = "") -> None:
    t = label(title, 52, theme.FG, width=26, weight="BOLD")
    bar = Line(LEFT * 2.2, RIGHT * 2.2, color=theme.ACCENT, stroke_width=6)
    parts = [bar, t]
    if subtitle:
        parts.append(label(subtitle, 28, theme.MUTED, width=55))
    g = VGroup(*parts).arrange(DOWN, buff=0.45)
    ctx.fit(g)
    ctx.play(Create(bar), run_time=0.6)
    ctx.play(Write(t), run_time=1.2)
    if subtitle:
        ctx.play(FadeIn(g[2], shift=UP * 0.2), run_time=0.8)


@component(
    "bullet_points", "A heading with up to 6 key points revealed one by one. Good for lists of facts or steps.",
    {"heading": P("string", "Slide heading", required=True),
     "points": P("string[]", "3-6 short points (under 70 characters each)", required=True)},
    {"heading": "Main parts", "points": ["Stator carries the 3-phase winding", "Rotor carries the DC field", "Air gap links them"]},
)
def bullet_points(ctx: Ctx, heading: str, points: list[str]) -> None:
    points = points[:6]
    head = ctx.heading(heading)
    rows = VGroup(*[
        VGroup(Dot(color=theme.ACCENT, radius=0.08), label(p, 30, theme.FG, width=58, align="left")).arrange(RIGHT, buff=0.35)
        for p in points
    ]).arrange(DOWN, aligned_edge=LEFT, buff=0.45)
    rows.next_to(head, DOWN, buff=0.7).set_x(0)
    ctx.fit(rows, max_h=4.6, center=(0, 0.2, 0))
    ctx.play(Write(head), run_time=0.8)
    step = ctx.beat(ctx.remaining, len(rows))
    for r in rows:
        ctx.play(FadeIn(r, shift=RIGHT * 0.3), run_time=min(0.7, step))
        ctx.wait(max(0, step - 0.7))


@component(
    "equation", "Shows one formula (LaTeX) with an optional title and a legend explaining each symbol.",
    {"latex": P("string", "LaTeX without $ delimiters, e.g. N_s = \\frac{120 f}{P}", required=True),
     "title": P("string", "What the formula gives, e.g. 'Synchronous speed'", default=""),
     "terms": P("string[]", "Legend lines like 'f: supply frequency (Hz)'", default=[])},
    {"latex": "N_s = \\frac{120\\,f}{P}", "title": "Synchronous speed",
     "terms": ["N_s: speed in rpm", "f: supply frequency in Hz", "P: number of poles"]},
)
def equation(ctx: Ctx, latex: str, title: str = "", terms: list[str] | None = None) -> None:
    latex = normalize_tex(latex)
    eq = None
    if HAS_LATEX:
        try:
            eq = MathTex(latex, font_size=72, color=theme.FG)
        except Exception:
            eq = None
    if eq is None:
        eq = Text(tex_to_plain(latex), font_size=44, color=theme.FG)
    if eq.width > 11:
        eq.scale_to_fit_width(11)
    parts: list = []
    if title:
        parts.append(label(title, 34, theme.ACCENT, width=50, weight="BOLD"))
    parts.append(eq)
    legend = VGroup(*[label(t, 26, theme.MUTED, width=70, align="left") for t in (terms or [])[:6]]).arrange(DOWN, aligned_edge=LEFT, buff=0.18)
    if len(legend):
        parts.append(legend)
    g = VGroup(*parts).arrange(DOWN, buff=0.6)
    ctx.fit(g)
    i = 0
    if title:
        ctx.play(FadeIn(g[0], shift=DOWN * 0.2), run_time=0.6)
        i = 1
    ctx.play(Write(g[i]), run_time=min(2.0, max(1.0, ctx.remaining / 3)))
    if len(legend):
        ctx.play(LaggedStart(*[FadeIn(t, shift=UP * 0.15) for t in legend], lag_ratio=0.35),
                 run_time=max(1.0, min(3.0, ctx.remaining - 0.5)))


@component(
    "function_plot", "Plots y = f(x) on labelled axes. Expression may use x, pi, e; sin, cos, tan, asin, acos, atan; "
    "sinh, cosh, tanh; exp, log, ln, log10, log2, sqrt, abs, floor, ceil; and + - * / % ^ (or **).",
    {"expression": P("string", "e.g. 'sin(x)' or 'x^2/4'", required=True, validator=validate_expr),
     "title": P("string", "Plot title", default=""),
     "x_min": P("number", "Left limit of x", default=-6.3), "x_max": P("number", "Right limit of x", default=6.3),
     "y_min": P("number", "Bottom limit of y", default=-1.5), "y_max": P("number", "Top limit of y", default=1.5),
     "x_label": P("string", "x-axis label", default="x"), "y_label": P("string", "y-axis label", default="y")},
    {"expression": "sin(x)", "title": "A sine wave", "x_label": "angle", "y_label": "value"},
)
def function_plot(ctx: Ctx, expression: str, title: str = "", x_min: float = -6.3, x_max: float = 6.3,
                  y_min: float = -1.5, y_max: float = 1.5, x_label: str = "x", y_label: str = "y") -> None:
    if x_max <= x_min:
        x_min, x_max = -6.3, 6.3
    if y_max <= y_min:
        y_min, y_max = -1.5, 1.5
    f = compile_expr(expression)
    xs, ys = _nice_step(x_max - x_min, 8), _nice_step(y_max - y_min, 4)
    dec = lambda st: max(0, -math.floor(math.log10(st)))
    axes = Axes(x_range=[x_min, x_max, xs], y_range=[y_min, y_max, ys], x_length=10, y_length=4.4,
                axis_config={"color": theme.MUTED, "include_numbers": HAS_LATEX, "font_size": 20, "include_tip": True},
                x_axis_config={"decimal_number_config": {"num_decimal_places": dec(xs)}},
                y_axis_config={"decimal_number_config": {"num_decimal_places": dec(ys)}},
                ).move_to((0, 0.1, 0))
    curve = axes.plot(f, color=theme.ACCENT, stroke_width=5, use_smoothing=False,
                      x_range=[x_min, x_max, (x_max - x_min) / 300])
    xl = axes.get_x_axis_label(Text(x_label, font_size=24, color=theme.MUTED), edge=RIGHT, direction=DOWN, buff=0.3)
    yl = axes.get_y_axis_label(Text(y_label, font_size=24, color=theme.MUTED), edge=UP, direction=LEFT, buff=0.3)
    expr = Text(f"y = {expression}", font_size=26, color=theme.YELLOW).to_edge(DOWN, buff=1.5)
    if title:
        ctx.play(Write(ctx.heading(title)), run_time=0.7)
    ctx.play(Create(axes), FadeIn(xl), FadeIn(yl), run_time=1.0)
    ctx.play(Create(curve), run_time=max(1.5, min(4.0, ctx.remaining - 1.0)))
    ctx.play(FadeIn(expr), run_time=0.5)


@component(
    "flowchart", "A chain of 2-8 labelled boxes connected by arrows (process, signal path, cause and effect).",
    {"steps": P("string[]", "Box labels in order, under 30 characters each", required=True),
     "title": P("string", "Chart title", default="")},
    {"steps": ["AC supply", "Rotating field", "Rotor locks on", "Shaft torque"], "title": "How it runs"},
)
def flowchart(ctx: Ctx, steps: list[str], title: str = "") -> None:
    steps = steps[:8]
    n = len(steps)
    cols = min(n, 4)
    rows_n = math.ceil(n / cols)
    dx, dy = 3.5, 2.0
    boxes = []
    for i, s in enumerate(steps):
        r, c = divmod(i, cols)
        if r % 2 == 1:
            c = cols - 1 - c  # snake layout keeps arrows short
        txt = label(s, 24, theme.FG, width=13)
        box = RoundedRectangle(corner_radius=0.18, width=2.4, height=max(1.2, txt.height + 0.5), color=theme.ACCENT,
                               fill_color=theme.PANEL, fill_opacity=1, stroke_width=3)
        txt.move_to(box)
        g = VGroup(box, txt)
        g.move_to(((c - (cols - 1) / 2) * dx, -(r - (rows_n - 1) / 2) * dy, 0))
        boxes.append(g)
    arrows = [Arrow(boxes[i].get_edge_center(boxes[i + 1].get_center() - boxes[i].get_center()),
                    boxes[i + 1].get_edge_center(boxes[i].get_center() - boxes[i + 1].get_center()),
                    buff=0.08, color=theme.MUTED, stroke_width=4, max_tip_length_to_length_ratio=0.25)
              for i in range(n - 1)]
    chart = VGroup(*boxes, *arrows)
    ctx.fit(chart, max_h=4.4, center=(0, 0.1, 0))
    if title:
        ctx.play(Write(ctx.heading(title)), run_time=0.7)
    step = ctx.beat(ctx.remaining, n)
    for i, b in enumerate(boxes):
        anims = [FadeIn(b, scale=0.9)]
        if i > 0:
            anims.append(Create(arrows[i - 1]))
        ctx.play(*anims, run_time=min(0.7, step))
        ctx.wait(max(0, step - 0.7))


@component(
    "compare_two", "Two columns comparing two things side by side, each with a title and 2-5 points.",
    {"left_title": P("string", "Left column title", required=True), "left_points": P("string[]", "Left points", required=True),
     "right_title": P("string", "Right column title", required=True), "right_points": P("string[]", "Right points", required=True)},
    {"left_title": "Synchronous", "left_points": ["Constant speed", "Needs DC excitation"],
     "right_title": "Induction", "right_points": ["Speed drops with load", "No rotor supply"]},
)
def compare_two(ctx: Ctx, left_title: str, left_points: list[str], right_title: str, right_points: list[str]) -> None:
    def column(title: str, pts: list[str], color: str) -> VGroup:
        head = label(title, 34, color, width=22, weight="BOLD")
        items = VGroup(*[label("• " + p, 26, theme.FG, width=30, align="left") for p in pts[:5]]).arrange(DOWN, aligned_edge=LEFT, buff=0.3)
        return VGroup(head, items).arrange(DOWN, aligned_edge=LEFT, buff=0.5)

    left = column(left_title, left_points, theme.ACCENT).move_to((-3.1, 0.5, 0))
    right = column(right_title, right_points, theme.WARN).move_to((3.1, 0.5, 0))
    for col, cx in ((left, -3.1), (right, 3.1)):
        if col.width > 5.6:
            col.scale_to_fit_width(5.6)
        col.move_to((cx, 0.5, 0))
    divider = Line((0, -2.2, 0), (0, 3.2, 0), color=theme.MUTED, stroke_width=2)
    ctx.play(Create(divider), run_time=0.5)
    for col in (left, right):
        ctx.play(FadeIn(col[0], shift=DOWN * 0.2), run_time=0.6)
        ctx.play(LaggedStart(*[FadeIn(i, shift=RIGHT * 0.2) for i in col[1]], lag_ratio=0.4),
                 run_time=max(0.8, min(2.5, ctx.remaining / 3)))


@component(
    "callout", "A highlighted box for one key takeaway, definition, or warning. Good as the final scene.",
    {"text": P("string", "The message, one or two sentences", required=True),
     "kind": P("string", "Style of the box", default="takeaway", choices=["takeaway", "definition", "warning"])},
    {"text": "A synchronous motor runs at exactly the speed of the rotating field.", "kind": "takeaway"},
)
def callout(ctx: Ctx, text: str, kind: str = "takeaway") -> None:
    color, tag = {"takeaway": (theme.GOOD, "KEY TAKEAWAY"), "definition": (theme.ACCENT, "DEFINITION"),
                  "warning": (theme.WARN, "WARNING")}[kind]
    body = label(text, 34, theme.FG, width=44, align="left")
    tag_t = label(tag, 22, color, weight="BOLD")
    inner = VGroup(tag_t, body).arrange(DOWN, aligned_edge=LEFT, buff=0.35)
    box = RoundedRectangle(corner_radius=0.2, width=inner.width + 1.0, height=inner.height + 0.9, color=color,
                           fill_color=theme.PANEL, fill_opacity=1, stroke_width=4)
    inner.move_to(box)
    g = VGroup(box, inner)
    ctx.fit(g)
    ctx.play(FadeIn(box, scale=0.95), run_time=0.7)
    ctx.play(Write(inner), run_time=min(2.0, max(1.0, ctx.remaining / 2)))
    ctx.play(Indicate(box, color=color, scale_factor=1.03), run_time=0.8)


@component(
    "bar_chart", "A simple bar chart comparing 2-8 values.",
    {"title": P("string", "Chart title", default=""),
     "labels": P("string[]", "Category names", required=True),
     "values": P("number[]", "One number per label", required=True),
     "unit": P("string", "Unit shown after each value, e.g. 'rpm'", default="")},
    {"title": "Synchronous speed at 50 Hz", "labels": ["2 poles", "4 poles", "6 poles"], "values": [3000, 1500, 1000], "unit": "rpm"},
)
def bar_chart(ctx: Ctx, labels: list[str], values: list[float], title: str = "", unit: str = "") -> None:
    n = min(len(labels), len(values), 8)
    labels, values = labels[:n], [max(0.0, float(v)) for v in values[:n]]
    top = max(values) or 1.0
    base_y, max_h, width = -1.6, 3.8, min(1.3, 10 / max(n, 1) * 0.7)
    gap = min(2.0, 11 / max(n, 1))
    bars, names, vals = [], [], []
    for i, (name, v) in enumerate(zip(labels, values)):
        x = (i - (n - 1) / 2) * gap
        h = max(0.05, v / top * max_h)
        bar = Rectangle(width=width, height=h, fill_color=theme.ACCENT if i % 2 == 0 else theme.PURPLE,
                        fill_opacity=0.95, stroke_width=0).move_to((x, base_y + h / 2, 0))
        names.append(label(name, 22, theme.FG, width=12).next_to(bar, DOWN, buff=0.2))
        vals.append(Text(f"{v:g}{(' ' + unit) if unit else ''}", font_size=22, color=theme.YELLOW).next_to(bar, UP, buff=0.12))
        bars.append(bar)
    axis = Line((-6, base_y, 0), (6, base_y, 0), color=theme.MUTED, stroke_width=2)
    if title:
        ctx.play(Write(ctx.heading(title)), run_time=0.7)
    ctx.play(Create(axis), *[FadeIn(nm) for nm in names], run_time=0.6)
    ctx.play(*[GrowFromEdge(b, DOWN) for b in bars], run_time=1.2)
    ctx.play(*[FadeIn(v, shift=UP * 0.1) for v in vals], run_time=0.6)
