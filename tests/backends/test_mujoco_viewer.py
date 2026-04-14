"""Headless tests for MuJoCo viewer command/hud logic."""

from __future__ import annotations

import sys
import types

import numpy as np
import pytest

from motion_player.backends.mujoco_backend.viewer import MuJoCoViewer
from motion_player.core.kinematics.pose_target import PoseTarget
from motion_player.core.ui import CommandDispatcher, PlayerCommand, PlayerState
from tests.conftest import make_motion


class _DispatcherSpy:
    def __init__(self) -> None:
        self.commands: list[PlayerCommand] = []
        self.events: list[tuple[PlayerCommand, object | None]] = []

    def dispatch(self, command: PlayerCommand, payload: object | None = None) -> None:
        self.events.append((command, payload))
        self.commands.append(command)


def _viewer_with_spy() -> tuple[MuJoCoViewer, _DispatcherSpy]:
    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    spy = _DispatcherSpy()
    viewer._dispatcher = spy
    return viewer, spy


def test_on_key_accepts_single_keycode_signature() -> None:
    """MuJoCo runtime may call key callbacks with only keycode."""
    viewer, spy = _viewer_with_spy()

    viewer._on_key(32)  # GLFW_KEY_SPACE

    assert spy.commands == [PlayerCommand.PLAY_PAUSE]


def test_on_key_accepts_full_glfw_signature() -> None:
    """Newer runtimes call key callbacks with GLFW-style full signature."""
    viewer, spy = _viewer_with_spy()

    viewer._on_key(262, 0, 1, 0)  # GLFW_KEY_RIGHT, GLFW_PRESS

    assert spy.commands == [PlayerCommand.STEP_FWD_1]


@pytest.mark.parametrize(
    ("keycode", "mods", "expected_command", "expected_payload"),
    [
        (263, 0, PlayerCommand.STEP_BWD_1, None),
        (262, 1, PlayerCommand.STEP_FWD_10, None),
        (263, 1, PlayerCommand.STEP_BWD_10, None),
        (262, 2, PlayerCommand.STEP_FWD_100, None),
        (263, 2, PlayerCommand.STEP_BWD_100, None),
        (82, 0, PlayerCommand.RESET, None),
        (76, 0, PlayerCommand.TOGGLE_LOOP, None),
        (80, 0, PlayerCommand.TOGGLE_PINGPONG, None),
        (77, 0, PlayerCommand.MARK_KEYFRAME, None),
        (66, 0, PlayerCommand.PREV_MARKED_FRAME, None),
        (78, 0, PlayerCommand.NEXT_MARKED_FRAME, None),
        (71, 0, PlayerCommand.TOGGLE_GHOST, None),
        (69, 0, PlayerCommand.TOGGLE_EDIT, None),
        (83, 0, PlayerCommand.SAVE_MOTION, None),
        (81, 0, PlayerCommand.TOGGLE_HUD, None),
        (91, 0, PlayerCommand.SPEED_DOWN, None),
        (93, 0, PlayerCommand.SPEED_UP, None),
        (49, 0, PlayerCommand.CLIP_SELECT, 0),
        (57, 0, PlayerCommand.CLIP_SELECT, 8),
        (256, 0, PlayerCommand.EXIT, None),
    ],
)
def test_on_key_maps_commands(
    keycode: int,
    mods: int,
    expected_command: PlayerCommand,
    expected_payload: object | None,
) -> None:
    viewer, spy = _viewer_with_spy()

    viewer._on_key(keycode, 0, 1, mods)

    assert spy.events == [(expected_command, expected_payload)]


@pytest.fixture
def fake_mujoco_modules(monkeypatch: pytest.MonkeyPatch) -> None:
    """Install lightweight fake `mujoco` modules for headless viewer tests."""
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
        self.applied = None

    def bind_motion(self, motion):
        self.bound = motion

    def apply_frame(self, frame_idx: int) -> None:
        self.applied = frame_idx

    def dof_joint_name(self, dof_idx: int) -> str:
        return f"joint_{dof_idx}"

    def dof_joint_body_id(self, dof_idx: int) -> int:
        return dof_idx


