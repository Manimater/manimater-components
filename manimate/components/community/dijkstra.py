"""Educational visualization of Dijkstra's shortest path algorithm."""
from __future__ import annotations

import math
import re
from dataclasses import dataclass

import numpy as np
from manim import (
    Circle, Line, FadeIn, Indicate,
    Transform, VGroup,
)

from ... import theme
from ...ctx import Ctx, label
from ...registry import Param as P, component


@dataclass
class Step:
    settled: str
    relaxed: list[tuple[str, str, int, bool]]
    distances: dict[str, float]
    predecessors: dict[str, str]


def parse_weighted_edges(edges):
    """Parse an undirected graph with positive integer weights."""
    graph = {}

    if not edges:
        raise ValueError("provide at least one edge")

    for edge in edges:
        match = re.fullmatch(
            r"([A-Za-z0-9]{1,3})-([A-Za-z0-9]{1,3}):([+-]?\d+)",
            edge.strip(),
        )

        if not match:
            raise ValueError(
                "use A-B:4 format with positive whole-number weights"
            )

        a, b, raw_weight = match.groups()
        weight = int(raw_weight)

        if weight <= 0:
            raise ValueError(
                "weights must be positive whole numbers; "
                "negative weights invalidate Dijkstra's guarantee "
                "and zero weights are excluded by this component"
            )

        if a == b:
            raise ValueError("self-loops are not supported")

        if b in graph.get(a, {}):
            raise ValueError("duplicate edges are not supported")

        graph.setdefault(a, {})[b] = weight
        graph.setdefault(b, {})[a] = weight

    if len(graph) > 8:
        raise ValueError("at most 8 nodes are supported")

    return graph


def _edges_ok(edges):
    try:
        parse_weighted_edges(edges)
    except ValueError as error:
        return str(error)
    return None


def dijkstra_steps(edges, start):
    """Return settlement steps with distance and predecessor snapshots."""
    graph = parse_weighted_edges(edges)

    if start not in graph:
        raise ValueError("start must be a node in the graph")

    distances = {
        node: math.inf for node in graph
    }

    distances[start] = 0
    predecessors = {}
    unsettled = set(graph)
    steps = []

    while unsettled:
        node = min(
            unsettled,
            key=lambda n: (distances[n], n),
        )

        if math.isinf(distances[node]):
            break

        unsettled.discard(node)
        relaxed = []

        for neighbor, weight in sorted(
            graph[node].items()
        ):
            if neighbor not in unsettled:
                continue

            candidate = distances[node] + weight
            improved = candidate < distances[neighbor]

            if improved:
                distances[neighbor] = candidate
                predecessors[neighbor] = node

            relaxed.append(
                (node, neighbor, weight, improved)
            )

        steps.append(
            Step(
                node,
                relaxed,
                distances.copy(),
                predecessors.copy(),
            )
        )

    return steps


def shortest_path(steps, start, target):
    """Reconstruct the shortest path, or return an empty list."""
    final = steps[-1]

    if target not in final.distances:
        raise ValueError("target must be a node in the graph")

    if math.isinf(final.distances[target]):
        return []

    path = [target]

    while path[-1] != start:
        path.append(final.predecessors[path[-1]])

    return path[::-1]


def _distance_text(value):
    return "∞" if math.isinf(value) else str(value)


