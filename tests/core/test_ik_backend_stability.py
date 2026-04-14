"""Stability regression tests for IK backend iteration updates."""

from __future__ import annotations

import numpy as np

from motion_player.core.kinematics.ik_backends.mujoco_xml_backend import MujocoXmlIKBackend
from motion_player.core.kinematics.pose_target import PoseTarget


def _identity_quat() -> np.ndarray:
    return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)


def test_xml_backend_bounds_single_iteration_joint_update_norm() -> None:
    backend = MujocoXmlIKBackend(
        dof_names=("joint_0", "joint_1"),
        fk=lambda q, _name: np.array([q[0], q[1], 0.0], dtype=np.float64),
        jac=lambda _q, _name: np.array(
            [[1.0, 0.0], [0.0, 1.0], [0.0, 0.0]],
            dtype=np.float64,
        ),
        fk_rot=lambda _q, _name: _identity_quat(),
        jac_rot=lambda _q, _name: np.zeros((3, 2), dtype=np.float64),
        step_size=1.0,
        max_iters=1,
        max_dq_norm=0.05,
    )
    q0 = np.zeros(2, dtype=np.float64)
    target = PoseTarget(position_m=np.array([2.0, 2.0, 0.0], dtype=np.float64), orientation_wxyz=_identity_quat())

    q1 = backend.solve(q0, {"joint_0": target})

    assert np.linalg.norm(q1 - q0, ord=2) <= 0.0500001


def test_xml_backend_skips_ill_conditioned_solve_when_requested() -> None:
    backend = MujocoXmlIKBackend(
        dof_names=("joint_0",),
        fk=lambda q, _name: np.array([q[0], 0.0, 0.0], dtype=np.float64),
        jac=lambda _q, _name: np.zeros((3, 1), dtype=np.float64),
        fk_rot=lambda _q, _name: _identity_quat(),
        jac_rot=lambda _q, _name: np.zeros((3, 1), dtype=np.float64),
        damping=0.0,
        step_size=1.0,
        max_iters=1,
        min_condition_eps=1e-8,
    )
    q0 = np.zeros(1, dtype=np.float64)
    target = PoseTarget(position_m=np.array([1.0, 0.0, 0.0], dtype=np.float64), orientation_wxyz=_identity_quat())

    q1 = backend.solve(q0, {"joint_0": target})

    np.testing.assert_allclose(q1, q0)
