# Copyright 2026 Mr-tooth
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MuJoCoViewer — interactive playback viewer using mujoco.viewer.launch_passive.

This module provides a thin wrapper around the official MuJoCo Python viewer
API (``mujoco.viewer.launch_passive``, available since MuJoCo 3.0) that:

* Steps through frames driven by :class:`MuJoCoStateDriver`.
* Draws a text HUD with quality metrics from :class:`MetricEngine`.
* Forwards keyboard events to :class:`CommandDispatcher`.

Camera preset
-------------
The default camera tracks the root body in third-person view.  Override
:meth:`MuJoCoViewer._setup_camera` to change the camera configuration.

Key bindings (mirrors docs/requirements.md §6)
----------------------------------------------
Space      Play/Pause
→ / ←      ±1 frame
Shift+→/←  ±10 frames
Ctrl+→/←   ±100 frames
R          Reset
L          Toggle loop
P          Toggle ping-pong
M          Mark keyframe
B          Jump to previous marked frame
N          Jump to next marked frame
G          Toggle ghost
E          Toggle edit mode
S          Save motion
Q          Toggle HUD
Esc        Exit
"""

from __future__ import annotations

import logging
import time
from typing import TYPE_CHECKING

import numpy as np

from motion_player.backends.mujoco_backend.state_driver import MuJoCoStateDriver
from motion_player.core.dataset.motion import StandardMotion
from motion_player.core.editing.editor_session import EditorSession
from motion_player.core.kinematics.frame_transform import compose_pose
from motion_player.core.kinematics.ik_backend_factory import create_ik_solver_for_robot
from motion_player.core.kinematics.pose_target import PoseTarget
from motion_player.core.ui import CommandDispatcher, PlayerCommand, PlayerState
from motion_player.core.ui.ik_payload import build_pose_target_from_payload
from motion_player.core.ui.state_monitor import PlaybackSnapshot, StateMonitorBus

if TYPE_CHECKING:
    from motion_player.core.ui.command_queue import CommandQueue

logger = logging.getLogger(__name__)


class MuJoCoViewer:
    """Interactive motion player backed by MuJoCo's passive viewer.

    Parameters
    ----------
    driver:
        A configured :class:`MuJoCoStateDriver` with a motion already bound.
    motions:
        List of :class:`~motion_player.core.dataset.motion.StandardMotion`
        objects to play (multi-clip support).
    """

    def __init__(
        self,
        driver: MuJoCoStateDriver,
        motions: list[StandardMotion],
        external_queue: CommandQueue | None = None,
        monitor_bus: StateMonitorBus | None = None,
    ) -> None:
        try:
            import mujoco  # type: ignore[import]
            import mujoco.viewer  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "mujoco package is required for MuJoCoViewer. "
                "Install it with: pip install mujoco"
            ) from exc

        self._mujoco = mujoco
        self._driver = driver
        self._motions = motions
        if not self._motions:
            raise ValueError("motions must be non-empty for MuJoCoViewer.")
        model_path = getattr(driver, "model_path", "")
        self._ik_solver = create_ik_solver_for_robot(model_path, driver=self._driver)
        self._editor_sessions = [
            EditorSession(motion.clone(), ik_solver=self._ik_solver) for motion in self._motions
        ]
        self._state = PlayerState()
        self._dispatcher = CommandDispatcher(self._state)
        self._external_queue = external_queue
        self._monitor_bus = monitor_bus
        self._should_exit = False
        self._last_hud_text: str = ""
        self._register_default_handlers()

    # ------------------------------------------------------------------
    # Playback entry point
    # ------------------------------------------------------------------

    def run(self) -> None:
        """Launch the viewer and block until the user closes it."""
        mj = self._mujoco
        driver = self._driver

        if not self._motions:
            raise ValueError("No motions available; provide at least one clip.")

        # Bind the first clip
        self._bind_clip(0)
        driver.apply_frame(0)

        with mj.viewer.launch_passive(
            driver.model,
            driver.data,
            key_callback=self._on_key,
        ) as viewer:
            self._setup_camera(viewer)
            self._publish_state_snapshot()
            while viewer.is_running() and not self._should_exit:
                step_start = time.perf_counter()
                self._poll_external_commands()

                if self._state.playing:
                    motion = self._current_motion()
                    self._state.step(1, motion.num_frames)
                    driver.apply_frame(self._state.frame)

                if hasattr(viewer, "user_scn"):
                    self._reset_user_scene(viewer)
                    self._draw_selected_joint_highlight(viewer)

                if self._state.show_hud:
                    self._draw_hud(viewer)

                self._publish_state_snapshot()

                viewer.sync()

                # Throttle to motion FPS * speed
                motion = self._current_motion()
                frame_duration = 1.0 / (motion.fps * self._state.speed)
                elapsed = time.perf_counter() - step_start
                if elapsed < frame_duration:
                    time.sleep(frame_duration - elapsed)

    # ------------------------------------------------------------------
    # Camera setup
    # ------------------------------------------------------------------

    def _setup_camera(self, viewer: object) -> None:
        """Configure the default third-person tracking camera.

        Override in a subclass to change camera behaviour.
        """
        try:
            cam = self._mujoco.MjvCamera()
            cam.type = self._mujoco.mjtCamera.mjCAMERA_TRACKING
            cam.trackbodyid = self._driver.model.nbody - 1  # root body heuristic
            cam.distance = 3.0
            cam.elevation = -20.0
            viewer.cam.type = cam.type
            viewer.cam.trackbodyid = cam.trackbodyid
            viewer.cam.distance = cam.distance
            viewer.cam.elevation = cam.elevation
        except Exception:  # noqa: BLE001
            pass  # Camera setup is best-effort

    # ------------------------------------------------------------------
    # HUD
    # ------------------------------------------------------------------

    def _build_hud_lines(self) -> list[str]:
        """Build HUD text lines for current playback state."""
        motion = self._current_motion()
        return [
            f"Clip {self._state.current_clip + 1}/{len(self._motions)}",
            f"Frame {self._state.frame + 1}/{motion.num_frames}",
            f"FPS {motion.fps:.0f}  Speed {self._state.speed:.1f}x",
            f"{'PLAY' if self._state.playing else 'PAUSE'}  "
            f"{'LOOP' if self._state.loop else ''}  "
            f"{'PING' if self._state.pingpong else ''}",
            f"{'EDIT ON' if self._state.edit_mode else 'EDIT OFF'}",
        ]

    def _draw_hud(self, viewer: object) -> None:
        """Draw a text overlay with playback and quality info."""
        lines = self._build_hud_lines()
        text = "\n".join(lines)
        try:
            grid = getattr(self._mujoco, "mjtGridPos", None)
            grid_pos = grid.mjGRID_TOPLEFT if grid is not None else 0
            add_overlay = getattr(viewer, "add_overlay", None)
            if callable(add_overlay):
                add_overlay(grid_pos, "Motion Player", text)
            elif text != self._last_hud_text:
                logger.info("HUD: %s", " | ".join(lines))
            self._last_hud_text = text
        except (AttributeError, TypeError, ValueError) as exc:
            logger.debug("HUD draw fallback path: %s", exc)

    def _reset_user_scene(self, viewer: object) -> None:
        scn = getattr(viewer, "user_scn", None)
        if scn is not None:
            scn.ngeom = 0

    def _draw_selected_joint_highlight(self, viewer: object) -> None:
        if not self._state.edit_mode:
            return
        scn = getattr(viewer, "user_scn", None)
        if scn is None or scn.ngeom >= scn.maxgeom:
            return
        if not hasattr(self._driver, "dof_joint_body_id"):
            return
        try:
            body_id = int(self._driver.dof_joint_body_id(self._state.selected_joint_idx))
            xpos = np.asarray(self._driver.data.xpos, dtype=np.float64)
            if body_id < 0 or body_id >= xpos.shape[0]:
                return
            pos = xpos[body_id]

            # draw inner marker
            geom = scn.geoms[scn.ngeom]
            self._mujoco.mjv_initGeom(
                geom,
                self._mujoco.mjtGeom.mjGEOM_SPHERE,
                np.array([0.028, 0.028, 0.028], dtype=np.float64),
                pos,
                np.eye(3, dtype=np.float64).reshape(9),
                np.array([1.0, 0.55, 0.1, 0.95], dtype=np.float64),
            )
            scn.ngeom += 1

            # draw outer shell when geometry budget allows it for better occlusion visibility
            if scn.ngeom < scn.maxgeom:
                geom_outer = scn.geoms[scn.ngeom]
                self._mujoco.mjv_initGeom(
                    geom_outer,
                    self._mujoco.mjtGeom.mjGEOM_SPHERE,
                    np.array([0.06, 0.06, 0.06], dtype=np.float64),
                    pos,
                    np.eye(3, dtype=np.float64).reshape(9),
                    np.array([1.0, 0.82, 0.2, 0.22], dtype=np.float64),
                )
                scn.ngeom += 1
        except (AttributeError, IndexError, TypeError, ValueError):
            return

    # ------------------------------------------------------------------
    # Key callback
    # ------------------------------------------------------------------

    def _on_key(
        self,
        keycode: int,
        scancode: int | None = None,
        action: int | None = None,
        mods: int | None = None,
    ) -> None:
        """Forward keyboard events to the command dispatcher."""
        # MuJoCo key codes (GLFW convention)
        GLFW_KEY_SPACE = 32
        GLFW_KEY_RIGHT = 262
        GLFW_KEY_LEFT = 263
        GLFW_KEY_R = 82
        GLFW_KEY_L = 76
        GLFW_KEY_P = 80
        GLFW_KEY_M = 77
        GLFW_KEY_B = 66
        GLFW_KEY_N = 78
        GLFW_KEY_G = 71
        GLFW_KEY_E = 69
        GLFW_KEY_S = 83
        GLFW_KEY_Q = 81
        GLFW_KEY_LEFT_BRACKET = 91
        GLFW_KEY_RIGHT_BRACKET = 93
        GLFW_KEY_ESCAPE = 256
        GLFW_MOD_SHIFT = 1
        GLFW_MOD_CTRL = 2
        GLFW_PRESS = 1

        # MuJoCo Python bindings have used multiple callback signatures
        # across versions/runtime paths:
        #   (keycode) or (keycode, scancode, action, mods).
        # Treat keycode-only callbacks as key-press events with no modifiers.
        del scancode
        if action is None:
            action = GLFW_PRESS
        if mods is None:
            mods = 0

        if action != GLFW_PRESS:
            return

        shift = bool(mods & GLFW_MOD_SHIFT)
        ctrl = bool(mods & GLFW_MOD_CTRL)

        if keycode == GLFW_KEY_SPACE:
            self._dispatcher.dispatch(PlayerCommand.PLAY_PAUSE)
        elif keycode == GLFW_KEY_RIGHT:
            if ctrl:
                self._dispatcher.dispatch(PlayerCommand.STEP_FWD_100)
            elif shift:
                self._dispatcher.dispatch(PlayerCommand.STEP_FWD_10)
            else:
                self._dispatcher.dispatch(PlayerCommand.STEP_FWD_1)
        elif keycode == GLFW_KEY_LEFT:
            if ctrl:
                self._dispatcher.dispatch(PlayerCommand.STEP_BWD_100)
            elif shift:
                self._dispatcher.dispatch(PlayerCommand.STEP_BWD_10)
            else:
                self._dispatcher.dispatch(PlayerCommand.STEP_BWD_1)
        elif keycode == GLFW_KEY_R:
            self._dispatcher.dispatch(PlayerCommand.RESET)
        elif keycode == GLFW_KEY_L:
            self._dispatcher.dispatch(PlayerCommand.TOGGLE_LOOP)
        elif keycode == GLFW_KEY_P:
            self._dispatcher.dispatch(PlayerCommand.TOGGLE_PINGPONG)
        elif keycode == GLFW_KEY_M:
            self._dispatcher.dispatch(PlayerCommand.MARK_KEYFRAME)
        elif keycode == GLFW_KEY_B:
            self._dispatcher.dispatch(PlayerCommand.PREV_MARKED_FRAME)
        elif keycode == GLFW_KEY_N:
            self._dispatcher.dispatch(PlayerCommand.NEXT_MARKED_FRAME)
        elif keycode == GLFW_KEY_G:
            self._dispatcher.dispatch(PlayerCommand.TOGGLE_GHOST)
        elif keycode == GLFW_KEY_E:
            self._dispatcher.dispatch(PlayerCommand.TOGGLE_EDIT)
        elif keycode == GLFW_KEY_S:
            self._dispatcher.dispatch(PlayerCommand.SAVE_MOTION)
        elif keycode == GLFW_KEY_Q:
            self._dispatcher.dispatch(PlayerCommand.TOGGLE_HUD)
        elif keycode == GLFW_KEY_LEFT_BRACKET:
            self._dispatcher.dispatch(PlayerCommand.SPEED_DOWN)
        elif keycode == GLFW_KEY_RIGHT_BRACKET:
            self._dispatcher.dispatch(PlayerCommand.SPEED_UP)
        elif keycode == GLFW_KEY_ESCAPE:
            self._dispatcher.dispatch(PlayerCommand.EXIT)
        elif 49 <= keycode <= 57:
            # Number keys 1..9 select clips 0..8
            self._dispatcher.dispatch(PlayerCommand.CLIP_SELECT, keycode - 49)

    # ------------------------------------------------------------------
    # Default command handlers
    # ------------------------------------------------------------------

    def _register_default_handlers(self) -> None:
        d = self._dispatcher

        d.register(
            PlayerCommand.PLAY_PAUSE,
            lambda state, _: state.toggle_play(),
        )
        d.register(
            PlayerCommand.STEP_FWD_1,
            lambda state, _: self._step(1),
        )
        d.register(
            PlayerCommand.STEP_BWD_1,
            lambda state, _: self._step(-1),
        )
        d.register(
            PlayerCommand.STEP_FWD_10,
            lambda state, _: self._step(10),
        )
        d.register(
            PlayerCommand.STEP_BWD_10,
            lambda state, _: self._step(-10),
        )
        d.register(
            PlayerCommand.STEP_FWD_100,
            lambda state, _: self._step(100),
        )
        d.register(
            PlayerCommand.STEP_BWD_100,
            lambda state, _: self._step(-100),
        )
        d.register(
            PlayerCommand.RESET,
            lambda state, _: setattr(state, "frame", 0),
        )
        d.register(
            PlayerCommand.SEEK_FRAME,
            lambda state, payload: self._seek_to(int(payload)),
        )
        d.register(
            PlayerCommand.TOGGLE_LOOP,
            lambda state, _: setattr(state, "loop", not state.loop),
        )
        d.register(
            PlayerCommand.TOGGLE_PINGPONG,
            lambda state, _: setattr(state, "pingpong", not state.pingpong),
        )
        d.register(
            PlayerCommand.MARK_KEYFRAME,
            lambda state, _: self._toggle_keyframe(),
        )
        d.register(
            PlayerCommand.PREV_MARKED_FRAME,
            lambda state, _: self._jump_to_prev_marked_frame(),
        )
        d.register(
            PlayerCommand.NEXT_MARKED_FRAME,
            lambda state, _: self._jump_to_next_marked_frame(),
        )
        d.register(
            PlayerCommand.TOGGLE_GHOST,
            lambda state, _: setattr(state, "show_ghost", not state.show_ghost),
        )
        d.register(
            PlayerCommand.TOGGLE_EDIT,
            lambda state, _: setattr(state, "edit_mode", not state.edit_mode),
        )
        d.register(
            PlayerCommand.EDIT_DOF_DELTA,
            lambda state, payload: self._handle_edit_dof_payload(payload),
        )
        d.register(
            PlayerCommand.EDIT_ROOT_POS_DELTA,
            lambda state, payload: self._handle_edit_root_pos_payload(payload),
        )
        d.register(
            PlayerCommand.SET_EDIT_JOINT,
            lambda state, payload: self._handle_set_edit_joint(payload),
        )
        d.register(
            PlayerCommand.UNDO_EDIT,
            lambda state, _: self._handle_undo(),
        )
        d.register(
            PlayerCommand.REDO_EDIT,
            lambda state, _: self._handle_redo(),
        )
        d.register(
            PlayerCommand.APPLY_IK_TARGET,
            lambda state, payload: self._handle_apply_ik_payload(payload),
        )
        d.register(
            PlayerCommand.TOGGLE_HUD,
            lambda state, _: setattr(state, "show_hud", not state.show_hud),
        )
        d.register(
            PlayerCommand.SET_SPEED,
            lambda state, payload: state.set_speed(float(payload)),
        )
        d.register(
            PlayerCommand.CLIP_SELECT,
            lambda state, payload: self._clip_select(int(payload)),
        )
        d.register(
            PlayerCommand.SAVE_MOTION,
            lambda state, _: self._save_motion_handler(),
        )
        d.register(
            PlayerCommand.EXPORT_VIDEO,
            lambda state, payload: self._handle_export_video(payload),
        )
        d.register(
            PlayerCommand.SPEED_UP,
            lambda state, _: self._adjust_speed(0.1),
        )
        d.register(
            PlayerCommand.SPEED_DOWN,
            lambda state, _: self._adjust_speed(-0.1),
        )
        d.register(
            PlayerCommand.EXIT,
            lambda state, _: setattr(self, "_should_exit", True),
        )

    def _step(self, delta: int) -> None:
        motion = self._current_motion()
        self._state.frame = max(
            0,
            min(self._state.frame + delta, motion.num_frames - 1),
        )
        self._driver.apply_frame(self._state.frame)

    def _current_motion(self) -> StandardMotion:
        sessions = getattr(self, "_editor_sessions", None)
        if sessions is None:
            return self._motions[self._state.current_clip]
        return sessions[self._state.current_clip].motion

    def _current_editor(self) -> EditorSession:
        return self._editor_sessions[self._state.current_clip]

    def _joint_names_for_current_clip(self) -> tuple[str, ...]:
        motion = self._current_motion()
        num_dofs = int(getattr(motion, "num_dofs", 0))
        names = getattr(motion, "joint_names", None)
        if names is not None and len(names) == num_dofs:
            return tuple(str(name) for name in names)
        if num_dofs <= 0:
            return ()
        if hasattr(self._driver, "dof_joint_name"):
            return tuple(str(self._driver.dof_joint_name(i)) for i in range(num_dofs))
        return tuple(f"joint_{i}" for i in range(num_dofs))

    def _publish_state_snapshot(self) -> None:
        if self._monitor_bus is None:
            return
        motion = self._current_motion()
        joint_names = self._joint_names_for_current_clip()
        if joint_names:
            selected_joint_idx = max(0, min(self._state.selected_joint_idx, len(joint_names) - 1))
        else:
            selected_joint_idx = 0
        selected_pos = np.zeros(3, dtype=np.float64)
        selected_quat = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        try:
            body_id = int(self._driver.dof_joint_body_id(selected_joint_idx))
            xpos = np.asarray(self._driver.data.xpos, dtype=np.float64)
            if 0 <= body_id < xpos.shape[0]:
                selected_pos = np.asarray(xpos[body_id], dtype=np.float64)
            xquat = getattr(self._driver.data, "xquat", None)
            if xquat is not None:
                xquat_arr = np.asarray(xquat, dtype=np.float64)
                if 0 <= body_id < xquat_arr.shape[0]:
                    selected_quat = np.asarray(xquat_arr[body_id], dtype=np.float64)
        except (AttributeError, IndexError, TypeError, ValueError):
            pass
        self._monitor_bus.publish(
            PlaybackSnapshot(
                frame=self._state.frame,
                total_frames=motion.num_frames,
                clip=self._state.current_clip,
                total_clips=len(self._motions),
                speed=self._state.speed,
                playing=self._state.playing,
                loop=self._state.loop,
                pingpong=self._state.pingpong,
                edit_mode=self._state.edit_mode,
                show_hud=self._state.show_hud,
                show_ghost=self._state.show_ghost,
                keyframe_count=len(self._state.keyframes),
                marked_frames=tuple(int(x) for x in self._state.keyframes),
                mark_history=tuple(int(x) for x in self._state.mark_history),
                joint_names=joint_names,
                selected_joint_idx=selected_joint_idx,
                ik_target_joint=joint_names[selected_joint_idx] if joint_names else "",
                selected_joint_pos_m=(
                    float(selected_pos[0]),
                    float(selected_pos[1]),
                    float(selected_pos[2]),
                ),
                selected_joint_quat_wxyz=(
                    float(selected_quat[0]),
                    float(selected_quat[1]),
                    float(selected_quat[2]),
                    float(selected_quat[3]),
                ),
            )
        )

    def _seek_to(self, frame_idx: int) -> None:
        motion = self._current_motion()
        self._state.frame = max(0, min(int(frame_idx), motion.num_frames - 1))
        self._driver.apply_frame(self._state.frame)

    def _bind_clip(self, clip_idx: int) -> None:
        self._state.current_clip = clip_idx
        self._state.frame = 0
        self._state.keyframes = self._editor_sessions[clip_idx].keyframes()
        self._state.mark_history = self._editor_sessions[clip_idx].mark_history()
        self._state.selected_joint_idx = 0
        self._driver.bind_motion(self._editor_sessions[clip_idx].motion)

    def _clip_select(self, clip_idx: int) -> None:
        """Select a clip by index with safe bounds checks."""
        if clip_idx < 0 or clip_idx >= len(self._motions):
            logger.warning("Clip index %s out of range [0, %s).", clip_idx, len(self._motions))
            return
        self._state.playing = False
        self._bind_clip(clip_idx)
        self._driver.apply_frame(0)

    def _adjust_speed(self, delta: float) -> None:
        self._state.adjust_speed(delta, min_speed=0.1, max_speed=4.0)

    def _poll_external_commands(self) -> None:
        queue = self._external_queue
        if queue is None:
            return
        for queued in queue.drain():
            self._dispatcher.dispatch(queued.command, queued.payload)

    def _save_motion_handler(self) -> None:
        """Save current clip to a versioned edited file."""
        session = self._current_editor()
        motion = self._current_motion()
        src = motion.source_path or f"clip_{self._state.current_clip + 1}.pkl"

        try:
            output_path = session.save_versioned(src)
            logger.info("Motion saved to %s", output_path)
        except (OSError, PermissionError, ValueError) as exc:
            logger.error("Failed to save motion from %s: %s", src, exc)

    def _toggle_keyframe(self) -> None:
        editor = self._current_editor()
        editor.mark_keyframe(self._state.frame)
        self._state.keyframes = editor.keyframes()
        self._state.mark_history = editor.mark_history()

    def _jump_to_prev_marked_frame(self) -> None:
        editor = self._current_editor()
        frame = editor.prev_marked_frame(self._state.frame, wrap=True)
        if frame is None:
            logger.info("No marked frames available. Mark a frame first.")
            return
        self._seek_to(frame)

    def _jump_to_next_marked_frame(self) -> None:
        editor = self._current_editor()
        frame = editor.next_marked_frame(self._state.frame, wrap=True)
        if frame is None:
            logger.info("No marked frames available. Mark a frame first.")
            return
        self._seek_to(frame)

    def _handle_edit_dof_payload(self, payload: object | None) -> None:
        if not isinstance(payload, dict):
            return
        joint_idx = int(payload.get("joint_idx", 0))
        delta = float(payload.get("delta", 0.0))
        radius = int(payload.get("propagate_radius", 0))
        self._current_editor().apply_dof_edit(
            frame=self._state.frame,
            joint_idx=joint_idx,
            delta=delta,
            propagate_radius=radius,
        )
        self._driver.apply_frame(self._state.frame)

    def _handle_edit_root_pos_payload(self, payload: object | None) -> None:
        if not isinstance(payload, dict):
            return
        dx = float(payload.get("dx", 0.0))
        dy = float(payload.get("dy", 0.0))
        dz = float(payload.get("dz", 0.0))
        self._current_editor().frame_editor.edit_root_pos(
            frame=self._state.frame,
            delta_xyz=np.array([dx, dy, dz], dtype=np.float32),
            push_history=True,
        )
        self._driver.apply_frame(self._state.frame)

    def _handle_set_edit_joint(self, payload: object | None) -> None:
        motion = self._current_motion()
        num_dofs = int(getattr(motion, "num_dofs", 0))
        if num_dofs <= 0:
            self._state.selected_joint_idx = 0
            return
        idx = int(payload) if payload is not None else self._state.selected_joint_idx
        self._state.selected_joint_idx = max(0, min(idx, num_dofs - 1))

    def _handle_undo(self) -> None:
        try:
            self._current_editor().undo()
        except IndexError:
            logger.info("No undo history for current clip. Nothing changed.")
            return
        self._driver.apply_frame(self._state.frame)

    def _handle_redo(self) -> None:
        try:
            self._current_editor().redo()
        except IndexError:
            logger.info("No redo history for current clip. Nothing changed.")
            return
        self._driver.apply_frame(self._state.frame)

    def _handle_apply_ik_payload(self, payload: object | None) -> None:
        if not isinstance(payload, dict):
            return

        editor = self._current_editor()
        if editor.ik_solver is None:
            logger.info("IK backend unavailable for current robot model; command skipped.")
            return

        joint_names = self._joint_names_for_current_clip()
        if not joint_names:
            logger.info("IK command skipped: no joints available.")
            return

        default_joint_idx = max(0, min(self._state.selected_joint_idx, len(joint_names) - 1))
        target_joint = str(payload.get("target_joint", joint_names[default_joint_idx]))
        if target_joint not in joint_names:
            logger.info("IK command skipped: unknown target joint '%s'.", target_joint)
            return
        target_idx = joint_names.index(target_joint)
        body_id = int(self._driver.dof_joint_body_id(target_idx))
        current_pos = np.asarray(self._driver.data.xpos[body_id], dtype=np.float64)
        current_quat = np.asarray(getattr(self._driver.data, "xquat", np.array([[1.0, 0.0, 0.0, 0.0]])), dtype=np.float64)
        if body_id >= current_quat.shape[0]:
            current_quat_wxyz = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        else:
            current_quat_wxyz = np.asarray(current_quat[body_id], dtype=np.float64)
        reference_frame = str(payload.get("reference_frame", "world")).strip().lower()
        if reference_frame not in {"world", "local"}:
            reference_frame = "world"
        propagate_radius = max(0, int(payload.get("propagate_radius", 0)))

        if "position" in payload and "rotation" in payload:
            try:
                parsed_joint, pose_target = build_pose_target_from_payload(payload)
            except (KeyError, TypeError, ValueError) as exc:
                logger.info("IK command skipped: invalid pose payload (%s).", exc)
                return
            if parsed_joint != target_joint:
                logger.info(
                    "IK command skipped: payload joint mismatch ('%s' != '%s').",
                    parsed_joint,
                    target_joint,
                )
                return
            if reference_frame == "local":
                pose_pos_world, pose_quat_world = compose_pose(
                    current_pos,
                    current_quat_wxyz,
                    pose_target.position_m,
                    pose_target.orientation_wxyz,
                )
                pose_target = PoseTarget(
                    position_m=pose_pos_world,
                    orientation_wxyz=pose_quat_world,
                    position_weight=pose_target.position_weight,
                    rotation_weight=pose_target.rotation_weight,
                )
        else:
            delta = np.array(
                [
                    float(payload.get("dx", 0.0)),
                    float(payload.get("dy", 0.0)),
                    float(payload.get("dz", 0.0)),
                ],
                dtype=np.float64,
            )
            pose_target = PoseTarget(
                position_m=current_pos + delta,
                orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            )

        try:
            editor.apply_eef_edit(
                frame=self._state.frame,
                targets={target_joint: pose_target},
                propagate_radius=propagate_radius,
            )
        except (KeyError, RuntimeError, ValueError) as exc:
            logger.info("IK command skipped: %s", exc)
            return

        self._driver.apply_frame(self._state.frame)

    def _handle_export_video(self, payload: object | None) -> None:
        # v0.3.0 step: export command is handled by CLI subcommand path.
        del payload