def test_hud_text_generation(fake_mujoco_modules: None) -> None:
    viewer = MuJoCoViewer(_DummyDriver(), [make_motion(num_frames=20)])
    lines = viewer._build_hud_lines()
    assert "Clip 1/1" in lines[0]
    assert "Frame 1/20" in lines[1]
    assert "Speed 1.0x" in lines[2]


def test_hud_no_crash_on_error(fake_mujoco_modules: None) -> None:
    viewer = MuJoCoViewer(_DummyDriver(), [make_motion(num_frames=20)])

    class _BadOverlayViewer:
        def add_overlay(self, *_args, **_kwargs):
            raise AttributeError("overlay not supported")

    viewer._draw_hud(_BadOverlayViewer())  # should not raise


def test_clip_select_valid_indices(fake_mujoco_modules: None) -> None:
    driver = _DummyDriver()
    motions = [make_motion(num_frames=5), make_motion(num_frames=7)]
    viewer = MuJoCoViewer(driver, motions)
    viewer._clip_select(1)
    assert viewer._state.current_clip == 1
    assert viewer._state.frame == 0
    assert driver.applied == 0


def test_clip_select_out_of_range(fake_mujoco_modules: None) -> None:
    driver = _DummyDriver()
    motions = [make_motion(num_frames=5), make_motion(num_frames=7)]
    viewer = MuJoCoViewer(driver, motions)
    viewer._clip_select(99)
    assert viewer._state.current_clip == 0


def test_hud_shows_current_clip_number(fake_mujoco_modules: None) -> None:
    driver = _DummyDriver()
    motions = [make_motion(num_frames=5), make_motion(num_frames=7)]
    viewer = MuJoCoViewer(driver, motions)
    viewer._clip_select(1)
    assert "Clip 2/2" in viewer._build_hud_lines()[0]


def test_seek_frame_command_sets_current_frame() -> None:
    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    viewer._state = PlayerState(frame=0)
    viewer._motions = [types.SimpleNamespace(num_frames=100, fps=30.0)]
    viewer._driver = _DummyDriver()
    viewer._dispatcher = CommandDispatcher(viewer._state)
    viewer._register_default_handlers()

    viewer._dispatcher.dispatch(PlayerCommand.SEEK_FRAME, 42)

    assert viewer._state.frame == 42
    assert viewer._driver.applied == 42


def test_set_speed_command_clamps_speed() -> None:
    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    viewer._state = PlayerState(speed=1.0)
    viewer._motions = [types.SimpleNamespace(num_frames=100, fps=30.0)]
    viewer._driver = _DummyDriver()
    viewer._dispatcher = CommandDispatcher(viewer._state)
    viewer._register_default_handlers()

    viewer._dispatcher.dispatch(PlayerCommand.SET_SPEED, 10.0)
    assert viewer._state.speed == 4.0
    viewer._dispatcher.dispatch(PlayerCommand.SET_SPEED, 0.01)
    assert viewer._state.speed == 0.1


def test_set_edit_joint_command_clamps_and_updates_state() -> None:
    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    viewer._state = PlayerState(frame=0, selected_joint_idx=0)
    viewer._editor_sessions = [types.SimpleNamespace(motion=types.SimpleNamespace(num_dofs=4, joint_names=None))]
    viewer._motions = [types.SimpleNamespace(num_frames=20, fps=30.0, num_dofs=4, joint_names=None)]
    viewer._driver = _DummyDriver()
    viewer._dispatcher = CommandDispatcher(viewer._state)
    viewer._register_default_handlers()

    viewer._dispatcher.dispatch(PlayerCommand.SET_EDIT_JOINT, 99)
    assert viewer._state.selected_joint_idx == 3