@component(
    "dijkstra",
    "Dijkstra's shortest path with weighted edges, relaxation and a distance table.",
    {
        "edges": P(
            "string[]",
            "Weighted undirected edges, e.g. A-B:4",
            validator=_edges_ok,
        ),
        "start": P("string", "Starting node", default="A"),
        "target": P("string", "Target node", default="E"),
    },
    {
        "edges": [
            "A-B:4", "A-C:2", "B-C:1",
            "B-D:5", "C-D:8", "D-E:2",
            "C-E:10",
        ],
        "start": "A",
        "target": "E",
    },
    domain="computer-science",
)
def dijkstra(
    ctx: Ctx,
    edges: list[str] | None = None,
    start: str = "A",
    target: str = "E",
) -> None:
    if edges is None:
        edges = [
            "A-B:4", "A-C:2", "B-C:1",
            "B-D:5", "C-D:8", "D-E:2",
            "C-E:10",
        ]

    graph = parse_weighted_edges(edges)
    steps = dijkstra_steps(edges, start)
    path = shortest_path(steps, start, target)

    names = sorted(graph)
    positions = {}
    nodes = {}
    lines = {}
    weights = VGroup()

    head = ctx.heading("Dijkstra's shortest path")

    for i, node in enumerate(names):
        angle = math.pi / 2 - math.tau * i / len(names)

        positions[node] = np.array([
            -2.8 + 2.15 * math.cos(angle),
            0.35 + 1.55 * math.sin(angle),
            0,
        ])

        circle = Circle(
            radius=0.30,
            color=theme.ACCENT,
            stroke_width=3,
            fill_color=theme.PANEL,
            fill_opacity=1,
        )

        name = label(node, 21, theme.FG)
        nodes[node] = VGroup(
            circle, name
        ).move_to(positions[node])

    for a in names:
        for b, weight in sorted(graph[a].items()):
            if a >= b:
                continue

            p, q = positions[a], positions[b]
            direction = q - p
            unit = direction / np.linalg.norm(direction)

            line = Line(
                p + 0.30 * unit,
                q - 0.30 * unit,
                color=theme.MUTED,
                stroke_width=2,
            )

            lines[(a, b)] = line

            normal = np.array([-unit[1], unit[0], 0])

            weight_label = label(
                str(weight), 19, theme.YELLOW
            ).move_to(
                (p + q) / 2 + 0.18 * normal
            )

            weights.add(weight_label)

    table_title = label(
        "Node     Distance", 23, theme.ACCENT
    ).move_to((3.2, 2.0, 0))

    table = VGroup(table_title)
    distance_cells = {}

    for i, node in enumerate(names):
        y = 1.48 - i * 0.43

        node_label = label(
            node, 21, theme.FG
        ).move_to((2.45, y, 0))

        value = label(
            "0" if node == start else "∞",
            21, theme.FG,
        ).move_to((3.95, y, 0))

        distance_cells[node] = value
        table.add(node_label, value)

    status = label(
        f"Start: {start}  |  Target: {target}",
        23, theme.FG,
    ).move_to((0, -2.35, 0))

    group = VGroup(
        head, *lines.values(), weights,
        *nodes.values(), table, status,
    )

    ctx.fit(group)

    beats = 2 + len(steps) + sum(
        len(step.relaxed) for step in steps
    )

    beat = ctx.remaining * 0.85 / beats

    ctx.play(
        FadeIn(group),
        run_time=beat,
    )

    current = {
        node: math.inf for node in names
    }

    current[start] = 0

    for step in steps:
        node = step.settled

        message = (
            f"Settle {node}: distance "
            f"{_distance_text(current[node])}"
        )

        ctx.play(
            nodes[node][0].animate.set_stroke(theme.GOOD),
            Transform(
                status,
                label(message, 23, theme.GOOD)
                .move_to(status.get_center()),
            ),
            run_time=beat,
        )

        for a, b, weight, improved in step.relaxed:
            edge = lines[tuple(sorted((a, b)))]
            candidate = current[a] + weight

            message = (
                f"{a} → {b}: "
                f"{current[a]} + {weight} = {candidate}"
            )

            animations = [
                Indicate(edge, color=theme.YELLOW),
                Transform(
                    status,
                    label(
                        message, 23, theme.YELLOW
                    ).move_to(status.get_center()),
                ),
            ]

            if improved:
                current[b] = candidate

                animations.append(
                    Transform(
                        distance_cells[b],
                        label(
                            _distance_text(candidate),
                            21, theme.GOOD,
                        ).move_to(
                            distance_cells[b].get_center()
                        ),
                    )
                )

            ctx.play(*animations, run_time=beat)

    animations = []

    if path:
        distance = steps[-1].distances[target]

        message = (
            " → ".join(path)
            + f"  |  Distance: {distance}"
        )

        for node in path:
            animations.append(
                nodes[node][0].animate.set_stroke(
                    theme.GOOD, width=5
                )
            )

        for a, b in zip(path, path[1:]):
            animations.append(
                lines[tuple(sorted((a, b)))]
                .animate.set_stroke(theme.GOOD, width=5)
            )

        color = theme.GOOD

    else:
        message = f"{target} is unreachable: distance = ∞"
        color = theme.YELLOW

    result = label(message, 23, color)

    if result.width > 10:
        result.scale_to_fit_width(10)

    result.move_to(status.get_center())

    animations.append(Transform(status, result))

    ctx.play(*animations, run_time=beat)
    ctx.finish()
