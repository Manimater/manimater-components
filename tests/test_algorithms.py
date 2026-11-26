"""The computer-science algorithms pack (plain Manim, no plugin): the algorithms are checked on their own, then each
component is dry-run against a real Scene, followed by the fade-out a storyboard scene performs."""
import math
import warnings

import pytest

from manimate import registry
from manimate.components import load_all
from manimate.components.algorithms import (
    PLACES, binary_search_steps, build_buckets, fib_tree, hash_key, lcs_backtrack, lcs_table, norm_bigo, parse_messages,
    repeated_calls, reverse_list, reverse_steps, to_bits,
)
from manimate.storyboard import validate

load_all()
CS = ["binary_search", "big_o_growth", "recursion_tree", "hash_table", "linked_list_reverse", "dp_table", "sequence_diagram",
      "binary_representation"]


def is_subsequence(small: str, big: str) -> bool:
    it = iter(big)
    return all(c in it for c in small)


# ---- the algorithms ---------------------------------------------------------------------------------------------
@pytest.mark.parametrize("target", [3, 8, 15, 23, 42, 57, 71])
def test_binary_search_finds_every_present_value(target):
    vals = [3, 8, 15, 23, 42, 57, 71]
    steps = binary_search_steps(vals, target)
    lo, mid, hi, verdict = steps[-1]
    assert verdict == "found" and vals[mid] == target
    assert len(steps) <= int(math.log2(len(vals))) + 1


@pytest.mark.parametrize("target", [0, 5, 50, 99])
def test_binary_search_reports_absent_values_without_a_found_step(target):
    steps = binary_search_steps([3, 8, 15, 23, 42, 57, 71], target)
    assert steps and all(v != "found" for *_, v in steps)


def test_binary_search_window_always_shrinks():
    vals = list(range(0, 80, 10))
    steps = binary_search_steps(vals, 70)
    widths = [hi - lo for lo, _, hi, _ in steps]
    assert widths == sorted(widths, reverse=True) and len(set(widths)) == len(widths)


@pytest.mark.parametrize("raw,key", [("n^2", "n^2"), ("O(n²)", "n^2"), ("O(log n)", "log n"), ("n log n", "n log n"),
                                     ("NLOGN", "n log n"), ("2ⁿ", "2^n"), ("linear", "n"), ("Constant", "1"), ("O(1)", "1")])
def test_big_o_names_are_understood(raw, key):
    assert norm_bigo(raw) == key


def test_big_o_rejects_nonsense():
    assert norm_bigo("banana") is None
    assert registry.get("big_o_growth").params["functions"].validator(["n", "banana"]) is not None
    assert registry.get("big_o_growth").params["functions"].validator(["n"]) is not None   # one curve is not a comparison
    assert registry.get("big_o_growth").params["functions"].validator(["n", "O(n²)"]) is None


def _fib(n):
    return n if n < 2 else _fib(n - 1) + _fib(n - 2)


@pytest.mark.parametrize("n", [2, 3, 4, 5])
def test_fib_tree_has_one_node_per_call(n):
    nodes = fib_tree(n)
    assert len(nodes) == 2 * _fib(n + 1) - 1
    by_id = {d["id"]: d for d in nodes}
    for d in nodes:
        for k in d["kids"]:
            assert by_id[k]["depth"] == d["depth"] + 1
        if d["kids"]:
            xs = [by_id[k]["x"] for k in d["kids"]]
            assert min(xs) <= d["x"] <= max(xs)          # a parent sits over its children
    assert [d["depth"] for d in nodes] == sorted(d["depth"] for d in nodes)   # breadth-first order


def test_fib_repeats():
    assert repeated_calls(fib_tree(5)) == {3: 2, 2: 3}
    assert repeated_calls(fib_tree(2)) == {}


def test_hash_and_chaining():
    assert hash_key("cat", 5) == (99 + 97 + 116) % 5 == 2
    buckets, collided = build_buckets(["cat", "act", "dog"], 5)
    assert buckets[2] == ["cat", "act"] and collided == [False, True, False]
    assert sum(len(b) for b in buckets) == 3


@pytest.mark.parametrize("values", [["1", "2", "3"], ["a", "b", "c", "d", "e", "f"], ["x", "y", "z", "w"]])
def test_reverse_list_matches_python(values):
    assert reverse_list(values) == values[::-1]
    steps = reverse_steps(len(values))
    assert [c for _, c, _ in steps] == list(range(len(values)))
    assert steps[0][0] is None and steps[-1][2] is None


@pytest.mark.parametrize("a,b,length", [("ABCBD", "BDCAB", 3), ("AGCAT", "GAC", 2), ("ABC", "DEF", 0), ("ABC", "ABC", 3)])
def test_lcs(a, b, length):
    L = lcs_table(a, b)
    word, path = lcs_backtrack(a, b, L)
    assert L[len(a)][len(b)] == length == len(word)
    assert is_subsequence(word, a) and is_subsequence(word, b)
    assert all(1 <= i <= len(a) and 1 <= j <= len(b) for i, j in path)


