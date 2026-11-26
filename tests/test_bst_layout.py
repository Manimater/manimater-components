import math
import random
from itertools import combinations

import pytest

from manimate.components.datastructures import (
    build_bst,
    bst_layout,
    bst_is_chain,
)


@pytest.mark.parametrize("size", range(2, 9))
@pytest.mark.parametrize("order", ["sorted", "reverse", "random"])
def test_bst_layout_bounds_and_spacing(size, order):
    values = list(range(1, size + 1))

    if order == "reverse":
        values.reverse()
    elif order == "random":
        random.Random(42).shuffle(values)

    positions = bst_layout(build_bst(values))

    assert set(positions) == {str(v) for v in values}

    xs = [x for x, y in positions.values()]
    ys = [y for x, y in positions.values()]

    diameter = 0.66

    assert max(xs) - min(xs) + diameter <= 10.0
    assert max(ys) - min(ys) + diameter <= 3.9

    for a, b in combinations(positions.values(), 2):
        assert math.dist(a, b) >= diameter

    ordered_x = [positions[str(v)][0] for v in sorted(values)]
    assert ordered_x == sorted(ordered_x)


def test_empty_layout():
    assert bst_layout(None) == {}


def test_single_node_layout():
    assert bst_layout(build_bst([5])) == {"5": (0.0, 0.0)}


def test_sorted_tree_is_chain():
    assert bst_is_chain(build_bst(list(range(1, 9))))


def test_reverse_tree_is_chain():
    assert bst_is_chain(build_bst(list(range(8, 0, -1))))


def test_balanced_tree_is_not_chain():
    assert not bst_is_chain(build_bst([4, 2, 6, 1, 3, 5, 7]))


def test_parent_child_positions():
    positions = bst_layout(build_bst([4, 2, 6]))

    assert positions["2"][0] < positions["4"][0]
    assert positions["6"][0] > positions["4"][0]
    assert positions["2"][1] < positions["4"][1]
    assert positions["6"][1] < positions["4"][1]
