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

"""SegmentEditor — range-level edits to a StandardMotion.

Operations
----------
* :meth:`keyframe_interpolate` — interpolate all frames in ``[i0, i1]``
  between the values at ``i0`` and ``i1`` (linear/slerp/spline).
* :meth:`smooth_segment` — apply Savitzky–Golay or Butterworth low-pass
  filter to a named field over a segment.
* :meth:`propagate_edit` — apply an edit at *anchor_frame* and decay it
  smoothly to zero over *decay_frames* subsequent frames.

Extension points
----------------
Register new interpolation or filter strategies by subclassing and overriding
:meth:`keyframe_interpolate` or :meth:`smooth_segment`.
"""

from __future__ import annotations

import numpy as np
from scipy.interpolate import CubicSpline
from scipy.signal import butter, savgol_filter, sosfilt

from motion_player.core.dataset.motion import StandardMotion
from motion_player.core.dataset.quat_utils import normalize


def _slerp(q0: np.ndarray, q1: np.ndarray, t: np.ndarray) -> np.ndarray:
    """Spherical linear interpolation between two xyzw quaternions.

    Parameters
    ----------
    q0, q1:
        Unit quaternions of shape ``(4,)``.
    t:
        Interpolation parameters of shape ``(K,)`` in ``[0, 1]``.

    Returns
    -------
    np.ndarray
        Interpolated quaternions, shape ``(K, 4)``.
    """
    q0 = q0 / (np.linalg.norm(q0) + 1e-12)
    q1 = q1 / (np.linalg.norm(q1) + 1e-12)
    dot = np.clip(np.dot(q0, q1), -1.0, 1.0)
    # Ensure shortest path
    if dot < 0.0:
        q1 = -q1
        dot = -dot
    # If quaternions are nearly identical use linear interpolation
    if dot > 0.9999:
        result = q0[np.newaxis] + t[:, np.newaxis] * (q1 - q0)[np.newaxis]
        return result / np.linalg.norm(result, axis=1, keepdims=True)
    theta0 = np.arccos(dot)
    sin0 = np.sin(theta0)
    if abs(float(sin0)) < 1e-10:
        result = q0[np.newaxis] + t[:, np.newaxis] * (q1 - q0)[np.newaxis]
        return result / np.linalg.norm(result, axis=1, keepdims=True)
    return (
        np.sin((1.0 - t) * theta0)[:, np.newaxis] / sin0 * q0
        + np.sin(t * theta0)[:, np.newaxis] / sin0 * q1
    )


