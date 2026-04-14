from __future__ import annotations

import numpy as np

from motion_player.core.editing.editor_session import EditorSession
from motion_player.core.kinematics.pose_target import PoseTarget
from tests.conftest import make_motion


class _ShiftIk:
    def solve(self, current_qpos, targets):
        del targets
        out = current_qpos.copy()
        out[0] += 0.2
        return out


def test_apply_eef_edit_propagates_decay_to_following_frames() -> None:
    motion = make_motion(num_frames=40, num_dofs=6)
    session = EditorSession(motion, ik_solver=_ShiftIk())
    base = motion.dof_pos.copy()
    session.apply_eef_edit(
        frame=5,
        targets={
            "joint_0": PoseTarget(
                position_m=np.zeros(3, dtype=np.float64),
                orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            )
        },
        propagate_radius=6,
    )
    assert motion.dof_pos[5, 0] > base[5, 0]
    assert motion.dof_pos[9, 0] > base[9, 0]
    assert abs(float(motion.dof_pos[20, 0] - base[20, 0])) < 1e-6

