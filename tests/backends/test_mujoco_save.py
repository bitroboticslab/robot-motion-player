"""Tests for MuJoCo viewer save-motion command path."""

from __future__ import annotations

import sys
import types

import numpy as np
import pytest

from motion_player.backends.mujoco_backend.viewer import MuJoCoViewer
from motion_player.core.dataset.loader import DatasetLoader
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

    def bind_motion(self, _motion):
        return None

    def apply_frame(self, _frame_idx: int) -> None:
        return None


def test_save_motion_creates_file(tmp_path, fake_mujoco_modules: None) -> None:
    motion = make_motion(num_frames=6)
    motion.source_path = str(tmp_path / "walk.pkl")
    viewer = MuJoCoViewer(_DummyDriver(), [motion])
    viewer._save_motion_handler()
    assert (tmp_path / "walk_edited_v1.pkl").exists()


def test_save_motion_format_preserved_npy(tmp_path, fake_mujoco_modules: None) -> None:
    motion = make_motion(num_frames=6)
    motion.source_path = str(tmp_path / "walk.npy")
    viewer = MuJoCoViewer(_DummyDriver(), [motion])
    viewer._save_motion_handler()
    out = tmp_path / "walk_edited_v1.npy"
    assert out.exists()
    loaded = np.load(out, allow_pickle=True).item()
    assert "root_pos" in loaded


def test_save_motion_versioning(tmp_path, fake_mujoco_modules: None) -> None:
    motion = make_motion(num_frames=6)
    motion.source_path = str(tmp_path / "walk.pkl")
    viewer = MuJoCoViewer(_DummyDriver(), [motion])
    viewer._save_motion_handler()
    viewer._save_motion_handler()
    assert (tmp_path / "walk_edited_v1.pkl").exists()
    assert (tmp_path / "walk_edited_v2.pkl").exists()


def test_save_motion_error_feedback(
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
    tmp_path,
    fake_mujoco_modules: None,
) -> None:
    motion = make_motion(num_frames=6)
    motion.source_path = str(tmp_path / "walk.pkl")
    viewer = MuJoCoViewer(_DummyDriver(), [motion])

    def _raise(*_args, **_kwargs):
        raise PermissionError("no write permission")

    monkeypatch.setattr(DatasetLoader, "save", _raise)
    caplog.set_level("ERROR")
    viewer._save_motion_handler()
    assert "Failed to save motion" in caplog.text
