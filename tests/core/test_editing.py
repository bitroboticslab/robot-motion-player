"""Tests for motion editing modules."""

from __future__ import annotations

import numpy as np
import pytest

from motion_player.core.editing.edit_history import EditHistory
from motion_player.core.editing.frame_editor import FrameEditor
from motion_player.core.editing.segment_editor import SegmentEditor, _slerp
from tests.conftest import make_motion

# ---------------------------------------------------------------------------
# EditHistory
# ---------------------------------------------------------------------------


class TestEditHistory:
    def test_push_and_undo(self):
        m = make_motion(num_frames=10)
        hist = EditHistory()
        hist.push(m)
        m.dof_pos[0, 0] = 999.0
        restored = hist.undo()
        assert restored.dof_pos[0, 0] != 999.0

    def test_double_undo_raises(self):
        hist = EditHistory()
        with pytest.raises(IndexError):
            hist.undo()

    def test_redo_after_undo(self):
        m = make_motion(num_frames=10)
        hist = EditHistory()
        hist.push(m)
        hist.undo()
        assert hist.can_redo()

    def test_max_depth(self):
        m = make_motion(num_frames=5)
        hist = EditHistory(max_depth=3)
        for _ in range(10):
            hist.push(m)
        assert len(hist._undo_stack) <= 3

    def test_new_push_clears_redo(self):
        m = make_motion(num_frames=5)
        hist = EditHistory()
        hist.push(m)
        hist.undo()
        assert hist.can_redo()
        hist.push(m)
        assert not hist.can_redo()


# ---------------------------------------------------------------------------
# FrameEditor
# ---------------------------------------------------------------------------


class TestFrameEditor:
    def test_edit_dof_increments_value(self):
        m = make_motion(num_frames=20, num_dofs=8)
        orig_val = float(m.dof_pos[5, 2])
        editor = FrameEditor(m)
        editor.edit_dof(frame=5, joint_idx=2, delta=0.1, push_history=False)
        assert abs(m.dof_pos[5, 2] - (orig_val + 0.1)) < 1e-5

    def test_edit_root_pos_adds_delta(self):
        m = make_motion(num_frames=20)
        orig_pos = m.root_pos[3].copy()
        editor = FrameEditor(m)
        editor.edit_root_pos(3, np.array([0.1, 0.0, 0.0]), push_history=False)
        assert abs(m.root_pos[3, 0] - (orig_pos[0] + 0.1)) < 1e-5

    def test_edit_root_rot_normalises(self):
        m = make_motion(num_frames=20)
        editor = FrameEditor(m)
        editor.edit_root_rot(0, np.array([0.0, 0.0, 0.1]), push_history=False)
        norm = np.linalg.norm(m.root_rot[0])
        assert abs(norm - 1.0) < 1e-5

    def test_undo_restores_state(self):
        m = make_motion(num_frames=20, num_dofs=8)
        orig_val = float(m.dof_pos[5, 2])
        editor = FrameEditor(m)
        editor.edit_dof(frame=5, joint_idx=2, delta=0.5)  # push_history=True default
        editor.undo()
        assert abs(m.dof_pos[5, 2] - orig_val) < 1e-5

    def test_clamp_joint_limits(self):
        m = make_motion(num_frames=10, num_dofs=4)
        m.dof_pos[0, :] = 5.0  # way above limits
        lo = np.full(4, -1.0)
        hi = np.full(4, 1.0)
        editor = FrameEditor(m, joint_lower_limits=lo, joint_upper_limits=hi)
        editor.clamp_joint_limits(0)
        assert np.all(m.dof_pos[0] <= 1.0)
        assert np.all(m.dof_pos[0] >= -1.0)

    def test_out_of_range_frame_raises(self):
        m = make_motion(num_frames=10)
        editor = FrameEditor(m)
        with pytest.raises(IndexError):
            editor.edit_dof(frame=100, joint_idx=0, delta=0.1, push_history=False)


# ---------------------------------------------------------------------------
# SegmentEditor
# ---------------------------------------------------------------------------


class TestSegmentEditor:
    def test_keyframe_interpolate_slerp(self):
        m = make_motion(num_frames=50, num_dofs=6)
        # Save anchor values
        q_start = m.root_rot[10].copy()
        q_end = m.root_rot[40].copy()
        seg = SegmentEditor(m)
        seg.keyframe_interpolate(10, 40, mode="slerp")
        # Anchors should be unchanged
        assert np.allclose(m.root_rot[10], q_start, atol=1e-5)
        assert np.allclose(m.root_rot[40], q_end, atol=1e-5)
        # Intermediate quats should be unit length
        for i in range(10, 41):
            norm = np.linalg.norm(m.root_rot[i])
            assert abs(norm - 1.0) < 1e-5, f"Frame {i}: norm={norm}"

    def test_keyframe_interpolate_spline(self):
        m = make_motion(num_frames=50, num_dofs=6)
        seg = SegmentEditor(m)
        seg.keyframe_interpolate(5, 45, mode="spline")
        # Check that the interpolated dof_pos is within a reasonable range
        assert np.all(np.isfinite(m.dof_pos[5:46]))

    def test_smooth_segment_savgol(self):
        m = make_motion(num_frames=100, num_dofs=8)
        # Inject noise
        rng = np.random.default_rng(1)
        m.dof_pos += rng.random(m.dof_pos.shape).astype(np.float32) * 0.5
        seg = SegmentEditor(m)
        orig_dof = m.dof_pos[10:50].copy()
        seg.smooth_segment(10, 49, "dof_pos", filter_type="savgol", window_length=7)
        smoothed = m.dof_pos[10:50]
        # Smoothed variance should be lower
        assert smoothed.var() <= orig_dof.var() + 0.01

    def test_smooth_segment_butter(self):
        m = make_motion(num_frames=100, num_dofs=4)
        seg = SegmentEditor(m)
        seg.smooth_segment(0, 99, "dof_pos", filter_type="butter", cutoff_hz=5.0)
        assert np.all(np.isfinite(m.dof_pos))

    def test_propagate_edit(self):
        m = make_motion(num_frames=60, num_dofs=4)
        orig = m.dof_pos.copy()
        delta = np.array([0.1, 0.0, 0.0, 0.0])
        seg = SegmentEditor(m)
        seg.propagate_edit(anchor_frame=10, delta_dof=delta, decay_frames=10)
        # At anchor, delta should be applied with weight 1.0
        assert m.dof_pos[10, 0] > orig[10, 0]
        # After decay_frames, should be back to original
        assert abs(m.dof_pos[21, 0] - orig[21, 0]) < 1e-5

    def test_invalid_segment_raises(self):
        m = make_motion(num_frames=20)
        seg = SegmentEditor(m)
        with pytest.raises(IndexError):
            seg.keyframe_interpolate(15, 25)

    def test_slerp_antipodal_is_finite(self):
        q0 = np.array([0.0, 0.0, 0.0, 1.0], dtype=np.float64)
        q1 = np.array([0.0, 0.0, 0.0, -1.0], dtype=np.float64)
        t = np.linspace(0.0, 1.0, 11)
        out = _slerp(q0, q1, t)
        assert np.all(np.isfinite(out))
        norms = np.linalg.norm(out, axis=1)
        assert np.allclose(norms, 1.0, atol=1e-6)
