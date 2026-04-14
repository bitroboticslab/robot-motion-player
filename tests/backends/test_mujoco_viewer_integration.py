"""Mock integration tests for end-to-end viewer command chain."""

from __future__ import annotations

import sys
import types

import pytest

from motion_player.backends.mujoco_backend.viewer import MuJoCoViewer
from motion_player.core.ui import PlayerCommand
from tests.conftest import make_motion


@pytest.fixture
def fake_mujoco_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_mujoco = types.ModuleType("mujoco")
    fake_mujoco.mjtGridPos = types.SimpleNamespace(mjGRID_TOPLEFT=1)
    fake_mujoco.mjtCamera = types.SimpleNamespace(mjCAMERA_TRACKING=1)

    class _Cam:
        type: int = 0
        trackbodyid: int = 0
        distance: float = 0.0
        elevation: float = 0.0

    fake_mujoco.MjvCamera = _Cam
    fake_mujoco_viewer = types.ModuleType("mujoco.viewer")
    fake_mujoco.viewer = fake_mujoco_viewer
    monkeypatch.setitem(sys.modules, "mujoco", fake_mujoco)
    monkeypatch.setitem(sys.modules, "mujoco.viewer", fake_mujoco_viewer)


class _DummyDriver:
    def __init__(self) -> None:
        self.model = types.SimpleNamespace(nbody=1)
        self.data = object()
        self.bound = None
        self.applied = []

    def bind_motion(self, motion):
        self.bound = motion

    def apply_frame(self, frame_idx: int) -> None:
        self.applied.append(frame_idx)


@pytest.mark.headless_integration
def test_viewer_interaction_chain(tmp_path, fake_mujoco_modules: None) -> None:
    m0 = make_motion(num_frames=8)
    m0.source_path = str(tmp_path / "clip0.pkl")
    m1 = make_motion(num_frames=12)
    m1.source_path = str(tmp_path / "clip1.pkl")
    driver = _DummyDriver()
    viewer = MuJoCoViewer(driver, [m0, m1])

    # play/pause
    viewer._dispatcher.dispatch(PlayerCommand.PLAY_PAUSE)
    assert viewer._state.playing
    viewer._dispatcher.dispatch(PlayerCommand.PLAY_PAUSE)
    assert not viewer._state.playing

    # step forward / backward
    viewer._step(1)
    assert viewer._state.frame == 1
    viewer._step(-1)
    assert viewer._state.frame == 0

    # clip switch
    viewer._dispatcher.dispatch(PlayerCommand.CLIP_SELECT, 1)
    assert viewer._state.current_clip == 1
    assert viewer._state.frame == 0

    # save
    viewer._dispatcher.dispatch(PlayerCommand.SAVE_MOTION)
    assert (tmp_path / "clip1_edited_v1.pkl").exists()

    # hud
    overlays = []

    class _HudViewer:
        def add_overlay(self, _pos, _title, text):
            overlays.append(text)

    viewer._draw_hud(_HudViewer())
    assert overlays
