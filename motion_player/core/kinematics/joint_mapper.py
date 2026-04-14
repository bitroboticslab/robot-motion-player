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

"""JointMapper — maps dataset DOF columns to robot model joint indices.

The mapping is configured via a YAML file (``mapping.yaml``) that records:

* The robot MJCF or URDF path.
* The dataset joint name ordering.
* An optional name translation map (dataset name → model joint name).
* Optional sign-flip and angular offset corrections per joint.

Extension points
----------------
Override :meth:`JointMapper.build_mapping` to implement custom name-matching
heuristics (e.g. prefix stripping, left↔right side symmetry detection).
"""

from __future__ import annotations

import warnings
from pathlib import Path

import numpy as np
import yaml


class JointMapper:
    """Maps dataset DOF columns to robot model joint indices.

    Parameters
    ----------
    dataset_joint_names:
        Ordered list of joint names as they appear in the dataset ``dof_pos``
        columns.  If ``None`` the identity permutation is used.
    model_joint_names:
        Ordered list of joint names as they appear in the robot model (MJCF /
        URDF).  If ``None`` the identity permutation is used.
    name_map:
        Optional translation dict ``{dataset_name: model_name}`` for joints
        whose names differ between the dataset and the model.
    sign_flip:
        Optional per-joint sign flip ``{model_name: ±1}`` for joints whose
        positive direction differs between the dataset and the model.
    offset:
        Optional per-joint angular offset (radians) ``{model_name: value}``
        applied *after* the sign flip.
    """

    def __init__(
        self,
        dataset_joint_names: list[str] | None = None,
        model_joint_names: list[str] | None = None,
        name_map: dict[str, str] | None = None,
        sign_flip: dict[str, float] | None = None,
        offset: dict[str, float] | None = None,
    ) -> None:
        self.dataset_joint_names = dataset_joint_names or []
        self.model_joint_names = model_joint_names or []
        self.name_map = name_map or {}
        self.sign_flip = sign_flip or {}
        self.offset = offset or {}

        # Build the index mapping lazily on first call to apply()
        self._perm: list[int | None] | None = None

    # ------------------------------------------------------------------
    # Factory
    # ------------------------------------------------------------------

    @classmethod
    def from_yaml(cls, path: str | Path) -> JointMapper:
        """Load a ``JointMapper`` from a ``mapping.yaml`` file.

        Expected YAML structure::

            robot_mjcf_path: assets/booster_t1/scene.xml
            root_joint_name: root
            dof_order_in_dataset:
              - left_hip_yaw
              - left_hip_roll
              # ...
            name_map:
              left_hip_yaw: LHipYaw
            sign_flip:
              right_knee: -1
            offset:
              left_ankle: 0.05
        """
        with open(path, encoding="utf-8") as f:
            cfg = yaml.safe_load(f)
        return cls(
            dataset_joint_names=cfg.get("dof_order_in_dataset"),
            model_joint_names=cfg.get("dof_order_in_model"),
            name_map=cfg.get("name_map"),
            sign_flip=cfg.get("sign_flip"),
            offset=cfg.get("offset"),
        )

    # ------------------------------------------------------------------
    # Core mapping
    # ------------------------------------------------------------------

    def build_mapping(
        self,
        dataset_names: list[str],
        model_names: list[str],
    ) -> list[int | None]:
        """Build a permutation list mapping dataset column *i* to model index.

        Returns a list of length ``len(model_names)`` where ``perm[j]`` is the
        dataset column index for model joint *j*, or ``None`` if no match.

        Override this method to implement custom matching heuristics.

        Parameters
        ----------
        dataset_names:
            Ordered DOF names from the dataset.
        model_names:
            Ordered joint names from the robot model.
        """
        # Build reverse lookup: model_name → dataset_index (after translation)
        translated: dict[str, int] = {}
        for i, dname in enumerate(dataset_names):
            mname = self.name_map.get(dname, dname)
            translated[mname] = i

        perm: list[int | None] = []
        for mname in model_names:
            idx = translated.get(mname)
            if idx is None:
                warnings.warn(
                    f"JointMapper: model joint '{mname}' has no match in dataset. "
                    "Column will be filled with zeros.",
                    stacklevel=3,
                )
            perm.append(idx)
        return perm

    def apply(self, dof_pos: np.ndarray) -> np.ndarray:
        """Apply the mapping to a ``dof_pos`` array.

        Parameters
        ----------
        dof_pos:
            Array of shape ``(N, D_dataset)`` from the dataset.

        Returns
        -------
        np.ndarray
            Array of shape ``(N, D_model)`` ordered for the robot model,
            with sign flips and offsets applied.
        """
        if not self.dataset_joint_names or not self.model_joint_names:
            # Identity mapping — return as-is
            return dof_pos

        if self._perm is None:
            self._perm = self.build_mapping(
                self.dataset_joint_names, self.model_joint_names
            )

        n = dof_pos.shape[0]
        d_model = len(self.model_joint_names)
        out = np.zeros((n, d_model), dtype=dof_pos.dtype)

        for j, (src_idx, mname) in enumerate(
            zip(self._perm, self.model_joint_names)
        ):
            if src_idx is not None:
                col = dof_pos[:, src_idx].copy()
                col *= self.sign_flip.get(mname, 1.0)
                col += self.offset.get(mname, 0.0)
                out[:, j] = col
        return out
