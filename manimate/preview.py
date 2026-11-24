"""Render one component to an MP4, so you can see what you built.

    python -m manimate.preview step_chain
    python -m manimate.preview bar_chart --params '{"labels": ["a", "b"], "values": [3, 5]}' --seconds 8 --quality medium
    python -m manimate.preview --list

With no ``--params`` the component's own ``example`` is used. The video lands in ``./previews/<name>.mp4``
(change it with ``--out``). Needs Manim's system packages (ffmpeg, Cairo, Pango); LaTeX only for components that use it.
"""
from __future__ import annotations

import argparse
import json
import math
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

from manim import Scene

from manimate import registry, theme
from manimate.components import load_all
from manimate.ctx import Ctx

QUALITY_FLAGS = {"low": "-ql", "medium": "-qm", "high": "-qh"}


class PreviewScene(Scene):
    """Plays the component named in ``MANIMATER_COMPONENT`` with the JSON params in ``MANIMATER_PARAMS``."""

    def construct(self) -> None:
        load_all()
        comp = registry.get(os.environ["MANIMATER_COMPONENT"])
        params = json.loads(os.environ.get("MANIMATER_PARAMS") or "null") or comp.example
        clean, errors = registry.validate_params(comp, params)
        if errors:
            raise SystemExit("invalid params: " + "; ".join(errors))
        self.camera.background_color = theme.BG
        ctx = Ctx(self, float(os.environ.get("MANIMATER_SECONDS", "8")))
        comp.fn(ctx, **clean)
        ctx.finish()


def render(name: str, params: dict | None = None, seconds: float = 8.0, quality: str = "low", out: Path = Path("previews")) -> Path:
    load_all()
    if registry.get(name) is None:
        raise SystemExit(f"unknown component {name!r}. Run with --list to see them all.")
    out.mkdir(parents=True, exist_ok=True)
    env = {**os.environ, "MANIMATER_COMPONENT": name, "MANIMATER_SECONDS": str(seconds),
           "MANIMATER_PARAMS": json.dumps(params) if params else "",
           "PYTHONPATH": os.pathsep.join(filter(None, [str(Path(__file__).resolve().parents[1]), os.environ.get("PYTHONPATH", "")]))}
    with tempfile.TemporaryDirectory() as tmp:
        cmd = [sys.executable, "-m", "manim", "render", QUALITY_FLAGS[quality], "--media_dir", tmp, "-o", name,
               str(Path(__file__).resolve()), "PreviewScene"]
        proc = subprocess.run(cmd, env=env, capture_output=True, text=True)
        videos = sorted(Path(tmp).rglob(f"{name}.mp4"))
        if proc.returncode != 0 or not videos:
            sys.stderr.write(proc.stderr[-3000:])
            raise SystemExit(f"rendering {name} failed")
        if "Traceback" in proc.stderr:  # the component raised; Manim still exits 0 in some cases
            sys.stderr.write(proc.stderr[-3000:])
            raise SystemExit(f"{name} raised an error while rendering")
        target = out / f"{name}.mp4"
        shutil.copyfile(videos[0], target)
    return target


def _validate_seconds(val: str) -> float:
    try:
        f = float(val)
    except ValueError:
        raise argparse.ArgumentTypeError(f"seconds must be a valid number (got {val!r})")
    if not math.isfinite(f) or f < 1.0 or f > 150.0:
        raise argparse.ArgumentTypeError(f"seconds must be a finite number between 1 and 150 (got {val!r})")
    return f


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="python -m manimate.preview", description=__doc__.split("\n\n")[0])
    ap.add_argument("name", nargs="?", help="component name")
    ap.add_argument("--list", action="store_true", help="list every component and exit")
    ap.add_argument("--params", help="JSON object of params (default: the component's example)")
    ap.add_argument("--seconds", type=_validate_seconds, default=8.0, help="scene length in seconds (default 8)")
    ap.add_argument("--quality", choices=sorted(QUALITY_FLAGS), default="low")
    ap.add_argument("--out", type=Path, default=Path("previews"))
    args = ap.parse_args(argv)
    load_all()
    if args.list or not args.name:
        for c in registry.all_components():
            print(f"{c.name:28} {c.domain:18} {c.description}")
        return 0
    print(render(args.name, json.loads(args.params) if args.params else None, args.seconds, args.quality, args.out))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
