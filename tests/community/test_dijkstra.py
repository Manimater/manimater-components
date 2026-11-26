import math

import pytest

from manimate.components.community.dijkstra import (
    parse_weighted_edges,
    dijkstra_steps,
    shortest_path,
)


def test_undirected_edges():
    graph = parse_weighted_edges(["A-B:4"])
    assert graph["A"]["B"] == 4
    assert graph["B"]["A"] == 4


def test_shortest_path():
    edges = ["A-B:4", "A-C:2", "C-B:1"]
    steps = dijkstra_steps(edges, "A")

    assert steps[-1].distances["B"] == 3
    assert shortest_path(
        steps, "A", "B"
    ) == ["A", "C", "B"]


def test_settlement_order():
    steps = dijkstra_steps(
        ["A-B:4", "A-C:2", "C-B:1"], "A"
    )

    assert [s.settled for s in steps] == [
        "A", "C", "B"
    ]


def test_unreachable_target():
    steps = dijkstra_steps(
        ["A-B:2", "C-D:3"], "A"
    )

    assert math.isinf(steps[-1].distances["D"])
    assert shortest_path(steps, "A", "D") == []


def test_ties():
    steps = dijkstra_steps(
        ["A-B:2", "A-C:2", "B-D:1", "C-D:1"],
        "A",
    )

    assert steps[-1].distances["D"] == 3
    assert shortest_path(
        steps, "A", "D"
    ) == ["A", "B", "D"]


def test_start_equals_target():
    steps = dijkstra_steps(["A-B:4"], "A")
    assert shortest_path(steps, "A", "A") == ["A"]


def test_distance_snapshots():
    steps = dijkstra_steps(
        ["A-B:4", "A-C:2", "C-B:1"], "A"
    )

    assert steps[0].distances["B"] == 4
    assert steps[-1].distances["B"] == 3


def test_relaxation():
    steps = dijkstra_steps(
        ["A-B:4", "A-C:2", "C-B:1"], "A"
    )

    assert ("C", "B", 1, True) in steps[1].relaxed


def test_no_improvement():
    steps = dijkstra_steps(
        ["A-B:2", "A-C:3", "B-C:5"], "A"
    )

    assert ("B", "C", 5, False) in steps[1].relaxed


def test_eight_nodes():
    edges = [
        f"{chr(65+i)}-{chr(66+i)}:1"
        for i in range(7)
    ]

    steps = dijkstra_steps(edges, "A")

    assert steps[-1].distances["H"] == 7
    assert len(shortest_path(steps, "A", "H")) == 8


@pytest.mark.parametrize(
    "edges",
    [
        [],
        ["A-B:0"],
        ["A-B:-2"],
        ["A-B:1.5"],
        ["A-B"],
        ["A-A:2"],
        ["A-B:abc"],
        ["A-B:2", "B-A:3"],
        [
            f"{chr(65+i)}-{chr(66+i)}:1"
            for i in range(8)
        ],
    ],
)
def test_invalid_edges(edges):
    with pytest.raises(ValueError):
        parse_weighted_edges(edges)


def test_unknown_start():
    with pytest.raises(ValueError, match="start"):
        dijkstra_steps(["A-B:2"], "Z")


def test_unknown_target():
    steps = dijkstra_steps(["A-B:2"], "A")

    with pytest.raises(ValueError, match="target"):
        shortest_path(steps, "A", "Z")
