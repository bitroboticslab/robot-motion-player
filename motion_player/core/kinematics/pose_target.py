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

"""Canonical IK pose target model."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class PoseTarget:
    """Canonical full-pose IK target in SI units."""

    position_m: np.ndarray
    orientation_wxyz: np.ndarray
    position_weight: float = 1.0
    rotation_weight: float = 1.0

    def __post_init__(self) -> None:
        p = np.asarray(self.position_m, dtype=np.float64)
        q = np.asarray(self.orientation_wxyz, dtype=np.float64)

        if p.shape != (3,):
            raise ValueError(f"position_m must be shape (3,), got {p.shape}")
        if q.shape != (4,):
            raise ValueError(f"orientation_wxyz must be shape (4,), got {q.shape}")

        norm = float(np.linalg.norm(q))
        if norm <= 0.0:
            raise ValueError("orientation_wxyz must have non-zero norm.")

        object.__setattr__(self, "position_m", p)
        object.__setattr__(self, "orientation_wxyz", q / norm)
