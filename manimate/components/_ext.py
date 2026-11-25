"""One generic adapter for the community library manim-extensions (https://github.com/ExploreMaths/manim_extensions, MIT).

The library ships dozens of ready-made Manim objects (economics diagrams, mind maps, gears, automata, queues, ...).
Writing a hand-made scene for each one would repeat the same boilerplate, so each is declared as an ``ExtSpec``:

* ``build(params)`` makes the library object and returns a ``Built``: the object itself (``stage``) plus a list of
  ``Beat``s, the things to *do* with it once it is on screen (shift a curve, enqueue an item, run a string through an
  automaton, ...).
* ``run`` is the only code that touches the scene. It writes the heading, scales and centres the object, fades it in
  as a whole, plays the beats one after another with a short on-screen note each, and uses the rest of the narration
  time to hold the finished picture.

Adding another object from the library is therefore one ``ExtSpec`` (see ``ext_economics.py``): no new scene code, and
the same timing, layout, credit and failure behaviour for all of them.

Rules every spec follows
* The library is imported inside ``build`` (through ``lib``), never at import time, so the registry, the catalog and
  storyboard validation work on a machine that does not have it. A missing library raises ``PluginMissing``.
  The renderer decides how to handle the missing plugin.
* A ``Beat.play`` is a function, not an animation, because many library methods change the diagram's state the moment
  they are called (``diagram.shift_ad(...)`` updates the stored curve). It is called when its beat starts.
* Only the declared, validated params reach ``build``. Nothing the planner writes is ever executed or imported.
"""
from __future__ import annotations

import sys
import traceback
from dataclasses import dataclass, field
from types import ModuleType
from typing import Any, Callable, Sequence, Union

from manim import DOWN, Animation, FadeIn, FadeOut, Mobject, Write

from .. import registry, theme
from ..ctx import Ctx, label
from ..registry import Param
from ._plugin import fit, require

PLUGIN = "manim-extensions"
_PIP = "manim-extensions"

Anims = Union[Animation, Sequence[Animation]]

# Where the object may sit: below the heading (y 3.35) and its note line, above the narration caption at the bottom.
STAGE_W = 12.0
STAGE_H = 4.5
STAGE_CENTER = (0.0, 0.1, 0.0)
NOTE_Y = 2.75  # the one-line note under the heading


def lib(sub: str = "") -> ModuleType:
    """Import ``manim_extensions`` (or one of its subpackages) at render time, or raise ``PluginMissing``."""
    return require("manim_extensions" + (f".{sub}" if sub else ""), _PIP)


@dataclass
class Beat:
    """One step after the picture is on screen."""

    play: Callable[[], Anims]  # called when the beat starts; returns one animation or a list to play in order
    note: str = ""  # short line shown under the heading while this beat plays
    weight: float = 1.0  # share of the beat time (a slow long-run adjustment can ask for more)


@dataclass
class Built:
    stage: Mobject
    beats: list[Beat] = field(default_factory=list)
    note: str = ""  # shown under the heading from the start
    max_w: float = STAGE_W
    max_h: float = STAGE_H
    max_scale: float = 1.0  # most the object is enlarged; 1.0 means it is only ever shrunk to fit
    reveal: Callable[[Mobject], Animation] | None = None  # default: fade the whole object in


@dataclass(frozen=True)
class ExtSpec:
    name: str
    description: str
    domain: str
    params: dict[str, Param]
    example: dict[str, Any]
    title: Callable[[dict[str, Any]], str]
    build: Callable[[dict[str, Any]], Built]


def _as_list(a: Anims | None) -> list[Animation]:
    if a is None:
        return []
    if isinstance(a, Animation):
        return [a]
    return [x for x in a if x is not None]


def _note(text: str) -> Mobject:
    n = label(text, 22, theme.MUTED, width=95)
    if n.width > STAGE_W:
        n.scale_to_fit_width(STAGE_W)
    n.move_to((0, NOTE_Y, 0))
    return n


def run(ctx: Ctx, spec: ExtSpec, raw: dict[str, Any]) -> None:
    params = {k: p.default for k, p in spec.params.items() if p.default is not None}
    params.update({k: v for k, v in raw.items() if v is not None})
    built = spec.build(params)

    head = ctx.heading(spec.title(params))
    fit(built.stage, built.max_w, built.max_h, STAGE_CENTER, built.max_scale)
    note = _note(built.note) if built.note else None

    ctx.play(Write(head), *([FadeIn(note)] if note else []), run_time=0.7)
    reveal = built.reveal(built.stage) if built.reveal else FadeIn(built.stage)
    ctx.play(reveal, run_time=min(1.3, max(0.5, ctx.remaining * 0.25)))

    beats = built.beats
    if beats:
        pool = max(0.0, ctx.remaining - 0.6)  # keep a short hold on the finished picture
        total_weight = sum(b.weight for b in beats)
        try:
            for b in beats:
                budget = max(0.5, pool * b.weight / total_weight)
                anims = _as_list(b.play())
                fresh = _note(b.note) if b.note else None
                swap: list[Animation] = []
                if fresh is not None:
                    swap = [FadeIn(fresh)] + ([FadeOut(note)] if note else [])
                for i, a in enumerate(anims):
                    ctx.play(a, *(swap if i == 0 else []), run_time=budget / len(anims))
                if not anims and swap:
                    ctx.play(*swap, run_time=min(0.5, budget))
                if fresh is not None:
                    note = fresh
        except Exception:  # keep the finished picture on screen for the rest of the narration rather than dropping to a callout
            traceback.print_exc(file=sys.stderr)
    ctx.wait(ctx.remaining)


def register(spec: ExtSpec) -> ExtSpec:
    """Register a spec as a storyboard component credited to manim-extensions."""

    def fn(ctx: Ctx, **params: Any) -> None:
        run(ctx, spec, params)

    fn.__name__ = spec.name
    fn.__qualname__ = spec.name
    registry.component(spec.name, spec.description, spec.params, spec.example, domain=spec.domain, plugin=PLUGIN)(fn)
    return spec


# ---------------------------------------------------------------------------------------------------------------
# Small shared helpers for the specs
# ---------------------------------------------------------------------------------------------------------------
def choose(value: Any, options: Sequence[str], default: str) -> str:
    return value if value in options else default


def clamp(value: Any, lo: float, hi: float, default: float) -> float:
    try:
        v = float(value)
    except (TypeError, ValueError):
        return default
    return max(lo, min(hi, v))


def plain_text_ok(text: str, max_len: int = 28) -> bool:
    """Labels are drawn with Manim's Text (no LaTeX), but keep them short and printable so nothing can run off stage."""
    return isinstance(text, str) and 0 < len(text.strip()) <= max_len and text.isprintable() and "\n" not in text


def split_labelled(items: Sequence[str]) -> list[tuple[str, list[str]]]:
    """``["Branch: a, b", "Other"]`` -> ``[("Branch", ["a", "b"]), ("Other", [])]``."""
    out: list[tuple[str, list[str]]] = []
    for raw in items:
        head, _, tail = raw.partition(":")
        subs = [s.strip() for s in tail.split(",") if s.strip()]
        out.append((head.strip(), subs))
    return out
