from __future__ import annotations

import numpy as np

from motion_player.gui.tune_state import IkTuneState


def test_unit_switch_preserves_internal_si_values() -> None:
    s = IkTuneState()
    s.set_position_display((10.0, 0.0, 0.0), unit="cm")
    assert np.isclose(s.position_m[0], 0.1)
    s.switch_position_unit("mm")
    assert np.isclose(s.display_position()[0], 100.0)


def test_nudge_position_uses_step_in_current_unit() -> None:
    s = IkTuneState()
    s.set_position_display((0.0, 0.0, 0.0), unit="cm")
    s.step_position_m = 0.01  # 1 cm
    s.nudge_position(axis=0, sign=1)
    assert np.isclose(s.position_m[0], 0.01)


def test_angle_unit_switch_preserves_internal_rotation() -> None:
    s = IkTuneState()
    s.set_rotation_display((90.0, 0.0, 0.0), unit="deg")
    assert np.isclose(s.euler_rad[0], np.pi / 2.0)
    s.switch_angle_unit("rad")
    rot = s.display_rotation()
    assert np.isclose(rot[0], np.pi / 2.0)


def test_step_inputs_are_clamped_positive_for_stability() -> None:
    s = IkTuneState()
    s.switch_position_unit("cm")
    s.set_step_position_display(-2.5)
    assert np.isclose(s.step_position_m, 0.025)

    s.switch_angle_unit("deg")
    s.set_step_angle_display(-5.0)
    assert np.isclose(s.step_angle_rad, np.deg2rad(5.0))


def test_zero_step_inputs_fallback_to_small_positive_values() -> None:
    s = IkTuneState()
    s.switch_position_unit("mm")
    s.set_step_position_display(0.0)
    assert s.step_position_m > 0.0

    s.switch_angle_unit("rad")
    s.set_step_angle_display(0.0)
    assert s.step_angle_rad > 0.0
