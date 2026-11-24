"""Computer-science pack, built on the community plugin manim-dsa (https://github.com/F4bbi/manim-dsa).

(manim-dsa is the "Manim Data Structures & Algorithms" plugin; it is what `pip install manim-dsa` installs.)
The algorithms themselves (sort order, traversal order, BST insertion) are computed here in plain Python, so the
video always shows the real steps; the plugin only draws and animates them.
"""
from __future__ import annotations

import copy
import math
import re
from collections import deque

import numpy as np
from manim import DOWN, LEFT, Create, FadeIn, Transform, VGroup, Write

from .. import theme
from ..ctx import Ctx, label
from ..registry import Param as P, component
from ._plugin import fit, require

_PIP = "manim-dsa"
_CY = 0.55


def _clamp(x: float, lo: float, hi: float) -> float:
    return max(lo, min(hi, x))


# --------------------------------------------------------------------------------------------------------------
# Sorting
# --------------------------------------------------------------------------------------------------------------
def sort_steps(values: list[int], algorithm: str) -> list[tuple[str, int, int]]:
    """Return the compare/swap steps ("cmp", i, j) and ("swap", i, j) that sort ``values`` with ``algorithm``."""
    a, n, ops = list(values), len(values), []
    if algorithm == "bubble":
        for i in range(n - 1):
            for j in range(n - 1 - i):
                ops.append(("cmp", j, j + 1))
                if a[j] > a[j + 1]:
                    a[j], a[j + 1] = a[j + 1], a[j]
                    ops.append(("swap", j, j + 1))
    elif algorithm == "selection":
        for i in range(n - 1):
            m = i
            for j in range(i + 1, n):
                ops.append(("cmp", m, j))
                if a[j] < a[m]:
                    m = j
            if m != i:
                a[i], a[m] = a[m], a[i]
                ops.append(("swap", i, m))
    else:  # insertion: each new element is swapped left until it is in place
        for i in range(1, n):
            j = i
            while j > 0:
                ops.append(("cmp", j - 1, j))
                if a[j - 1] <= a[j]:
                    break
                a[j - 1], a[j] = a[j], a[j - 1]
                ops.append(("swap", j - 1, j))
                j -= 1
    return ops


def _values_ok(v: list) -> str | None:
    if not 2 <= len(v) <= 8:
        return "needs 2 to 8 values"
    if any(not float(x).is_integer() or not 0 <= x <= 99 for x in v):
        return "values must be whole numbers from 0 to 99"
    return None


@component(
    "array_sort",
    "Bubble, selection or insertion sort of a short array, step by step.",
    {"values": P("number[]", "2-8 whole numbers 0-99, e.g. [5, 2, 8, 1, 9]", validator=_values_ok),
     "algorithm": P("string", "algorithm", default="bubble", choices=["bubble", "selection", "insertion"])},
    {"values": [5, 2, 8, 1, 9], "algorithm": "bubble"},
    domain="computer-science",
    plugin="manim-dsa",
)
def array_sort(ctx: Ctx, values: list[float] | None = None, algorithm: str = "bubble") -> None:
    dsa = require("manim_dsa", _PIP)
    vals = [int(v) for v in (values or [5, 2, 8, 1, 9])]
    ops = sort_steps(vals, algorithm)
    arr = dsa.MArray(vals)
    arr.add_indexes()
    fit(arr, max_w=11.5, max_h=3.0, center=(0, _CY, 0))
    head = ctx.heading(f"{algorithm.capitalize()} sort")
    key = label("yellow = being compared, green = sorted", 22, theme.MUTED).next_to(head, DOWN, buff=0.15)
    ctx.play(Write(head), FadeIn(key), run_time=0.7)
    ctx.play(Create(arr), run_time=0.9)
    t = _clamp((ctx.remaining - 1.8) / max(1, len(ops)), 0.12, 0.9)
    active: list = []
    for kind, i, j in ops:
        if kind == "cmp":
            now = [arr[i], arr[j]]
            ctx.play(*[e.animate.unhighlight() for e in active], *[e.animate.highlight(theme.YELLOW) for e in now],
                     run_time=t)
            active = now
        else:
            ctx.play(arr.animate.swap(i, j), run_time=t)
    if active:
        ctx.play(*[e.animate.unhighlight() for e in active], run_time=0.2)
    ctx.play(*[arr[k].animate.highlight(theme.GOOD) for k in range(len(vals))], run_time=0.6)
    ctx.wait(ctx.remaining)


