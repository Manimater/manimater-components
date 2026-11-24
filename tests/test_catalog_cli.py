import json
from pathlib import Path
from unittest.mock import MagicMock

from manimate import registry
from manimate.catalog import build_catalog, main
import manimate.preview as preview_mod


def test_catalog_main_emits_json_and_returns_success(capsys):
    assert main() == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == build_catalog()
    assert captured.err == ""


def test_preview_render_passes_empty_params_in_env(monkeypatch, tmp_path):
    recorded_env = {}

    def fake_run(cmd, env=None, capture_output=True, text=True):
        recorded_env.clear()
        recorded_env.update(env or {})
        for idx, arg in enumerate(cmd):
            if arg == "--media_dir" and idx + 1 < len(cmd):
                media_dir = Path(cmd[idx + 1])
                fake_mp4 = media_dir / "title_card.mp4"
                fake_mp4.parent.mkdir(parents=True, exist_ok=True)
                fake_mp4.write_text("fake video", encoding="utf-8")
                break
        res = MagicMock()
        res.returncode = 0
        res.stderr = ""
        return res

    monkeypatch.setattr(preview_mod.subprocess, "run", fake_run)

    preview_mod.render("title_card", params={}, out=tmp_path)
    assert recorded_env.get("MANIMATER_PARAMS") == "{}"

    preview_mod.render("title_card", params=None, out=tmp_path)
    assert recorded_env.get("MANIMATER_PARAMS") == ""


def test_preview_scene_construct_uses_defaults_when_empty_params(monkeypatch):
    recorded = []

    @registry.component(
        "_test_preview_defaults", "Test component",
        {"val": registry.Param("string", "desc", default="default_value")},
        {"val": "example_value"},
    )
    def _test_comp_fn(ctx, val):
        recorded.append(val)

    scene = preview_mod.PreviewScene.__new__(preview_mod.PreviewScene)
    monkeypatch.setattr(preview_mod.PreviewScene, "camera", MagicMock())

    monkeypatch.setenv("MANIMATER_COMPONENT", "_test_preview_defaults")
    monkeypatch.setenv("MANIMATER_PARAMS", "{}")
    monkeypatch.setattr(preview_mod, "Ctx", lambda self, sec: MagicMock())

    scene.construct()
    assert recorded == ["default_value"]

    recorded.clear()
    monkeypatch.setenv("MANIMATER_PARAMS", "")
    scene.construct()
    assert recorded == ["example_value"]


def test_preview_cli_empty_params(monkeypatch, tmp_path):
    rendered_params = []

    monkeypatch.setattr(
        preview_mod, "render",
        lambda name, params, seconds, quality, out: (rendered_params.append(params), tmp_path / f"{name}.mp4")[1]
    )

    preview_mod.main(["title_card", "--params", "{}"])
    assert rendered_params == [{}]

    rendered_params.clear()
    preview_mod.main(["title_card"])
    assert rendered_params == [None]
