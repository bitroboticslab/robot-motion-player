"""Regression tests for viewer state snapshot pose publication."""

from __future__ import annotations

import types

import numpy as np

from motion_player.backends.mujoco_backend.viewer import MuJoCoViewer
from motion_player.core.ui import PlayerState
from motion_player.core.ui.state_monitor import StateMonitorBus


def test_publish_snapshot_includes_selected_joint_world_pose() -> None:
    viewer = MuJoCoViewer.__new__(MuJoCoViewer)
    viewer._state = PlayerState(frame=0, selected_joint_idx=0)
    viewer._motions = [
        types.SimpleNamespace(num_frames=10, fps=30.0, num_dofs=1, joint_names=["joint_0"])
    ]
    viewer._editor_sessions = [types.SimpleNamespace(motion=viewer._motions[0])]
    viewer._monitor_bus = StateMonitorBus()
    viewer._driver = types.SimpleNamespace(
        data=types.SimpleNamespace(
            xpos=np.array([[0.0, 0.0, 0.0], [0.25, -0.10, 0.55]], dtype=np.float64),
            xquat=np.array(
                [[1.0, 0.0, 0.0, 0.0], [0.9238795, 0.0, 0.3826834, 0.0]], dtype=np.float64
            ),
        ),
        dof_joint_body_id=lambda _idx: 1,
        dof_joint_name=lambda _idx: "joint_0",
    )

    viewer._publish_state_snapshot()
    snap = viewer._monitor_bus.latest()
    assert snap is not None
    np.testing.assert_allclose(
        snap.selected_joint_pos_m, np.array([0.25, -0.10, 0.55], dtype=np.float64)
    )
    np.testing.assert_allclose(
        snap.selected_joint_quat_wxyz, np.array([0.9238795, 0.0, 0.3826834, 0.0])
    )
