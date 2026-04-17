"""Tests for isolated GUI runtime orchestration."""

from __future__ import annotations

import queue
import sys
import types

import pytest

import motion_player.cli.gui_runtime_isolated as gui_runtime_isolated
from motion_player.cli.gui_runtime_isolated import run_backend_connected_gui_isolated
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


def test_isolated_runtime_panel_start_failure_falls_back_to_viewer_only(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    captured: dict[str, object] = {}
    _install_fake_runtime(captured)

    motion = tmp_path / "walk.pkl"
    robot = tmp_path / "robot.xml"
    _write_motion(motion)
    robot.write_text("<mujoco/>", encoding="utf-8")

    from motion_player.gui.dearpygui_panel import DearPyGuiPanel

    monkeypatch.setattr(DearPyGuiPanel, "is_available", staticmethod(lambda: True), raising=False)

    def _boom(**_kwargs):
        raise RuntimeError("panel process failed")

    monkeypatch.setattr("motion_player.cli.gui_runtime_isolated._start_panel_runtime", _boom)

    rc = run_backend_connected_gui_isolated(
        motion=str(motion),
        robot=str(robot),
        root_joint="root",
        backend="mujoco",
        require_panel=False,
        warn_if_panel_unavailable=True,
    )
    captured_io = capsys.readouterr()

    assert rc == 0
    assert captured.get("viewer_run") is True
    assert captured.get("external_queue") is None
    assert captured.get("monitor_bus") is None
    assert "continuing with mujoco keyboard controls only" in captured_io.err.lower()


def test_isolated_runtime_warns_and_falls_back_when_dearpygui_missing(
    tmp_path,
    monkeypatch,
    capsys,
) -> None:
    captured: dict[str, object] = {}
    _install_fake_runtime(captured)

    motion = tmp_path / "walk.pkl"
    robot = tmp_path / "robot.xml"
    _write_motion(motion)
    robot.write_text("<mujoco/>", encoding="utf-8")

    from motion_player.gui.dearpygui_panel import DearPyGuiPanel

    monkeypatch.setattr(DearPyGuiPanel, "is_available", staticmethod(lambda: False), raising=False)

    rc = run_backend_connected_gui_isolated(
        motion=str(motion),
        robot=str(robot),
        root_joint="root",
        backend="mujoco",
        require_panel=False,
        warn_if_panel_unavailable=True,
    )
    captured_io = capsys.readouterr()

    assert rc == 0
    assert captured.get("viewer_run") is True
    assert captured.get("external_queue") is None
    assert captured.get("monitor_bus") is None
    assert "dearpygui is not installed" in captured_io.err.lower()


def test_isolated_runtime_raises_when_panel_required_and_start_fails(tmp_path, monkeypatch) -> None:
    captured: dict[str, object] = {}
    _install_fake_runtime(captured)

    motion = tmp_path / "walk.pkl"
    robot = tmp_path / "robot.xml"
    _write_motion(motion)
    robot.write_text("<mujoco/>", encoding="utf-8")

    from motion_player.gui.dearpygui_panel import DearPyGuiPanel

    monkeypatch.setattr(DearPyGuiPanel, "is_available", staticmethod(lambda: True), raising=False)

    def _boom(**_kwargs):
        raise RuntimeError("panel process failed")

    monkeypatch.setattr("motion_player.cli.gui_runtime_isolated._start_panel_runtime", _boom)

    with pytest.raises(RuntimeError):
        run_backend_connected_gui_isolated(
            motion=str(motion),
            robot=str(robot),
            root_joint="root",
            backend="mujoco",
            require_panel=True,
            warn_if_panel_unavailable=True,
        )


def test_isolated_runtime_passes_initial_font_size_key_to_panel_runtime(
    tmp_path, monkeypatch
) -> None:
    captured: dict[str, object] = {}
    _install_fake_runtime(captured)

    motion = tmp_path / "walk.pkl"
    robot = tmp_path / "robot.xml"
    _write_motion(motion)
    robot.write_text("<mujoco/>", encoding="utf-8")

    from motion_player.gui.dearpygui_panel import DearPyGuiPanel

    monkeypatch.setattr(DearPyGuiPanel, "is_available", staticmethod(lambda: True), raising=False)

    class _RuntimeStub:
        command_receiver = object()
        monitor_publisher = object()

        def close(self) -> None:
            return None

    start_kwargs: dict[str, object] = {}

    def _fake_start_panel_runtime(**kwargs):
        start_kwargs.update(kwargs)
        return _RuntimeStub()

    monkeypatch.setattr(
        "motion_player.cli.gui_runtime_isolated._start_panel_runtime",
        _fake_start_panel_runtime,
    )

    rc = run_backend_connected_gui_isolated(
        motion=str(motion),
        robot=str(robot),
        root_joint="root",
        backend="mujoco",
        require_panel=False,
        warn_if_panel_unavailable=True,
        initial_font_size_key="xlarge",
    )

    assert rc == 0
    assert start_kwargs["initial_font_size_key"] == "xlarge"


def test_start_panel_runtime_waits_for_ready_not_starting(monkeypatch) -> None:
    class _FakeQueue:
        def __init__(self, values: list[object]) -> None:
            self._values = values

        def get(self, timeout: float = 0.0) -> object:
            del timeout
            if self._values:
                return self._values.pop(0)
            raise queue.Empty

    class _FakeProcess:
        def __init__(self, *args, **kwargs) -> None:
            del args, kwargs
            self._alive = True

        def start(self) -> None:
            return None

        def is_alive(self) -> bool:
            return self._alive

        def join(self, timeout: float | None = None) -> None:
            del timeout
            return None

        def terminate(self) -> None:
            self._alive = False

    class _FakeCtx:
        def __init__(self) -> None:
            self._status_queue = _FakeQueue(["starting", "failed:boom"])

        def Queue(self, maxsize: int = 0):
            if maxsize == 16:
                return self._status_queue
            return _FakeQueue([])

        def Event(self):
            return object()

        def Process(self, *args, **kwargs):
            return _FakeProcess(*args, **kwargs)

    monkeypatch.setattr(
        gui_runtime_isolated.multiprocessing,
        "get_context",
        lambda _name: _FakeCtx(),
    )

    with pytest.raises(RuntimeError, match="boom"):
        gui_runtime_isolated._start_panel_runtime(
            default_motion_path="walk.pkl",
            default_robot_path="robot.xml",
            initial_font_size_key="medium",
            startup_timeout_s=0.2,
        )
