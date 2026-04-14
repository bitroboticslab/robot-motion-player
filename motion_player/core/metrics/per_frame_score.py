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

"""PerFrameScore — result container for a single quality metric term."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class PerFrameScore:
    """Result of evaluating a single quality metric term.

    Parameters
    ----------
    term_name:
        Human-readable name of the metric term (e.g. ``"joint_limit_violation"``).
    values:
        Per-frame metric values, shape ``(N,)``.  Lower is better for penalty
        terms; this is the convention used throughout robot-motion-player to
        mirror the GMR retargeting loss.
    weight:
        Relative weight of this term in the overall quality score.
    summary:
        Scalar summary of ``values`` (weighted mean by default).
    threshold:
        Optional warning threshold; frames where ``values > threshold`` are
        flagged as problematic.
    """

    term_name: str
    values: np.ndarray   # (N,)
    weight: float = 1.0
    summary: float | None = None
    threshold: float | None = None

    def __post_init__(self) -> None:
        if self.summary is None:
            self.summary = float(np.mean(self.values))

    @property
    def bad_frames(self) -> np.ndarray:
        """Indices of frames that exceed *threshold*.

        Returns an empty array if no threshold is set.
        """
        if self.threshold is None:
            return np.array([], dtype=int)
        return np.where(self.values > self.threshold)[0]

    @property
    def worst_frame(self) -> int:
        """Index of the frame with the highest metric value."""
        return int(np.argmax(self.values))
