"""Shared test fixtures and helpers."""

from __future__ import annotations

import numpy as np
import pytest

from motion_player.backends.isaac_backend import IsaacBackend
from motion_player.core.dataset.motion import StandardMotion


def make_motion(
    num_frames: int = 60,
    num_dofs: int = 12,
    fps: float = 30.0,
    num_bodies: int = 20,
    rng: np.random.Generator | None = None,
) -> StandardMotion:
    """Create a synthetic StandardMotion for testing.

    Parameters
    ----------
    num_frames:
        Number of playable frames.
    num_dofs:
        Number of degrees of freedom.
    fps:
        Frame rate.
    num_bodies:
        Number of bodies included in key_body_pos_local.
    rng:
        Optional random generator (deterministic if provided).
    """
    if rng is None:
        rng = np.random.default_rng(42)

    # Root position: walk forward along X
    t = np.linspace(0, num_frames / fps, num_frames)
    root_pos = np.stack([t * 0.5, np.zeros(num_frames), np.full(num_frames, 0.9)], axis=1).astype(
        np.float32
    )

    # Root rotation: identity quaternions (xyzw)
    root_rot = np.zeros((num_frames, 4), dtype=np.float32)
    root_rot[:, 3] = 1.0  # w = 1 → identity

    # Small random DOF motion
    dof_pos = (rng.random((num_frames, num_dofs)) * 0.2 - 0.1).astype(np.float32)
    dof_vel = np.gradient(dof_pos, 1.0 / fps, axis=0).astype(np.float32)

    projected_gravity = np.tile([0.0, 0.0, -1.0], (num_frames, 1)).astype(np.float32)
    root_lin_vel = np.zeros((num_frames, 3), dtype=np.float32)
    root_lin_vel[:, 0] = 0.5
    root_ang_vel = np.zeros((num_frames, 3), dtype=np.float32)

    key_body_pos_local = rng.random((num_frames, num_bodies * 3)).astype(np.float32)

    return StandardMotion(
        fps=fps,
        root_pos=root_pos,
        root_rot=root_rot,
        dof_pos=dof_pos,
        dof_vel=dof_vel,
        projected_gravity=projected_gravity,
        root_lin_vel=root_lin_vel,
        root_ang_vel=root_ang_vel,
        key_body_pos_local=key_body_pos_local,
        joint_names=[f"joint_{i}" for i in range(num_dofs)],
        source_path="synthetic",
    )


@pytest.fixture
def motion() -> StandardMotion:
    """Pytest fixture: 60-frame, 12-DOF synthetic motion."""
    return make_motion()


@pytest.fixture
def motion_20dof() -> StandardMotion:
    """Pytest fixture: 120-frame, 20-DOF synthetic motion."""
    return make_motion(num_frames=120, num_dofs=20)


@pytest.fixture
def isaac_backend_mock():
    """Mock Isaac backend for tests without Isaac runtime."""

    class _IsaacBackendMock(IsaacBackend):
        def __init__(self) -> None:
            self._task_class = None
            self._motion = None

        @staticmethod
        def is_available() -> bool:
            return True

        def apply_frame(self, frame_idx: int) -> None:
            if self._motion is None:
                raise RuntimeError("No motion bound; call bind_motion() first.")
            if frame_idx < 0 or frame_idx >= self._motion.num_frames:
                raise IndexError(f"Frame {frame_idx} out of range [0, {self._motion.num_frames}).")

    return _IsaacBackendMock()
