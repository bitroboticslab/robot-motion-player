from __future__ import annotations

import numpy as np

from motion_player.gui.tune_state import IkTuneState


def test_tune_state_tracks_current_and_target_pose_separately() -> None:
    state = IkTuneState()
    state.set_current_position_m((0.2, 0.0, 0.5))
    state.set_target_position_display((0.21, 0.0, 0.5), unit="m")
    assert tuple(state.current_position_m.tolist()) == (0.2, 0.0, 0.5)
    assert tuple(state.target_position_m.tolist()) == (0.21, 0.0, 0.5)


def test_tune_state_reference_frame_accepts_world_and_local() -> None:
    state = IkTuneState()
    state.set_reference_frame("local")
    assert state.reference_frame == "local"
    state.set_reference_frame("world")
    assert state.reference_frame == "world"


def test_reset_target_from_current_copies_position() -> None:
    state = IkTuneState()
    state.set_current_position_m((0.4, -0.1, 0.9))
    state.target_position_m = np.array([0.0, 0.0, 0.0], dtype=np.float64)
    state.reset_target_from_current()
    np.testing.assert_allclose(
        state.target_position_m, np.array([0.4, -0.1, 0.9], dtype=np.float64)
    )
