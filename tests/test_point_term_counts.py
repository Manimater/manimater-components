import pytest

from manimate.components.general import (
    _validate_bullet_count,
    _validate_term_count,
    bullet_points,
    equation,
)


@pytest.mark.parametrize("count", range(1, 7))
def test_valid_bullet_count(count):
    assert _validate_bullet_count(["Point"] * count) is None


@pytest.mark.parametrize("count", [0, 7, 8, 9])
def test_invalid_bullet_count(count):
    assert _validate_bullet_count(["Point"] * count)


@pytest.mark.parametrize("count", range(7))
def test_valid_term_count(count):
    assert _validate_term_count(["Term"] * count) is None


@pytest.mark.parametrize("count", [7, 8, 9])
def test_invalid_term_count(count):
    assert _validate_term_count(["Term"] * count)


@pytest.mark.parametrize("count", [0, 7, 8])
def test_bullet_renderer_rejects_invalid_count(count):
    with pytest.raises(ValueError, match="1 to 6 points"):
        bullet_points(None, "Heading", ["Point"] * count)


@pytest.mark.parametrize("count", [7, 8])
def test_equation_renderer_rejects_invalid_count(count):
    with pytest.raises(ValueError, match="at most 6 terms"):
        equation(None, "x+y=z", terms=["Term"] * count)
