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

"""UI payload conversion for full-pose IK apply commands."""

from __future__ import annotations

from typing import Any

import numpy as np

from motion_player.core.kinematics.pose_target import PoseTarget
from motion_player.core.kinematics.unit_conversion import (
    AngleUnit,
    PositionUnit,
    convert_position_to_m,
    euler_xyz_to_quat_wxyz,
)


def build_pose_target_from_payload(payload: dict[str, Any]) -> tuple[str, PoseTarget]:
    """Build canonical IK target from UI payload."""
    joint = str(payload["target_joint"])
    pos_cfg = payload["position"]
    rot_cfg = payload["rotation"]

    p = np.array([pos_cfg["x"], pos_cfg["y"], pos_cfg["z"]], dtype=np.float64)
    e = np.array([rot_cfg["roll"], rot_cfg["pitch"], rot_cfg["yaw"]], dtype=np.float64)

    p_m = convert_position_to_m(p, PositionUnit(pos_cfg.get("unit", "m")))
    q = euler_xyz_to_quat_wxyz(e, AngleUnit(rot_cfg.get("unit", "rad")))
    return joint, PoseTarget(position_m=p_m, orientation_wxyz=q)
