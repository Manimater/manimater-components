"""Visualize merge sort: divide and conquer recursive splitting into subarrays, followed by step-by-step merging with comparisons highlighted."""
from __future__ import annotations

import copy
from dataclasses import dataclass
import math

from manim import FadeIn, FadeOut, Indicate, Rectangle, Text, VGroup

from ... import theme
from ...ctx import Ctx
from ...registry import Param as P, component


@dataclass
class Step:
    """A discrete visual state in the merge sort process."""
    phase: str
    message: str
    tree: list[list[list[float | None]]]
    active_compared: list[tuple[int, int, int]]
    active_merged: list[tuple[int, int, int]]
    comparisons: int
    is_stable_tie: bool = False


def _values_ok(values: list[float]) -> str | None:
    if not (2 <= len(values) <= 8):
        return "needs 2 to 8 values"
    for v in values:
        try:
            val = float(v)
            if not math.isfinite(val):
                return "values must all be finite numbers"
            if val < 0 or val > 99:
                return "values must be between 0 and 99"
        except (ValueError, TypeError):
            return "values must all be numbers"
    return None


def merge_sort_steps(values: list[float]) -> list[Step]:
    """Pure Python step generator for merge sort: builds tree layers, splits, and merges."""
    if not values:
        return []
    items = [float(v) for v in values]
    steps: list[Step] = []

    # 1. Build tree layers for recursive division
    layers: list[list[list[float]]] = [[items.copy()]]
    curr = [items.copy()]
    while any(len(sub) > 1 for sub in curr):
        next_layer: list[list[float]] = []
        for sub in curr:
            if len(sub) <= 1:
                next_layer.append(sub.copy())
            else:
                mid = len(sub) // 2
                next_layer.append(sub[:mid].copy())
                next_layer.append(sub[mid:].copy())
        layers.append(next_layer)
        curr = next_layer

    depth = len(layers)
    tree_display: list[list[list[float | None]]] = [
        [[None for _ in sub] for sub in layer] for layer in layers
    ]
    tree_display[0] = [[v for v in items]]

    comparisons = 0
    steps.append(Step(
        phase="split",
        message=f"Start with array of {len(items)} elements",
        tree=copy.deepcopy(tree_display),
        active_compared=[],
        active_merged=[],
        comparisons=comparisons,
    ))

    # Divide levels step-by-step
    for d in range(1, depth):
        for s_idx, sub in enumerate(layers[d]):
            tree_display[d][s_idx] = [v for v in sub]
        steps.append(Step(
            phase="split",
            message=f"Divide level {d - 1} into subarrays at level {d}",
            tree=copy.deepcopy(tree_display),
            active_compared=[],
            active_merged=[],
            comparisons=comparisons,
        ))

    # 2. Merge back up from bottom layer to root
    merged_layers = copy.deepcopy(layers)
    for d in range(depth - 1):
        tree_display[d] = [[None for _ in sub] for sub in layers[d]]

    for d in range(depth - 2, -1, -1):
        parent_subs = layers[d]
        child_subs = merged_layers[d + 1]
        new_parents: list[list[float]] = []
        c_idx = 0

        for p_idx, p_sub in enumerate(parent_subs):
            if len(p_sub) <= 1:
                child = child_subs[c_idx]
                c_idx += 1
                new_parents.append(child.copy())
                tree_display[d][p_idx] = child.copy()
                steps.append(Step(
                    phase="merge",
                    message=f"Pass single element {child[0]:g} up to level {d}",
                    tree=copy.deepcopy(tree_display),
                    active_compared=[],
                    active_merged=[(d, p_idx, 0)],
                    comparisons=comparisons,
                ))
            else:
                left = child_subs[c_idx]
                right = child_subs[c_idx + 1]
                c_idx += 2

                merged: list[float] = []
                i, j = 0, 0
                out_idx = 0

                while i < len(left) and j < len(right):
                    comparisons += 1
                    l_val, r_val = left[i], right[j]
                    comp_coords = [(d + 1, c_idx - 2, i), (d + 1, c_idx - 1, j)]

                    if l_val <= r_val:
                        if l_val == r_val:
                            is_tie = True
                            msg = f"Tie ({l_val:g} == {r_val:g}): take left element to preserve stability"
                        else:
                            is_tie = False
                            msg = f"Compare {l_val:g} and {r_val:g}: {l_val:g} < {r_val:g} -> take {l_val:g}"
                        chosen = l_val
                        i += 1
                    else:
                        is_tie = False
                        msg = f"Compare {l_val:g} and {r_val:g}: {r_val:g} < {l_val:g} -> take {r_val:g}"
                        chosen = r_val
                        j += 1

                    merged.append(chosen)
                    tree_display[d][p_idx][out_idx] = chosen
                    steps.append(Step(
                        phase="compare",
                        message=msg,
                        tree=copy.deepcopy(tree_display),
                        active_compared=comp_coords,
                        active_merged=[(d, p_idx, out_idx)],
                        comparisons=comparisons,
                        is_stable_tie=is_tie,
                    ))
                    out_idx += 1

                while i < len(left):
                    chosen = left[i]
                    i += 1
                    merged.append(chosen)
                    tree_display[d][p_idx][out_idx] = chosen
                    steps.append(Step(
                        phase="merge",
                        message=f"Right run finished: drop remaining left element {chosen:g}",
                        tree=copy.deepcopy(tree_display),
                        active_compared=[],
                        active_merged=[(d, p_idx, out_idx)],
                        comparisons=comparisons,
                    ))
                    out_idx += 1

                while j < len(right):
                    chosen = right[j]
                    j += 1
                    merged.append(chosen)
                    tree_display[d][p_idx][out_idx] = chosen
                    steps.append(Step(
                        phase="merge",
                        message=f"Left run finished: drop remaining right element {chosen:g}",
                        tree=copy.deepcopy(tree_display),
                        active_compared=[],
                        active_merged=[(d, p_idx, out_idx)],
                        comparisons=comparisons,
                    ))
                    out_idx += 1

                new_parents.append(merged)
        merged_layers[d] = new_parents

    steps.append(Step(
        phase="done",
        message=f"Merge sort complete: {merged_layers[0][0]} in {comparisons} comparisons",
        tree=copy.deepcopy(tree_display),
        active_compared=[],
        active_merged=[(0, 0, idx) for idx in range(len(items))],
        comparisons=comparisons,
    ))
    return steps


