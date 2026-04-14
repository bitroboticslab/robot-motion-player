"""Tests for kinematics modules (joint mapper, auditor)."""

from __future__ import annotations

import numpy as np
import pytest

from motion_player.core.kinematics.joint_mapper import JointMapper
from motion_player.core.kinematics.joint_order_auditor import (
    JointOrderAuditor,
)
from tests.conftest import make_motion

# ---------------------------------------------------------------------------
# JointMapper
# ---------------------------------------------------------------------------


class TestJointMapper:
    def test_identity_mapping(self):
        """No name lists → identity pass-through."""
        m = make_motion(num_frames=10, num_dofs=4)
        mapper = JointMapper()
        result = mapper.apply(m.dof_pos)
        assert np.allclose(result, m.dof_pos)

    def test_exact_name_match(self):
        names = ["hip", "knee", "ankle"]
        mapper = JointMapper(
            dataset_joint_names=names,
            model_joint_names=names,
        )
        dof = np.arange(6).reshape(2, 3).astype(np.float32)
        result = mapper.apply(dof)
        assert np.allclose(result, dof)

    def test_name_reorder(self):
        """Dataset order [a,b,c] → model order [c,a,b]."""
        mapper = JointMapper(
            dataset_joint_names=["a", "b", "c"],
            model_joint_names=["c", "a", "b"],
        )
        dof = np.array([[1.0, 2.0, 3.0]], dtype=np.float32)
        result = mapper.apply(dof)
        assert np.allclose(result, [[3.0, 1.0, 2.0]])

    def test_sign_flip(self):
        mapper = JointMapper(
            dataset_joint_names=["j0", "j1"],
            model_joint_names=["j0", "j1"],
            sign_flip={"j1": -1.0},
        )
        dof = np.array([[1.0, 2.0]], dtype=np.float32)
        result = mapper.apply(dof)
        assert abs(result[0, 1] - (-2.0)) < 1e-6

    def test_offset(self):
        mapper = JointMapper(
            dataset_joint_names=["j0"],
            model_joint_names=["j0"],
            offset={"j0": 0.5},
        )
        dof = np.array([[1.0]], dtype=np.float32)
        result = mapper.apply(dof)
        assert abs(result[0, 0] - 1.5) < 1e-6

    def test_name_map_translation(self):
        mapper = JointMapper(
            dataset_joint_names=["hip_yaw"],
            model_joint_names=["HipYaw"],
            name_map={"hip_yaw": "HipYaw"},
        )
        dof = np.array([[0.3]], dtype=np.float32)
        result = mapper.apply(dof)
        assert np.allclose(result, dof)

    def test_missing_joint_fills_zero(self):
        mapper = JointMapper(
            dataset_joint_names=["a"],
            model_joint_names=["a", "b"],  # "b" not in dataset
        )
        dof = np.array([[1.0]], dtype=np.float32)
        result = mapper.apply(dof)
        assert result.shape == (1, 2)
        assert abs(result[0, 1]) < 1e-9  # filled with zero


# ---------------------------------------------------------------------------
# JointOrderAuditor
# ---------------------------------------------------------------------------


class TestJointOrderAuditor:
    def test_audit_count_match(self):
        m = make_motion(num_frames=10, num_dofs=4)
        m.joint_names = ["a", "b", "c", "d"]
        auditor = JointOrderAuditor(model_joint_names=["a", "b", "c", "d"])
        report = auditor.audit(m)
        assert not report.count_mismatch
        assert report.is_ok()

    def test_audit_count_mismatch(self):
        m = make_motion(num_frames=10, num_dofs=4)
        auditor = JointOrderAuditor(model_joint_names=["a", "b"])
        report = auditor.audit(m)
        assert report.count_mismatch

    def test_audit_name_mismatch(self):
        m = make_motion(num_frames=10, num_dofs=3)
        m.joint_names = ["a", "b", "c"]
        auditor = JointOrderAuditor(model_joint_names=["a", "b", "X"])
        report = auditor.audit(m)
        assert "X" in report.unmatched_model
        assert not report.is_ok()

    def test_apply_permutation(self):
        m = make_motion(num_frames=5, num_dofs=3)
        m.joint_names = ["j0", "j1", "j2"]
        m.dof_pos[:] = np.array([[0.0, 1.0, 2.0]])

        auditor = JointOrderAuditor(model_joint_names=["j2", "j0", "j1"])
        perm = [2, 0, 1]
        fixed = auditor.apply_permutation(m, perm)
        assert np.allclose(fixed.dof_pos[0], [2.0, 0.0, 1.0])
        assert fixed.joint_names == ["j2", "j0", "j1"]

    def test_generate_sidecar_yaml(self, tmp_path):
        m = make_motion(num_frames=5, num_dofs=3)
        m.joint_names = ["j0", "j1", "j2"]
        auditor = JointOrderAuditor(model_joint_names=["j0", "j1", "j2"])
        out = tmp_path / "joint_order.yaml"
        auditor.generate_sidecar_yaml(m, out)
        assert out.exists()
        import yaml

        data = yaml.safe_load(out.read_text())
        assert data["dataset_dof_count"] == 3

    def test_register_custom_strategy(self):
        m = make_motion(num_frames=5, num_dofs=3)
        auditor = JointOrderAuditor()

        def my_strategy(motion, **kwargs):
            c = motion.clone()
            c.dof_pos[:] = 0.0
            return c

        auditor.register_strategy("zero_dof", my_strategy)
        result = auditor.apply_strategy("zero_dof", m)
        assert np.allclose(result.dof_pos, 0.0)

    def test_unknown_strategy_raises(self):
        auditor = JointOrderAuditor()
        with pytest.raises(KeyError):
            auditor.apply_strategy("nonexistent", make_motion())
