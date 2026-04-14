from __future__ import annotations

import numpy as np

from motion_player.core.editing.editor_session import EditorSession
from motion_player.core.kinematics.pose_target import PoseTarget
from tests.conftest import make_motion


def test_apply_dof_edit_with_propagation_keeps_anchor_keyframe() -> None:
    motion = make_motion(num_frames=40, num_dofs=6)
    session = EditorSession(motion)
    session.mark_keyframe(10)
    session.mark_keyframe(20)

    base_anchor = float(motion.dof_pos[20, 1])
    session.apply_dof_edit(frame=10, joint_idx=1, delta=0.2, propagate_radius=12)

    assert motion.dof_pos[10, 1] > base_anchor - 10.0
    assert abs(float(motion.dof_pos[20, 1]) - base_anchor) < 1e-6


def test_undo_redo_roundtrip_on_dof_edit() -> None:
    motion = make_motion(num_frames=20, num_dofs=4)
    session = EditorSession(motion)

    original = float(motion.dof_pos[5, 2])
    session.apply_dof_edit(frame=5, joint_idx=2, delta=0.3, propagate_radius=0)
    changed = float(motion.dof_pos[5, 2])

    assert changed != original

    session.undo()
    assert float(motion.dof_pos[5, 2]) == original

    session.redo()
    assert float(motion.dof_pos[5, 2]) == changed


def test_keyframe_list_is_sorted_and_unique() -> None:
    motion = make_motion(num_frames=20)
    session = EditorSession(motion)

    session.mark_keyframe(8)
    session.mark_keyframe(3)
    session.mark_keyframe(8)  # toggle off
    session.mark_keyframe(3)  # toggle off
    session.mark_keyframe(5)

    assert session.keyframes() == [5]


def test_mark_history_tracks_insertion_order() -> None:
    motion = make_motion(num_frames=20)
    session = EditorSession(motion)

    session.mark_keyframe(3)
    session.mark_keyframe(9)
    session.mark_keyframe(5)
    session.mark_keyframe(9)  # toggle off removes from history

    assert session.keyframes() == [3, 5]
    assert session.mark_history() == [3, 5]


def test_next_prev_marked_frame_wraps() -> None:
    motion = make_motion(num_frames=20)
    session = EditorSession(motion)
    session.mark_keyframe(2)
    session.mark_keyframe(7)
    session.mark_keyframe(14)

    assert session.next_marked_frame(6) == 7
    assert session.next_marked_frame(14) == 2
    assert session.prev_marked_frame(6) == 2
    assert session.prev_marked_frame(2) == 14


def test_apply_eef_edit_updates_dof_vector_with_solver() -> None:
    motion = make_motion(num_frames=20, num_dofs=6)

    class _IkStub:
        def solve(self, current_qpos, targets):
            del targets
            out = current_qpos.copy()
            out[2] += 0.05
            return out

    session = EditorSession(motion, ik_solver=_IkStub())
    before = float(motion.dof_pos[4, 2])

    session.apply_eef_edit(
        frame=4,
        targets={
            "left_foot": PoseTarget(
                position_m=np.array([0.0, 0.0, 0.0], dtype=np.float64),
                orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            )
        },
    )

    assert abs(float(motion.dof_pos[4, 2]) - (before + 0.05)) < 1e-6
