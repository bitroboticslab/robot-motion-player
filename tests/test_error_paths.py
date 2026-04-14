"""Error-path and boundary tests for CLI/viewer/backends."""

from __future__ import annotations

import argparse
import pickle
import sys
import types

import pytest

from motion_player.backends.isaac_backend import IsaacBackend
from motion_player.backends.mujoco_backend.viewer import MuJoCoViewer
from motion_player.cli.main import _cmd_play
from tests.conftest import make_motion


def test_invalid_frame_index_raises() -> None:
    backend = IsaacBackend()
    backend.bind_motion(make_motion(num_frames=4))
    with pytest.raises(IndexError):
        backend.apply_frame(4)


def test_empty_motions_list_raises(monkeypatch: pytest.MonkeyPatch) -> None:
    fake_mujoco = types.ModuleType("mujoco")
    fake_mujoco.viewer = types.SimpleNamespace()
    monkeypatch.setitem(sys.modules, "mujoco", fake_mujoco)
    monkeypatch.setitem(sys.modules, "mujoco.viewer", types.ModuleType("mujoco.viewer"))

    class DummyDriver:
        pass

    with pytest.raises(ValueError, match="non-empty"):
        MuJoCoViewer(DummyDriver(), [])


def test_missing_motion_file(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    args = argparse.Namespace(
        motion=str(tmp_path / "missing.pkl"),
        robot=str(tmp_path / "robot.xml"),
        root_joint="root",
        mapping=None,
        backend="mujoco",
    )
    # Create robot path only, so motion-file path check is the failing one.
    (tmp_path / "robot.xml").write_text("<mujoco/>", encoding="utf-8")
    rc = _cmd_play(args)
    captured = capsys.readouterr()
    assert rc == 1
    assert "Motion path not found" in captured.err


def test_missing_robot_model(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    motion_path = tmp_path / "motion.pkl"
    with open(motion_path, "wb") as f:
        pickle.dump({"not": "a motion"}, f)

    args = argparse.Namespace(
        motion=str(motion_path),
        robot=str(tmp_path / "missing.xml"),
        root_joint="root",
        mapping=None,
        backend="mujoco",
    )
    rc = _cmd_play(args)
    captured = capsys.readouterr()
    assert rc == 1
    assert "Robot model path not found" in captured.err


def test_corrupted_motion_data(capsys: pytest.CaptureFixture[str], tmp_path) -> None:
    motion_path = tmp_path / "bad.pkl"
    with open(motion_path, "wb") as f:
        pickle.dump({"fps": 30.0}, f)
    (tmp_path / "robot.xml").write_text("<mujoco/>", encoding="utf-8")

    args = argparse.Namespace(
        motion=str(motion_path),
        robot=str(tmp_path / "robot.xml"),
        root_joint="root",
        mapping=None,
        backend="mujoco",
    )
    rc = _cmd_play(args)
    captured = capsys.readouterr()
    assert rc == 1
    assert "Failed to load motion file" in captured.err
