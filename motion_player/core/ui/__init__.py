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

"""Abstract UI command layer (backend-agnostic).

This module defines :class:`PlayerCommand` and :class:`PlayerState` — the
abstract interaction model shared by all rendering backends.  Backends convert
native keyboard/mouse events into ``PlayerCommand`` values and dispatch them
through :class:`CommandDispatcher`.
"""

from __future__ import annotations

import enum
from dataclasses import dataclass, field
from typing import Callable


class PlayerCommand(enum.Enum):
    """Enumeration of all player interaction commands.

    Backends map native key events to these values so that the core player
    logic is independent of the rendering framework.
    """

    PLAY_PAUSE = "play_pause"
    STEP_FWD_1 = "step_fwd_1"
    STEP_BWD_1 = "step_bwd_1"
    STEP_FWD_10 = "step_fwd_10"
    STEP_BWD_10 = "step_bwd_10"
    STEP_FWD_100 = "step_fwd_100"
    STEP_BWD_100 = "step_bwd_100"
    SEEK_FRAME = "seek_frame"      # payload: target frame index (int)
    RESET = "reset"
    TOGGLE_LOOP = "toggle_loop"
    TOGGLE_PINGPONG = "toggle_pingpong"
    CLIP_SELECT = "clip_select"      # payload: clip index (int)
    MARK_KEYFRAME = "mark_keyframe"
    PREV_MARKED_FRAME = "prev_marked_frame"
    NEXT_MARKED_FRAME = "next_marked_frame"
    TOGGLE_GHOST = "toggle_ghost"
    TOGGLE_EDIT = "toggle_edit"
    EDIT_DOF_DELTA = "edit_dof_delta"            # payload: {joint_idx, delta, propagate_radius?}
    EDIT_ROOT_POS_DELTA = "edit_root_pos_delta"  # payload: {dx, dy, dz}
    APPLY_IK_TARGET = "apply_ik_target"          # payload: legacy {target_joint, dx, dy, dz} or full-pose payload
    SET_EDIT_JOINT = "set_edit_joint"            # payload: dof index (int)
    UNDO_EDIT = "undo_edit"
    REDO_EDIT = "redo_edit"
    SAVE_MOTION = "save_motion"
    EXPORT_VIDEO = "export_video"                # payload: {output, fps}
    TOGGLE_HUD = "toggle_hud"
    SET_SPEED = "set_speed"        # payload: playback speed (float)
    SPEED_UP = "speed_up"
    SPEED_DOWN = "speed_down"
    EXIT = "exit"


@dataclass
class PlayerState:
    """Mutable state of the player (shared between backend and core logic)."""

    frame: int = 0
    playing: bool = False
    loop: bool = True
    pingpong: bool = False
    edit_mode: bool = False
    show_ghost: bool = False
    show_hud: bool = True
    speed: float = 1.0
    current_clip: int = 0
    keyframes: list[int] = field(default_factory=list)
    mark_history: list[int] = field(default_factory=list)
    selected_joint_idx: int = 0
    direction: int = 1   # 1 = forward, -1 = backward (ping-pong)

    def toggle_play(self) -> None:
        self.playing = not self.playing

    def step(self, num_frames: int, total_frames: int) -> None:
        """Advance the frame counter by *num_frames* with loop/pingpong logic."""
        self.frame += num_frames * self.direction
        if self.pingpong:
            if self.frame >= total_frames:
                self.frame = total_frames - 2
                self.direction = -1
            elif self.frame < 0:
                self.frame = 1
                self.direction = 1
        elif self.loop:
            self.frame = self.frame % total_frames
        else:
            self.frame = max(0, min(self.frame, total_frames - 1))

    def toggle_mark_keyframe(self) -> None:
        if self.frame in self.keyframes:
            self.keyframes.remove(self.frame)
            if self.frame in self.mark_history:
                self.mark_history.remove(self.frame)
        else:
            self.keyframes.append(self.frame)
            self.keyframes.sort()
            if self.frame not in self.mark_history:
                self.mark_history.append(self.frame)

    def set_speed(
        self,
        value: float,
        min_speed: float = 0.1,
        max_speed: float = 4.0,
    ) -> None:
        """Set playback speed while clamping to safe bounds."""
        self.speed = max(min_speed, min(max_speed, float(value)))

    def adjust_speed(
        self,
        delta: float,
        min_speed: float = 0.1,
        max_speed: float = 4.0,
    ) -> None:
        """Adjust playback speed while clamping to safe bounds."""
        self.set_speed(self.speed + delta, min_speed=min_speed, max_speed=max_speed)


class CommandDispatcher:
    """Dispatches :class:`PlayerCommand` values to registered handlers.

    Each command can have at most one handler registered.  Handlers are
    callables with signature ``(state: PlayerState, payload=None) -> None``.
    """

    def __init__(self, state: PlayerState) -> None:
        self.state = state
        self._handlers: dict[PlayerCommand, Callable] = {}

    def register(
        self,
        command: PlayerCommand,
        handler: Callable,
    ) -> None:
        """Register a handler for *command*.

        Parameters
        ----------
        command:
            The command to handle.
        handler:
            Callable ``(state, payload=None) -> None``.
        """
        self._handlers[command] = handler

    def dispatch(
        self,
        command: PlayerCommand,
        payload: object | None = None,
    ) -> None:
        """Dispatch *command* to its registered handler.

        If no handler is registered, the command is silently ignored.
        """
        handler = self._handlers.get(command)
        if handler is not None:
            handler(self.state, payload)
