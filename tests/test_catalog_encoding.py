import json
import sys

from manimate import catalog


def test_catalog_utf8_lf_output(tmp_path, monkeypatch):
    data = [{"name": "example", "description": "π → 中文"}]
    target = tmp_path / "catalog.json"

    monkeypatch.setattr(catalog, "build_catalog", lambda: data)
    monkeypatch.setattr(
        sys, "argv", ["manimate-catalog", "--out", str(target)]
    )

    assert catalog.main() == 0

    raw = target.read_bytes()
    expected = json.dumps(data, indent=2, ensure_ascii=False) + "\n"

    assert raw == expected.encode("utf-8")
    assert b"\r\n" not in raw
    assert not raw.startswith(b"\xef\xbb\xbf")
    assert json.loads(raw.decode("utf-8")) == data


def test_catalog_stdout_compatibility(monkeypatch, capsys):
    data = [{"name": "example", "description": "π →"}]

    monkeypatch.setattr(catalog, "build_catalog", lambda: data)
    monkeypatch.setattr(sys, "argv", ["manimate-catalog"])

    assert catalog.main() == 0
    assert capsys.readouterr().out == (
        json.dumps(data, indent=2, ensure_ascii=False) + "\n"
    )
