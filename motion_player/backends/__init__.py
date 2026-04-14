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

"""Rendering backend contracts for robot-motion-player.

`BackendProtocol` defines the minimum interface shared by MuJoCo and Isaac
runtime backends in v0.1.
"""

from __future__ import annotations

from typing import Protocol, runtime_checkable

from motion_player.core.dataset.motion import StandardMotion


@runtime_checkable
class BackendProtocol(Protocol):
    """Minimal backend interface for clip playback."""

    def bind_motion(self, motion: StandardMotion) -> None:
        """Bind a motion clip to backend runtime state."""

    def apply_frame(self, frame_idx: int) -> None:
        """Apply a frame index from the currently bound motion."""

    def reset(self) -> None:
        """Reset runtime state to a deterministic initial state."""

    def close(self) -> None:
        """Release backend resources."""

    @staticmethod
    def is_available() -> bool:
        """Return whether backend runtime dependencies are available."""


__all__ = ["BackendProtocol"]
