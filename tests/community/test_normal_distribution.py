import math

import pytest

from manimate.components.community.normal_distribution import (
    normal_density,
    band_probability,
    _valid_mean,
    _valid_std,
)


@pytest.mark.parametrize(
    "k, expected",
    [
        (0, 0),
        (1, 0.682689492),
        (2, 0.954499736),
        (3, 0.997300204),
    ],
)
def test_band_probability(k, expected):
    assert band_probability(k) == pytest.approx(expected)


def test_standard_normal_peak():
    assert normal_density(0, 0, 1) == pytest.approx(
        1 / math.sqrt(2 * math.pi)
    )


def test_density_symmetry():
    assert normal_density(3, 5, 2) == pytest.approx(
        normal_density(7, 5, 2)
    )


def test_mean_shifts_curve():
    assert normal_density(10, 10, 1) == pytest.approx(
        normal_density(0, 0, 1)
    )


def test_larger_deviation_lowers_peak():
    assert normal_density(0, 0, 2) < normal_density(0, 0, 1)


@pytest.mark.parametrize(
    "std_dev", [0, -1, math.inf, -math.inf, math.nan]
)
def test_invalid_deviation(std_dev):
    assert _valid_std(std_dev) is not None

    with pytest.raises(ValueError):
        normal_density(0, 0, std_dev)


@pytest.mark.parametrize("mean", [math.inf, -math.inf, math.nan])
def test_invalid_mean(mean):
    assert _valid_mean(mean) is not None


@pytest.mark.parametrize("std_dev", [1e-12, 1e12])
def test_extreme_deviation(std_dev):
    result = normal_density(0, 0, std_dev)
    assert math.isfinite(result)
    assert result > 0


@pytest.mark.parametrize("mean", [-1e100, 1e100])
def test_large_mean(mean):
    assert normal_density(mean, mean, 1) == pytest.approx(
        normal_density(0, 0, 1)
    )


@pytest.mark.parametrize("k", [-1, math.inf, math.nan])
def test_invalid_band(k):
    with pytest.raises(ValueError):
        band_probability(k)
