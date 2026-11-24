import json
from pathlib import Path

import pytest

from manimate import registry
from manimate.catalog import build_catalog
from manimate.components import load_all
from manimate.safe_expr import compile_expr, validate_expr
from manimate.storyboard import MAX_SCENES, validate

load_all()
EXAMPLES = Path(__file__).parent.parent / "examples"


def sb(*scenes, title="t"):
    return {"title": title, "scenes": [{"component": c, "params": p, "narration": "Short narration here."} for c, p in scenes]}


def test_every_component_example_is_valid():
    for entry in build_catalog():
        comp = registry.get(entry["name"])
        _, errs = registry.validate_params(comp, entry["example"])
        assert not errs, (entry["name"], errs)


def test_catalog_shape():
    cat = build_catalog()
    assert {"title_card", "synchronous_motor", "circuit"} <= {c["name"] for c in cat}
    for c in cat:
        assert c["description"] and "params" in c and "example" in c
    json.dumps(cat)  # must be serialisable (the worker embeds it)


def test_example_storyboard_valid():
    out, errs = validate(json.loads((EXAMPLES / "synchronous_motor.json").read_text()))
    assert not errs and out is not None


def test_unknown_component_and_missing_param():
    _, errs = validate(sb(("nope", {}), ("title_card", {})))
    assert any("unknown component 'nope'" in e for e in errs)
    assert any("missing required param 'title'" in e for e in errs)


def test_defaults_applied_and_extras_dropped():
    out, errs = validate(sb(("rotating_field", {"junk": 1})))
    assert not errs
    assert out.scenes[0].params == {"poles": 2, "frequency_hz": 50}


def test_type_and_choice_errors():
    _, errs = validate(sb(("rotating_field", {"poles": 3}), ("bullet_points", {"heading": "h", "points": "not a list"})))
    assert any("one of" in e for e in errs)
    assert any("must be a list" in e for e in errs)


def test_integer_accepts_whole_float():
    out, errs = validate(sb(("rotating_field", {"poles": 4.0})))
    assert not errs and out.scenes[0].params["poles"] == 4



@pytest.mark.parametrize(
    ("param_type", "value"),
    [
        ("number", float("nan")),
        ("number", float("inf")),
        ("number", float("-inf")),
        ("integer", float("nan")),
        ("integer", float("inf")),
        ("integer", float("-inf")),
        ("number[]", [1.0, float("nan")]),
        ("number[]", [1.0, float("inf")]),
        ("number[]", [1.0, float("-inf")]),
    ],
)
def test_non_finite_numbers_are_rejected(param_type, value):
    comp = registry.Component(
        name="test",
        description="test",
        domain="test",
        params={
            "value": registry.Param(
                type=param_type,
                description="test parameter",
            )
        },
        example={},
        fn=lambda: None,
    )

    _, errors = registry.validate_params(comp, {"value": value})

    assert errors
    assert "param 'value'" in errors[0]


def test_integer_accepts_very_large_python_int():
    large_integer = 10**1000

    comp = registry.Component(
        name="test",
        description="test",
        domain="test",
        params={
            "value": registry.Param(
                type="integer",
                description="test parameter",
            )
        },
        example={},
        fn=lambda: None,
    )

    clean, errors = registry.validate_params(
        comp, {"value": large_integer}
    )

    assert not errors
    assert clean["value"] == large_integer


def test_scene_limits():
    _, errs = validate(sb(*[("callout", {"text": "x"})] * (MAX_SCENES + 1)))
    assert errs
    _, errs = validate({"title": "t", "scenes": []})
    assert errs


def test_total_duration_cap():
    long = "word " * 70
    raw = {"title": "t", "scenes": [{"component": "callout", "params": {"text": "x"}, "narration": long}] * 10}
    _, errs = validate(raw)
    assert any("too long" in e for e in errs)


def test_safe_expr():
    assert compile_expr("sin(x)^2 + 1")(0) == 1
    assert compile_expr("y = 2*x")(3) == 6
    assert compile_expr("log(x)")(-1) == 0.0  # domain errors are tamed
    for bad in ["__import__('os')", "x.__class__", "open('f')", "lambda: 1", "sin(x, 2)", "a+1", "[1]"]:
        assert validate_expr(bad), bad


def test_bad_expression_fails_validation():
    _, errs = validate(sb(("function_plot", {"expression": "__import__('os').system('x')"})))
    assert errs


@pytest.mark.parametrize(("expression", "expected"), [("x^0.5", 4.0), ("sqrt(x**0.5)", 2.0)])
def test_safe_expr_handles_fractional_powers_outside_the_real_domain(expression, expected):
    f = compile_expr(expression)
    assert f(-4) == 0.0
    assert f(16) == expected


def test_power_pack_registered():
    names = {c["name"] for c in build_catalog()}
    assert {"transformer", "power_triangle", "torque_speed_curve"} <= names


def test_power_pack_param_ranges():
    _, errs = validate(sb(("transformer", {"turns_ratio": 50})))
    assert any("between 0.1 and 10" in e for e in errs)
    _, errs = validate(sb(("power_triangle", {"real_power_kw": 4, "power_factor": 1.5})))
    assert any("power_factor" in e for e in errs)
    _, errs = validate(sb(("torque_speed_curve", {"motor": "stepper"})))
    assert any("must be one of" in e for e in errs)
    out, errs = validate(sb(("power_triangle", {"real_power_kw": 4})))
    assert not errs and out.scenes[0].params["power_factor"] == 0.8


def test_power_basics_example_valid():
    out, errs = validate(json.loads((EXAMPLES / "power_basics.json").read_text()))
    assert not errs and out is not None

@pytest.mark.parametrize("title", ["", "   ", "\t\n"])
def test_blank_storyboard_title_rejected(title):
    out, errs = validate(sb(("rotating_field", {}), title=title))
    assert out is None
    assert any(e.startswith("title:") for e in errs)


@pytest.mark.parametrize("title", ["Python Tutorial", "  Python Tutorial  "])
def test_storyboard_title_normalized(title):
    out, errs = validate(sb(("rotating_field", {}), title=title))
    assert not errs
    assert out is not None
    assert out.title == "Python Tutorial"


@pytest.mark.parametrize("component", ["", "   ", "\t\n"])
def test_blank_scene_component_rejected(component):
    out, errs = validate(sb((component, {})))
    assert out is None
    assert any(e.startswith("scenes.0.component:") for e in errs)


@pytest.mark.parametrize("component", ["rotating_field", "  rotating_field  "])
def test_scene_component_normalized(component):
    out, errs = validate(sb((component, {})))
    assert not errs
    assert out is not None
    assert out.scenes[0].component == "rotating_field"


def test_storyboard_title_max_length():
    out, errs = validate(sb(("rotating_field", {}), title="a" * 121))
    assert out is None
    assert any(e.startswith("title:") for e in errs)
