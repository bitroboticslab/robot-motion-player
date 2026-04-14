# Copyright 2026 Mr-tooth
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""MuJoCoStateDriver — writes StandardMotion frame state into MuJoCo mjData.

Replay Mode (v0.1): KINEMATIC
------------------------------
Each frame is applied by directly setting ``mjData.qpos`` (free joint:
``pos[3] + quat[4]`` in wxyz, followed by ``dof_pos``) and then calling
``mj_forward()`` to update all kinematic quantities.  Physics integration is
**not** performed, so the replay is a faithful reconstruction of the data
regardless of dynamic feasibility.

Extension point (v0.2): override :meth:`apply_frame` to implement physics
replay via PD control or torque tracking.

Free joint layout (MuJoCo convention)
--------------------------------------
A MuJoCo free joint occupies 7 qpos values::

    qpos[free_adr:free_adr+3]  = position (x, y, z)
    qpos[free_adr+3:free_adr+7] = quaternion (w, x, y, z)  ← wxyz!

The :class:`MuJoCoStateDriver` converts the StandardMotion ``root_rot`` from
xyzw to wxyz before writing.

Quaternion convention reminder
--------------------------------
StandardMotion stores ``root_rot`` as **xyzw** (scalar-last).
MuJoCo expects **wxyz** (scalar-first).
Conversion: ``[w, x, y, z] = [q[3], q[0], q[1], q[2]]``.
"""

from __future__ import annotations

from pathlib import Path

import numpy as np

from motion_player.core.dataset.motion import StandardMotion
from motion_player.core.dataset.quat_utils import xyzw_to_wxyz


class MuJoCoStateDriver:
    """Drives MuJoCo mjData from a StandardMotion.

    Parameters
    ----------
    model_path:
        Path to the robot MJCF ``.xml`` file.
    root_joint_name:
        Name of the free joint in the MJCF that represents the root body.
        Defaults to ``"root"``.
    """

    def __init__(
        self,
        model_path: str | Path,
        root_joint_name: str = "root",
    ) -> None:
        try:
            import mujoco  # type: ignore[import]
        except ImportError as exc:
            raise ImportError(
                "mujoco package is required for MuJoCoStateDriver. "
                "Install it with: pip install mujoco"
            ) from exc

        self._mujoco = mujoco
        self.model_path = Path(model_path)
        self.model = mujoco.MjModel.from_xml_path(str(model_path))
        self.data = mujoco.MjData(self.model)
        self._root_joint_name = root_joint_name
        self._free_joint_adr: int | None = None
        self._dof_qpos_adr: np.ndarray | None = None
        self._dof_joint_ids: np.ndarray | None = None
        self._motion: StandardMotion | None = None

        self._discover_joints()

    # ------------------------------------------------------------------
    # Setup
    # ------------------------------------------------------------------

    def _discover_joints(self) -> None:
        """Cache qpos addresses for the root free joint and DOF joints."""
        mj = self._mujoco
        model = self.model

        # Find root free joint address
        for i in range(model.njnt):
            name = mj.mj_id2name(model, mj.mjtObj.mjOBJ_JOINT, i)
            if name == self._root_joint_name:
                if model.jnt_type[i] != mj.mjtJoint.mjJNT_FREE:
                    raise ValueError(
                        f"Joint '{self._root_joint_name}' is not a free joint "
                        f"(type={model.jnt_type[i]})."
                    )
                self._free_joint_adr = int(model.jnt_qposadr[i])
                break

        if self._free_joint_adr is None:
            raise ValueError(
                f"Free joint '{self._root_joint_name}' not found in the model. "
                "Check your MJCF and root_joint_name setting."
            )

        # Collect qpos addresses for all non-free joints (DOFs)
        addrs: list[int] = []
        joint_ids: list[int] = []
        for i in range(model.njnt):
            if model.jnt_type[i] != mj.mjtJoint.mjJNT_FREE:
                addrs.append(int(model.jnt_qposadr[i]))
                joint_ids.append(i)
        self._dof_qpos_adr = np.array(addrs, dtype=int)
        self._dof_joint_ids = np.array(joint_ids, dtype=int)

    def bind_motion(self, motion: StandardMotion) -> None:
        """Bind a :class:`~motion_player.core.dataset.motion.StandardMotion` to this driver.

        Parameters
        ----------
        motion:
            The motion to replay.
        """
        if motion.num_dofs != len(self._dof_qpos_adr):
            raise ValueError(
                f"Motion has {motion.num_dofs} DOFs but model has "
                f"{len(self._dof_qpos_adr)} non-free joints."
            )
        self._motion = motion

    def reset(self) -> None:
        """Reset MuJoCo data and current playback frame state."""
        self._mujoco.mj_resetData(self.model, self.data)
        if self._motion is not None:
            self.apply_frame(0)

    def close(self) -> None:
        """Release backend runtime state (no-op for MuJoCo Python bindings)."""
        # MuJoCo Python objects are managed by GC; keep explicit API for parity.
        return None

    def dof_joint_name(self, dof_idx: int) -> str:
        """Return MuJoCo joint name for the given DOF index."""
        joint_id = int(self._dof_joint_ids[dof_idx])
        return str(
            self._mujoco.mj_id2name(
                self.model,
                self._mujoco.mjtObj.mjOBJ_JOINT,
                joint_id,
            )
        )

    def dof_joint_body_id(self, dof_idx: int) -> int:
        """Return body id owning the given DOF index."""
        joint_id = int(self._dof_joint_ids[dof_idx])
        return int(self.model.jnt_bodyid[joint_id])

    def dof_qpos_addresses(self) -> np.ndarray:
        """Return qpos addresses for non-free joints in motion DOF order."""
        return np.array(self._dof_qpos_adr, dtype=int, copy=True)

    def dof_velocity_addresses(self) -> np.ndarray:
        """Return velocity-space addresses (nv indices) for non-free joints."""
        addrs = [int(self.model.jnt_dofadr[int(jid)]) for jid in self._dof_joint_ids]
        return np.array(addrs, dtype=int)

    @staticmethod
    def is_available() -> bool:
        """Return whether MuJoCo runtime is importable."""
        try:
            import mujoco  # type: ignore[import]  # noqa: F401

            return True
        except ImportError:
            return False

    # ------------------------------------------------------------------
    # Frame application
    # ------------------------------------------------------------------

    def apply_frame(self, frame_idx: int) -> None:
        """Write motion frame *frame_idx* into ``mjData.qpos`` and call ``mj_forward``.

        Parameters
        ----------
        frame_idx:
            Zero-based frame index.  Must be in ``[0, motion.num_frames)``.

        Notes
        -----
        Override this method in a subclass to implement physics-based replay
        (v0.2): instead of directly setting ``qpos``, compute joint torques
        via PD control and step the physics.
        """
        if self._motion is None:
            raise RuntimeError("No motion bound; call bind_motion() first.")
        if not isinstance(frame_idx, int):
            raise TypeError(f"frame_idx must be int, got {type(frame_idx).__name__}.")
        if frame_idx < 0 or frame_idx >= self._motion.num_frames:
            raise IndexError(
                f"Frame {frame_idx} out of range [0, {self._motion.num_frames})."
            )

        m = self._motion
        mj = self._mujoco

        # Root position (x, y, z)
        adr = self._free_joint_adr
        self.data.qpos[adr: adr + 3] = m.root_pos[frame_idx]

        # Root quaternion: xyzw → wxyz
        q_xyzw = m.root_rot[frame_idx].astype(np.float64)
        q_wxyz = xyzw_to_wxyz(q_xyzw)
        self.data.qpos[adr + 3: adr + 7] = q_wxyz

        # DOF positions
        for j, dof_adr in enumerate(self._dof_qpos_adr):
            self.data.qpos[dof_adr] = m.dof_pos[frame_idx, j]

        # Update all kinematic quantities
        mj.mj_forward(self.model, self.data)
