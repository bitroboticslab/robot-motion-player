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

"""Framework-agnostic GUI callbacks that enqueue player commands."""

from __future__ import annotations

from motion_player.core.ui import PlayerCommand
from motion_player.core.ui.command_queue import CommandQueue


class GuiController:
    """Translate GUI widget events into queued player commands."""

    def __init__(self, queue: CommandQueue) -> None:
        self._queue = queue

    def on_play_pause(self) -> None:
        self._queue.push(PlayerCommand.PLAY_PAUSE)

    def on_reset(self) -> None:
        self._queue.push(PlayerCommand.RESET)

    def on_prev_frame(self) -> None:
        self._queue.push(PlayerCommand.STEP_BWD_1)

    def on_next_frame(self) -> None:
        self._queue.push(PlayerCommand.STEP_FWD_1)

    def on_prev_10(self) -> None:
        self._queue.push(PlayerCommand.STEP_BWD_10)

    def on_next_10(self) -> None:
        self._queue.push(PlayerCommand.STEP_FWD_10)

    def on_prev_100(self) -> None:
        self._queue.push(PlayerCommand.STEP_BWD_100)

    def on_next_100(self) -> None:
        self._queue.push(PlayerCommand.STEP_FWD_100)

    def on_seek_frame(self, frame_idx: int) -> None:
        self._queue.push(PlayerCommand.SEEK_FRAME, int(frame_idx))

    def on_speed_changed(self, speed: float) -> None:
        self._queue.push(PlayerCommand.SET_SPEED, float(speed))

    def on_speed_up(self) -> None:
        self._queue.push(PlayerCommand.SPEED_UP)

    def on_speed_down(self) -> None:
        self._queue.push(PlayerCommand.SPEED_DOWN)

    def on_clip_selected(self, clip_idx: int) -> None:
        self._queue.push(PlayerCommand.CLIP_SELECT, int(clip_idx))

    def on_toggle_loop(self) -> None:
        self._queue.push(PlayerCommand.TOGGLE_LOOP)

    def on_toggle_pingpong(self) -> None:
        self._queue.push(PlayerCommand.TOGGLE_PINGPONG)

    def on_mark_keyframe(self) -> None:
        self._queue.push(PlayerCommand.MARK_KEYFRAME)

    def on_prev_marked_frame(self) -> None:
        self._queue.push(PlayerCommand.PREV_MARKED_FRAME)

    def on_next_marked_frame(self) -> None:
        self._queue.push(PlayerCommand.NEXT_MARKED_FRAME)

    def on_jump_marked_frame(self, frame_idx: int) -> None:
        self._queue.push(PlayerCommand.SEEK_FRAME, int(frame_idx))

    def on_toggle_ghost(self) -> None:
        self._queue.push(PlayerCommand.TOGGLE_GHOST)

    def on_toggle_edit(self) -> None:
        self._queue.push(PlayerCommand.TOGGLE_EDIT)

    def on_edit_dof_delta(self, joint_idx: int, delta: float, propagate_radius: int = 0) -> None:
        self._queue.push(
            PlayerCommand.EDIT_DOF_DELTA,
            {
                "joint_idx": int(joint_idx),
                "delta": float(delta),
                "propagate_radius": int(propagate_radius),
            },
        )

    def on_select_edit_joint(self, joint_idx: int) -> None:
        self._queue.push(PlayerCommand.SET_EDIT_JOINT, int(joint_idx))

    def on_apply_ik_target(self, target_joint: str, dx: float, dy: float, dz: float) -> None:
        self._queue.push(
            PlayerCommand.APPLY_IK_TARGET,
            {
                "target_joint": str(target_joint),
                "dx": float(dx),
                "dy": float(dy),
                "dz": float(dz),
            },
        )

    def on_apply_ik_pose(
        self,
        target_joint: str,
        position: tuple[float, float, float],
        rotation: tuple[float, float, float],
        position_unit: str,
        angle_unit: str,
        reference_frame: str = "world",
        propagate_radius: int = 0,
    ) -> None:
        self._queue.push(
            PlayerCommand.APPLY_IK_TARGET,
            {
                "target_joint": str(target_joint),
                "position": {
                    "x": float(position[0]),
                    "y": float(position[1]),
                    "z": float(position[2]),
                    "unit": str(position_unit),
                },
                "rotation": {
                    "roll": float(rotation[0]),
                    "pitch": float(rotation[1]),
                    "yaw": float(rotation[2]),
                    "unit": str(angle_unit),
                },
                "reference_frame": str(reference_frame),
                "propagate_radius": int(propagate_radius),
            },
        )

    def on_undo_edit(self) -> None:
        self._queue.push(PlayerCommand.UNDO_EDIT)

    def on_redo_edit(self) -> None:
        self._queue.push(PlayerCommand.REDO_EDIT)

    def on_toggle_hud(self) -> None:
        self._queue.push(PlayerCommand.TOGGLE_HUD)

    def on_save_motion(self) -> None:
        self._queue.push(PlayerCommand.SAVE_MOTION)

    def on_exit(self) -> None:
        self._queue.push(PlayerCommand.EXIT)