def test_marked_frame_navigation_commands_seek_with_wrap() -> None:
    class _EditorStub:
        def __init__(self) -> None:
            self.motion = types.SimpleNamespace(num_frames=30, fps=30.0, num_dofs=2, joint_names=["j0", "j1"])
            self._keys = [2, 8, 14]

        def next_marked_frame(self, frame: int, wrap: bool = True) -> int | None:
            del wrap
            for marked in self._keys:
                if marked > frame:
                    return marked
            return self._keys[0]

        def prev_marked_frame(self, frame: int, wrap: bool = True) -> int | None:
            del wrap
            for marked in reversed(self._keys):
                if marked < frame:
                    return marked
            return self._keys[-1]

    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    viewer._state = PlayerState(frame=6)
    viewer._editor_sessions = [_EditorStub()]
    viewer._motions = [types.SimpleNamespace(num_frames=30, fps=30.0)]
    viewer._driver = _DummyDriver()
    viewer._dispatcher = CommandDispatcher(viewer._state)
    viewer._register_default_handlers()

    viewer._dispatcher.dispatch(PlayerCommand.NEXT_MARKED_FRAME)
    assert viewer._state.frame == 8
    assert viewer._driver.applied == 8

    viewer._state.frame = 14
    viewer._dispatcher.dispatch(PlayerCommand.NEXT_MARKED_FRAME)
    assert viewer._state.frame == 2
    assert viewer._driver.applied == 2

    viewer._state.frame = 2
    viewer._dispatcher.dispatch(PlayerCommand.PREV_MARKED_FRAME)
    assert viewer._state.frame == 14
    assert viewer._driver.applied == 14


def test_editor_commands_dispatch_to_editor_session() -> None:
    class _EditorStub:
        def __init__(self) -> None:
            self.calls = []

        def apply_dof_edit(
            self,
            frame: int,
            joint_idx: int,
            delta: float,
            propagate_radius: int = 0,
        ) -> None:
            self.calls.append(("dof", frame, joint_idx, delta, propagate_radius))

        def undo(self) -> None:
            self.calls.append(("undo",))

        def redo(self) -> None:
            self.calls.append(("redo",))

    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    viewer._state = PlayerState(frame=7)
    viewer._editor_sessions = [_EditorStub()]
    viewer._motions = [types.SimpleNamespace(num_frames=100, fps=30.0)]
    viewer._driver = _DummyDriver()
    viewer._dispatcher = CommandDispatcher(viewer._state)
    viewer._register_default_handlers()

    viewer._dispatcher.dispatch(
        PlayerCommand.EDIT_DOF_DELTA,
        {"joint_idx": 3, "delta": 0.15, "propagate_radius": 5},
    )
    viewer._dispatcher.dispatch(PlayerCommand.UNDO_EDIT)
    viewer._dispatcher.dispatch(PlayerCommand.REDO_EDIT)

    calls = viewer._editor_sessions[0].calls
    assert calls[0] == ("dof", 7, 3, 0.15, 5)
    assert calls[1] == ("undo",)
    assert calls[2] == ("redo",)


def test_apply_ik_payload_calls_editor_session() -> None:
    class _EditorStub:
        def __init__(self) -> None:
            self.ik_solver = object()
            self.calls: list[tuple[int, dict[str, PoseTarget]]] = []
            self.motion = types.SimpleNamespace(num_frames=20, fps=30.0, num_dofs=1, joint_names=["joint_0"])

        def apply_eef_edit(
            self,
            frame: int,
            targets: dict[str, PoseTarget],
            propagate_radius: int = 0,
        ) -> None:
            self.calls.append((frame, targets, propagate_radius))

    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    viewer._state = PlayerState(frame=5, selected_joint_idx=0)
    viewer._editor_sessions = [_EditorStub()]
    viewer._motions = [types.SimpleNamespace(num_frames=20, fps=30.0, num_dofs=1, joint_names=["joint_0"])]
    viewer._driver = _DummyDriver()
    viewer._driver.data = types.SimpleNamespace(xpos=np.array([[0, 0, 0], [1, 1, 1]], dtype=np.float64))
    viewer._driver.dof_joint_body_id = lambda _idx: 1

    viewer._handle_apply_ik_payload({"target_joint": "joint_0", "dx": 0.1, "dy": 0.0, "dz": 0.0})
    assert len(viewer._editor_sessions[0].calls) == 1
    _frame, targets, propagate_radius = viewer._editor_sessions[0].calls[0]
    assert propagate_radius == 0
    np.testing.assert_allclose(targets["joint_0"].position_m, np.array([1.1, 1.0, 1.0], dtype=np.float64))
    np.testing.assert_allclose(targets["joint_0"].orientation_wxyz, np.array([1.0, 0.0, 0.0, 0.0]))


