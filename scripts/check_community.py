"""Static checks on everything contributed to ``manimate/components/community/``. Stdlib only; NOTHING is imported or run.

    python scripts/check_community.py            # check the whole folder (what CI runs)
    python scripts/check_community.py --list     # print the rules

It is the fast first gate in CI: it needs no Manim and no install, so a bad contribution fails in seconds. It does not
replace the dry-run tests (``tests/community``) or a maintainer reading the code.

Rules, per component file ``community/<name>.py``:
  * the file name is snake_case (3 to 41 characters) and the file is at most 40,000 characters
  * it passes the static safety check (allowed imports, no eval/exec/open/files/network)
  * it has a module docstring, no ``import *`` and no ``print()``
  * it declares exactly one ``@component`` and the name matches the file name
  * its test file (``tests/community/test_<name>.py``), if any, only uses allowed imports
The folder itself may only hold ``.py`` files and the README; ``tests/community`` may only hold ``test_<component>.py``
files for components that exist (plus ``__init__.py`` and the loader test).
"""
from __future__ import annotations

import ast
import importlib.util
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
COMMUNITY = ROOT / "manimate/components/community"
TESTS = ROOT / "tests/community"

NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,40}$")
MAX_CODE = 40_000
FOLDER_ALLOWED = {"README.md", "__init__.py"}
TESTS_ALLOWED = {"__init__.py", "test_community_loader.py"}


def _load(path: Path, name: str):
    spec = importlib.util.spec_from_file_location(name, path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


_safety = _load(COMMUNITY / "_safety.py", "_safety")  # loaded by path: importing manimate would import Manim
_issue = _load(ROOT / "scripts/component_from_issue.py", "_component_from_issue")


declared_components = _issue.declared_components


def check_component_file(path: Path) -> list[str]:
    stem, src = path.stem, path.read_text()
    problems: list[str] = []
    if not NAME_RE.match(stem):
        problems.append(f"file name {path.name!r} must be snake_case: a lowercase letter first, then lowercase letters, digits or _ (3 to 41 characters)")
    if len(src) > MAX_CODE:
        problems.append(f"{len(src)} characters is over the {MAX_CODE} limit. A component is one small idea: split it up")
    safety = _safety.check_source(src)
    problems += [f"safety: {p}" for p in safety]
    if safety and safety[0].startswith("syntax error"):
        return problems
    tree = ast.parse(src)
    if not ast.get_docstring(tree):
        problems.append("add a module docstring: one or two sentences on what the component teaches")
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and any(a.name == "*" for a in node.names):
            problems.append(f"line {node.lineno}: `import *` hides where names come from. Import each name")
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "print":
            problems.append(f"line {node.lineno}: print() is not allowed in a component")
    declared = declared_components(tree)
    if len(declared) != 1:
        problems.append(f"declare exactly one @component (found {len(declared)}: {declared}). One idea per file")
    elif declared[0] != stem:
        problems.append(f"the component is named {declared[0]!r} but the file is {path.name!r}. They must match")
    test = TESTS / f"test_{stem}.py"
    if test.exists():
        problems += _issue.check_tests(test.read_text())
    return problems


def check_layout() -> list[str]:
    problems: list[str] = []
    stems = {p.stem for p in COMMUNITY.glob("*.py") if not p.name.startswith("_") and p.name != "__init__.py"}
    for p in sorted(COMMUNITY.iterdir()):
        if p.is_dir() and p.name != "__pycache__":
            problems.append(f"{p.relative_to(ROOT)}: sub-folders are not allowed here. One file per component")
        elif p.is_file() and p.suffix != ".py" and p.name not in FOLDER_ALLOWED:
            problems.append(f"{p.relative_to(ROOT)}: only .py files and README.md belong in the community folder")
    if TESTS.is_dir():
        for p in sorted(TESTS.glob("*")):
            if p.is_dir():
                continue
            if p.name in TESTS_ALLOWED:
                continue
            m = re.fullmatch(r"test_([a-z0-9_]+)\.py", p.name)
            if not m:
                problems.append(f"{p.relative_to(ROOT)}: tests here must be named test_<component>.py")
            elif m.group(1) not in stems:
                problems.append(f"{p.relative_to(ROOT)}: there is no community component called {m.group(1)!r}")
    return problems


def main(argv: list[str] | None = None) -> int:
    argv = sys.argv[1:] if argv is None else argv
    if "--list" in argv:
        print(__doc__)
        return 0
    failures = {"(layout)": check_layout()}
    for path in sorted(COMMUNITY.glob("*.py")):
        if not path.name.startswith("_") and path.name != "__init__.py":
            failures[str(path.relative_to(ROOT))] = check_component_file(path)
    bad = {k: v for k, v in failures.items() if v}
    for where, problems in bad.items():
        for p in problems:
            print(f"::error file={where}::{p}" if where != "(layout)" else f"::error::{p}")
    checked = len(failures) - 1
    print(f"checked {checked} community component(s): {'FAILED' if bad else 'ok'}")
    return 1 if bad else 0


if __name__ == "__main__":
    raise SystemExit(main())
