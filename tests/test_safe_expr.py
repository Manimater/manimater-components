import math

import pytest

from manimate.safe_expr import compile_expr, validate_expr


@pytest.mark.parametrize(
    "name, value, expected",
    [
        ("asin", -1, -math.pi / 2),
        ("asin", 0.5, math.pi / 6),
        ("asin", 1, math.pi / 2),
        ("acos", -1, math.pi),
        ("acos", 0.5, math.pi / 3),
        ("acos", 1, 0),
        ("log10", 100, 2),
        ("log10", 0.1, -1),
        ("log2", 8, 3),
        ("log2", 0.5, -1),
        ("floor", 1.5, 1),
        ("floor", -1.5, -2),
        ("ceil", 1.5, 2),
        ("ceil", -1.5, -1),
    ],
)
def test_additional_functions(name, value, expected):
    expression = f"{name}(x)"
    assert validate_expr(expression) is None
    result = compile_expr(expression)(value)
    assert isinstance(result, float)
    assert result == pytest.approx(expected)


@pytest.mark.parametrize("name", ["asin", "acos", "log10", "log2", "floor", "ceil"])
@pytest.mark.parametrize("arguments", ["", "x, 1", "x=x", "*x", "**x"])
def test_additional_functions_require_one_positional_argument(name, arguments):
    assert validate_expr(f"{name}({arguments})") is not None


@pytest.mark.parametrize(
    "expression",
    ["asin(2)", "asin(-2)", "acos(2)", "acos(-2)", "log10(0)", "log10(-1)", "log2(0)", "log2(-1)"],
)
def test_additional_functions_return_zero_for_domain_errors(expression):
    assert compile_expr(expression)(0) == 0.0


def test_additional_functions_compose_with_existing_expressions():
    assert compile_expr("floor(log2(x)) + ceil(sqrt(x))")(8) == 6.0
    assert compile_expr("asin(x) + acos(y)", variables=("x", "y"))(1, 0) == pytest.approx(math.pi)


@pytest.mark.parametrize("expression", ["math.asin(x)", "asin.__call__(x)", "unknown(x)"])
def test_additional_functions_do_not_allow_attribute_access_or_unknown_calls(expression):
    assert validate_expr(expression) is not None
