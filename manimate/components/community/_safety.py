"""Static safety check for community components. It reads source text with ``ast`` and NEVER imports or runs it.

Used by the CI tests and by the issue-to-pull-request bot (which must not execute code it has not reviewed). It is a
guard against honest mistakes and obvious abuse, not a sandbox: a maintainer still reads every contribution.
"""
from __future__ import annotations

import ast

ALLOWED_IMPORTS = {
    "__future__", "manim", "numpy", "math", "cmath", "random", "itertools", "functools", "collections", "dataclasses",
    "typing", "textwrap", "colorsys", "enum", "fractions", "decimal", "statistics", "string", "re", "copy", "operator",
}
# Relative imports reach back into the library: ``from ...ctx import Ctx`` (from community/) or ``from manimate.x import``.
ALLOWED_LIBRARY = {"ctx", "theme", "registry", "tex", "safe_expr", "viz", "plugins", "components"}
BANNED_CALLS = {"eval", "exec", "compile", "open", "__import__", "globals", "locals", "vars", "breakpoint", "input",
                "exit", "quit", "setattr", "delattr", "getattr"}
BANNED_ATTRS = {"popen", "spawn", "fork", "rmtree", "unlink", "environ", "getenv",
                # file and network access that the allowed imports (numpy, pathlib-like helpers) would otherwise give
                "loadtxt", "genfromtxt", "fromfile", "tofile", "memmap", "savez", "savez_compressed",
                "savetxt", "ctypeslib", "read_text", "read_bytes", "write_text", "write_bytes", "urlopen", "urlretrieve",
                "Popen", "check_output", "startfile"}
# Harmless on a list, group or domain object (``group.remove(m)``, ``motor.load``), dangerous on a module
# that touches the host. Only these attribute names are judged by their receiver.
CONTEXTUAL_ATTRS = {"system", "remove", "load", "save"}
DANGEROUS_ROOTS = {"os", "subprocess", "shutil", "sys", "np", "numpy", "pathlib", "builtins"}
# Manim names that read files or change global settings. Components draw from parameters; they never load assets.
BANNED_NAMES = {"ImageMobject", "SVGMobject", "VideoMobject", "config", "tempconfig", "__builtins__", "__file__",
                "__loader__", "__spec__"}
# Reached through ``import manim; manim.config`` or ``from manim import config as c`` these are just as dangerous.
BANNED_MANIM = BANNED_NAMES - {"__builtins__", "__file__", "__loader__", "__spec__"}
BANNED_KEYWORDS = {"code_file", "file_name", "filename", "image_filename"}


def _root_name(node: ast.AST) -> str:
    """The left-most name in an attribute chain: ``np.os.system`` -> ``np``."""
    while isinstance(node, ast.Attribute):
        node = node.value
    return node.id if isinstance(node, ast.Name) else ""


def check_source(source: str) -> list[str]:
    """Return a list of problems (empty means it passed the static check)."""
    try:
        tree = ast.parse(source)
    except SyntaxError as e:
        return [f"syntax error on line {e.lineno}: {e.msg}"]
    problems: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for a in node.names:
                if a.name.split(".")[0] not in ALLOWED_IMPORTS | {"manimate"}:
                    problems.append(f"line {node.lineno}: import of {a.name!r} is not allowed")
        elif isinstance(node, ast.ImportFrom):
            root = (node.module or "").split(".")[0]
            if node.level:  # relative: from ...ctx import X, or from ... import theme
                names = [(node.module or "").split(".")[0]] if node.module else [a.name for a in node.names]
                if not all(n in ALLOWED_LIBRARY or n == "_plugin" for n in names):
                    problems.append(f"line {node.lineno}: relative import {'.' * node.level}{node.module or ''} is not allowed")
            elif root not in ALLOWED_IMPORTS | {"manimate"}:
                problems.append(f"line {node.lineno}: import from {node.module!r} is not allowed")
            for a in node.names:
                if a.name in BANNED_MANIM or a.name in BANNED_CALLS:
                    problems.append(f"line {node.lineno}: importing {a.name} is not allowed (components cannot load files, "
                                    "change Manim's settings or run code)")
        elif isinstance(node, ast.Name) and node.id in BANNED_CALLS and isinstance(node.ctx, ast.Load):
            problems.append(f"line {node.lineno}: {node.id} is not allowed (if this is your own variable, give it another name)")
        elif isinstance(node, ast.Attribute):
            if node.attr.startswith("__") and node.attr.endswith("__") and node.attr not in {"__name__", "__doc__"}:
                problems.append(f"line {node.lineno}: access to {node.attr} is not allowed")
            elif (node.attr in BANNED_ATTRS or node.attr in BANNED_MANIM
                  or (node.attr in CONTEXTUAL_ATTRS and _root_name(node.value) in DANGEROUS_ROOTS)):
                problems.append(f"line {node.lineno}: .{node.attr} is not allowed")
        elif isinstance(node, ast.Name) and node.id in BANNED_NAMES:
            problems.append(f"line {node.lineno}: {node.id} is not allowed (components cannot load files or change Manim's settings)")
        elif isinstance(node, ast.keyword) and node.arg in BANNED_KEYWORDS:
            problems.append(f"line {node.value.lineno}: the {node.arg}= argument is not allowed (components cannot read files)")
        elif isinstance(node, (ast.Global, ast.Nonlocal)):
            problems.append(f"line {node.lineno}: global/nonlocal is not allowed")
    return problems
