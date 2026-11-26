"""Components built on manim-extensions through the generic adapter (components/_ext.py).

The pure logic is always tested. Each component is also executed against a real Scene in dry-run mode, followed by the
fade-out a storyboard scene performs, wherever manim-extensions is installed (scripts/install_plugins.sh).
"""
from __future__ import annotations

import importlib.util
import warnings

import pytest

from manimate import registry
from manimate.components import load_all
from manimate.components.extensions import (
    ADAS_EVENTS, ISLM_POLICIES, LINKED, SOLOW, SD_EVENTS, build_tree, gear_ratio, map_data, parse_queue_ops,
    sd_equilibrium, sd_shifts, tree_lines,
)

load_all()
NAMES = ["supply_demand", "ad_as_model", "is_lm_model", "is_lm_ad_as", "solow_growth", "concept_map", "hierarchy_tree",
         "timeline", "file_tree", "gear_train", "queue_operations"]


def test_every_component_is_credited_to_manim_extensions():
    for n in NAMES:
        assert registry.get(n).plugin == "manim-extensions", n


def test_supply_demand_equilibrium_moves_the_right_way():
    assert sd_equilibrium() == (6, 5)
    q, p = sd_equilibrium(*sd_shifts("demand_increase", 2))
    assert q > 6 and p > 5
    q, p = sd_equilibrium(*sd_shifts("supply_increase", 2))
    assert q > 6 and p < 5
    q, p = sd_equilibrium(*sd_shifts("demand_decrease", 2))
    assert q < 6 and p < 5
    q, p = sd_equilibrium(*sd_shifts("supply_decrease", 2))
    assert q < 6 and p > 5
    assert sd_shifts("demand_increase", 99) == (3, 0)  # size is clamped to 3


def test_choice_tables_match_the_declared_choices():
    for name, table in [("supply_demand", SD_EVENTS), ("ad_as_model", ADAS_EVENTS), ("is_lm_model", ISLM_POLICIES),
                        ("is_lm_ad_as", LINKED), ("solow_growth", SOLOW)]:
        choices = next(iter(registry.get(name).params.values())).choices
        assert set(choices) == set(table), name


def test_file_tree_order_matches_drawing_order():
    tree = build_tree(["src/main.py", "src/utils/helpers.py", "README.md"])
    assert tree_lines(tree) == ["src", "src/main.py", "src/utils", "src/utils/helpers.py", "README.md"]
    v = registry.get("file_tree").params["paths"].validator
    assert v(["a/b.py", "c.md"]) is None
    for bad in [["a"], ["../etc/passwd", "b"], ["a b", "c"], ["a/b/c/d/e/f.py", "x"]]:
        assert v(bad) is not None, bad


def test_queue_operations_are_checked():
    assert parse_queue_ops(["enqueue 4", "dequeue"], 3, 5) == [("enqueue", "4"), ("dequeue", None)]
    for bad in [["dequeue"] * 4, ["enqueue 1"] * 3, ["push 1"], ["enqueue"]]:
        with pytest.raises(ValueError):
            parse_queue_ops(bad, 3, 5)
    assert registry.get("queue_operations").params["operations"].validator(["dequeue"] * 4) is not None


def test_map_inputs_are_validated_and_become_nested_data():
    v = registry.get("concept_map").params["branches"].validator
    assert v(["A: x, y", "B"]) is None
    assert v(["only one"]) is not None and v(["A: 1, 2, 3, 4, 5", "B"]) is not None
    data = map_data("Root", ["A: x, y", "B"])
    assert len(data["child"]) == 2 and len(data["child"][0]["child"]) == 2 and "child" not in data["child"][1]
    assert registry.get("timeline").params["events"].validator(["no colon here", "2000: ok"]) is not None


def test_gear_ratio():
    assert gear_ratio(15, 30) == 2


@pytest.mark.parametrize("name", NAMES)
def test_component_runs_and_fades_out(name):
    if importlib.util.find_spec("manim_extensions") is None:
        pytest.skip("manim-extensions is not installed")
    from manim import FadeOut, Scene, tempconfig
    from manimate.ctx import Ctx

    comp = registry.get(name)
    with tempconfig({"dry_run": True, "disable_caching": True, "verbosity": "ERROR", "progress_bar": "none", "write_to_movie": False}):
        scene = Scene()
        ctx = Ctx(scene, 8.0)
        comp.fn(ctx, **comp.example)
        if ctx.overrun > 0.05:
            warnings.warn(
                f"{name} exceeded its 8.00s budget "
                f"by {ctx.overrun:.2f}s",
                RuntimeWarning,
            )
        assert scene.mobjects, "nothing was left on screen"
        scene.play(*[FadeOut(m) for m in scene.mobjects], run_time=0.5)


@pytest.mark.slow  # every choice of every economics component, about 5 minutes; CI runs it with `pytest -m slow`
@pytest.mark.parametrize("name,param,values", [
    ("supply_demand", "event", list(SD_EVENTS)), ("ad_as_model", "event", list(ADAS_EVENTS)),
    ("is_lm_model", "policy", list(ISLM_POLICIES)), ("is_lm_ad_as", "policy", list(LINKED)),
    ("solow_growth", "change", list(SOLOW)),
])
def test_every_choice_plays(name, param, values, capfd):
    if importlib.util.find_spec("manim_extensions") is None:
        pytest.skip("manim-extensions is not installed")
    from manim import Scene, tempconfig
    from manimate.ctx import Ctx

    comp = registry.get(name)
    for v in values:
        with tempconfig({"dry_run": True, "disable_caching": True, "verbosity": "ERROR", "progress_bar": "none", "write_to_movie": False}):
            ctx = Ctx(Scene(), 12.0)
            comp.fn(ctx, **{**comp.example, param: v})
            if ctx.overrun > 0.05:
                warnings.warn(
                    f"{name} ({param}={v}) exceeded its 12.00s budget "
                    f"by {ctx.overrun:.2f}s",
                    RuntimeWarning,
                )
    assert "Traceback" not in capfd.readouterr().err  # a failing beat is caught by the runner, so check it did not
