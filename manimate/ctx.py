"""Context handed to every component: a time budget plus small layout helpers."""
from __future__ import annotations

import shutil
import textwrap

from manim import DOWN, LEFT, ORIGIN, Mobject, Scene, Text, UP, VGroup

from . import theme

HAS_LATEX = bool(shutil.which("latex") and shutil.which("dvisvgm"))

# Usable stage area (the bottom ~1.2 units hold the caption).
STAGE_CENTER = (0.0, 0.55, 0.0)
STAGE_W = 12.4
STAGE_H = 5.8


def wrap(text: str, width: int) -> str:
    """Wrap each line separately, preserving explicit breaks and empty lines."""
    lines = []
    for line in text.split("\n"):
        lines.extend(textwrap.wrap(line, width=width) or [line])
    return "\n".join(lines)


def label(text: str, size: int = 28, color: str = theme.FG, width: int | None = None, align: str = "center", **kw) -> Mobject:
    """Text with optional word-wrap. Multi-line text is built line by line so it can be centred (Manim's Text is left-aligned)."""
    s = wrap(text, width) if width else text
    if "\n" not in s:
        return Text(s, font_size=size, color=color, **kw)
    lines = [Text(line, font_size=size, color=color, **kw) for line in s.split("\n")]
    return VGroup(*lines).arrange(DOWN, buff=size * 0.004, aligned_edge=LEFT if align == "left" else ORIGIN)


class Ctx:
    """Tracks how much of a scene's time budget the component has used."""

    def __init__(self, scene: Scene, duration: float):
        self.scene = scene
        self.duration = duration
        self.elapsed = 0.0

    @property
    def remaining(self) -> float:
        return max(0.0, self.duration - self.elapsed)

    def play(self, *anims, run_time: float = 1.0, **kw) -> None:
        run_time = max(0.1, float(run_time))
        self.scene.play(*anims, run_time=run_time, **kw)
        self.elapsed += run_time

    def wait(self, seconds: float) -> None:
        seconds = max(0.0, seconds)
        if seconds > 0.01:
            self.scene.wait(seconds)
            self.elapsed += seconds

    def add(self, *mobjects: Mobject) -> None:
        self.scene.add(*mobjects)

    def finish(self) -> None:
        self.wait(self.remaining)

    def fit(self, mob: Mobject, max_w: float = STAGE_W, max_h: float = STAGE_H,
            center: tuple[float, float, float] = STAGE_CENTER) -> Mobject:
        """Scale down (never up) to fit the stage, then centre."""
        factor = min(1.0, max_w / max(mob.width, 1e-6), max_h / max(mob.height, 1e-6))
        if factor < 1.0:
            mob.scale(factor)
        mob.move_to(center)
        return mob

    def heading(self, text: str) -> Text:
        h = label(text, 36, theme.ACCENT, width=60, weight="BOLD")
        h.move_to((0, 3.35, 0))
        if h.width > STAGE_W:
            h.scale_to_fit_width(STAGE_W)
        return h

    @staticmethod
    def beat(remaining: float, n: int, cap: float = 1.0, floor: float = 0.3) -> float:
        """Seconds per reveal when ``n`` items must share the remaining time."""
        if n <= 0:
            return cap
        return max(floor, min(cap, remaining / (n + 1)))
