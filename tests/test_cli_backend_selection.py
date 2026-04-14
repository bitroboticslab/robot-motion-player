"""CLI backend dispatch and fallback behavior tests."""

from __future__ import annotations

import argparse
import sys
import types

from motion_player.cli.main import _cmd_play
from motion_player.core.dataset.loader import DatasetLoader
from tests.conftest import make_motion


def _write_valid_motion(path) -> None:
    loader = DatasetLoader()
    loader.save(make_motion(num_frames=6), path, fmt=path.suffix.lstrip("."))


def _install_fake_mujoco_runtime() -> None:
    """Install fake MuJoCo backend modules for headless CLI tests."""
    fake_state_driver = types.ModuleType("motion_player.backends.mujoco_backend.state_driver")
    fake_viewer = types.ModuleType("motion_player.backends.mujoco_backend.viewer")

    class _Driver:
        def __init__(self, model_path, root_joint_name="root"):
            self.model_path = model_path
            self.root_joint_name = root_joint_name

        def bind_motion(self, _motion):
            return None

    class _Viewer:
        def __init__(self, _driver, _motions):
            self.ran = False

        def run(self):
            self.ran = True

    fake_state_driver.MuJoCoStateDriver = _Driver
    fake_viewer.MuJoCoViewer = _Viewer
    sys.modules["motion_player.backends.mujoco_backend.state_driver"] = fake_state_driver
    sys.modules["motion_player.backends.mujoco_backend.viewer"] = fake_viewer


def test_isaac_unavailable_fallback(tmp_path, monkeypatch, capsys) -> None:
    motion_path = tmp_path / "walk.pkl"
    robot_path = tmp_path / "robot.xml"
    _write_valid_motion(motion_path)
    robot_path.write_text("<mujoco/>", encoding="utf-8")
    _install_fake_mujoco_runtime()

    from motion_player.backends.isaac_backend import IsaacBackend

    monkeypatch.setattr(IsaacBackend, "is_available", staticmethod(lambda: False))
    args = argparse.Namespace(
        motion=str(motion_path),
        robot=str(robot_path),
        root_joint="root",
        mapping=None,
        backend="isaac",
    )
    rc = _cmd_play(args)
    captured = capsys.readouterr()
    assert rc == 0
    assert "falling back to MuJoCo" in captured.err


def test_cli_backend_selection_mujoco(tmp_path, capsys) -> None:
    motion_path = tmp_path / "walk.pkl"
    robot_path = tmp_path / "robot.xml"
    _write_valid_motion(motion_path)
    robot_path.write_text("<mujoco/>", encoding="utf-8")
    _install_fake_mujoco_runtime()

    args = argparse.Namespace(
        motion=str(motion_path),
        robot=str(robot_path),
        root_joint="root",
        mapping=None,
        backend="mujoco",
    )
    rc = _cmd_play(args)
    capsys.readouterr()
    assert rc == 0


def test_isaac_backend_selected_but_not_implemented(tmp_path, monkeypatch, capsys) -> None:
    motion_path = tmp_path / "walk.pkl"
    robot_path = tmp_path / "robot.xml"
    _write_valid_motion(motion_path)
    robot_path.write_text("<mujoco/>", encoding="utf-8")

    from motion_player.backends.isaac_backend import IsaacBackend

    monkeypatch.setattr(IsaacBackend, "is_available", staticmethod(lambda: True))
    args = argparse.Namespace(
        motion=str(motion_path),
        robot=str(robot_path),
        root_joint="root",
        mapping=None,
        backend="isaac",
    )
    rc = _cmd_play(args)
    captured = capsys.readouterr()
    assert rc == 1
    assert "v0.1-minimal" in captured.err