def test_apply_ik_payload_accepts_full_pose_payload() -> None:
    class _Editor:
        def __init__(self) -> None:
            self.ik_solver = object()
            self.seen = None
            self.motion = types.SimpleNamespace(num_frames=20, fps=30.0, num_dofs=1, joint_names=["joint_0"])

        def apply_eef_edit(
            self,
            frame: int,
            targets: dict[str, PoseTarget],
            propagate_radius: int = 0,
        ) -> None:
            self.seen = (frame, targets, propagate_radius)

    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    viewer._state = PlayerState(frame=7, selected_joint_idx=0)
    viewer._editor_sessions = [_Editor()]
    viewer._motions = [types.SimpleNamespace(num_frames=20, fps=30.0, num_dofs=1, joint_names=["joint_0"])]
    viewer._driver = _DummyDriver()
    viewer._driver.data = types.SimpleNamespace(xpos=np.array([[0, 0, 0], [1, 1, 1]], dtype=np.float64))
    viewer._driver.dof_joint_body_id = lambda _idx: 1
    viewer._handle_apply_ik_payload(
        {
            "target_joint": "joint_0",
            "position": {"x": 100.0, "y": 0.0, "z": 0.0, "unit": "cm"},
            "rotation": {"roll": 0.0, "pitch": 0.0, "yaw": 45.0, "unit": "deg"},
            "reference_frame": "world",
            "propagate_radius": 5,
        }
    )
    assert viewer._editor_sessions[0].seen is not None
    _frame, _targets, radius = viewer._editor_sessions[0].seen
    assert radius == 5


def test_apply_ik_payload_local_frame_is_converted_to_world() -> None:
    class _Editor:
        def __init__(self) -> None:
            self.ik_solver = object()
            self.seen = None
            self.motion = types.SimpleNamespace(num_frames=20, fps=30.0, num_dofs=1, joint_names=["joint_0"])

        def apply_eef_edit(
            self,
            frame: int,
            targets: dict[str, PoseTarget],
            propagate_radius: int = 0,
        ) -> None:
            self.seen = (frame, targets, propagate_radius)

    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    viewer._state = PlayerState(frame=7, selected_joint_idx=0)
    viewer._editor_sessions = [_Editor()]
    viewer._motions = [types.SimpleNamespace(num_frames=20, fps=30.0, num_dofs=1, joint_names=["joint_0"])]
    viewer._driver = _DummyDriver()
    viewer._driver.data = types.SimpleNamespace(
        xpos=np.array([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0]], dtype=np.float64),
        xquat=np.array([[1.0, 0.0, 0.0, 0.0], [1.0, 0.0, 0.0, 0.0]], dtype=np.float64),
    )
    viewer._driver.dof_joint_body_id = lambda _idx: 1
    viewer._handle_apply_ik_payload(
        {
            "target_joint": "joint_0",
            "position": {"x": 0.1, "y": 0.0, "z": 0.0, "unit": "m"},
            "rotation": {"roll": 0.0, "pitch": 0.0, "yaw": 0.0, "unit": "deg"},
            "reference_frame": "local",
        }
    )
    assert viewer._editor_sessions[0].seen is not None
    _frame, targets, _radius = viewer._editor_sessions[0].seen
    np.testing.assert_allclose(targets["joint_0"].position_m, np.array([1.1, 2.0, 3.0], dtype=np.float64), atol=1e-6)


