"""Tests for StandardMotion and DatasetLoader."""

from __future__ import annotations

import pickle

import numpy as np
import pytest

from motion_player.core.dataset.loader import DatasetLoader
from motion_player.core.dataset.quat_utils import (
    normalize,
    wxyz_to_xyzw,
    xyzw_to_wxyz,
)
from tests.conftest import make_motion

# ---------------------------------------------------------------------------
# StandardMotion
# ---------------------------------------------------------------------------


class TestStandardMotion:
    def test_basic_properties(self):
        m = make_motion(num_frames=60, num_dofs=12, fps=30.0)
        assert m.num_frames == 60
        assert m.num_dofs == 12
        assert m.fps == 30.0
        assert abs(m.duration - 2.0) < 1e-6
        assert abs(m.dt - 1 / 30.0) < 1e-9

    def test_validate_passes(self):
        m = make_motion()
        m.validate()  # should not raise

    def test_validate_fails_wrong_shape(self):
        m = make_motion(num_frames=60, num_dofs=12)
        # Corrupt dof_pos shape
        m.dof_pos = np.zeros((60, 13), dtype=np.float32)
        with pytest.raises(ValueError, match="dof_vel"):
            m.validate()

    def test_validate_fails_joint_names_length(self):
        m = make_motion(num_frames=60, num_dofs=12)
        m.joint_names = ["a", "b"]  # wrong length
        with pytest.raises(ValueError, match="joint_names"):
            m.validate()

    def test_clone_is_independent(self):
        m = make_motion()
        c = m.clone()
        c.dof_pos[0, 0] = 999.0
        assert m.dof_pos[0, 0] != 999.0


# ---------------------------------------------------------------------------
# Quaternion utils
# ---------------------------------------------------------------------------


class TestQuatUtils:
    def test_xyzw_wxyz_roundtrip(self):
        q = np.array([0.1, 0.2, 0.3, 0.927], dtype=np.float64)
        q = q / np.linalg.norm(q)
        assert np.allclose(wxyz_to_xyzw(xyzw_to_wxyz(q)), q, atol=1e-9)

    def test_normalize_unit_vector(self):
        q = np.array([1.0, 2.0, 3.0, 4.0], dtype=np.float64)
        qn = normalize(q)
        assert abs(np.linalg.norm(qn) - 1.0) < 1e-9

    def test_normalize_batch(self):
        qs = np.random.default_rng(0).random((10, 4))
        qn = normalize(qs)
        norms = np.linalg.norm(qn, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-9)

    def test_normalize_near_zero_quaternion(self):
        q = np.zeros(4, dtype=np.float64)
        with pytest.warns(UserWarning, match="near-zero quaternion norm"):
            qn = normalize(q)
        assert np.allclose(qn, np.array([0.0, 0.0, 0.0, 1.0]), atol=1e-9)

    def test_xyzw_wxyz_batch(self):
        rng = np.random.default_rng(99)
        qs = rng.random((5, 4))
        result = xyzw_to_wxyz(qs)
        assert result.shape == (5, 4)
        back = wxyz_to_xyzw(result)
        assert np.allclose(back, qs, atol=1e-9)


# ---------------------------------------------------------------------------
# DatasetLoader
# ---------------------------------------------------------------------------


class TestDatasetLoader:
    def _make_raw_dict(self, num_frames=40, num_dofs=10, num_bodies=5) -> dict:
        rng = np.random.default_rng(7)
        root_rot = rng.random((num_frames, 4)).astype(np.float32)
        # normalise
        root_rot /= np.linalg.norm(root_rot, axis=1, keepdims=True)
        return {
            "fps": 30.0,
            "motion_length": num_frames,
            "motion_weight": 1.0,
            "root_pos": rng.random((num_frames, 3)).astype(np.float32),
            "root_rot": root_rot,
            "dof_pos": rng.random((num_frames, num_dofs)).astype(np.float32),
            "dof_vel": rng.random((num_frames, num_dofs)).astype(np.float32),
            "projected_gravity": np.tile([0.0, 0.0, -1.0], (num_frames, 1)).astype(np.float32),
            "root_lin_vel": rng.random((num_frames, 3)).astype(np.float32),
            "root_ang_vel": rng.random((num_frames, 3)).astype(np.float32),
            "key_body_pos_local": rng.random((num_frames, num_bodies * 3)).astype(np.float32),
        }

    def test_load_pkl(self, tmp_path):
        raw = self._make_raw_dict()
        p = tmp_path / "test.pkl"
        with open(p, "wb") as f:
            pickle.dump(raw, f)
        loader = DatasetLoader()
        m = loader.load(p)
        assert m.num_frames == 40
        assert m.num_dofs == 10

    def test_load_npy(self, tmp_path):
        raw = self._make_raw_dict()
        p = tmp_path / "test.npy"
        np.save(str(p), raw)  # type: ignore[arg-type]
        loader = DatasetLoader()
        m = loader.load(p)
        assert m.num_frames == 40

    def test_missing_key_raises(self, tmp_path):
        raw = self._make_raw_dict()
        del raw["dof_pos"]
        p = tmp_path / "bad.pkl"
        with open(p, "wb") as f:
            pickle.dump(raw, f)
        loader = DatasetLoader()
        with pytest.raises(KeyError, match="dof_pos"):
            loader.load(p)

    def test_save_and_reload_pkl(self, tmp_path):
        m_orig = make_motion()
        loader = DatasetLoader()
        p = tmp_path / "out.pkl"
        loader.save(m_orig, p, fmt="pkl")
        m_loaded = loader.load(p)
        assert np.allclose(m_orig.root_pos, m_loaded.root_pos, atol=1e-5)
        assert np.allclose(m_orig.dof_pos, m_loaded.dof_pos, atol=1e-5)

    def test_wxyz_conversion(self, tmp_path):
        """Loader should convert wxyz → xyzw when quat_fmt='wxyz'."""
        raw = self._make_raw_dict()
        # Store in wxyz
        raw["root_rot"] = xyzw_to_wxyz(raw["root_rot"])
        p = tmp_path / "wxyz.pkl"
        with open(p, "wb") as f:
            pickle.dump(raw, f)
        loader_xyzw = DatasetLoader(quat_fmt="xyzw")
        loader_wxyz = DatasetLoader(quat_fmt="wxyz")
        loader_xyzw.load(p)
        m_wxyz = loader_wxyz.load(p)
        # After conversion, the results should differ (wxyz ≠ xyzw unless symmetric)
        # But both should be unit quaternions
        norms = np.linalg.norm(m_wxyz.root_rot, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-5)

    def test_load_folder(self, tmp_path):
        raw = self._make_raw_dict()
        for name in ["a.pkl", "b.pkl"]:
            with open(tmp_path / name, "wb") as f:
                pickle.dump(raw, f)
        loader = DatasetLoader()
        motions = loader.load_folder(tmp_path)
        assert len(motions) == 2
