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

"""Quaternion utility functions.

All functions in this module operate on numpy arrays and assume the
**xyzw** (scalar-last) convention unless otherwise noted, matching the
rsl-rl-ex / motion_loader canonical convention.

MuJoCo uses **wxyz** (scalar-first); backends that drive MuJoCo should call
:func:`xyzw_to_wxyz` before writing to ``mjData.qpos``.
"""

from __future__ import annotations

import warnings

import numpy as np


def xyzw_to_wxyz(q: np.ndarray) -> np.ndarray:
    """Convert quaternion(s) from xyzw to wxyz layout.

    Parameters
    ----------
    q:
        Array of shape ``(..., 4)`` in xyzw convention.

    Returns
    -------
    np.ndarray
        Array of same shape in wxyz convention.
    """
    q = np.asarray(q, dtype=np.float64)
    return np.concatenate([q[..., 3:4], q[..., :3]], axis=-1)


def wxyz_to_xyzw(q: np.ndarray) -> np.ndarray:
    """Convert quaternion(s) from wxyz to xyzw layout.

    Parameters
    ----------
    q:
        Array of shape ``(..., 4)`` in wxyz convention.

    Returns
    -------
    np.ndarray
        Array of same shape in xyzw convention.
    """
    q = np.asarray(q, dtype=np.float64)
    return np.concatenate([q[..., 1:4], q[..., 0:1]], axis=-1)


def normalize(q: np.ndarray) -> np.ndarray:
    """Normalise quaternion(s) to unit length.

    Parameters
    ----------
    q:
        Array of shape ``(..., 4)``.

    Returns
    -------
    np.ndarray
        Normalised array of same shape.  Rows with near-zero norm are
        returned as-is (identity quaternion set by caller if needed).
    """
    q = np.asarray(q, dtype=np.float64).copy()
    norm = np.linalg.norm(q, axis=-1, keepdims=True)
    near_zero = norm < 1e-12
    if np.any(near_zero):
        warnings.warn(
            "normalize(): near-zero quaternion norm encountered; using identity quaternion.",
            stacklevel=2,
        )
        if q.ndim == 1:
            q[:] = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)
        else:
            q[near_zero.squeeze(-1)] = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)
            norm = np.linalg.norm(q, axis=-1, keepdims=True)
    return q / np.where(norm < 1e-12, 1.0, norm)


def quat_rotate_vector(q_xyzw: np.ndarray, v: np.ndarray) -> np.ndarray:
    """Rotate vector(s) *v* by quaternion(s) *q* (xyzw convention).

    Parameters
    ----------
    q_xyzw:
        Quaternion(s) of shape ``(N, 4)`` or ``(4,)`` in xyzw convention.
    v:
        Vector(s) of shape ``(N, 3)`` or ``(3,)``.

    Returns
    -------
    np.ndarray
        Rotated vector(s) of the same leading shape as *v*.
    """
    q = np.asarray(q_xyzw, dtype=np.float64)
    v = np.asarray(v, dtype=np.float64)
    # Expand dims for broadcasting if single quaternion
    if q.ndim == 1:
        q = q[np.newaxis]
    if v.ndim == 1:
        v = v[np.newaxis]
    x, y, z, w = q[..., 0], q[..., 1], q[..., 2], q[..., 3]
    vx, vy, vz = v[..., 0], v[..., 1], v[..., 2]
    # Sandwich product: q ⊗ (0,v) ⊗ q*
    t_x = 2 * (y * vz - z * vy)
    t_y = 2 * (z * vx - x * vz)
    t_z = 2 * (x * vy - y * vx)
    rx = vx + w * t_x + y * t_z - z * t_y
    ry = vy + w * t_y + z * t_x - x * t_z
    rz = vz + w * t_z + x * t_y - y * t_x
    return np.stack([rx, ry, rz], axis=-1).squeeze()
