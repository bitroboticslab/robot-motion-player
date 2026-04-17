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

"""FrameEditor — per-frame edits to a StandardMotion.

All edits are applied **in-place** on the motion's arrays.  To preserve the
original data, pass a clone (``motion.clone()``) to the editor, or call
:meth:`FrameEditor.snapshot` before editing to push a copy to the history.

Supported per-frame edit operations
-------------------------------------
* :meth:`edit_dof` — increment a single joint angle.
* :meth:`edit_root_pos` — translate the root position.
* :meth:`edit_root_rot` — rotate the root by a delta in roll/pitch/yaw.
* :meth:`clamp_joint_limits` — clip DOF values to model limits.
* :meth:`normalize_quat` — normalise root quaternion.
"""

from __future__ import annotations

import numpy as np

from motion_player.core.dataset.motion import StandardMotion
from motion_player.core.dataset.quat_utils import normalize
from motion_player.core.editing.edit_history import EditHistory


def _rpy_to_quat_xyzw(rpy: np.ndarray) -> np.ndarray:
    """Convert roll-pitch-yaw (radians) to xyzw quaternion."""
    r, p, y = rpy
    cr, sr = np.cos(r / 2), np.sin(r / 2)
    cp, sp = np.cos(p / 2), np.sin(p / 2)
    cy, sy = np.cos(y / 2), np.sin(y / 2)
    w = cr * cp * cy + sr * sp * sy
    x = sr * cp * cy - cr * sp * sy
    y_ = cr * sp * cy + sr * cp * sy
    z = cr * cp * sy - sr * sp * cy
    return np.array([x, y_, z, w], dtype=np.float64)


def _quat_multiply_xyzw(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    """Multiply two xyzw quaternions: q_result = q1 ⊗ q2."""
    x1, y1, z1, w1 = q1
    x2, y2, z2, w2 = q2
    return np.array(
        [
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
        ],
        dtype=np.float64,
    )


class FrameEditor:
    """Applies single-frame edits to a :class:`~motion_player.core.dataset.motion.StandardMotion`.

    Parameters
    ----------
    motion:
        The motion to edit.  Edits are applied **in-place**.
    history:
        Optional :class:`~motion_player.core.editing.edit_history.EditHistory`
        for undo/redo support.  If ``None`` a new history is created.
    joint_lower_limits / joint_upper_limits:
        Per-DOF joint angle limits in radians.  Used by
        :meth:`clamp_joint_limits`.
    """

    def __init__(
        self,
        motion: StandardMotion,
        history: EditHistory | None = None,
        joint_lower_limits: np.ndarray | None = None,
        joint_upper_limits: np.ndarray | None = None,
    ) -> None:
        self.motion = motion
        self.history = history or EditHistory()
        self._lo = joint_lower_limits
        self._hi = joint_upper_limits

    # ------------------------------------------------------------------
    # Snapshot (push current state to undo stack)
    # ------------------------------------------------------------------

    def snapshot(self) -> None:
        """Push a snapshot of the current motion to the undo stack."""
        self.history.push(self.motion)

    def undo(self) -> None:
        """Undo the last edit."""
        prev = self.history.undo(self.motion)
        # Restore all arrays in-place
        self.motion.root_pos[:] = prev.root_pos
        self.motion.root_rot[:] = prev.root_rot
        self.motion.dof_pos[:] = prev.dof_pos
        self.motion.dof_vel[:] = prev.dof_vel

    def redo(self) -> None:
        """Redo the previously undone edit."""
        nxt = self.history.redo(self.motion)
        self.motion.root_pos[:] = nxt.root_pos
        self.motion.root_rot[:] = nxt.root_rot
        self.motion.dof_pos[:] = nxt.dof_pos
        self.motion.dof_vel[:] = nxt.dof_vel

    # ------------------------------------------------------------------
    # Per-frame edits
    # ------------------------------------------------------------------

    def edit_dof(
        self,
        frame: int,
        joint_idx: int,
        delta: float,
        push_history: bool = True,
    ) -> None:
        """Increment a single DOF at *frame* by *delta* radians.

        Parameters
        ----------
        frame:
            Frame index (0-based).
        joint_idx:
            DOF column index.
        delta:
            Increment in radians.
        push_history:
            If ``True``, push a snapshot to the undo stack before editing.
        """
        self._check_frame(frame)
        if push_history:
            self.snapshot()
        self.motion.dof_pos[frame, joint_idx] += delta
        self.clamp_joint_limits(frame)

    def edit_root_pos(
        self,
        frame: int,
        delta_xyz: np.ndarray,
        push_history: bool = True,
    ) -> None:
        """Translate the root position at *frame* by *delta_xyz* metres.

        Parameters
        ----------
        frame:
            Frame index.
        delta_xyz:
            Translation increment ``[dx, dy, dz]`` in metres.
        push_history:
            If ``True``, push a snapshot to the undo stack before editing.
        """
        self._check_frame(frame)
        if push_history:
            self.snapshot()
        self.motion.root_pos[frame] += np.asarray(delta_xyz, dtype=np.float32)

    def edit_root_rot(
        self,
        frame: int,
        delta_rpy: np.ndarray,
        push_history: bool = True,
    ) -> None:
        """Apply a roll-pitch-yaw delta to the root quaternion at *frame*.

        The delta rotation is applied **in the current root frame** (i.e.
        ``q_new = q_current ⊗ q_delta``).

        Parameters
        ----------
        frame:
            Frame index.
        delta_rpy:
            Rotation increment ``[droll, dpitch, dyaw]`` in radians.
        push_history:
            If ``True``, push a snapshot to the undo stack before editing.
        """
        self._check_frame(frame)
        if push_history:
            self.snapshot()
        q_cur = self.motion.root_rot[frame].astype(np.float64)
        q_delta = _rpy_to_quat_xyzw(np.asarray(delta_rpy, dtype=np.float64))
        q_new = _quat_multiply_xyzw(q_cur, q_delta)
        self.motion.root_rot[frame] = normalize(q_new).astype(np.float32)

    def clamp_joint_limits(self, frame: int) -> None:
        """Clip DOF values at *frame* to model joint limits.

        Does nothing if ``joint_lower_limits`` / ``joint_upper_limits`` were
        not provided at construction time.
        """
        if self._lo is not None and self._hi is not None:
            self.motion.dof_pos[frame] = np.clip(self.motion.dof_pos[frame], self._lo, self._hi)

    def normalize_quat(self, frame: int) -> None:
        """Normalise the root quaternion at *frame* to unit length."""
        q = self.motion.root_rot[frame].astype(np.float64)
        self.motion.root_rot[frame] = normalize(q).astype(np.float32)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_frame(self, frame: int) -> None:
        if not (0 <= frame < self.motion.num_frames):
            raise IndexError(f"Frame {frame} out of range [0, {self.motion.num_frames}).")
