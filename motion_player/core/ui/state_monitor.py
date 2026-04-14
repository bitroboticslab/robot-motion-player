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

"""Read-only playback state publication for GUI monitoring."""

from __future__ import annotations

from dataclasses import dataclass
from threading import Lock


@dataclass(frozen=True)
class PlaybackSnapshot:
    """Immutable playback snapshot published by viewer and read by GUI."""

    frame: int
    total_frames: int
    clip: int
    total_clips: int
    speed: float
    playing: bool
    loop: bool
    pingpong: bool
    edit_mode: bool
    show_hud: bool
    show_ghost: bool
    keyframe_count: int
    marked_frames: tuple[int, ...] = ()
    mark_history: tuple[int, ...] = ()
    joint_names: tuple[str, ...] = ()
    selected_joint_idx: int = 0
    ik_target_joint: str = ""
    selected_joint_pos_m: tuple[float, float, float] = (0.0, 0.0, 0.0)
    selected_joint_quat_wxyz: tuple[float, float, float, float] = (1.0, 0.0, 0.0, 0.0)


class StateMonitorBus:
    """Thread-safe holder for the latest playback snapshot."""

    def __init__(self) -> None:
        self._lock = Lock()
        self._latest: PlaybackSnapshot | None = None

    def publish(self, snapshot: PlaybackSnapshot) -> None:
        with self._lock:
            self._latest = snapshot

    def latest(self) -> PlaybackSnapshot | None:
        with self._lock:
            return self._latest
