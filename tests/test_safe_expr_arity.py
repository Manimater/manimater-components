import math

import pytest

from manimate.safe_expr import compile_expr


@pytest.mark.parametrize("expr,x,expected", [
    ("atan2(x, 1)", 2, math.atan2(2, 1)),
    ("max(x, 0)", -2, 0),
    ("max(x, 0)", 2, 2),
    ("min(x, 0)", -2, -2),
    ("hypot(x, 4)", 3, 5),
    ("sign(x)", -5, -1),
    ("sign(x)", 0, 0),
    ("sign(x)", 5, 1),
    ("radians(x)", 180, math.pi),
    ("sec(x)", 0, 1),
    ("asinh(x)", 2, math.asinh(2)),
    ("max(sin(x), min(x, 0))", 0, 0),
])
def test_supported_functions(expr, x, expected):
    assert compile_expr(expr)(x) == pytest.approx(expected)


@pytest.mark.parametrize("expr", [
    "max(x)",
    "max(x, 0, 1)",
    "atan2(x)",
    "hypot()",
    "sin(x, 1)",
    "sign()",
    "max(x, y=0)",
    "max(*(x, 0))",
    "math.atan2(x, 1)",
    "max(x, unknown)",
    "max(x, open('file'))",
    "max(x, [1, 2])",
    "max(x, True)",
    "max(x, x.real)",
])
def test_reject_invalid_calls(expr):
    with pytest.raises(ValueError):
        compile_expr(expr)


def test_multiple_variables():
    f = compile_expr("hypot(x, y)", variables=("x", "y"))
    assert f(3, 4) == pytest.approx(5)