def _draw_board(step: Step, show_counts: bool) -> VGroup:
    """Render a visual frame of the merge sort tree, active comparison, and step message."""
    parts = []

    msg_color = theme.YELLOW if step.is_stable_tie else (theme.GOOD if step.phase in ("merge", "done") else theme.FG)
    parts.append(Text(step.message, font_size=18, color=msg_color).move_to([0, 2.3, 0]))

    if show_counts:
        parts.append(Text(f"Comparisons: {step.comparisons}", font_size=14, color=theme.MUTED).move_to([0, 1.9, 0]))

    depth = len(step.tree)
    y_top = 1.3
    y_step = min(1.0, 3.8 / max(1, depth - 1))

    cell_w = 0.58
    cell_h = 0.44
    gap_between_subs = 0.35

    for d, layer in enumerate(step.tree):
        y = y_top - d * y_step

        sub_widths = [len(sub) * cell_w for sub in layer]
        total_w = sum(sub_widths) + (len(layer) - 1) * gap_between_subs
        start_x = -total_w / 2.0

        curr_x = start_x
        for s_idx, sub in enumerate(layer):
            for i, val in enumerate(sub):
                cx = curr_x + (i + 0.5) * cell_w
                coord = (d, s_idx, i)

                is_comp = coord in step.active_compared
                is_merged = coord in step.active_merged

                if is_comp:
                    stroke_c = theme.YELLOW
                    fill_c = theme.PANEL
                    stroke_w = 3.5
                elif is_merged:
                    stroke_c = theme.GOOD
                    fill_c = theme.PANEL
                    stroke_w = 3.0
                elif val is not None:
                    stroke_c = theme.ACCENT
                    fill_c = theme.PANEL
                    stroke_w = 1.8
                else:
                    stroke_c = theme.MUTED
                    fill_c = theme.BG
                    stroke_w = 1.0

                rect = Rectangle(
                    width=cell_w - 0.06,
                    height=cell_h,
                    color=stroke_c,
                    stroke_width=stroke_w,
                    fill_color=fill_c,
                    fill_opacity=1.0 if val is not None else 0.4,
                ).move_to([cx, y, 0])
                parts.append(rect)

                if val is not None:
                    txt = Text(f"{val:g}", font_size=16, color=theme.FG).move_to(rect)
                    parts.append(txt)
            curr_x += len(sub) * cell_w + gap_between_subs

    phase_label = ("DIVIDE PHASE (Splitting)" if step.phase == "split"
                   else ("MERGE PHASE (Combining)" if step.phase != "done" else "SORT COMPLETE"))
    parts.append(Text(phase_label, font_size=13, color=theme.ACCENT).move_to([0, -2.6, 0]))

    return VGroup(*parts)


@component(
    "merge_sort",
    "Visualize merge sort: divide and conquer recursive splitting into subarrays, followed by step-by-step merging with comparisons highlighted.",
    {
        "values": P("number[]", "2-8 numbers to sort (whole numbers 0-99)",
                     default=[38, 27, 43, 3, 9, 82, 10], validator=_values_ok),
        "show_counts": P("boolean", "Show running count of comparisons", default=True),
    },
    {"values": [38, 27, 43, 3, 9, 82, 10], "show_counts": True},
    domain="computer-science",
)
def merge_sort(ctx: Ctx, values: list[float] | None = None, show_counts: bool = True) -> None:
    items = list([38, 27, 43, 3, 9, 82, 10] if values is None else values[:8])
    steps = merge_sort_steps(items)
    if not steps:
        return

    heading = ctx.heading("Merge Sort")
    ctx.add(heading)

    board = _draw_board(steps[0], show_counts)
    ctx.fit(board, max_h=5.2)
    ctx.play(FadeIn(board), run_time=0.8)

    if len(steps) > 1:
        beat = max(0.12, min(0.35, (ctx.remaining - 0.4) / len(steps)))
        for step in steps[1:]:
            target = _draw_board(step, show_counts)
            ctx.fit(target, max_h=5.2)
            ctx.play(FadeOut(board), FadeIn(target), run_time=beat)
            board = target
    else:
        ctx.play(Indicate(board, color=theme.ACCENT), run_time=min(0.5, max(0.1, ctx.remaining)))
