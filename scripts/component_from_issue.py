"""Turn a "New component (from an LLM)" issue into files, WITHOUT running the submitted code.

Reads the issue body from $ISSUE_BODY (or --body-file), checks it statically, and writes
``manimate/components/community/<name>.py`` (and ``tests/community/test_<name>.py``). The result goes to
``issue-result.json``: {"ok": bool, "name": str, "errors": [...], "files": [...]}. The workflow reads that file and
either opens a pull request or comments the errors on the issue. Stdlib only, so it needs no install.
"""
from __future__ import annotations

import ast
import json
import os
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
# Import the checker without importing manim: load the file directly.
import importlib.util  # noqa: E402

_spec = importlib.util.spec_from_file_location("_safety", ROOT / "manimate/components/community/_safety.py")
_safety = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_safety)

NAME_RE = re.compile(r"^[a-z][a-z0-9_]{2,40}$")
MAX_CODE = 40_000
TEST_ALLOWED = _safety.ALLOWED_IMPORTS | {"pytest", "manimate"}


def parse_form(body: str) -> dict[str, str]:
    """Split issue-form sections without splitting fenced code."""
    sections: dict[str, str] = {}
    label = None
    lines: list[str] = []
    fence = None

    def save():
        if label is not None:
            value = "\n".join(lines).strip()
            sections[label] = "" if value == "_No response_" else value

    for line in body.replace("\r\n", "\n").split("\n"):
        marker = re.match(r"^ {0,3}(`{3,}|~{3,})(.*)$", line)

        if fence is not None:
            lines.append(line)
            if (marker and marker[1][0] == fence[0]
                    and len(marker[1]) >= len(fence)
                    and not marker[2].strip()):
                fence = None
            continue

        if marker:
            fence = marker[1]
            lines.append(line)
            continue

        heading = re.match(r"^### +(.+?)\s*$", line)
        if heading:
            save()
            label = heading[1].strip()
            lines = []
        else:
            lines.append(line)

    if fence is not None:
        raise ValueError("Unclosed code fence in issue form.")

    save()
    return sections


def unfence(text: str) -> str:
    """The form wraps `render: python` fields in a code fence; take what is inside (or the text itself)."""
    m = re.search(r"```[a-zA-Z]*\n(.*?)\n?```", text, flags=re.S)
    return (m.group(1) if m else text).strip("\n") + "\n"


def find(sections: dict[str, str], *starts: str) -> str:
    for label, value in sections.items():
        if any(label.lower().startswith(s) for s in starts):
            return value
    return ""


def check_tests(src: str) -> list[str]:
    try:
        tree = ast.parse(src)
    except SyntaxError as e:
        return [f"tests: syntax error on line {e.lineno}: {e.msg}"]
    errs = []
    for node in ast.walk(tree):
        names = [a.name for a in node.names] if isinstance(node, ast.Import) else \
                [node.module or ""] if isinstance(node, ast.ImportFrom) and not node.level else []
        for n in names:
            if n.split(".")[0] not in TEST_ALLOWED:
                errs.append(f"tests: line {node.lineno}: import of {n!r} is not allowed")
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in {"eval", "exec", "open", "__import__", "compile"}:
            errs.append(f"tests: line {node.lineno}: {node.func.id}() is not allowed")
    return errs


def declared_names(src: str) -> list[str]:
    """Names passed as the first argument of @component(...), read from the syntax tree."""
    out = []
    for node in ast.walk(ast.parse(src)):
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id == "component" and node.args:
            a = node.args[0]
            if isinstance(a, ast.Constant) and isinstance(a.value, str):
                out.append(a.value)
    return out


def process(body: str) -> dict:
    try:
        sections = parse_form(body)
    except ValueError as exc:
        return {"ok": False, "errors": [str(exc)]}
    name = find(sections, "component name").strip().strip("`")
    code = unfence(find(sections, "python code")) if find(sections, "python code") else ""
    tests = unfence(find(sections, "test code")) if find(sections, "test code") else ""
    errors: list[str] = []

    if not NAME_RE.match(name):
        errors.append(f"The component name {name!r} must be lowercase letters, digits and underscores, starting with a letter (3 to 41 characters).")
    if not code.strip():
        errors.append("The Python code is empty. Paste the whole file the LLM gave you.")
    elif len(code) > MAX_CODE:
        errors.append(f"The code is longer than {MAX_CODE} characters. Components should be small; split it up.")
    else:
        errors += _safety.check_source(code)
        if not errors:
            declared = declared_names(code)
            if not declared:
                errors.append("No `@component(\"name\", ...)` declaration was found. Start from the template in docs/LLM_PROMPT.md.")
            elif declared != [name]:
                errors.append(f"The code declares {declared} but the form says {name!r}. They must match, and each submission is one component.")
    existing = {c["name"] for c in json.loads((ROOT / "catalog.json").read_text())}
    if name in existing:
        errors.append(f"A component named {name!r} already exists. Choose another name.")
    if (ROOT / "manimate/components/community" / f"{name}.py").exists():
        errors.append(f"manimate/components/community/{name}.py already exists.")
    if tests.strip():
        errors += check_tests(tests)

    files: list[str] = []
    if not errors:
        target = ROOT / "manimate/components/community" / f"{name}.py"
        target.write_text(code)
        files.append(str(target.relative_to(ROOT)))
        if tests.strip():
            tdir = ROOT / "tests/community"
            tdir.mkdir(parents=True, exist_ok=True)
            tfile = tdir / f"test_{name}.py"
            tfile.write_text(tests)
            files.append(str(tfile.relative_to(ROOT)))
    return {"ok": not errors, "name": name, "errors": errors, "files": files,
            "teaches": find(sections, "what does it teach"), "domain": find(sections, "subject area"),
            "notes": find(sections, "anything else")}


def main() -> int:
    body = Path(sys.argv[sys.argv.index("--body-file") + 1]).read_text() if "--body-file" in sys.argv else os.environ.get("ISSUE_BODY", "")
    result = process(body)
    Path(os.environ.get("RESULT_FILE", "issue-result.json")).write_text(json.dumps(result, indent=2))
    print(json.dumps({k: v for k, v in result.items() if k in ("ok", "name", "errors", "files")}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
