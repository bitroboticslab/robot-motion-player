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

"""JointOrderAuditor — inspects and repairs joint ordering between a dataset
and a robot model.

Background
----------
In the GMR retargeting pipeline the ``dof_pos`` column order in the produced
standard motion file is determined by the **source MJCF joint order** of the
robot model used in GMR.  If the downstream player or training framework
expects a different joint order (e.g. alphabetical or the order in the target
robot's MJCF), the dataset and the model will be silently misaligned.

This module provides tools to:
1. **Audit** — compare the column count of ``dof_pos`` against the number of
   non-free joints in a MuJoCo model, and optionally match names.
2. **Generate a sidecar YAML** — write a ``joint_order.yaml`` that records
   the ordering alongside the motion file.
3. **Apply a permutation** — reorder ``dof_pos`` columns in a
   :class:`~motion_player.core.dataset.motion.StandardMotion` to match a
   target joint order.

Extension points
----------------
Register new repair strategies via :meth:`JointOrderAuditor.register_strategy`.
"""

from __future__ import annotations

import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import yaml

from motion_player.core.dataset.motion import StandardMotion


@dataclass
class AuditReport:
    """Result of a joint order audit."""

    dataset_dof_count: int
    model_joint_count: int
    matched_names: list[str] = field(default_factory=list)
    unmatched_dataset: list[str] = field(default_factory=list)
    unmatched_model: list[str] = field(default_factory=list)
    count_mismatch: bool = False
    warnings: list[str] = field(default_factory=list)

    def is_ok(self) -> bool:
        """Return ``True`` if there are no mismatches."""
        return not self.count_mismatch and not self.unmatched_model


class JointOrderAuditor:
    """Audits and repairs joint ordering between a dataset and a robot model.

    Parameters
    ----------
    model_joint_names:
        Ordered list of joint names as they appear in the robot model.
        Provide this if you have already loaded the model outside this class.
        If ``None``, attempt to load from ``model_path`` using MuJoCo.
    model_path:
        Path to a MJCF ``.xml`` file.  Used to extract joint names when
        ``model_joint_names`` is ``None``.
    """

    def __init__(
        self,
        model_joint_names: list[str] | None = None,
        model_path: str | Path | None = None,
    ) -> None:
        self._model_joint_names = model_joint_names
        self._model_path = Path(model_path) if model_path else None
        self._strategies: dict[str, Callable] = {}

    # ------------------------------------------------------------------
    # Joint name extraction
    # ------------------------------------------------------------------

    @property
    def model_joint_names(self) -> list[str]:
        """Return (and cache) the robot model joint names."""
        if self._model_joint_names is None:
            self._model_joint_names = self._load_from_mjcf()
        return self._model_joint_names

    def _load_from_mjcf(self) -> list[str]:
        """Load non-free joint names from a MuJoCo MJCF file."""
        if self._model_path is None:
            return []
        try:
            import mujoco  # type: ignore[import]

            model = mujoco.MjModel.from_xml_path(str(self._model_path))
            names = []
            for i in range(model.njnt):
                jnt_type = model.jnt_type[i]
                # mujoco.mjtJoint.mjJNT_FREE == 0; skip free joints
                if jnt_type != 0:
                    name = mujoco.mj_id2name(
                        model, mujoco.mjtObj.mjOBJ_JOINT, i
                    )
                    if name:
                        names.append(name)
            return names
        except ImportError:
            warnings.warn(
                "mujoco package not installed; cannot load joint names from MJCF.",
                stacklevel=3,
            )
            return []

    # ------------------------------------------------------------------
    # Audit
    # ------------------------------------------------------------------

    def audit(
        self,
        motion: StandardMotion,
        model_joint_names: list[str] | None = None,
    ) -> AuditReport:
        """Compare dataset DOF count and names against the robot model.

        Parameters
        ----------
        motion:
            Motion to audit.
        model_joint_names:
            Override the model joint names for this call only.

        Returns
        -------
        AuditReport
        """
        mjnames = model_joint_names or self.model_joint_names
        report = AuditReport(
            dataset_dof_count=motion.num_dofs,
            model_joint_count=len(mjnames),
        )

        if motion.num_dofs != len(mjnames):
            report.count_mismatch = True
            report.warnings.append(
                f"DOF count mismatch: dataset has {motion.num_dofs} columns "
                f"but model has {len(mjnames)} joints."
            )

        if motion.joint_names is not None:
            ds_set = set(motion.joint_names)
            mo_set = set(mjnames)
            report.matched_names = sorted(ds_set & mo_set)
            report.unmatched_dataset = sorted(ds_set - mo_set)
            report.unmatched_model = sorted(mo_set - ds_set)
            if report.unmatched_model:
                report.warnings.append(
                    f"Model joints not found in dataset: {report.unmatched_model}"
                )

        return report

    # ------------------------------------------------------------------
    # Sidecar YAML generation
    # ------------------------------------------------------------------

    def generate_sidecar_yaml(
        self,
        motion: StandardMotion,
        path: str | Path,
        model_joint_names: list[str] | None = None,
    ) -> None:
        """Write a ``joint_order.yaml`` alongside the motion file.

        Parameters
        ----------
        motion:
            Source motion.
        path:
            Output path (e.g. ``/data/clip01_joint_order.yaml``).
        model_joint_names:
            Override the model joint names for this call only.
        """
        mjnames = model_joint_names or self.model_joint_names
        data = {
            "source_file": str(motion.source_path or "unknown"),
            "dataset_dof_count": motion.num_dofs,
            "dataset_joint_names": motion.joint_names,
            "model_joint_count": len(mjnames),
            "model_joint_names": mjnames,
        }
        with open(path, "w", encoding="utf-8") as f:
            yaml.dump(data, f, default_flow_style=False, allow_unicode=True)

    # ------------------------------------------------------------------
    # Permutation
    # ------------------------------------------------------------------

    def apply_permutation(
        self,
        motion: StandardMotion,
        perm: list[int],
    ) -> StandardMotion:
        """Return a new ``StandardMotion`` with ``dof_pos`` / ``dof_vel``
        columns reordered according to *perm*.

        Parameters
        ----------
        motion:
            Source motion (not modified in-place).
        perm:
            List of *dataset* column indices in the desired *model* order.
            E.g. ``[2, 0, 1]`` means model_dof[0] ← dataset_dof[2], etc.

        Returns
        -------
        StandardMotion
            Clone with reordered DOF arrays.
        """
        new = motion.clone()
        new.dof_pos = motion.dof_pos[:, perm]
        new.dof_vel = motion.dof_vel[:, perm]
        if motion.joint_names is not None:
            new.joint_names = [motion.joint_names[i] for i in perm]
        return new

    # ------------------------------------------------------------------
    # Extension: custom repair strategies
    # ------------------------------------------------------------------

    def register_strategy(self, name: str, fn: Callable) -> None:
        """Register a custom repair strategy callable.

        Parameters
        ----------
        name:
            Strategy identifier (e.g. ``"strip_prefix"``).
        fn:
            Callable ``fn(motion: StandardMotion, **kwargs) -> StandardMotion``.
        """
        self._strategies[name] = fn

    def apply_strategy(
        self, name: str, motion: StandardMotion, **kwargs
    ) -> StandardMotion:
        """Apply a registered repair strategy.

        Parameters
        ----------
        name:
            Strategy identifier.
        motion:
            Input motion.
        **kwargs:
            Passed through to the strategy function.
        """
        if name not in self._strategies:
            raise KeyError(
                f"Unknown strategy '{name}'. "
                f"Available: {list(self._strategies)}"
            )
        return self._strategies[name](motion, **kwargs)
