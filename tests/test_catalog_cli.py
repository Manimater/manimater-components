import json

from manimate.catalog import build_catalog, main


def test_catalog_main_emits_json_and_returns_success(capsys, monkeypatch):
    monkeypatch.setattr("sys.argv", ["manimate-catalog"])
    assert main() == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == build_catalog()
    assert captured.err == ""
