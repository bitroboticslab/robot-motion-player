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

"""Pose-frame transform helpers for IK payload frame conversion."""

from __future__ import annotations

import numpy as np


def normalize_quat_wxyz(q: np.ndarray) -> np.ndarray:
    quat = np.asarray(q, dtype=np.float64)
    norm = float(np.linalg.norm(quat))
    if norm <= 0.0:
        return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    return quat / norm


def quat_conjugate_wxyz(q: np.ndarray) -> np.ndarray:
    quat = normalize_quat_wxyz(q)
    return np.array([quat[0], -quat[1], -quat[2], -quat[3]], dtype=np.float64)


def quat_mul_wxyz(q1: np.ndarray, q2: np.ndarray) -> np.ndarray:
    a = normalize_quat_wxyz(q1)
    b = normalize_quat_wxyz(q2)
    w1, x1, y1, z1 = a
    w2, x2, y2, z2 = b
    out = np.array(
        [
            w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
            w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
            w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
            w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
        ],
        dtype=np.float64,
    )
    return normalize_quat_wxyz(out)


def rotate_point_wxyz(quat_wxyz: np.ndarray, point_xyz: np.ndarray) -> np.ndarray:
    q = normalize_quat_wxyz(quat_wxyz)
    p = np.asarray(point_xyz, dtype=np.float64)
    q_vec = q[1:]
    # Fast quaternion-vector rotation: v' = v + 2*w*(q_vec x v) + 2*(q_vec x (q_vec x v))
    t = 2.0 * np.cross(q_vec, p)
    return p + q[0] * t + np.cross(q_vec, t)


def transform_point(parent_pos: np.ndarray, parent_quat_wxyz: np.ndarray, point_local: np.ndarray) -> np.ndarray:
    return np.asarray(parent_pos, dtype=np.float64) + rotate_point_wxyz(parent_quat_wxyz, point_local)


def invert_pose(pos_w: np.ndarray, quat_wxyz: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    q_inv = quat_conjugate_wxyz(quat_wxyz)
    p_inv = -rotate_point_wxyz(q_inv, np.asarray(pos_w, dtype=np.float64))
    return p_inv, q_inv


def compose_pose(
    parent_pos: np.ndarray,
    parent_quat_wxyz: np.ndarray,
    child_pos_local: np.ndarray,
    child_quat_local_wxyz: np.ndarray,
) -> tuple[np.ndarray, np.ndarray]:
    pos = transform_point(parent_pos, parent_quat_wxyz, child_pos_local)
    quat = quat_mul_wxyz(parent_quat_wxyz, child_quat_local_wxyz)
    return pos, quat
