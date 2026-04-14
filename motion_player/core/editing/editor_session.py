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

"""EditorSession — stateful orchestration over frame and segment editors."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

import numpy as np

from motion_player.core.dataset.loader import DatasetLoader
from motion_player.core.dataset.motion import StandardMotion
from motion_player.core.editing.frame_editor import FrameEditor
from motion_player.core.editing.segment_editor import SegmentEditor
from motion_player.core.kinematics.pose_target import PoseTarget


class _IKSolverProtocol(Protocol):
    def solve(self, current_qpos: np.ndarray, targets: dict[str, PoseTarget]) -> np.ndarray:
        """Solve an IK target for the current qpos."""


@dataclass
class EditorSession:
    """Session-scoped editing state for a single motion clip."""

    motion: StandardMotion
    ik_solver: _IKSolverProtocol | None = None
    frame_editor: FrameEditor = field(init=False)
    segment_editor: SegmentEditor = field(init=False)
    _keyframes: list[int] = field(default_factory=list)
    _mark_history: list[int] = field(default_factory=list)

    def __post_init__(self) -> None:
        self.frame_editor = FrameEditor(self.motion)
        self.segment_editor = SegmentEditor(self.motion)

    def mark_keyframe(self, frame: int) -> None:
        if frame in self._keyframes:
            self._keyframes.remove(frame)
            if frame in self._mark_history:
                self._mark_history.remove(frame)
        else:
            self._keyframes.append(frame)
            self._keyframes.sort()
            if frame not in self._mark_history:
                self._mark_history.append(frame)

    def keyframes(self) -> list[int]:
        return list(self._keyframes)

    def mark_history(self) -> list[int]:
        """Return marked-frame history in insertion order."""
        return list(self._mark_history)

    def next_marked_frame(self, frame: int, wrap: bool = True) -> int | None:
        """Return the next marked frame relative to *frame*."""
        if not self._keyframes:
            return None
        current = int(frame)
        for marked in self._keyframes:
            if marked > current:
                return int(marked)
        return int(self._keyframes[0]) if wrap else None

    def prev_marked_frame(self, frame: int, wrap: bool = True) -> int | None:
        """Return the previous marked frame relative to *frame*."""
        if not self._keyframes:
            return None
        current = int(frame)
        for marked in reversed(self._keyframes):
            if marked < current:
                return int(marked)
        return int(self._keyframes[-1]) if wrap else None

    def apply_dof_edit(self, frame: int, joint_idx: int, delta: float, propagate_radius: int = 0) -> None:
        self.frame_editor.edit_dof(frame=frame, joint_idx=joint_idx, delta=delta, push_history=True)
        if propagate_radius <= 0:
            return
        delta_vec = np.zeros(self.motion.num_dofs, dtype=self.motion.dof_pos.dtype)
        delta_vec[joint_idx] = delta
        self._propagate_with_keyframe_guards(anchor_frame=frame, delta_dof=delta_vec, radius=propagate_radius)

    def undo(self) -> None:
        self.frame_editor.undo()

    def redo(self) -> None:
        self.frame_editor.redo()

    def apply_eef_edit(
        self,
        frame: int,
        targets: dict[str, PoseTarget],
        propagate_radius: int = 0,
    ) -> None:
        self.frame_editor._check_frame(frame)  # noqa: SLF001
        if self.ik_solver is None:
            raise RuntimeError("IK solver is not configured for this session.")
        current = self.motion.dof_pos[frame].astype(np.float64)
        solved = np.asarray(self.ik_solver.solve(current, targets), dtype=np.float64)
        if solved.shape != current.shape:
            raise ValueError(f"IK solve shape mismatch: expected {current.shape}, got {solved.shape}")
        self.frame_editor.snapshot()
        self.motion.dof_pos[frame] = solved.astype(self.motion.dof_pos.dtype)
        if propagate_radius > 0:
            delta = solved - current
            self._propagate_with_keyframe_guards(
                anchor_frame=frame,
                delta_dof=delta,
                radius=int(propagate_radius),
            )

    def save_versioned(self, source_path: str | None = None) -> Path:
        src = Path(source_path or self.motion.source_path or "edited_motion.pkl")
        suffix = src.suffix.lower()
        fmt = "npy" if suffix == ".npy" else "pkl"
        ext = ".npy" if fmt == "npy" else ".pkl"
        out = src.with_name(f"{src.stem}_edited_v1{ext}")
        idx = 1
        while out.exists():
            idx += 1
            out = src.with_name(f"{src.stem}_edited_v{idx}{ext}")
        DatasetLoader(validate=False).save(self.motion, out, fmt=fmt)
        return out

    def _propagate_with_keyframe_guards(self, anchor_frame: int, delta_dof: np.ndarray, radius: int) -> None:
        end = min(anchor_frame + radius + 1, self.motion.num_frames)
        blocked = set(self._keyframes) - {anchor_frame}
        for frame in range(anchor_frame + 1, end):
            if frame in blocked:
                break
            alpha = 1.0 - (frame - anchor_frame) / (radius + 1)
            self.motion.dof_pos[frame] += (alpha * delta_dof).astype(self.motion.dof_pos.dtype)
