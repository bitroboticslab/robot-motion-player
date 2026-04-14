"""Tests for MuJoCo XML IK backend core behavior."""

from __future__ import annotations

import numpy as np
import pytest

from motion_player.core.kinematics.ik_backends.mujoco_xml_backend import MujocoXmlIKBackend
from motion_player.core.kinematics.pose_target import PoseTarget


def test_backend_rejects_unknown_target_name() -> None:
    backend = MujocoXmlIKBackend(
        dof_names=("joint_0", "joint_1"),
        fk=lambda q, name: np.zeros(3, dtype=np.float64),
        jac=lambda q, name: np.eye(3, 2, dtype=np.float64),
    )
    with pytest.raises(KeyError):
        backend.solve(
            np.zeros(2, dtype=np.float64),
            {
                "unknown": PoseTarget(
                    position_m=np.ones(3, dtype=np.float64),
                    orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
                )
            },
        )


def test_backend_returns_same_shape_as_input() -> None:
    backend = MujocoXmlIKBackend(
        dof_names=("joint_0", "joint_1"),
        fk=lambda q, name: np.zeros(3, dtype=np.float64),
        jac=lambda q, name: np.eye(3, 2, dtype=np.float64),
    )
    out = backend.solve(
        np.zeros(2, dtype=np.float64),
        {
            "joint_0": PoseTarget(
                position_m=np.array([0.1, 0.0, 0.0], dtype=np.float64),
                orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            )
        },
    )
    assert out.shape == (2,)


def test_backend_can_build_from_runtime_driver_and_solve() -> None:
    class _Model:
        nv = 2

    class _Data:
        def __init__(self) -> None:
            self.qpos = np.zeros(2, dtype=np.float64)
            self.xpos = np.zeros((3, 3), dtype=np.float64)
            self.xquat = np.zeros((3, 4), dtype=np.float64)
            self.xquat[:, 0] = 1.0

    class _FakeMj:
        @staticmethod
        def mj_forward(_model, data) -> None:
            data.xpos[1] = np.array([data.qpos[0], data.qpos[1], 0.0], dtype=np.float64)
            data.xpos[2] = np.array([data.qpos[0] + data.qpos[1], 0.0, 0.0], dtype=np.float64)

        @staticmethod
        def mj_jacBody(_model, _data, jacp, _jacr, body_id: int) -> None:
            jacp[:] = 0.0
            if body_id == 1:
                jacp[:, 0] = np.array([1.0, 0.0, 0.0], dtype=np.float64)
                jacp[:, 1] = np.array([0.0, 1.0, 0.0], dtype=np.float64)
            else:
                jacp[:, 0] = np.array([1.0, 0.0, 0.0], dtype=np.float64)
                jacp[:, 1] = np.array([1.0, 0.0, 0.0], dtype=np.float64)

    class _Driver:
        def __init__(self) -> None:
            self.model = _Model()
            self.data = _Data()
            self._mujoco = _FakeMj()

        @staticmethod
        def dof_qpos_addresses() -> np.ndarray:
            return np.array([0, 1], dtype=int)

        @staticmethod
        def dof_velocity_addresses() -> np.ndarray:
            return np.array([0, 1], dtype=int)

        @staticmethod
        def dof_joint_name(dof_idx: int) -> str:
            return ("joint_0", "joint_1")[dof_idx]

        @staticmethod
        def dof_joint_body_id(dof_idx: int) -> int:
            return (1, 2)[dof_idx]

    backend = MujocoXmlIKBackend.from_runtime_driver(_Driver())
    out = backend.solve(
        np.zeros(2, dtype=np.float64),
        {
            "joint_0": PoseTarget(
                position_m=np.array([0.15, -0.05, 0.0], dtype=np.float64),
                orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            )
        },
    )
    assert out.shape == (2,)
    assert not np.allclose(out, np.zeros(2, dtype=np.float64))


def test_backend_pose_solver_uses_position_and_rotation_weights() -> None:
    backend = MujocoXmlIKBackend(
        dof_names=("joint_0",),
        fk=lambda q, _name: np.array([q[0], 0.0, 0.0], dtype=np.float64),
        jac=lambda _q, _name: np.array([[1.0], [0.0], [0.0]], dtype=np.float64),
    )
    target = PoseTarget(
        position_m=np.array([0.2, 0.0, 0.0], dtype=np.float64),
        orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
    )
    out = backend.solve(np.zeros(1, dtype=np.float64), {"joint_0": target})
    assert out.shape == (1,)
