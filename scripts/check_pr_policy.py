"""Pull-request policy: the rules CI cannot see in the code itself. Stdlib only; it never imports or runs the PR's code.

    python scripts/check_pr_policy.py --base origin/main --head HEAD \\
        --head-ref component/binary_heap --title "feat(community): add binary_heap" --body-file body.md

Rules (see CONTRIBUTING.md for the human version):
  1. The title is a Conventional Commit: ``type(scope): summary``.
  2. A NEW component is pushed from a branch named ``component/<name>``, one component per pull request, and the branch
     carries that component and nothing else (its test, the regenerated catalog/docs, and plugin wiring if it needs one).
  3. A new component by a person also adds ``tests/community/test_<name>.py`` and answers the five design questions.
  4. No checklist box is left unticked (the "New component only" section is skipped for other pull requests).
  5. No added binaries, media, secrets or files over 1 MB (``assets/`` is the one place for images).

Bots (the issue-to-pull-request bot, Dependabot) are exempt from rules 3 and 4. A maintainer can bypass everything with
the ``policy-override`` label.
"""
from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
from pathlib import Path

COMMUNITY = "manimate/components/community/"
TESTS = "tests/community/"
NAME_RE = r"[a-z][a-z0-9_]{2,40}"
NAME_FULL = re.compile(NAME_RE)
TITLE_RE = re.compile(r"^(feat|fix|docs|chore|test|ci|refactor|build|perf|revert)(\([a-z0-9_./-]+\))?!?: \S.{3,}$")
GENERATED = {"catalog.json", "docs/LLM_PROMPT.md", "skills/manimater-components/references/catalog.md"}
PLUGIN_WIRING = {"manimate/plugins.py", "scripts/install_plugins.sh", "docs/THIRD_PARTY.md"}
BANNED_SUFFIX = {".mp4", ".mov", ".webm", ".avi", ".gif", ".png", ".jpg", ".jpeg", ".zip", ".tar", ".gz", ".whl", ".so",
                 ".dll", ".exe", ".pyc", ".pem", ".key", ".p12"}
SECRET_NAMES = {".env", "id_rsa", "id_ed25519", ".npmrc", ".pypirc"}
MAX_BYTES = 1_000_000
QUESTIONS = ("Teaches", "Params", "Layout", "Beats", "Failure cases")
BOTS = {"github-actions[bot]", "dependabot[bot]"}


def new_components(changes: list[tuple[str, str]]) -> list[str]:
    out = []
    for status, path in changes:
        m = re.fullmatch(re.escape(COMMUNITY) + r"([a-z0-9_]+)\.py", path)
        if status == "A" and m and not m.group(1).startswith("_"):
            out.append(m.group(1))
    return out


def strip_comments(text: str) -> str:
    return re.sub(r"<!--.*?-->", "", text, flags=re.S)


def unticked(body: str, skip_component_section: bool) -> list[str]:
    boxes: list[str] = []
    for part in re.split(r"(?m)^(?=#{1,3} )", strip_comments(body)):
        heading = part.splitlines()[0] if part.strip() else ""
        if skip_component_section and "new component" in heading.lower():
            continue
        boxes += [m.group(1).strip() for m in re.finditer(r"(?m)^\s*[-*] \[ \] (.+)$", part)]
    return boxes


def unanswered(body: str) -> list[str]:
    text, missing = strip_comments(body), []
    for q in QUESTIONS:
        m = re.search(rf"\*\*{re.escape(q)}:?\*\*:?[ \t]*(.*?)(?=\n[ \t]*\n|\n[ \t]*[-*] |\n#|\Z)", text, flags=re.S | re.I)
        if not m or len(m.group(1).strip()) < 8:
            missing.append(q)
    return missing


