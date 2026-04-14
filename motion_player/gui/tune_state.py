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

"""State model for precision IK tune controls."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from motion_player.core.kinematics.unit_conversion import (
    AngleUnit,
    PositionUnit,
    convert_position_from_m,
    convert_position_to_m,
)


@dataclass
class IkTuneState:
    """Canonical tune state (SI inside, display-units at boundary)."""

    target_joint: str = ""
    reference_frame: str = "world"
    current_position_m: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    current_quat_wxyz: np.ndarray = field(default_factory=lambda: np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64))
    target_position_m: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    target_euler_rad: np.ndarray = field(default_factory=lambda: np.zeros(3, dtype=np.float64))
    position_unit: PositionUnit = PositionUnit.M
    angle_unit: AngleUnit = AngleUnit.DEG
    step_position_m: float = 0.01
    step_angle_rad: float = np.deg2rad(1.0)
    _min_step_position_m: float = 1e-6
    _min_step_angle_rad: float = np.deg2rad(0.01)

    @property
    def position_m(self) -> np.ndarray:
        """Backward-compatible alias to target position."""
        return self.target_position_m

    @position_m.setter
    def position_m(self, value: np.ndarray) -> None:
        self.target_position_m = np.asarray(value, dtype=np.float64)

    @property
    def euler_rad(self) -> np.ndarray:
        """Backward-compatible alias to target euler."""
        return self.target_euler_rad

    @euler_rad.setter
    def euler_rad(self, value: np.ndarray) -> None:
        self.target_euler_rad = np.asarray(value, dtype=np.float64)

    def set_reference_frame(self, frame: str) -> None:
        mode = str(frame).strip().lower()
        if mode in {"world", "local"}:
            self.reference_frame = mode

    def set_current_position_m(self, vec: tuple[float, float, float]) -> None:
        self.current_position_m = np.asarray(vec, dtype=np.float64)

    def set_current_quat_wxyz(self, quat: tuple[float, float, float, float] | np.ndarray) -> None:
        q = np.asarray(quat, dtype=np.float64)
        norm = float(np.linalg.norm(q))
        if q.shape != (4,) or norm <= 0.0:
            self.current_quat_wxyz = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
            return
        self.current_quat_wxyz = q / norm

    def display_current_position(self) -> np.ndarray:
        return convert_position_from_m(self.current_position_m, self.position_unit)

    def set_position_display(self, vec: tuple[float, float, float], unit: str) -> None:
        self.position_unit = PositionUnit(unit)
        self.target_position_m = convert_position_to_m(np.asarray(vec, dtype=np.float64), self.position_unit)

    def set_target_position_display(self, vec: tuple[float, float, float], unit: str) -> None:
        self.set_position_display(vec, unit)

    def display_position(self) -> np.ndarray:
        return convert_position_from_m(self.target_position_m, self.position_unit)

    def display_target_position(self) -> np.ndarray:
        return self.display_position()

    def switch_position_unit(self, unit: str) -> None:
        self.position_unit = PositionUnit(unit)

    def set_rotation_display(self, vec: tuple[float, float, float], unit: str) -> None:
        self.angle_unit = AngleUnit(unit)
        raw = np.asarray(vec, dtype=np.float64)
        if self.angle_unit is AngleUnit.DEG:
            self.target_euler_rad = np.deg2rad(raw)
        else:
            self.target_euler_rad = raw

    def set_target_rotation_display(self, vec: tuple[float, float, float], unit: str) -> None:
        self.set_rotation_display(vec, unit)

    def display_rotation(self) -> np.ndarray:
        if self.angle_unit is AngleUnit.DEG:
            return np.rad2deg(self.target_euler_rad)
        return self.target_euler_rad.copy()

    def display_target_rotation(self) -> np.ndarray:
        return self.display_rotation()

    def switch_angle_unit(self, unit: str) -> None:
        self.angle_unit = AngleUnit(unit)

    def set_step_position_display(self, value: float) -> None:
        converted = float(convert_position_to_m(np.array([value], dtype=np.float64), self.position_unit)[0])
        if not np.isfinite(converted):
            converted = self.step_position_m
        self.step_position_m = max(abs(converted), self._min_step_position_m)

    def display_step_position(self) -> float:
        return float(convert_position_from_m(np.array([self.step_position_m], dtype=np.float64), self.position_unit)[0])

    def set_step_angle_display(self, value: float) -> None:
        v = float(value)
        if not np.isfinite(v):
            v = self.display_step_angle()
        v = abs(v)
        if self.angle_unit is AngleUnit.DEG:
            converted = float(np.deg2rad(v))
        else:
            converted = v
        self.step_angle_rad = max(converted, self._min_step_angle_rad)

    def display_step_angle(self) -> float:
        if self.angle_unit is AngleUnit.DEG:
            return float(np.rad2deg(self.step_angle_rad))
        return float(self.step_angle_rad)

    def nudge_position(self, axis: int, sign: int) -> None:
        self.target_position_m[axis] += float(sign) * self.step_position_m

    def nudge_rotation(self, axis: int, sign: int) -> None:
        self.target_euler_rad[axis] += float(sign) * self.step_angle_rad

    def reset_target_from_current(self) -> None:
        self.target_position_m = self.current_position_m.copy()
        # current orientation is represented in world quaternion, target input remains Euler
        self.target_euler_rad = np.zeros(3, dtype=np.float64)
