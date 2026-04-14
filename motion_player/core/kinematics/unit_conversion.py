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

"""Unit and rotation conversion helpers for IK/UI boundaries."""

from __future__ import annotations

import enum

import numpy as np


class PositionUnit(enum.Enum):
    M = "m"
    CM = "cm"
    MM = "mm"


class AngleUnit(enum.Enum):
    RAD = "rad"
    DEG = "deg"


def convert_position_to_m(vec: np.ndarray, unit: PositionUnit) -> np.ndarray:
    v = np.asarray(vec, dtype=np.float64)
    scale = {PositionUnit.M: 1.0, PositionUnit.CM: 0.01, PositionUnit.MM: 0.001}[unit]
    return v * scale


def convert_position_from_m(vec_m: np.ndarray, unit: PositionUnit) -> np.ndarray:
    v = np.asarray(vec_m, dtype=np.float64)
    scale = {PositionUnit.M: 1.0, PositionUnit.CM: 100.0, PositionUnit.MM: 1000.0}[unit]
    return v * scale


def _euler_rad_to_quat_wxyz(euler_rad: np.ndarray) -> np.ndarray:
    cx, cy, cz = np.cos(euler_rad / 2.0)
    sx, sy, sz = np.sin(euler_rad / 2.0)
    w = cx * cy * cz + sx * sy * sz
    x = sx * cy * cz - cx * sy * sz
    y = cx * sy * cz + sx * cy * sz
    z = cx * cy * sz - sx * sy * cz
    q = np.array([w, x, y, z], dtype=np.float64)
    return q / np.linalg.norm(q)


def euler_xyz_to_quat_wxyz(euler: np.ndarray, angle_unit: AngleUnit) -> np.ndarray:
    e = np.asarray(euler, dtype=np.float64)
    if angle_unit is AngleUnit.DEG:
        e = np.deg2rad(e)
    return _euler_rad_to_quat_wxyz(e)


def quat_wxyz_to_euler_xyz(quat: np.ndarray, angle_unit: AngleUnit) -> np.ndarray:
    w, x, y, z = np.asarray(quat, dtype=np.float64)

    t0 = 2.0 * (w * x + y * z)
    t1 = 1.0 - 2.0 * (x * x + y * y)
    roll = np.arctan2(t0, t1)

    t2 = 2.0 * (w * y - z * x)
    t2 = np.clip(t2, -1.0, 1.0)
    pitch = np.arcsin(t2)

    t3 = 2.0 * (w * z + x * y)
    t4 = 1.0 - 2.0 * (y * y + z * z)
    yaw = np.arctan2(t3, t4)

    out = np.array([roll, pitch, yaw], dtype=np.float64)
    if angle_unit is AngleUnit.DEG:
        out = np.rad2deg(out)
    return out
