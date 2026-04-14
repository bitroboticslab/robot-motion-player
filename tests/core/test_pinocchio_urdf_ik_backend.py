"""Tests for Pinocchio URDF IK backend wrapper."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pytest

from motion_player.core.kinematics.ik_backends.pinocchio_urdf_backend import PinocchioUrdfIKBackend
from motion_player.core.kinematics.pose_target import PoseTarget


def test_pin_backend_requires_joint_name_mapping() -> None:
    backend = PinocchioUrdfIKBackend(dof_names=("hip",), solver=lambda q, t: q.copy())
    with pytest.raises(KeyError):
        backend.solve(
            np.zeros(1),
            {
                "knee": PoseTarget(
                    position_m=np.zeros(3, dtype=np.float64),
                    orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
                )
            },
        )


def test_pin_backend_returns_solved_vector() -> None:
    backend = PinocchioUrdfIKBackend(
        dof_names=("hip",),
        solver=lambda q, t: np.asarray([0.25], dtype=np.float64),
    )
    out = backend.solve(
        np.zeros(1),
        {
            "hip": PoseTarget(
                position_m=np.array([0.1, 0.2, 0.3], dtype=np.float64),
                orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            )
        },
    )
    assert out.shape == (1,)
    assert float(out[0]) == 0.25


def test_pin_backend_can_build_from_urdf_and_solve(monkeypatch, tmp_path: Path) -> None:
    urdf = tmp_path / "robot.urdf"
    urdf.write_text("<robot name='r'/>", encoding="utf-8")

    class _Transform:
        def __init__(self, xyz: list[float]) -> None:
            self.translation = np.asarray(xyz, dtype=np.float64)
            self.rotation = np.eye(3, dtype=np.float64)

    class _Data:
        def __init__(self) -> None:
            self.oMi = {1: _Transform([0.0, 0.0, 0.0])}

    class _Joint:
        def __init__(self, nq: int) -> None:
            self.nq = nq

    class _Model:
        nq = 1
        nv = 1
        njoints = 2
        names = ["universe", "hip"]
        joints = [_Joint(0), _Joint(1)]
        idx_qs = [0, 0]

        @staticmethod
        def createData() -> _Data:
            return _Data()

        @staticmethod
        def getJointId(name: str) -> int:
            return 1 if name == "hip" else 0

    class _FakePin:
        @staticmethod
        def buildModelFromUrdf(_path: str) -> _Model:
            return _Model()

        @staticmethod
        def forwardKinematics(_model: _Model, data: _Data, q: np.ndarray) -> None:
            data.oMi[1] = _Transform([float(q[0]), 0.0, 0.0])

        @staticmethod
        def computeJointJacobian(
            _model: _Model,
            _data: _Data,
            _q: np.ndarray,
            _joint_id: int,
        ) -> np.ndarray:
            return np.asarray([[1.0], [0.0], [0.0], [0.0], [0.0], [0.0]], dtype=np.float64)

        @staticmethod
        def integrate(_model: _Model, q: np.ndarray, dq: np.ndarray) -> np.ndarray:
            return np.asarray(q, dtype=np.float64) + np.asarray(dq, dtype=np.float64)

    monkeypatch.setitem(sys.modules, "pin", _FakePin())
    backend = PinocchioUrdfIKBackend.from_urdf_path(urdf)
    out = backend.solve(
        np.zeros(1, dtype=np.float64),
        {
            "hip": PoseTarget(
                position_m=np.array([0.2, 0.0, 0.0], dtype=np.float64),
                orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            )
        },
    )
    assert out.shape == (1,)
    assert float(out[0]) > 0.0


def test_pin_backend_runtime_solver_accepts_pose_target() -> None:
    backend = PinocchioUrdfIKBackend(
        dof_names=("hip",),
        solver=lambda _q, _t: np.asarray([0.12], dtype=np.float64),
    )
    target = PoseTarget(
        position_m=np.array([0.1, 0.0, 0.0], dtype=np.float64),
        orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
    )
    out = backend.solve(np.zeros(1), {"hip": target})
    assert np.isclose(out[0], 0.12)
