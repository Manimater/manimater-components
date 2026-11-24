import math
import pytest

from manimate.components.community.merge_sort import merge_sort_steps, _values_ok
from manimate import registry


@pytest.mark.parametrize("values", [
    [38, 27, 43, 3, 9, 82, 10],
    [5, 1],
    [10, 20],
    [1, 2, 3, 4, 5],
    [9, 8, 7, 6, 5],
    [64, 25, 12, 22, 11, 90, 88, 45],
    [42, 42, 42, 42],
    [0, 99, 50, 0, 99],
])
def test_merge_sort_steps_sorts_correctly(values):
    steps = merge_sort_steps(values)
    assert len(steps) >= 2
    assert steps[0].phase == "split"
    assert steps[-1].phase == "done"
    final_sorted = steps[-1].tree[0][0]
    assert final_sorted == [float(x) for x in sorted(values)]


def test_merge_sort_stability_on_duplicates():
    values = [15, 15]
    steps = merge_sort_steps(values)
    tie_steps = [s for s in steps if s.is_stable_tie]
    assert len(tie_steps) >= 1
    assert any("preserve stability" in s.message for s in tie_steps)


def test_merge_sort_empty_input():
    assert merge_sort_steps([]) == []


def test_merge_sort_input_not_mutated():
    original = [4, 2, 9, 1]
    copy_orig = original.copy()
    merge_sort_steps(original)
    assert original == copy_orig


def test_merge_sort_comparisons_monotonic():
    steps = merge_sort_steps([5, 4, 3, 2, 1])
    counts = [s.comparisons for s in steps]
    for a, b in zip(counts[:-1], counts[1:]):
        assert a <= b
    assert steps[-1].comparisons > 0


@pytest.mark.parametrize("valid_values", [
    [0, 99],
    [1, 2, 3, 4, 5, 6, 7, 8],
    [50, 50, 50],
])
def test_values_ok_accepts_valid_inputs(valid_values):
    assert _values_ok(valid_values) is None


@pytest.mark.parametrize("invalid_values,expected_err", [
    ([], "needs 2 to 8 values"),
    ([1], "needs 2 to 8 values"),
    ([1, 2, 3, 4, 5, 6, 7, 8, 9], "needs 2 to 8 values"),
    ([-1, 10], "between 0 and 99"),
    ([10, 100], "between 0 and 99"),
    ([math.nan, 5], "finite numbers"),
    ([math.inf, 5], "finite numbers"),
])
def test_values_ok_rejects_invalid_inputs(invalid_values, expected_err):
    err = _values_ok(invalid_values)
    assert err is not None
    assert expected_err in err


def test_merge_sort_component_registered():
    comp = registry.get("merge_sort")
    assert comp is not None
    assert comp.name == "merge_sort"
    assert comp.domain == "computer-science"
    assert "values" in comp.params
    assert "show_counts" in comp.params

    clean, errs = registry.validate_params(comp, comp.example)
    assert not errs
    assert clean["values"] == [38, 27, 43, 3, 9, 82, 10]
    assert clean["show_counts"] is True