def test_undo_redo_without_history_logs_hint_and_keeps_running(caplog: pytest.LogCaptureFixture) -> None:
    class _EditorEmpty:
        def undo(self) -> None:
            raise IndexError("Nothing to undo.")

        def redo(self) -> None:
            raise IndexError("Nothing to redo.")

    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    viewer._state = PlayerState(frame=3)
    viewer._editor_sessions = [_EditorEmpty()]
    viewer._motions = [types.SimpleNamespace(num_frames=30, fps=30.0)]
    viewer._driver = _DummyDriver()
    viewer._dispatcher = CommandDispatcher(viewer._state)
    viewer._register_default_handlers()

    caplog.set_level("INFO")

    viewer._dispatcher.dispatch(PlayerCommand.UNDO_EDIT)
    viewer._dispatcher.dispatch(PlayerCommand.REDO_EDIT)

    assert "No undo history" in caplog.text
    assert "No redo history" in caplog.text
    assert viewer._driver.applied is None


def test_selected_joint_highlight_draws_marker_when_edit_mode_on() -> None:
    fake_mj = types.SimpleNamespace(
        mjtGeom=types.SimpleNamespace(mjGEOM_SPHERE=2),
        mjv_initGeom=lambda *args, **kwargs: None,
    )
    fake_scn = types.SimpleNamespace(
        ngeom=0,
        maxgeom=10,
        geoms=[object() for _ in range(10)],
    )
    fake_viewer = types.SimpleNamespace(user_scn=fake_scn)

    class _DriverWithBody:
        def __init__(self) -> None:
            self.data = types.SimpleNamespace(
                xpos=np.array([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0]], dtype=np.float64)
            )

        def dof_joint_body_id(self, _idx: int) -> int:
            return 1

    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    viewer._mujoco = fake_mj
    viewer._driver = _DriverWithBody()
    viewer._state = PlayerState(edit_mode=True, selected_joint_idx=0)

    viewer._draw_selected_joint_highlight(fake_viewer)
    assert fake_scn.ngeom == 2


def test_selected_joint_highlight_respects_scene_capacity() -> None:
    fake_mj = types.SimpleNamespace(
        mjtGeom=types.SimpleNamespace(mjGEOM_SPHERE=2),
        mjv_initGeom=lambda *args, **kwargs: None,
    )
    fake_scn = types.SimpleNamespace(
        ngeom=0,
        maxgeom=1,
        geoms=[object()],
    )
    fake_viewer = types.SimpleNamespace(user_scn=fake_scn)

    class _DriverWithBody:
        def __init__(self) -> None:
            self.data = types.SimpleNamespace(
                xpos=np.array([[0.0, 0.0, 0.0], [1.0, 2.0, 3.0]], dtype=np.float64)
            )

        def dof_joint_body_id(self, _idx: int) -> int:
            return 1

    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    viewer._mujoco = fake_mj
    viewer._driver = _DriverWithBody()
    viewer._state = PlayerState(edit_mode=True, selected_joint_idx=0)

    viewer._draw_selected_joint_highlight(fake_viewer)
    assert fake_scn.ngeom == 1


class _CaptureBus:
    def __init__(self) -> None:
        self.items = []

    def publish(self, snapshot) -> None:
        self.items.append(snapshot)


def test_publish_state_snapshot_emits_current_state() -> None:
    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    viewer._state = PlayerState(frame=9, speed=1.2, playing=True, current_clip=0)
    viewer._motions = [types.SimpleNamespace(num_frames=88, fps=30.0)]
    viewer._monitor_bus = _CaptureBus()

    viewer._publish_state_snapshot()

    assert len(viewer._monitor_bus.items) == 1
    snap = viewer._monitor_bus.items[0]
    assert snap.frame == 9
    assert snap.total_frames == 88
    assert snap.speed == 1.2
    assert snap.playing is True
    assert snap.marked_frames == ()
    assert snap.mark_history == ()
