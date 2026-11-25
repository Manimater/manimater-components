"""Helpers shared by the packs that wrap community Manim plugins.

The plugins are optional at import time: a pack imports its plugin inside the component function (through
``require``), so the registry, the catalog and storyboard validation work even on a machine that does not have
the plugins installed. If a plugin is missing at render time, ``PluginMissing`` is raised.
The renderer decides how to handle the missing plugin.

Plugin versions used by CI are pinned in scripts/install_plugins.sh.
"""
from __future__ import annotations

import contextlib
import importlib
import io
import typing
from types import ModuleType
from typing import Iterator

from manim import AnimationGroup, Mobject, Wait

from ..ctx import STAGE_CENTER, STAGE_H, STAGE_W


class PluginMissing(RuntimeError):
    """A community plugin is not installed (or fails to import) in this renderer."""


def _backport_typing() -> None:
    """manim-dsa 0.4.0 does ``from typing import override``, which only exists on Python 3.12+. The renderer image runs
    3.11, so provide it from typing_extensions (a dependency of Manim) before the plugin is imported."""
    if not hasattr(typing, "override"):
        import typing_extensions

        typing.override = typing_extensions.override  # type: ignore[attr-defined]


def require(module: str, pip_name: str) -> ModuleType:
    _backport_typing()
    try:
        return importlib.import_module(module)
    except Exception as e:  # noqa: BLE001 - any import failure means the component cannot run
        raise PluginMissing(f"{pip_name} is not available in this renderer ({type(e).__name__}: {e})") from e


def fit(mob: Mobject, max_w: float = STAGE_W, max_h: float = STAGE_H,
        center: tuple[float, float, float] = STAGE_CENTER, max_scale: float = 4.0) -> Mobject:
    """Scale to fill the stage (up *or* down, up to ``max_scale``), then centre.

    ``Ctx.fit`` only ever shrinks, but plugin objects are often built small (a neural network is about 2 units wide).
    """
    factor = min(max_scale, max_w / max(mob.width, 1e-6), max_h / max(mob.height, 1e-6))
    mob.scale(factor)
    mob.move_to(center)
    return mob


@contextlib.contextmanager
def quiet() -> Iterator[None]:
    """Swallow stdout while a plugin builds objects (ManimML prints debug lines)."""
    with contextlib.redirect_stdout(io.StringIO()):
        yield


@contextlib.contextmanager
def tolerate_empty_groups() -> Iterator[None]:
    """ManimML builds empty ``AnimationGroup()`` placeholders, which Manim 0.19+ refuses to play.

    While active, an ``AnimationGroup`` created with no animations gets a near-zero ``Wait`` instead.
    """
    original = AnimationGroup.__init__

    def patched(self, *animations, **kwargs):
        if not animations and "group" not in kwargs:
            animations = (Wait(0.01),)
        original(self, *animations, **kwargs)

    AnimationGroup.__init__ = patched  # type: ignore[method-assign]
    try:
        yield
    finally:
        AnimationGroup.__init__ = original  # type: ignore[method-assign]