# --------------------------------------------------------------------------------------------------------------
# Stack
# --------------------------------------------------------------------------------------------------------------
_OP = re.compile(r"^\s*(push\s+(-?\d{1,3})|pop)\s*$", re.IGNORECASE)


def parse_stack_ops(ops: list[str]) -> list[tuple[str, int | None]]:
    out: list[tuple[str, int | None]] = []
    for text in ops:
        m = _OP.match(text)
        if not m:
            raise ValueError(f"bad operation {text!r}")
        out.append(("push", int(m.group(2))) if m.group(2) is not None else ("pop", None))
    return out


def _stack_ops_ok(v: list) -> str | None:
    if not 1 <= len(v) <= 8:
        return "needs 1 to 8 operations"
    try:
        parsed = parse_stack_ops(v)
    except ValueError as e:
        return f"{e}; use 'push 5' or 'pop'"
    depth = 0
    for kind, _ in parsed:
        depth += 1 if kind == "push" else -1
        if depth < 0:
            return "cannot pop from an empty stack"
    return None


@component(
    "stack_operations",
    "A stack (LIFO) as values are pushed on and popped off.",
    {"operations": P("string[]", "1-8 of 'push N' or 'pop'", validator=_stack_ops_ok)},
    {"operations": ["push 3", "push 7", "push 1", "pop", "pop"]},
    domain="computer-science",
    plugin="manim-dsa",
)
def stack_operations(ctx: Ctx, operations: list[str] | None = None) -> None:
    dsa = require("manim_dsa", _PIP)
    ops = parse_stack_ops(operations or ["push 3", "push 7", "push 1", "pop"])
    stack = dsa.MStack([])
    fit(stack, max_w=3.0, max_h=3.6, center=(-3.2, _CY - 0.5, 0))
    log = VGroup(*[
        label(f"{k + 1}.  " + (f"push {v}" if kind == "push" else "pop"), 28, theme.MUTED, align="left")
        for k, (kind, v) in enumerate(ops)
    ]).arrange(DOWN, aligned_edge=LEFT, buff=0.3).move_to((3.2, _CY, 0))
    head = ctx.heading("Stack: last in, first out")
    ctx.play(Write(head), Create(stack), FadeIn(log), run_time=1.0)
    t = _clamp((ctx.remaining - 1.0) / len(ops), 0.5, 1.4)
    for k, (kind, v) in enumerate(ops):
        step = log[k].animate.set_color(theme.YELLOW)
        ctx.play(step, stack.animate.append(v) if kind == "push" else stack.animate.pop(), run_time=t)
    ctx.wait(ctx.remaining)


# --------------------------------------------------------------------------------------------------------------
# Graph traversal
# --------------------------------------------------------------------------------------------------------------
_EDGE = re.compile(r"^([A-Za-z0-9]{1,3})-([A-Za-z0-9]{1,3})$")


def parse_edges(edges: list[str]) -> dict[str, list[str]]:
    """'A-B' strings to an undirected adjacency dict with sorted neighbour lists."""
    adj: dict[str, set[str]] = {}
    for e in edges:
        m = _EDGE.match(e.strip())
        if not m:
            raise ValueError(f"bad edge {e!r}")
        a, b = m.group(1), m.group(2)
        if a == b:
            raise ValueError(f"edge {e!r} joins a node to itself")
        adj.setdefault(a, set()).add(b)
        adj.setdefault(b, set()).add(a)
    return {k: sorted(v) for k, v in adj.items()}


def resolve_start(adj: dict[str, list[str]], start: str) -> str:
    """The node's own spelling, matching case-insensitively, or a clear error."""
    if start in adj:
        return start
    folded = {node.lower(): node for node in adj}
    if start.lower() in folded:
        return folded[start.lower()]
    options = ", ".join(sorted(adj))
    raise ValueError(f"start node {start!r} is not in edges; use one of: {options}")


