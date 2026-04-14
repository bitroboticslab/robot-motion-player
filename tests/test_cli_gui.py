"""CLI tests for optional GUI control-panel entry point."""

from __future__ import annotations

import argparse
import sys
import types

from motion_player.cli.main import _cmd_play, build_parser
from motion_player.core.dataset.loader import DatasetLoader
from tests.conftest import make_motion


def _write_valid_motion(path) -> None:
    loader = DatasetLoader()
    loader.save(make_motion(num_frames=6), path, fmt=path.suffix.lstrip("."))


def _install_fake_mujoco_runtime(captured: dict[str, object]) -> None:
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
            self.ran = False

        def run(self):
            self.ran = True

    fake_state_driver.MuJoCoStateDriver = _Driver
    fake_viewer.MuJoCoViewer = _Viewer
    sys.modules["motion_player.backends.mujoco_backend.state_driver"] = fake_state_driver
    sys.modules["motion_player.backends.mujoco_backend.viewer"] = fake_viewer


def test_play_has_gui_flag() -> None:
    parser = build_parser()
    args = parser.parse_args(
        ["play", "--motion", "m.pkl", "--robot", "r.xml", "--gui"]
    )
    assert args.gui is True


def test_parser_exposes_gui_subcommand() -> None:
    parser = build_parser()
    args = parser.parse_args(["gui"])
    assert args.command == "gui"


def test_cmd_play_gui_wires_external_queue(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}
    _install_fake_mujoco_runtime(captured)

    motion_path = tmp_path / "walk.pkl"
    robot_path = tmp_path / "robot.xml"
    _write_valid_motion(motion_path)
    robot_path.write_text("<mujoco/>", encoding="utf-8")

    from motion_player.gui.dearpygui_panel import DearPyGuiPanel

    monkeypatch.setattr(
        DearPyGuiPanel,
        "is_available",
        staticmethod(lambda: True),
        raising=False,
    )
    monkeypatch.setattr(
        DearPyGuiPanel,
        "launch_non_blocking",
        lambda self: captured.setdefault("panel_launched", True),
    )

    args = argparse.Namespace(
        motion=str(motion_path),
        robot=str(robot_path),
        root_joint="root",
        mapping=None,
        backend="mujoco",
        gui=True,
    )
    rc = _cmd_play(args)
    assert rc == 0
    assert captured.get("external_queue") is not None
    assert captured.get("monitor_bus") is not None
    assert captured.get("panel_launched") is True


def test_cmd_play_gui_missing_dependency_falls_back(tmp_path, monkeypatch, capsys) -> None:
    captured: dict[str, object] = {}
    _install_fake_mujoco_runtime(captured)

    motion_path = tmp_path / "walk.pkl"
    robot_path = tmp_path / "robot.xml"
    _write_valid_motion(motion_path)
    robot_path.write_text("<mujoco/>", encoding="utf-8")

    from motion_player.gui.dearpygui_panel import DearPyGuiPanel

    monkeypatch.setattr(
        DearPyGuiPanel,
        "is_available",
        staticmethod(lambda: False),
        raising=False,
    )
    monkeypatch.setattr(
        DearPyGuiPanel,
        "launch_non_blocking",
        lambda self: captured.setdefault("panel_launched", True),
    )

    args = argparse.Namespace(
        motion=str(motion_path),
        robot=str(robot_path),
        root_joint="root",
        mapping=None,
        backend="mujoco",
        gui=True,
    )
    rc = _cmd_play(args)
    captured_io = capsys.readouterr()

    assert rc == 0
    assert captured.get("external_queue") is None
    assert captured.get("monitor_bus") is None
    assert captured.get("panel_launched") is None
    assert "--gui was requested but DearPyGui is not installed" in captured_io.err
