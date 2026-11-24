"""The issue-to-pull-request bot's parser and static checks (it must never run submitted code)."""
from __future__ import annotations

import importlib.util
import json
import pathlib
import shutil

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("component_from_issue", ROOT / "scripts" / "component_from_issue.py")
cfi = importlib.util.module_from_spec(spec)
spec.loader.exec_module(cfi)

TEMPLATE = (ROOT / "manimate/components/community/_template.py").read_text()


def form(name="pipeline_steps", code=None, tests="_No response_") -> str:
    code = code if code is not None else TEMPLATE.replace("step_chain", name)
    return (f"### Component name\n\n{name}\n\n### Subject area\n\ngeneral\n\n### What does it teach?\n\nStages of a process.\n\n"
            f"### Python code\n\n```python\n{code}```\n\n### Test code (optional)\n\n{tests}\n\n"
            "### Anything else? (optional)\n\n_No response_\n\n### Licence\n\n- [x] I agree\n")


@pytest.fixture()
def root(tmp_path, monkeypatch):
    (tmp_path / "manimate/components/community").mkdir(parents=True)
    shutil.copy(ROOT / "catalog.json", tmp_path / "catalog.json")
    monkeypatch.setattr(cfi, "ROOT", tmp_path)
    return tmp_path


def test_parse_form_and_unfence():
    s = cfi.parse_form(form())
    assert s["Component name"] == "pipeline_steps"
    assert cfi.unfence(s["Python code"]).startswith('"""TEMPLATE')
    assert cfi.parse_form(form(tests="_No response_"))["Test code (optional)"] == ""


def test_a_good_submission_writes_the_files(root):
    r = cfi.process(form(tests="```python\ndef test_x():\n    assert 1\n```"))
    assert r["ok"], r["errors"]
    assert (root / "manimate/components/community/pipeline_steps.py").exists()
    assert (root / "tests/community/test_pipeline_steps.py").exists()
    assert r["teaches"] == "Stages of a process."


@pytest.mark.parametrize("mutate,expect", [
    (lambda c: "import os\n" + c, "not allowed"),
    (lambda c: c + "\neval('1')\n", "eval"),
    (lambda c: c.replace('"pipeline_steps"', '"other_name"', 1), "must match"),
    (lambda c: "def broken(:\n", "syntax"),
    (lambda c: "x = 1\n", "No `@component"),
])
def test_bad_submissions_are_rejected_without_writing(root, mutate, expect):
    r = cfi.process(form(code=mutate(TEMPLATE.replace("step_chain", "pipeline_steps"))))
    assert not r["ok"] and any(expect in e for e in r["errors"]), r["errors"]
    assert not list((root / "manimate/components/community").glob("*.py"))


def test_names_must_be_valid_and_unused(root):
    assert not cfi.process(form(name="Bad-Name"))["ok"]
    r = cfi.process(form(name="callout"))
    assert not r["ok"] and any("already exists" in e for e in r["errors"])


def test_bad_tests_are_rejected(root):
    r = cfi.process(form(tests="```python\nimport subprocess\n```"))
    assert not r["ok"] and any("subprocess" in e for e in r["errors"])


@pytest.mark.parametrize(("src", "expected"), [
    ('@component("demo_thing")\ndef demo(): pass',
     ["demo_thing"]),
    ('@component(name="demo_thing")\ndef demo(): pass',
     ["demo_thing"]),
    ('@component("first")\ndef first(): pass\n'
     '@component(name="second")\ndef second(): pass',
     ["first", "second"]),
    ('@component(123)\ndef demo(): pass',
     ["<not a plain string>"]),
    ('@component(name=123)\ndef demo(): pass',
     ["<not a plain string>"]),
    ('@component("demo_thing")\ndef demo(): pass\n'
     '@component(name=123)\ndef second(): pass',
     ["demo_thing", "<not a plain string>"]),
])
def test_declared_names(src, expected):
    assert cfi.declared_names(src) == expected
