import argparse
import json
import pytest

from manimate.catalog import build_catalog, main
from manimate.preview import _validate_seconds


def test_catalog_main_emits_json_and_returns_success(capsys):
    assert main() == 0
    captured = capsys.readouterr()
    assert json.loads(captured.out) == build_catalog()
    assert captured.err == ""


@pytest.mark.parametrize("val", ["0", "-5", "nan", "inf", "-inf", "151", "abc"])
def test_preview_seconds_validation_rejects_invalid_values(val):
    with pytest.raises(argparse.ArgumentTypeError):
        _validate_seconds(val)


@pytest.mark.parametrize("val,expected", [("1", 1.0), ("8.0", 8.0), ("150", 150.0), ("4.5", 4.5)])
def test_preview_seconds_validation_accepts_valid_values(val, expected):
    assert _validate_seconds(val) == pytest.approx(expected)
