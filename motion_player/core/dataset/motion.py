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

"""StandardMotion — canonical in-memory motion representation.

This dataclass is the single source of truth for motion data inside
robot-motion-player.  All backends, metrics modules, and editors consume
a ``StandardMotion`` object rather than raw numpy dicts.

Compatibility notes
-------------------
* ``root_rot`` is stored as **xyzw** (scalar-last) to match the rsl-rl-ex /
  motion_loader convention.  MuJoCo requires **wxyz**; backends must convert
  using :func:`motion_player.core.dataset.quat_utils.xyzw_to_wxyz`.
* ``N`` equals ``motion_length`` from the standard file (i.e. the ``N-1``
  t₀-aligned frames produced by rsl-rl-ex ``data_builder``).
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass
class StandardMotion:
    """Canonical in-memory motion representation.

    All arrays share the same first dimension ``N`` (number of playable
    frames, equal to the ``motion_length`` field in the standard file).

    Parameters
    ----------
    fps:
        Frame rate of the original capture (e.g. 30.0 or 60.0).
    root_pos:
        Root position in world frame, shape ``(N, 3)``, metres.
    root_rot:
        Root quaternion in **xyzw** (scalar-last) convention, shape ``(N, 4)``.
    dof_pos:
        Joint positions in radians, shape ``(N, D)`` where *D* is the number
        of degrees of freedom.
    dof_vel:
        Joint velocities in rad/s, shape ``(N, D)``.  Computed via finite
        difference in the standard pipeline.
    projected_gravity:
        World gravity vector ``[0, 0, -1]`` projected into the root-local
        frame, shape ``(N, 3)``.  Used as AMP discriminator input.
    root_lin_vel:
        Root linear velocity in the root-local frame, shape ``(N, 3)``.
    root_ang_vel:
        Root angular velocity in the root-local frame, shape ``(N, 3)``.
        Derived from relative rotations (rotvec / dt) in the standard pipeline.
    key_body_pos_local:
        All body positions in the root-local frame, flattened to
        shape ``(N, K*3)`` where *K* is the total number of bodies.
        Downstream consumers (e.g. LeggedLabUltra) select a subset of
        bodies (typically four limb end-effectors) at training time.
    joint_names:
        Optional list of joint/DOF names matching the columns of ``dof_pos``.
        Not always present in the standard file; can be injected by
        :class:`~motion_player.core.kinematics.joint_order_auditor.JointOrderAuditor`.
    source_path:
        Optional path of the file this motion was loaded from; used for
        logging and export.
    motion_weight:
        Sampling weight for this clip (used by motion_loader during training).
    """

    fps: float
    root_pos: np.ndarray  # (N, 3)   world frame, metres
    root_rot: np.ndarray  # (N, 4)   xyzw scalar-last
    dof_pos: np.ndarray  # (N, D)   radians
    dof_vel: np.ndarray  # (N, D)   rad/s
    projected_gravity: np.ndarray  # (N, 3)   root-local
    root_lin_vel: np.ndarray  # (N, 3)   root-local m/s
    root_ang_vel: np.ndarray  # (N, 3)   root-local rad/s
    key_body_pos_local: np.ndarray  # (N, K*3) root-local metres
    joint_names: list[str] | None = None
    source_path: str | None = None
    motion_weight: float = 1.0

    # ------------------------------------------------------------------
    # Derived properties
    # ------------------------------------------------------------------

    @property
    def num_frames(self) -> int:
        """Number of playable frames (*N*)."""
        return int(self.root_pos.shape[0])

    @property
    def num_dofs(self) -> int:
        """Number of degrees of freedom (*D*)."""
        return int(self.dof_pos.shape[1])

    @property
    def duration(self) -> float:
        """Clip duration in seconds."""
        return self.num_frames / self.fps

    @property
    def dt(self) -> float:
        """Time step between consecutive frames in seconds."""
        return 1.0 / self.fps

    # ------------------------------------------------------------------
    # Validation
    # ------------------------------------------------------------------

    def validate(self) -> None:
        """Raise ``ValueError`` if array shapes are inconsistent."""
        n = self.num_frames
        d = self.num_dofs
        expected: dict[str, tuple[int, ...]] = {
            "root_pos": (n, 3),
            "root_rot": (n, 4),
            "dof_pos": (n, d),
            "dof_vel": (n, d),
            "projected_gravity": (n, 3),
            "root_lin_vel": (n, 3),
            "root_ang_vel": (n, 3),
        }
        for attr, shape in expected.items():
            arr = getattr(self, attr)
            if arr.shape != shape:
                raise ValueError(f"StandardMotion.{attr}: expected shape {shape}, got {arr.shape}")
        # key_body_pos_local: first dim must be N, second must be multiple of 3
        kbl = self.key_body_pos_local
        if kbl.shape[0] != n:
            raise ValueError(
                f"StandardMotion.key_body_pos_local: first dim must be {n}, got {kbl.shape[0]}"
            )
        if kbl.shape[1] % 3 != 0:
            raise ValueError(
                "StandardMotion.key_body_pos_local: second dim must be "
                f"a multiple of 3, got {kbl.shape[1]}"
            )
        if self.joint_names is not None and len(self.joint_names) != d:
            raise ValueError(
                f"StandardMotion.joint_names: length {len(self.joint_names)} "
                f"does not match num_dofs {d}"
            )

    # ------------------------------------------------------------------
    # Copy helpers
    # ------------------------------------------------------------------

    def clone(self) -> StandardMotion:
        """Return a deep copy of this motion."""
        return StandardMotion(
            fps=self.fps,
            root_pos=self.root_pos.copy(),
            root_rot=self.root_rot.copy(),
            dof_pos=self.dof_pos.copy(),
            dof_vel=self.dof_vel.copy(),
            projected_gravity=self.projected_gravity.copy(),
            root_lin_vel=self.root_lin_vel.copy(),
            root_ang_vel=self.root_ang_vel.copy(),
            key_body_pos_local=self.key_body_pos_local.copy(),
            joint_names=list(self.joint_names) if self.joint_names else None,
            source_path=self.source_path,
            motion_weight=self.motion_weight,
        )
