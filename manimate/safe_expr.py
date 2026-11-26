"""Tiny, safe evaluator for y = f(x) expressions that come from an LLM. No eval()."""
from __future__ import annotations

import ast
import math
import operator as op
import re
from typing import Callable

_BIN = {ast.Add: op.add, ast.Sub: op.sub, ast.Mult: op.mul, ast.Div: op.truediv, ast.Pow: math.pow, ast.Mod: op.mod}
_UN = {ast.UAdd: op.pos, ast.USub: op.neg}
def _sign(x: float) -> float:
    return float((x > 0) - (x < 0))


_FUNCS = {
    "sin": (math.sin, 1),
    "cos": (math.cos, 1),
    "tan": (math.tan, 1),
    "exp": (math.exp, 1),
    "log": (math.log, 1),
    "ln": (math.log, 1),
    "sqrt": (math.sqrt, 1),
    "abs": (abs, 1),
    "sinh": (math.sinh, 1),
    "cosh": (math.cosh, 1),
    "tanh": (math.tanh, 1),
    "atan": (math.atan, 1),
    "asin": (math.asin, 1),
    "acos": (math.acos, 1),
    "log10": (math.log10, 1),
    "log2": (math.log2, 1),
    "floor": (math.floor, 1),
    "ceil": (math.ceil, 1),
    "atan2": (math.atan2, 2),
    "max": (max, 2),
    "min": (min, 2),
    "hypot": (math.hypot, 2),
    "sign": (_sign, 1),
    "radians": (math.radians, 1),
    "sec": (lambda x: 1.0 / math.cos(x), 1),
    "asinh": (math.asinh, 1),
}
_CONSTS = {"pi": math.pi, "e": math.e}
MAX_LEN = 120
ALLOWED_VARIABLES = ("x", "y", "t", "s")  # names a caller may ask for (multi-variable landscapes, vector fields)


def _check(node: ast.AST, names: tuple[str, ...] = ("x",)) -> None:
    if isinstance(node, ast.Expression):
        _check(node.body, names)
    elif isinstance(node, ast.BinOp) and type(node.op) in _BIN:
        _check(node.left, names); _check(node.right, names)
    elif isinstance(node, ast.UnaryOp) and type(node.op) in _UN:
        _check(node.operand, names)
    elif isinstance(node, ast.Constant) and isinstance(node.value, (int, float)) and not isinstance(node.value, bool):
        return
    elif isinstance(node, ast.Name) and (node.id in names or node.id in _CONSTS):
        return
    elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in _FUNCS \
            and len(node.args) == _FUNCS[node.func.id][1] and not node.keywords:
        for arg in node.args:
            _check(arg, names)
    else:
        raise ValueError(f"unsupported syntax: {type(node).__name__}")


def _eval(node: ast.AST, env: dict[str, float]) -> float:
    if isinstance(node, ast.Expression):
        return _eval(node.body, env)
    if isinstance(node, ast.BinOp):
        return _BIN[type(node.op)](_eval(node.left, env), _eval(node.right, env))
    if isinstance(node, ast.UnaryOp):
        return _UN[type(node.op)](_eval(node.operand, env))
    if isinstance(node, ast.Constant):
        return float(node.value)
    if isinstance(node, ast.Name):
        return env[node.id] if node.id in env else _CONSTS[node.id]
    if isinstance(node, ast.Call):
        fn, _ = _FUNCS[node.func.id]
        return fn(*(_eval(arg, env) for arg in node.args))
    raise ValueError("bad node")


def compile_expr(src: str, variables: tuple[str, ...] = ("x",)) -> Callable[..., float]:
    """Compile e.g. '2*sin(x) + x**2/10' into a function. Raises ValueError if not allowed.

    ``variables`` names the arguments of the returned function, in order (default: just ``x``). Only names from
    ``ALLOWED_VARIABLES`` are accepted, e.g. ``variables=("x", "y")`` for ``f(x, y)``.
    """
    variables = tuple(variables)
    if not variables or len(set(variables)) != len(variables) or any(v not in ALLOWED_VARIABLES for v in variables):
        raise ValueError(f"variables must be distinct names from {ALLOWED_VARIABLES}")
    src = re.sub(r"^\s*(y|f\(x\))\s*=\s*", "", src.replace("^", "**"), flags=re.I).strip() if variables == ("x",) \
        else src.replace("^", "**").strip()
    if not src or len(src) > MAX_LEN:
        raise ValueError("expression empty or too long")
    try:
        tree = ast.parse(src, mode="eval")
    except SyntaxError as e:
        raise ValueError(f"syntax error: {e.msg}") from None
    _check(tree, variables)

    def f(*args: float) -> float:
        if len(args) != len(variables):
            raise TypeError(f"expected {len(variables)} argument(s): {', '.join(variables)}")
        try:
            v = float(_eval(tree, dict(zip(variables, map(float, args)))))
            return v if math.isfinite(v) else 0.0
        except (ValueError, ZeroDivisionError, OverflowError):
            return 0.0

    return f


def validate_expr(src: str) -> str | None:
    try:
        compile_expr(src)
        return None
    except ValueError as e:
        return str(e)
