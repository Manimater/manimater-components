"""The pull-request policy: component branches, one component per PR, title, body and file hygiene."""
from __future__ import annotations

import importlib.util
import pathlib

import pytest

ROOT = pathlib.Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location("check_pr_policy", ROOT / "scripts" / "check_pr_policy.py")
pol = importlib.util.module_from_spec(spec)
spec.loader.exec_module(pol)

ANSWERS = "\n".join(f"- **{q}:** a real, specific answer for this" for q in pol.QUESTIONS)
BODY = f"""## What this changes

Adds a heap visualisation that shows sift-up and sift-down step by step.

## Checklist (every PR)

- [x] I ran the tests

## New component only

{ANSWERS}

- [x] I previewed it
"""
FILES = [("A", "manimate/components/community/binary_heap.py"), ("A", "tests/community/test_binary_heap.py"),
         ("M", "catalog.json"), ("M", "docs/LLM_PROMPT.md"), ("M", "skills/manimater-components/references/catalog.md")]


def run(**kw):
    args = dict(head_ref="component/binary_heap", title="feat(community): add binary_heap visualization", body=BODY,
                author="someone", changes=FILES)
    args.update(kw)
    return pol.evaluate(**args)


def test_a_well_formed_component_pr_passes():
    assert run() == []


def test_new_component_from_the_wrong_branch_is_rejected():
    errs = run(head_ref="my-feature")
    assert len(errs) == 1 and "component/binary_heap" in errs[0]


def test_the_issue_bot_branch_is_accepted():
    assert run(head_ref="component/issue-12-binary_heap", author="github-actions[bot]", body="") == []


def test_branch_name_must_match_the_component():
    assert any("must match" in e or "component/binary_heap" in e for e in run(head_ref="component/other_name"))


def test_one_component_per_pr():
    errs = run(changes=FILES + [("A", "manimate/components/community/sql_join.py")])
    assert any("one pull request per component" in e for e in errs)


def test_component_branch_must_not_carry_other_changes():
    errs = run(changes=FILES + [("M", "manimate/registry.py"), ("M", ".github/workflows/ci.yml")])
    assert any("nothing else" in e and "registry.py" in e for e in errs)


def test_component_branch_without_a_new_component_is_rejected():
    errs = run(head_ref="component/binary_heap", changes=[("M", "README.md")], title="docs: fix a typo in the readme")
    assert any("only for adding a new component" in e for e in errs)


def test_person_must_add_tests_and_answer_the_five_questions():
    errs = run(changes=[c for c in FILES if "tests/" not in c[1]], body=BODY.replace("a real, specific answer for this", ""))
    assert any("test_binary_heap.py" in e for e in errs)
    assert any("design questions" in e and "Teaches" in e and "Failure cases" in e for e in errs)


def test_bot_is_exempt_from_tests_body_and_boxes():
    assert run(author="github-actions[bot]", body="", head_ref="component/issue-3-binary_heap",
               changes=[c for c in FILES if "tests/" not in c[1]]) == []


@pytest.mark.parametrize("title", ["Add a thing", "feat: x", "feature(community): add binary_heap", "feat(community):add binary_heap",
                                   "feat(community): add binary_heap " + "x" * 100])
def test_bad_titles(title):
    assert any("Title" in e or "title" in e for e in run(title=title))


def test_component_title_names_the_component():
    assert any("must start with" in e for e in run(title="feat(community): add heap_viz"))


def test_unticked_boxes_fail_but_other_prs_skip_the_component_section():
    assert any("Tick every" in e for e in run(body=BODY.replace("[x] I ran", "[ ] I ran")))
    other = BODY.replace("- [x] I previewed it", "- [ ] I previewed it")
    assert pol.evaluate(head_ref="fix/typo", title="fix: correct a typo in a docstring", body=other, author="x",
                        changes=[("M", "manimate/theme.py")]) == []


def test_empty_description_is_rejected():
    assert any("Describe" in e for e in pol.evaluate(head_ref="fix/x", title="fix: handle empty lists", body="<!-- hi -->", author="x",
                                                      changes=[("M", "manimate/theme.py")]))


def test_binaries_secrets_and_big_files():
    changes = [("M", "manimate/theme.py"), ("A", "demo.mp4"), ("A", ".env"), ("A", "assets/gifs/new.gif"), ("A", "data.bin")]
    errs = pol.evaluate(head_ref="fix/x", title="fix: tidy things up", body=BODY, author="x", changes=changes,
                        sizes={"data.bin": 2_000_000, "catalog.json": 9_000_000})
    text = "\n".join(errs)
    assert "demo.mp4" in text and ".env" in text and "data.bin" in text
    assert "assets/gifs/new.gif" not in text and "catalog.json" not in text


def test_maintainer_override_label():
    assert run(head_ref="whatever", title="x", body="", labels=("policy-override",)) == []


def test_dependabot_titles_are_not_policed():
    assert pol.evaluate(head_ref="dependabot/pip/x", title="Bump manim from 0.19 to 0.20", body="", author="dependabot[bot]",
                        changes=[("M", "pyproject.toml")]) == []


@pytest.mark.parametrize("path", [
    "audio.mp3", "audio.wav", "audio.ogg", "audio.flac", "audio.m4a",
    "video.mkv", "image.webp", "image.bmp", "image.tif",
    "image.tiff", "image.heic", "image.ico",
    "archive.7z", "archive.rar", "archive.bz2", "archive.xz",
    "archive.jar", "document.pdf", "library.dylib",
    "data.npy", "data.npz", "model.pkl", "model.pt",
    "model.onnx", "model.h5", "audio.MP3",
])
def test_additional_binary_formats_are_rejected(path):
    errs = pol.evaluate(
        head_ref="fix/x", title="fix: tidy things up",
        body=BODY, author="x", changes=[("A", path)],
        sizes={path: 100},
    )
    assert any(path in e and "binaries and media" in e for e in errs)


@pytest.mark.parametrize("path", [
    ".env.local", ".env.production", "config/.env.dev",
    "id_ecdsa", "id_dsa", "credentials.json",
    ".netrc", ".git-credentials",
    "certificate.pfx", "private.p8", "app.keystore",
    "assets/private.pfx", "config/.ENV.LOCAL",
])
def test_additional_secret_files_are_rejected(path):
    errs = pol.evaluate(
        head_ref="fix/x", title="fix: tidy things up",
        body=BODY, author="x", changes=[("A", path)],
    )
    assert any(path in e and "secret or key" in e for e in errs)
