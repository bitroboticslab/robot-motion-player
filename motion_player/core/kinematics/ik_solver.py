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

"""IKSolver — pluggable inverse-kinematics adapter."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol

import numpy as np

from motion_player.core.kinematics.pose_target import PoseTarget


class IKBackend(Protocol):
    """Protocol for optional IK backends."""

    def solve(self, current_qpos: np.ndarray, targets: dict[str, PoseTarget]) -> np.ndarray:
        """Return solved joint position vector for target task constraints."""


@dataclass
class IKSolver:
    """Thin wrapper around an injected IK backend implementation."""

    backend: IKBackend

    def __init__(self, backend: IKBackend | None = None) -> None:
        if backend is None:
            raise ImportError(
                "No IK backend configured. Provide backend=... or install optional IK backend."
            )
        self.backend = backend

    def solve(self, current_qpos: np.ndarray, targets: dict[str, PoseTarget]) -> np.ndarray:
        return self.backend.solve(current_qpos, targets)