def unreached_nodes(adj: dict[str, list[str]], order: list[tuple[str, str | None]]) -> list[str]:
    """Nodes the traversal never visited, sorted."""
    seen = {node for node, _ in order}
    return sorted(node for node in adj if node not in seen)


def traversal_order(adj: dict[str, list[str]], start: str, algorithm: str) -> list[tuple[str, str | None]]:
    """Visit order as (node, node it was reached from), for BFS or DFS, neighbours in sorted order."""
    seen, order = {start}, [(start, None)]
    if algorithm == "bfs":
        queue = deque([start])
        while queue:
            u = queue.popleft()
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    order.append((v, u))
                    queue.append(v)
    else:
        def visit(u: str) -> None:
            for v in adj[u]:
                if v not in seen:
                    seen.add(v)
                    order.append((v, u))
                    visit(v)
        visit(start)
    return order


def _edges_ok(v: list) -> str | None:
    try:
        adj = parse_edges(v)
    except ValueError as e:
        return f"{e}; use names like 'A-B'"
    if not 1 <= len(v) <= 8:
        return "needs 1 to 8 edges"
    if len(adj) > 9:
        return "at most 9 nodes"
    return None


@component(
    "graph_traversal",
    "BFS or DFS on a small undirected graph, showing the visit order.",
    {"edges": P("string[]", "1-8 edges like 'A-B'", validator=_edges_ok),
     "start": P("string", "start node", default="A"),
     "algorithm": P("string", "search strategy", default="bfs", choices=["bfs", "dfs"])},
    {"edges": ["A-B", "A-C", "B-D", "C-D", "D-E"], "start": "A", "algorithm": "bfs"},
    domain="computer-science",
    plugin="manim-dsa",
)
def graph_traversal(ctx: Ctx, edges: list[str] | None = None, start: str = "A", algorithm: str = "bfs") -> None:
    dsa = require("manim_dsa", _PIP)
    adj = parse_edges(edges or ["A-B", "A-C", "B-D", "C-D", "D-E"])
    start = resolve_start(adj, start)
    order = traversal_order(adj, start, algorithm)
    undirected_once = {u: [v for v in nbrs if u < v] for u, nbrs in adj.items()}
    # The plugin's default layout needs scipy and collapses small graphs, so nodes go on a circle instead. Its edges
    # are arrows; a style with an invisible tip makes them look undirected.
    names = sorted(adj)
    pos = {n: np.array([2.2 * math.cos(math.pi / 2 - math.tau * k / len(names)),
                        2.2 * math.sin(math.pi / 2 - math.tau * k / len(names)), 0.0]) for k, n in enumerate(names)}
    style = copy.deepcopy(dsa.MGraphStyle.DEFAULT)
    style.edge_tip = {**style.edge_tip, "length": 0.001, "width": 0.001, "stroke_width": 0, "fill_opacity": 0}
    graph = dsa.MGraph(undirected_once, nodes_position=pos, style=style)
    fit(graph, max_w=8.0, max_h=3.9, center=(0, _CY - 0.2, 0), max_scale=1.3)
    head = ctx.heading("Breadth-first search" if algorithm == "bfs" else "Depth-first search")
    seen_text = label("Visited: ", 28, theme.FG).move_to((0, -2.45, 0))
    ctx.play(Write(head), Create(graph), run_time=1.2)
    ctx.add(seen_text)
    t = _clamp((ctx.remaining - 1.0) / len(order), 0.5, 1.4)
    names: list[str] = []
    for node, parent in order:
        names.append(node)
        anims = [graph[node].animate.highlight(theme.GOOD if parent else theme.WARN)]
        if parent is not None:
            key = (parent, node) if (parent, node) in graph.edges else (node, parent)
            if key in graph.edges:
                anims.append(graph.edges[key].animate.highlight(theme.GOOD))
        new_text = label("Visited: " + "  ".join(names), 28, theme.FG).move_to((0, -2.45, 0))
        ctx.play(*anims, Transform(seen_text, new_text), run_time=t)
    left = unreached_nodes(adj, order)
    if left:
        ctx.play(FadeIn(label("Not reached: " + ", ".join(left), 24, theme.MUTED).move_to((0, -2.85, 0))), run_time=0.6)
    ctx.wait(ctx.remaining)


