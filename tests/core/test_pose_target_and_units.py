from __future__ import annotations

import numpy as np
import pytest

from motion_player.core.kinematics.pose_target import PoseTarget
from motion_player.core.kinematics.unit_conversion import (
    AngleUnit,
    PositionUnit,
    convert_position_to_m,
    euler_xyz_to_quat_wxyz,
    quat_wxyz_to_euler_xyz,
)


def test_position_unit_conversion_to_m() -> None:
    vec = np.array([100.0, 20.0, 5.0], dtype=np.float64)
    out = convert_position_to_m(vec, PositionUnit.CM)
    np.testing.assert_allclose(out, np.array([1.0, 0.2, 0.05], dtype=np.float64))


def test_euler_deg_roundtrip_quaternion() -> None:
    euler_deg = np.array([10.0, -20.0, 30.0], dtype=np.float64)
    quat = euler_xyz_to_quat_wxyz(euler_deg, AngleUnit.DEG)
    assert np.isclose(np.linalg.norm(quat), 1.0)
    back = quat_wxyz_to_euler_xyz(quat, AngleUnit.DEG)
    np.testing.assert_allclose(back, euler_deg, atol=1e-6)


def test_pose_target_validation_rejects_wrong_shapes() -> None:
    with pytest.raises(ValueError):
        PoseTarget(
            position_m=np.array([1.0, 2.0], dtype=np.float64),
            orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
        )