class SegmentEditor:
    """Applies range-level edits to a :class:`~motion_player.core.dataset.motion.StandardMotion`.

    Parameters
    ----------
    motion:
        The motion to edit.  Edits are applied **in-place**.
    """

    def __init__(self, motion: StandardMotion) -> None:
        self.motion = motion

    # ------------------------------------------------------------------
    # Keyframe interpolation
    # ------------------------------------------------------------------

    def keyframe_interpolate(
        self,
        i0: int,
        i1: int,
        mode: str = "slerp",
    ) -> None:
        """Interpolate all frames in ``[i0, i1]`` between boundary values.

        The values at frames ``i0`` and ``i1`` are kept as anchor keyframes;
        all frames in between are overwritten by interpolation.

        Parameters
        ----------
        i0:
            Start frame index (inclusive).
        i1:
            End frame index (inclusive).
        mode:
            Interpolation mode:
            - ``"linear"`` — linear for root_pos and dof_pos; linear for
              root_rot (not recommended for rotations).
            - ``"slerp"`` (default) — linear for pos/dof, spherical linear
              for root_rot.
            - ``"spline"`` — cubic spline for dof_pos, slerp for root_rot,
              linear for root_pos.
        """
        self._check_segment(i0, i1)
        n = i1 - i0 + 1
        t = np.linspace(0.0, 1.0, n)  # (n,)

        m = self.motion

        # --- root_pos: always linear ---
        p0, p1 = m.root_pos[i0], m.root_pos[i1]
        m.root_pos[i0 : i1 + 1] = (
            p0[np.newaxis] + t[:, np.newaxis] * (p1 - p0)[np.newaxis]
        ).astype(np.float32)

        # --- root_rot ---
        q0, q1 = m.root_rot[i0].astype(np.float64), m.root_rot[i1].astype(np.float64)
        if mode in ("slerp", "spline"):
            m.root_rot[i0 : i1 + 1] = _slerp(q0, q1, t).astype(np.float32)
        else:
            # Linear interpolation (not recommended but available)
            interp_q = q0[np.newaxis] + t[:, np.newaxis] * (q1 - q0)[np.newaxis]
            m.root_rot[i0 : i1 + 1] = normalize(interp_q).astype(np.float32)

        # --- dof_pos ---
        d0, d1 = m.dof_pos[i0], m.dof_pos[i1]
        if mode == "spline":
            cs = CubicSpline([0.0, 1.0], np.stack([d0, d1]))
            m.dof_pos[i0 : i1 + 1] = cs(t).astype(np.float32)
        else:
            m.dof_pos[i0 : i1 + 1] = (
                d0[np.newaxis] + t[:, np.newaxis] * (d1 - d0)[np.newaxis]
            ).astype(np.float32)

    # ------------------------------------------------------------------
    # Smoothing
    # ------------------------------------------------------------------

    def smooth_segment(
        self,
        i0: int,
        i1: int,
        field: str,
        filter_type: str = "savgol",
        window_length: int = 11,
        polyorder: int = 3,
        cutoff_hz: float | None = None,
    ) -> None:
        """Smooth a named field over a segment ``[i0, i1]``.

        Parameters
        ----------
        i0, i1:
            Start and end frame indices (inclusive).
        field:
            Attribute name of :class:`~motion_player.core.dataset.motion.StandardMotion`
            to smooth (e.g. ``"dof_pos"``, ``"root_pos"``).
        filter_type:
            ``"savgol"`` (default) — Savitzky–Golay polynomial smoother.
            ``"butter"`` — Butterworth low-pass filter.
        window_length:
            Window length for Savitzky–Golay filter (must be odd).
        polyorder:
            Polynomial order for Savitzky–Golay filter.
        cutoff_hz:
            Cutoff frequency in Hz for Butterworth filter.  Required when
            ``filter_type="butter"``.
        """
        self._check_segment(i0, i1)
        arr: np.ndarray = getattr(self.motion, field)
        segment = arr[i0 : i1 + 1].copy()  # (K, ...)

        if segment.ndim == 1:
            segment = segment[:, np.newaxis]

        n_seg = segment.shape[0]
        if n_seg < 3:
            return  # too short to filter

        # Clamp window to segment length
        wl = min(window_length, n_seg if n_seg % 2 == 1 else n_seg - 1)
        if wl < 3:
            wl = 3

        smoothed = np.empty_like(segment)
        if filter_type == "savgol":
            for col in range(segment.shape[1]):
                smoothed[:, col] = savgol_filter(
                    segment[:, col], window_length=wl, polyorder=polyorder
                )
        elif filter_type == "butter":
            if cutoff_hz is None:
                raise ValueError("cutoff_hz is required for Butterworth filter.")
            nyq = 0.5 * self.motion.fps
            norm_cutoff = cutoff_hz / nyq
            sos = butter(4, norm_cutoff, btype="low", output="sos")
            for col in range(segment.shape[1]):
                smoothed[:, col] = sosfilt(sos, segment[:, col])
        else:
            raise ValueError(f"Unknown filter_type '{filter_type}'; use 'savgol' or 'butter'.")

        arr[i0 : i1 + 1] = smoothed.reshape(arr[i0 : i1 + 1].shape).astype(arr.dtype)

        # Re-normalise quaternions if we smoothed root_rot
        if field == "root_rot":
            for i in range(i0, i1 + 1):
                self.motion.root_rot[i] = normalize(
                    self.motion.root_rot[i].astype(np.float64)
                ).astype(np.float32)

    # ------------------------------------------------------------------
    # Cross-frame propagation
    # ------------------------------------------------------------------

    def propagate_edit(
        self,
        anchor_frame: int,
        delta_dof: np.ndarray,
        decay_frames: int = 30,
    ) -> None:
        """Apply a DOF delta at *anchor_frame* and decay it over subsequent frames.

        The edit is applied with full strength at *anchor_frame* and linearly
        decays to zero at ``anchor_frame + decay_frames``.

        Parameters
        ----------
        anchor_frame:
            The frame at which the edit has full effect.
        delta_dof:
            DOF increment vector of shape ``(D,)`` in radians.
        decay_frames:
            Number of frames over which the delta decays to zero.
        """
        m = self.motion
        end = min(anchor_frame + decay_frames + 1, m.num_frames)
        for i in range(anchor_frame, end):
            alpha = 1.0 - (i - anchor_frame) / (decay_frames + 1)
            m.dof_pos[i] += (alpha * delta_dof).astype(m.dof_pos.dtype)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _check_segment(self, i0: int, i1: int) -> None:
        n = self.motion.num_frames
        if not (0 <= i0 < i1 < n):
            raise IndexError(f"Segment [{i0}, {i1}] out of valid range [0, {n}).")