# --------------------------------------------------------------------------------------------------------------
# Binary search tree
# --------------------------------------------------------------------------------------------------------------
class _Node:
    def __init__(self, key: int):
        self.key, self.left, self.right = key, None, None


def build_bst(values: list[int]) -> _Node:
    root = _Node(values[0])
    for v in values[1:]:
        cur = root
        while True:
            side = "left" if v < cur.key else "right"
            nxt = getattr(cur, side)
            if nxt is None:
                setattr(cur, side, _Node(v))
                break
            cur = nxt
    return root


def walk(node: _Node | None, kind: str) -> list[int]:
    if node is None:
        return []
    left, right = walk(node.left, kind), walk(node.right, kind)
    return {"inorder": left + [node.key] + right, "preorder": [node.key] + left + right,
            "postorder": left + right + [node.key]}[kind]


def _bst_values_ok(v: list) -> str | None:
    if not 2 <= len(v) <= 8:
        return "needs 2 to 8 values"
    if any(not float(x).is_integer() or not 0 <= x <= 99 for x in v):
        return "values must be whole numbers from 0 to 99"
    if len(set(v)) != len(v):
        return "values must all be different"
    return None


@component(
    "binary_search_tree",
    "Binary search tree from inserted values, optionally traversed.",
    {"values": P("number[]", "2-8 different numbers 0-99, in insertion order", validator=_bst_values_ok),
     "traversal": P("string", "walk to animate", default="inorder",
                    choices=["none", "inorder", "preorder", "postorder"])},
    {"values": [8, 3, 10, 1, 6, 14], "traversal": "inorder"},
    domain="computer-science",
    plugin="manim-dsa",
)
def binary_search_tree(ctx: Ctx, values: list[float] | None = None, traversal: str = "inorder") -> None:
    dsa = require("manim_dsa", _PIP)
    root = build_bst([int(v) for v in (values or [8, 3, 10, 1, 6, 14])])
    # Own layout: x from the in-order position, y from the depth. The plugin's MTree layout puts an only child
    # straight under its parent, which would hide whether it is a left or a right child.
    positions: dict[str, np.ndarray] = {}
    children: dict[str, list[str]] = {}

    def place(node: _Node | None, depth: int, counter: list[int]) -> None:
        if node is None:
            return
        place(node.left, depth + 1, counter)
        positions[str(node.key)] = np.array([counter[0] * 1.3, -depth * 1.4, 0.0])
        counter[0] += 1
        place(node.right, depth + 1, counter)

    def link(node: _Node | None) -> None:
        if node is None:
            return
        children[str(node.key)] = [str(c.key) for c in (node.left, node.right) if c is not None]
        link(node.left)
        link(node.right)

    place(root, 0, [0])
    link(root)
    tree = dsa.MGraph(children, nodes_position=positions)
    fit(tree, max_w=10.0, max_h=3.9, center=(0, _CY - 0.1, 0), max_scale=1.2)
    head = ctx.heading("Binary search tree")
    ctx.play(Write(head), Create(tree), run_time=min(2.5, max(1.2, ctx.remaining * 0.3)))
    if traversal != "none":
        seq = walk(root, traversal)
        title = {"inorder": "In-order", "preorder": "Pre-order", "postorder": "Post-order"}[traversal]
        out = label(f"{title}: ", 28, theme.FG).move_to((0, -2.45, 0))
        ctx.add(out)
        t = _clamp((ctx.remaining - 1.0) / len(seq), 0.4, 1.2)
        shown: list[int] = []
        for key in seq:
            shown.append(key)
            new_out = label(f"{title}: " + "  ".join(str(k) for k in shown), 28, theme.FG).move_to((0, -2.45, 0))
            ctx.play(tree[str(key)].animate.highlight(theme.GOOD), Transform(out, new_out), run_time=t)
    ctx.wait(ctx.remaining)
