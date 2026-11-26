"""Propose a merged change to the Manimater app: copy exactly the files the merge touched, under ``renderer/``.

    python scripts/sync_to_app.py --base HEAD^ --head HEAD --app-dir ../app --summary summary.md

Stdlib only; it only reads this repository's git history and writes into the app checkout it is given. It copies the
files the change added or modified and deletes the ones it removed, and nothing else, so app-only files next to them
are never touched. The paths come from ``.github/sync-paths.txt``. Prints ``changed=<n>`` for the workflow.
"""
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
PATHS_FILE = ".github/sync-paths.txt"
IGNORED_PARTS = {"__pycache__", ".pytest_cache"}
IGNORED_SUFFIX = {".pyc", ".pyo"}


def load_paths(text: str) -> list[str]:
    """The synced paths: one per line, ``#`` comments and blank lines ignored."""
    return [ln.strip() for ln in text.splitlines() if ln.strip() and not ln.strip().startswith("#")]


def is_synced(path: str, paths: list[str]) -> bool:
    p = Path(path)
    if IGNORED_PARTS & set(p.parts) or p.suffix in IGNORED_SUFFIX:
        return False
    return any(path == s or (s.endswith("/") and path.startswith(s)) for s in paths)


def select(changes: list[tuple[str, str]], paths: list[str]) -> list[tuple[str, str]]:
    return [(st, p) for st, p in changes if is_synced(p, paths)]


def target(path: str, dest_root: str) -> str:
    return f"{dest_root.strip('/')}/{path}" if dest_root.strip("/") else path


def apply(changes: list[tuple[str, str]], read_blob, app_dir: Path, dest_root: str) -> list[str]:
    """Write the changes into ``app_dir``; return one summary line per file. Refuses anything that escapes ``app_dir``."""
    lines = []
    base = app_dir.resolve()
    for status, path in changes:
        dest = (app_dir / target(path, dest_root)).resolve()
        if base not in dest.parents:
            raise ValueError(f"refusing to write outside the app checkout: {path}")
        if status == "D":
            if dest.exists():
                dest.unlink()
            lines.append(f"- removed `{target(path, dest_root)}`")
        else:
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_bytes(read_blob(path))
            lines.append(f"- {'added' if status == 'A' else 'updated'} `{target(path, dest_root)}`")
    return lines


def git(*args: str, text: bool = True):
    return subprocess.run(["git", "-C", str(ROOT), *args], check=True, capture_output=True, text=text).stdout


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("--base", required=True)
    ap.add_argument("--head", default="HEAD")
    ap.add_argument("--app-dir", required=True, help="a checkout of the app repository")
    ap.add_argument("--dest-root", default="renderer", help="folder in the app that mirrors this repository's root")
    ap.add_argument("--summary", default="", help="write the list of changed files (markdown) to this file")
    a = ap.parse_args(argv)

    paths = load_paths((ROOT / PATHS_FILE).read_text(encoding="utf-8"))
    raw = git("diff", "--name-status", "--no-renames", f"{a.base}", f"{a.head}")
    changes = [(ln.split("\t")[0][0], ln.split("\t", 1)[1]) for ln in raw.splitlines() if "\t" in ln]
    chosen = select(changes, paths)
    lines = apply(chosen, lambda p: git("show", f"{a.head}:{p}", text=False), Path(a.app_dir), a.dest_root)
    if a.summary:
        Path(a.summary).write_text("\n".join(lines) + "\n", encoding="utf-8", newline="\n")
    out = os.environ.get("GITHUB_OUTPUT")
    if out:
        with open(out, "a") as f:
            f.write(f"changed={len(lines)}\n")
    print(f"changed={len(lines)}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