def test_message_parsing():
    out = parse_messages(["Client->Server: SYN", "Server-->Client: SYN-ACK"])
    assert out == [("Client", "Server", "SYN", False), ("Server", "Client", "SYN-ACK", True)]
    for bad in ["no arrow here", "A->A: loop", "A->B"]:
        with pytest.raises(ValueError):
            parse_messages([bad])


def test_binary_bits_rebuild_every_byte():
    for v in range(256):
        bits = to_bits(v)
        assert sum(p * b for p, b, _ in bits) == v
        assert bits[-1][2] == 0 and [p for p, _, _ in bits] == PLACES


# ---- validation -------------------------------------------------------------------------------------------------
def test_pack_is_registered_under_computer_science():
    by_name = {c.name: c for c in registry.all_components()}
    assert set(CS) <= set(by_name)
    assert all(by_name[n].domain == "computer-science" and by_name[n].plugin is None for n in CS)


def sb(component, params):
    return {"title": "t", "scenes": [{"component": component, "params": params, "narration": "Here we go through it step by step."}]}


@pytest.mark.parametrize("component,params,fragment", [
    ("binary_search", {"values": [1, 2], "target": 1}, "3 to 8"),
    ("binary_search", {"values": [1, 2, 300], "target": 1}, "0 to 99"),
    ("binary_search", {"values": [1, 2, 3]}, "missing required"),
    ("hash_table", {"keys": ["a"]}, "2 to 6"),
    ("hash_table", {"keys": ["a", "b"], "size": 3}, "one of"),
    ("linked_list_reverse", {"values": ["1", "2"]}, "3 to 6"),
    ("dp_table", {"a": "A", "b": "BC"}, "2-6 plain letters"),
    ("dp_table", {"a": "AB1", "b": "BC"}, "2-6 plain letters"),
    ("sequence_diagram", {"actors": ["A", "B"], "messages": ["A->A: x"]}, "itself"),
    ("sequence_diagram", {"actors": ["A"], "messages": ["A->B: x"]}, "2 to 5"),
    ("binary_representation", {"value": 256}, "0 to 255"),
    ("recursion_tree", {"n": 9}, "one of"),
])
def test_bad_parameters_are_rejected(component, params, fragment):
    _, errs = validate(sb(component, params))
    assert any(fragment in e for e in errs), errs


@pytest.mark.parametrize("name", CS)
def test_examples_validate(name):
    comp = registry.get(name)
    out, errs = validate(sb(name, comp.example))
    assert not errs and out is not None


# ---- running ----------------------------------------------------------------------------------------------------
def _dry_run(name, params, seconds=6.0):
    from manim import FadeOut, Scene, tempconfig
    from manimate.ctx import Ctx

    comp = registry.get(name)
    clean, errs = registry.validate_params(comp, params)
    assert not errs, errs
    with tempconfig({"dry_run": True, "disable_caching": True, "verbosity": "ERROR", "progress_bar": "none",
                     "write_to_movie": False, "frame_rate": 4}):
        scene = Scene()
        ctx = Ctx(scene, seconds)
        comp.fn(ctx, **clean)
        if ctx.overrun > 0.05:
            warnings.warn(
                f"{name} exceeded its {seconds:.2f}s budget "
                f"by {ctx.overrun:.2f}s",
                RuntimeWarning,
                stacklevel=2,
            )
        scene.play(*[FadeOut(m) for m in scene.mobjects], run_time=0.5)


@pytest.mark.parametrize("name", CS)
def test_component_runs_and_fades_out(name):
    _dry_run(name, registry.get(name).example)


@pytest.mark.parametrize("name,params", [
    ("binary_search", {"values": [9, 1, 5], "target": 7}),                              # not present, unsorted input
    ("binary_search", {"values": [1, 2, 3, 4, 5, 6, 7, 8], "target": 1}),
    ("big_o_growth", {"functions": ["O(n)", "linear", "quadratic"]}),                    # aliases collapse, never crash
    ("recursion_tree", {"n": 2}),
    ("hash_table", {"keys": ["alphabet", "Z"], "size": 8}),
    ("linked_list_reverse", {"values": ["a", "b", "c", "d", "e", "f"]}),
    ("dp_table", {"a": "ab", "b": "cd"}),                                                # no common subsequence
    ("dp_table", {"a": "ABCDEF", "b": "FEDCBA"}),                                        # biggest table
    ("sequence_diagram", {"actors": ["A", "B"], "messages": ["A->B: hi", "B-->C: unlisted actor gets a lifeline"]}),
    ("sequence_diagram", {"actors": ["A", "B", "C", "D", "E"], "messages": [f"A->E: message number {i}" for i in range(8)]}),
    ("binary_representation", {"value": 0}),
    ("binary_representation", {"value": 255}),
])
def test_edge_cases_run(name, params):
    _dry_run(name, params, seconds=4.0)                                                  # the shortest scene a storyboard allows
