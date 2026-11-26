import pytest

from manimate.components.community.merge_sort import (
    merge_sort_steps,
)


@pytest.mark.parametrize(
    "values",
    [
        [2, 1],
        [1, 2],
        [5, 5],
        [3, 1, 2],
        [4, 2, 4, 1],
        [9, 7, 5, 3, 1],
        list(range(8)),
        list(range(7, -1, -1)),
        [38, 12, 27, 43, 9, 31, 18, 25],
        [99, 0, 99, 0, 99, 0, 99, 0],
    ],
)
def test_sorted_result(values):
    original = values.copy()
    steps = merge_sort_steps(values)

    final = steps[-1]

    assert final.kind == "merged"
    assert final.depth == 0
    assert [values[i] for i in final.items] == sorted(values)
    assert values == original


@pytest.mark.parametrize(
    "values",
    [
        [2, 1, 2, 1],
        [5, 5, 5, 5],
        [3, 1, 3, 2, 1, 3, 2, 1],
    ],
)
def test_stability(values):
    steps = merge_sort_steps(values)

    expected = sorted(
        range(len(values)), key=lambda i: values[i]
    )

    assert list(steps[-1].items) == expected

    for step in steps:
        if step.kind == "compare":
            if values[step.left] == values[step.right]:
                assert step.chosen == step.left


@pytest.mark.parametrize(
    "values, expected",
    [
        ([2, 1], 1),
        ([1, 2], 1),
        ([1, 2, 3, 4], 4),
        ([4, 3, 2, 1], 4),
        (list(range(8)), 12),
    ],
)
def test_comparison_count(values, expected):
    steps = merge_sort_steps(values)

    assert sum(
        step.kind == "compare" for step in steps
    ) == expected


def test_single_element_leaves():
    values = list(range(8))
    steps = merge_sort_steps(values)

    leaves = [
        step for step in steps
        if step.kind == "split"
        and len(step.items) == 1
    ]

    assert len(leaves) == len(values)


@pytest.mark.parametrize(
    "values",
    [
        [],
        [1],
        list(range(9)),
        [-1, 2],
        [1, 100],
        [1.5, 2],
        [float("nan"), 2],
        [float("inf"), 2],
        [True, 2],
    ],
)
def test_invalid_values(values):
    with pytest.raises(ValueError):
        merge_sort_steps(values)
