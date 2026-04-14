from __future__ import annotations

import numpy as np

from motion_player.core.kinematics.ik_solver import IKSolver
from motion_player.core.kinematics.pose_target import PoseTarget


class _BackendStub:
    def solve(self, current_qpos: np.ndarray, targets: dict[str, PoseTarget]) -> np.ndarray:
        del targets
        out = current_qpos.copy()
        out[0] += 0.1
        return out


def test_ik_solver_uses_injected_backend() -> None:
    solver = IKSolver(backend=_BackendStub())
    cur = np.zeros(12, dtype=np.float64)
    out = solver.solve(
        cur,
        {
            "left_foot": PoseTarget(
                position_m=np.array([0.1, 0.0, 0.0], dtype=np.float64),
                orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            )
        },
    )
    assert out[0] == 0.1
