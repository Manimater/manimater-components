"""The community folder: every non-underscore module is loaded, and every component in it passes the same checks."""
from __future__ import annotations

import importlib.util
import warnings
import pathlib

import pytest
from manim import FadeOut, Scene, tempconfig

from manimate import registry
from manimate.components import community, load_all
from manimate.components.community._safety import check_source
from manimate.ctx import Ctx

load_all()
COMMUNITY_DIR = pathlib.Path(community.__file__).parent
COMMUNITY = [c for c in registry.all_components() if c.fn.__module__.startswith("manimate.components.community.")]


def _dry_run(comp, params, seconds: float = 6.0) -> None:
    clean, errs = registry.validate_params(comp, params)
    assert not errs, errs
    with tempconfig({"dry_run": True, "disable_caching": True, "verbosity": "ERROR", "progress_bar": "none",
                     "write_to_movie": False, "frame_rate": 4}):
        scene = Scene()
        ctx = Ctx(scene, seconds)
        comp.fn(ctx, **clean)
        if ctx.overrun > 0.05:
            warnings.warn(
                f"{comp.name} exceeded its {seconds:.2f}s budget "
                f"by {ctx.overrun:.2f}s",
                RuntimeWarning,
                stacklevel=2,
            )
        scene.play(*[FadeOut(m) for m in scene.mobjects], run_time=0.5)


def test_underscore_modules_are_not_loaded():
    assert "template" not in {c.name for c in COMMUNITY}
    assert not any(c.fn.__module__.endswith("._template") for c in registry.all_components())


@pytest.mark.parametrize("comp", COMMUNITY, ids=lambda c: c.name)
def test_every_community_component_example_renders(comp):
    _dry_run(comp, comp.example)


@pytest.mark.parametrize("comp", COMMUNITY, ids=lambda c: c.name)
def test_community_components_keep_to_the_rules(comp):
    assert comp.name == comp.name.lower() and comp.name.replace("_", "").isalnum(), "name must be snake_case"
    assert 0 < len(comp.params) <= 5, "few params (at most 5)"
    assert len(comp.description) <= 200
    src = pathlib.Path(importlib.import_module(comp.fn.__module__).__file__).read_text()
    assert check_source(src) == []


def test_the_template_is_a_working_component():
    """_template.py is never imported by the library, so load it here under a throwaway registry entry."""
    spec = importlib.util.spec_from_file_location("manimate.components.community._template_under_test", COMMUNITY_DIR / "_template.py")
    mod = importlib.util.module_from_spec(spec)
    mod.__package__ = "manimate.components.community"
    spec.loader.exec_module(mod)
    comp = registry.get("step_chain")
    try:
        assert comp is not None
        _dry_run(comp, comp.example)
        _dry_run(comp, {"steps": ["a", "b"]}, seconds=4.0)
        assert mod._clean_steps(["  one ", "", "two", "x" * 40])[2] == "x" * 24
    finally:
        registry._REGISTRY.pop("step_chain", None)


def test_the_template_passes_the_static_check():
    assert check_source((COMMUNITY_DIR / "_template.py").read_text()) == []


@pytest.mark.parametrize("bad", [
    "import os",
    "import subprocess",
    "from urllib import request",
    "eval('1+1')",
    "exec('x=1')",
    "open('/etc/passwd')",
    "x = ().__class__.__bases__",
    "import numpy as np\nnp.os.system('ls')",
    "import numpy as np\nnp.load('/etc/passwd', allow_pickle=True)",
    "import numpy as np\nnp.savetxt('out.txt', [1])",
    "from manim import ImageMobject\nImageMobject('secret.png')",
    "from manim import SVGMobject\nSVGMobject('/etc/hostname')",
    "from manim import config\nconfig.media_dir = '/tmp'",
    "from manim import Code\nCode(code_file='/etc/passwd')",
    "x = __builtins__",
    "def f(:\n pass",
])
def test_the_static_check_rejects_unsafe_code(bad):
    assert check_source(bad)


@pytest.mark.parametrize("src", [
    "f = open\nf('/etc/passwd')",                                   # a banned builtin used through an alias
    "e = eval\ne('1')",
    "fs = [open, eval]\nfs[0]('x')",                                # ... or stored somewhere
    "import manim\nmanim.config.media_dir = '/tmp'",                # a banned Manim name reached as an attribute
    "import manim\nm = manim.ImageMobject('x.png')",
    "import manim\nm = manim.SVGMobject('x.svg')",
    "from manim import ImageMobject as I\nI('x.png')",              # ... or imported under another name
    "from manim import config as c\nc.media_dir = '/x'",
])
def test_safety_check_blocks_aliases_and_attributes(src):
    assert check_source(src), f"should have been blocked: {src!r}"


def test_safety_check_only_blocks_using_a_banned_builtin_not_assigning_the_name():
    assert check_source("input = 3\n") == []                      # assigning is harmless
    assert check_source("input = 3\nprint_me = input\n")           # but reading it back is the builtin's name: rename it
