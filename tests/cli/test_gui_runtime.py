"""Tests for backend-connected `motion_player gui` runtime path."""

from __future__ import annotations

import argparse
import sys
import types

from motion_player.cli.main import _cmd_gui
from motion_player.core.dataset.loader import DatasetLoader
from tests.conftest import make_motion


def _write_motion(path) -> None:
    DatasetLoader().save(make_motion(num_frames=5), path, fmt=path.suffix.lstrip("."))


def _install_fake_runtime(captured: dict[str, object]) -> None:
    fake_state_driver = types.ModuleType("motion_player.backends.mujoco_backend.state_driver")
    fake_viewer = types.ModuleType("motion_player.backends.mujoco_backend.viewer")

    class _Driver:
        def __init__(self, model_path, root_joint_name="root"):
            self.model_path = model_path
            self.root_joint_name = root_joint_name

        def bind_motion(self, _motion):
            return None

    class _Viewer:
        def __init__(self, _driver, _motions, external_queue=None, monitor_bus=None):
            captured["external_queue"] = external_queue
            captured["monitor_bus"] = monitor_bus

        def run(self):
            captured["viewer_run"] = True

    fake_state_driver.MuJoCoStateDriver = _Driver
    fake_viewer.MuJoCoViewer = _Viewer
    sys.modules["motion_player.backends.mujoco_backend.state_driver"] = fake_state_driver
    sys.modules["motion_player.backends.mujoco_backend.viewer"] = fake_viewer


def test_cmd_gui_wires_backend_and_runtime(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}
    _install_fake_runtime(captured)

    motion = tmp_path / "walk.pkl"
    robot = tmp_path / "robot.xml"
    _write_motion(motion)
    robot.write_text("<mujoco/>", encoding="utf-8")

    from motion_player.gui.dearpygui_panel import DearPyGuiPanel

    monkeypatch.setattr(DearPyGuiPanel, "is_available", staticmethod(lambda: True), raising=False)
    monkeypatch.setattr(
        DearPyGuiPanel,
        "launch_non_blocking",
        lambda self: captured.setdefault("panel_launched", True),
    )

    args = argparse.Namespace(
        command="gui",
        motion=str(motion),
        robot=str(robot),
        root_joint="root",
        backend="mujoco",
    )

    rc = _cmd_gui(args)

    assert rc == 0
    assert captured.get("panel_launched") is True
    assert captured.get("external_queue") is not None
    assert captured.get("monitor_bus") is not None
    assert captured.get("viewer_run") is True
