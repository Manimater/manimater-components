"""Educational visualization of stable merge sort."""
from __future__ import annotations

from dataclasses import dataclass

from manim import (
    FadeIn, FadeOut, Indicate, Rectangle,
    Transform, TransformFromCopy, VGroup,
)

from ... import theme
from ...ctx import Ctx, label
from ...registry import Param as P, component


@dataclass(frozen=True)
class Step:
    kind: str
    depth: int
    start: int
    items: tuple[int, ...]
    left: int = -1
    right: int = -1
    chosen: int = -1


def _values_ok(values: list) -> str | None:
    if not 2 <= len(values) <= 8:
        return "needs 2 to 8 values"
    if any(
        not isinstance(v, (int, float))
        or isinstance(v, bool)
        or not float(v).is_integer()
        or not 0 <= v <= 99
        for v in values
    ):
        return "values must be whole numbers from 0 to 99"
    return None


def merge_sort_steps(values: list[int]) -> list[Step]:
    """Generate split, comparison and merge events.

    Items are original indices so duplicate values retain
    their identities and stability can be tested.
    """
    error = _values_ok(values)
    if error:
        raise ValueError(error)

    splits = []
    merges = []

    def visit(items, depth, start):
        splits.append(
            Step("split", depth, start, tuple(items))
        )

        if len(items) == 1:
            return items

        mid = len(items) // 2

        left = visit(items[:mid], depth + 1, start)
        right = visit(
            items[mid:], depth + 1, start + mid
        )

        result = []
        i = j = 0

        while i < len(left) and j < len(right):
            a, b = left[i], right[j]

            if values[a] <= values[b]:
                chosen = a
                i += 1
            else:
                chosen = b
                j += 1

            merges.append(
                Step(
                    "compare", depth, start,
                    tuple(result), a, b, chosen,
                )
            )

            result.append(chosen)

        for chosen in left[i:] + right[j:]:
            merges.append(
                Step(
                    "append", depth, start,
                    tuple(result), chosen=chosen,
                )
            )
            result.append(chosen)

        merges.append(
            Step("merged", depth, start, tuple(result))
        )

        return result

    visit(list(range(len(values))), 0, 0)

    return sorted(splits, key=lambda s: s.depth) + merges


def _cell(value, position, color):
    box = Rectangle(
        width=0.72,
        height=0.48,
        stroke_color=color,
        stroke_width=2,
        fill_color=theme.PANEL,
        fill_opacity=1,
    )

    number = label(str(value), 23, theme.FG)
    number.move_to(box.get_center())

    return VGroup(box, number).move_to(position)


def _position(n, depth, index, max_depth):
    spacing = 1.02
    row_gap = 3.0 / max(1, max_depth)

    return (
        (index - (n - 1) / 2) * spacing,
        1.65 - depth * row_gap,
        0,
    )


@component(
    "merge_sort",
    "Stable merge sort with recursive splits, comparisons and sorted merges.",
    {
        "values": P(
            "number[]",
            "2-8 whole numbers from 0 to 99",
            validator=_values_ok,
        ),
        "show_counts": P(
            "boolean",
            "Show the running comparison counter",
            default=True,
        ),
    },
    {
        "values": [38, 12, 27, 43, 9, 31, 18, 25],
        "show_counts": True,
    },
    domain="computer-science",
)
def merge_sort(
    ctx: Ctx,
    values: list[float] | None = None,
    show_counts: bool = True,
) -> None:
    if values is None:
        values = [38, 12, 27, 43, 9, 31, 18, 25]

    steps = merge_sort_steps(values)
    vals = [int(v) for v in values]
    n = len(vals)

    max_depth = max(s.depth for s in steps)

    head = ctx.heading("Merge sort: divide and conquer")

    status = label(
        "Split into smaller arrays",
        20, theme.MUTED,
    ).move_to((0, -1.95, 0))

    footer = label(
        "Stable: left wins ties  |  O(n log n)",
        19, theme.GOOD,
    ).move_to((0, -2.65, 0))

    counter = label(
        "Comparisons: 0", 20, theme.YELLOW,
    ).move_to((0, 2.35, 0))

    rows = {}
    count = 0

    animation_count = (
        2 + sum(
            2 if s.kind == "compare" else 1
            for s in steps
        )
    )

    beat = ctx.remaining * 0.85 / animation_count

    intro = [FadeIn(head), FadeIn(status)]

    if show_counts:
        intro.append(FadeIn(counter))

    ctx.play(*intro, run_time=beat)

    for step in steps:
        if step.kind == "split":
            cells = VGroup()

            for offset, item in enumerate(step.items):
                pos = _position(
                    n, step.depth,
                    step.start + offset, max_depth,
                )
                cell = _cell(
                    vals[item], pos, theme.ACCENT
                )
                rows[(step.depth, item)] = cell
                cells.add(cell)

            ctx.play(FadeIn(cells), run_time=beat)
            continue

        if step.kind == "compare":
            count += 1

            left = rows[(step.depth + 1, step.left)]
            right = rows[(step.depth + 1, step.right)]

            a, b = vals[step.left], vals[step.right]

            message = (
                f"{a} = {b}: take left (stable)"
                if a == b
                else f"Compare {a} and {b}: take {min(a, b)}"
            )

            animations = [
                Indicate(left, color=theme.YELLOW),
                Indicate(right, color=theme.YELLOW),
                Transform(
                    status,
                    label(message, 20, theme.YELLOW)
                    .move_to(status.get_center()),
                ),
            ]

            if show_counts:
                animations.append(
                    Transform(
                        counter,
                        label(
                            f"Comparisons: {count}",
                            20, theme.YELLOW,
                        ).move_to(counter.get_center()),
                    )
                )

            ctx.play(*animations, run_time=beat)

        if step.kind in ("compare", "append"):
            item = step.chosen

            source = rows[(step.depth + 1, item)]

            destination = _position(
                n, step.depth,
                step.start + len(step.items),
                max_depth,
            )

            target = _cell(
                vals[item], destination, theme.GOOD
            )

            old_cells = []

            for key, cell in rows.items():
                if (
                    key[0] == step.depth
                    and abs(
                        cell.get_center()[0] - destination[0]
                    ) < 0.1
                ):
                    old_cells.append((key, cell))

            animations = [
                TransformFromCopy(source, target)
            ]

            for key, cell in old_cells:
                animations.append(FadeOut(cell))
                rows.pop(key)

            rows[(step.depth, item)] = target

            ctx.play(*animations, run_time=beat)

        elif step.kind == "merged":
            ctx.play(
                Transform(
                    status,
                    label(
                        "Merged sorted run",
                        20, theme.GOOD,
                    ).move_to(status.get_center()),
                ),
                run_time=beat,
            )

    ctx.play(
        FadeIn(footer),
        Transform(
            status,
            label(
                "Sorting complete", 20, theme.GOOD
            ).move_to(status.get_center()),
        ),
        run_time=beat,
    )

    ctx.finish()
