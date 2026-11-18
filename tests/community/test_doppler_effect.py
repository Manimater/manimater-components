import math

import pytest

from manimate.components.community.doppler_effect import (
    _frequency_ok,
    _observed_frequencies,
    _observed_wavelengths,
    _source_speed_ok,
    _speeds_ok,
    _wavefronts,
)


def test_stationary_source_has_no_frequency_shift():
    approaching, receding = _observed_frequencies(440, 0, 1)
    assert approaching == pytest.approx(440)
    assert receding == pytest.approx(440)


def test_approaching_observer_hears_higher_frequency():
    approaching, receding = _observed_frequencies(440, 0.2, 1)
    assert approaching > 440
    assert receding < 440


def test_frequency_equations_match_expected_values():
    approaching, receding = _observed_frequencies(100, 0.25, 1)
    assert approaching == pytest.approx(100 / 0.75)
    assert receding == pytest.approx(100 / 1.25)


def test_stationary_source_has_equal_wavelengths():
    ahead, behind = _observed_wavelengths(10, 0, 2)
    assert ahead == pytest.approx(0.2)
    assert behind == pytest.approx(0.2)


def test_moving_source_compresses_ahead_and_stretches_behind():
    ahead, behind = _observed_wavelengths(10, 0.5, 2)
    assert ahead < 2 / 10
    assert behind > 2 / 10
    assert behind > ahead


def test_wavefront_centres_follow_source_motion():
    fronts = _wavefronts(0.5, 1, 2.5, 1)
    assert [centre for centre, _ in fronts] == pytest.approx([0, 0.5, 1.0])
    assert [radius for _, radius in fronts] == pytest.approx([2.5, 1.5, 0.5])


def test_wavefronts_are_concentric_for_stationary_source():
    fronts = _wavefronts(0, 2, 2.5, 1)
    assert [centre for centre, _ in fronts] == pytest.approx([0, 0, 0])
    assert [radius for _, radius in fronts] == pytest.approx([5.0, 3.0, 1.0])


@pytest.mark.parametrize(
    ("source_speed", "wave_speed"),
    [
        (-0.1, 1),
        (1, 1),
        (1.1, 1),
        (0.1, 0),
        (0.1, -1),
        (math.inf, 1),
        (0.1, math.inf),
        (math.nan, 1),
    ],
)
def test_rejects_invalid_speeds(source_speed, wave_speed):
    assert _speeds_ok(source_speed, wave_speed) is not None
    with pytest.raises(ValueError):
        _observed_frequencies(440, source_speed, wave_speed)


@pytest.mark.parametrize("frequency", [0, -1, math.inf, math.nan])
def test_rejects_invalid_frequency(frequency):
    assert _frequency_ok(frequency) is not None
    with pytest.raises(ValueError):
        _observed_frequencies(frequency, 0.2, 1)


@pytest.mark.parametrize("source_speed", [-1, math.inf, math.nan])
def test_source_speed_validator_rejects_invalid_values(source_speed):
    assert _source_speed_ok(source_speed) is not None


def test_source_speed_validator_accepts_zero():
    assert _source_speed_ok(0) is None


@pytest.mark.parametrize("elapsed", [-1, math.inf, math.nan])
def test_rejects_invalid_elapsed_time(elapsed):
    with pytest.raises(ValueError):
        _wavefronts(0.2, 1, elapsed, 1)


@pytest.mark.parametrize("period", [0, -1, math.inf, math.nan])
def test_rejects_invalid_emission_period(period):
    with pytest.raises(ValueError):
        _wavefronts(0.2, 1, 2, period)


def test_first_wavefront_expands_after_initial_emission():
    assert _wavefronts(0.2, 1, 0.5, 1) == [(0.0, 0.5)]
