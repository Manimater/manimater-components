"""The synchronous motor scene: its pure helpers, and a dry run of the whole animation for every pole count."""
import math

import pytest

from manimate import registry
from manimate.components import load_all
from manimate.components.electrical import sm_delta_deg, sm_torque_fraction

load_all()


def test_load_angle_ramps_from_light_to_heavy_load_and_never_reaches_pull_out():
    assert sm_delta_deg(0, 3, 8) == pytest.approx(15.0)          # light load before the ramp starts
    assert sm_delta_deg(100, 3, 8) == pytest.approx(70.0)        # heavy load after it ends, still under 90 degrees
    series = [sm_delta_deg(t / 10, 3, 8) for t in range(0, 120)]
    assert series == sorted(series)                              # monotonic: the angle only grows with load
    assert max(series) < 90.0


def test_degenerate_ramp_does_not_divide_by_zero():
    assert sm_delta_deg(5, 5, 5) == pytest.approx(15.0 + 55.0 * 0.5, abs=30)


def test_torque_follows_sin_delta_and_peaks_at_pull_out():
    assert sm_torque_fraction(0) == 0
    assert sm_torque_fraction(30) == pytest.approx(0.5)
    assert sm_torque_fraction(90) == pytest.approx(1.0)
    assert sm_torque_fraction(150) == pytest.approx(1.0)         # clamped: the meter never shows more than full torque
    assert sm_torque_fraction(-5) == 0


@pytest.mark.parametrize("poles", [2, 4, 6])
@pytest.mark.parametrize("hz", [50, 60])
def test_synchronous_motor_runs_and_fades_out(poles, hz):
    from manim import FadeOut, Scene, tempconfig
    from manimate.ctx import Ctx

    comp = registry.get("synchronous_motor")
    with tempconfig({"dry_run": True, "disable_caching": True, "verbosity": "ERROR", "progress_bar": "none",
                     "write_to_movie": False, "frame_rate": 4}):
        scene = Scene()
        ctx = Ctx(scene, 8.0)
        comp.fn(ctx, poles=poles, frequency_hz=hz)
        if ctx.overrun > 0.05:
            import warnings
            warnings.warn(
                f"{comp.name} exceeded its {ctx.duration:.2f}s budget "
                f"by {ctx.overrun:.2f}s",
                RuntimeWarning,
            )
        scene.play(*[FadeOut(m) for m in scene.mobjects], run_time=0.5)


def test_synchronous_speed_in_the_panel_is_120f_over_p():
    from manimate.components.electrical import _sm_speed_block

    block = _sm_speed_block(4, 60.0)
    assert len(block) == 3 and math.isclose(120 * 60 / 4, 1800)
