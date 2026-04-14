"""Mock-based integration tests for MuJoCo state driver."""

from __future__ import annotations

import sys
import types

import numpy as np
import pytest

from motion_player.backends.mujoco_backend.state_driver import MuJoCoStateDriver
from tests.conftest import make_motion


def _install_fake_mujoco(monkeypatch: pytest.MonkeyPatch) -> None:
    fake = types.ModuleType("mujoco")

    class _Model:
        njnt = 3
        # first joint is free root
        jnt_type = np.array([0, 1, 1], dtype=int)
        jnt_qposadr = np.array([0, 7, 8], dtype=int)
        jnt_bodyid = np.array([0, 1, 2], dtype=int)
        nbody = 1

    class _MjModel:
        @staticmethod
        def from_xml_path(_path: str):
            return _Model()

    class _MjData:
        def __init__(self, _model):
            self.qpos = np.zeros(9, dtype=np.float64)

    fake.MjModel = _MjModel
    fake.MjData = _MjData
    fake.mjtJoint = types.SimpleNamespace(mjJNT_FREE=0)
    fake.mjtObj = types.SimpleNamespace(mjOBJ_JOINT=0)

    def _id2name(_model, _obj, i: int):
        names = ["root", "joint_0", "joint_1"]
        return names[i]

    fake.mj_id2name = _id2name
    fake._forward_calls = 0

    def _forward(_model, _data):
        fake._forward_calls += 1

    def _reset_data(_model, data):
        data.qpos[:] = 0.0

    fake.mj_forward = _forward
    fake.mj_resetData = _reset_data
    monkeypatch.setitem(sys.modules, "mujoco", fake)


@pytest.mark.headless_integration
def test_state_driver_apply_frame_writes_qpos(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_mujoco(monkeypatch)
    motion = make_motion(num_frames=4, num_dofs=2)
    driver = MuJoCoStateDriver("robot.xml", root_joint_name="root")
    driver.bind_motion(motion)

    driver.apply_frame(1)
    np.testing.assert_allclose(driver.data.qpos[0:3], motion.root_pos[1], atol=1e-8)
    # xyzw -> wxyz
    np.testing.assert_allclose(driver.data.qpos[3:7], [1.0, 0.0, 0.0, 0.0], atol=1e-8)
    np.testing.assert_allclose(driver.data.qpos[7], motion.dof_pos[1, 0], atol=1e-8)
    np.testing.assert_allclose(driver.data.qpos[8], motion.dof_pos[1, 1], atol=1e-8)


@pytest.mark.headless_integration
def test_state_driver_invalid_frame_index(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_mujoco(monkeypatch)
    motion = make_motion(num_frames=3, num_dofs=2)
    driver = MuJoCoStateDriver("robot.xml", root_joint_name="root")
    driver.bind_motion(motion)
    with pytest.raises(IndexError):
        driver.apply_frame(3)


@pytest.mark.headless_integration
def test_state_driver_reset_applies_first_frame(monkeypatch: pytest.MonkeyPatch) -> None:
    _install_fake_mujoco(monkeypatch)
    motion = make_motion(num_frames=3, num_dofs=2)
    driver = MuJoCoStateDriver("robot.xml", root_joint_name="root")
    driver.bind_motion(motion)
    driver.apply_frame(2)
    driver.reset()
    np.testing.assert_allclose(driver.data.qpos[0:3], motion.root_pos[0], atol=1e-8)


@pytest.mark.headless_integration
def test_state_driver_exposes_joint_name_and_body_for_dof(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _install_fake_mujoco(monkeypatch)
    driver = MuJoCoStateDriver("robot.xml", root_joint_name="root")
    assert driver.dof_joint_name(0) == "joint_0"
    assert driver.dof_joint_body_id(0) == 1
