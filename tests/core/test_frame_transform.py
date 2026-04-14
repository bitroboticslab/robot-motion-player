from __future__ import annotations

import numpy as np

from motion_player.core.kinematics.frame_transform import (
    compose_pose,
    invert_pose,
    rotate_point_wxyz,
    transform_point,
)


def test_world_local_roundtrip_point() -> None:
    parent_pos = np.array([1.0, 2.0, 3.0], dtype=np.float64)
    parent_quat = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    p_local = np.array([0.1, -0.2, 0.3], dtype=np.float64)
    p_world = transform_point(parent_pos, parent_quat, p_local)
    inv_pos, inv_quat = invert_pose(parent_pos, parent_quat)
    back = transform_point(inv_pos, inv_quat, p_world)
    np.testing.assert_allclose(back, p_local, atol=1e-9)


def test_compose_pose_applies_rotation_and_translation() -> None:
    parent_pos = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    # +90 deg around z-axis in wxyz
    parent_quat = np.array([np.sqrt(0.5), 0.0, 0.0, np.sqrt(0.5)], dtype=np.float64)
    child_local = np.array([1.0, 0.0, 0.0], dtype=np.float64)
    child_quat = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
    pos, quat = compose_pose(parent_pos, parent_quat, child_local, child_quat)
    np.testing.assert_allclose(pos, np.array([1.0, 1.0, 0.0]), atol=1e-6)
    np.testing.assert_allclose(quat, parent_quat, atol=1e-6)


def test_rotate_point_identity_no_change() -> None:
    p = np.array([0.2, 0.3, 0.4], dtype=np.float64)
    out = rotate_point_wxyz(np.array([1.0, 0.0, 0.0, 0.0]), p)
    np.testing.assert_allclose(out, p, atol=1e-9)