def evaluate(*, head_ref: str, title: str, body: str, author: str, changes: list[tuple[str, str]],
             sizes: dict[str, int] | None = None, labels: tuple[str, ...] = ()) -> list[str]:
    """Return the list of policy violations (empty means the pull request is fine)."""
    if "policy-override" in labels:
        return []
    errors: list[str] = []
    bot = author in BOTS
    sizes = sizes or {}
    paths = [p for _, p in changes]

    if author != "dependabot[bot]" and (len(title) > 100 or not TITLE_RE.match(title)):
        errors.append(f"Title {title!r} must look like `type(scope): summary` (types: feat, fix, docs, chore, test, ci, refactor, build, "
                      "perf, revert; at most 100 characters). New components use `feat(community): add <name>`.")

    added = new_components(changes)
    if len(added) > 1:
        errors.append(f"This pull request adds {len(added)} components ({', '.join(added)}). Open one pull request per component, "
                      "each from its own `component/<name>` branch.")
    if len(added) == 1:
        name = added[0]
        if not re.fullmatch(rf"component/(issue-[0-9]+-)?{re.escape(name)}", head_ref):
            errors.append(f"A new component must be pushed from a branch named `component/{name}`, but this one is `{head_ref}`. "
                          f"Fix: `git switch -c component/{name}`, push it, and open the pull request from that branch.")
        if not NAME_FULL.fullmatch(name):
            errors.append(f"Component name {name!r} must be snake_case (3 to 41 characters).")
        if not title.startswith(f"feat(community): add {name}") and author != "dependabot[bot]":
            errors.append(f"A new component's title must start with `feat(community): add {name}`.")
        if not bot:
            if f"{TESTS}test_{name}.py" not in paths:
                errors.append(f"Add `{TESTS}test_{name}.py`: unit tests for the component's plain-Python logic and its edge cases.")
            missing = unanswered(body)
            if missing:
                errors.append("Answer the design questions in the description: " + ", ".join(missing) + ".")

    if head_ref.startswith("component/"):
        stem = re.sub(r"^component/(issue-[0-9]+-)?", "", head_ref)
        if not added:
            errors.append("A `component/*` branch is only for adding a new component. Rename the branch (for example `fix/<topic>`) or "
                          "add the component file.")
        else:
            allowed = {f"{COMMUNITY}{stem}.py", f"{TESTS}test_{stem}.py"} | GENERATED | PLUGIN_WIRING
            extra = sorted(p for p in paths if p not in allowed)
            if extra:
                errors.append("A component branch carries one component and nothing else. Move these to their own pull request: "
                              + ", ".join(f"`{p}`" for p in extra[:8]) + (" ..." if len(extra) > 8 else ""))
            if stem != added[0]:
                errors.append(f"The branch is for `{stem}` but the pull request adds `{added[0]}`. They must match.")

    for p in paths:
        suffix, base = Path(p).suffix.lower(), Path(p).name
        if base in SECRET_NAMES or suffix in {".pem", ".key", ".p12"}:
            errors.append(f"`{p}` looks like a secret or key. Remove it from the history, and rotate it if it was real.")
        elif suffix in BANNED_SUFFIX and not p.startswith("assets/"):
            errors.append(f"`{p}`: binaries and media do not belong in the repository (use `assets/` for README images only).")
        elif sizes.get(p, 0) > MAX_BYTES and p != "catalog.json":
            errors.append(f"`{p}` is {sizes[p] // 1000} kB. Files over 1 MB are not accepted.")

    if not bot:
        plain = strip_comments(body).strip()
        if len(re.sub(r"#+ .*|[-*] \[[ xX]\].*", "", plain).strip()) < 20:
            errors.append("Describe what this changes and why in the pull request description.")
        left = unticked(body, skip_component_section=not added)
        if left:
            errors.append("Tick every checklist box (only once it is true): " + "; ".join(f"“{b[:60]}”" for b in left[:6])
                          + (" ..." if len(left) > 6 else ""))
    return errors



def git(*args: str) -> str:
    return subprocess.run(["git", *args], check=True, capture_output=True, text=True).stdout


def collect(base: str, head: str) -> tuple[list[tuple[str, str]], dict[str, int]]:
    raw = git("diff", "--name-status", "--no-renames", f"{base}...{head}")
    changes = [(line.split("\t")[0][0], line.split("\t", 1)[1]) for line in raw.splitlines() if "\t" in line]
    sizes = {}
    for status, path in changes:
        if status != "D":
            try:
                sizes[path] = int(git("cat-file", "-s", f"{head}:{path}").strip())
            except subprocess.CalledProcessError:
                pass
    return changes, sizes


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--head-ref", required=True)
    ap.add_argument("--title", required=True)
    ap.add_argument("--body-file", default="")
    ap.add_argument("--author", default="")
    ap.add_argument("--labels", default="", help="comma-separated")
    a = ap.parse_args(argv)
    body = Path(a.body_file).read_text(encoding="utf-8") if a.body_file and Path(a.body_file).exists() else ""
    changes, sizes = collect(a.base, a.head)
    errors = evaluate(head_ref=a.head_ref, title=a.title, body=body, author=a.author, changes=changes, sizes=sizes,
                      labels=tuple(x.strip() for x in a.labels.split(",") if x.strip()))
    for e in errors:
        print(f"::error title=PR policy::{e}")
    summary = os.environ.get("GITHUB_STEP_SUMMARY")
    if summary:
        with open(summary, "a") as f:
            f.write("## PR policy\n\n" + ("All rules satisfied.\n" if not errors else "".join(f"- ❌ {e}\n" for e in errors))
                    + "\nThe rules are explained in CONTRIBUTING.md.\n")
    print(f"PR policy: {'FAILED, ' + str(len(errors)) + ' problem(s)' if errors else 'ok'}")
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
