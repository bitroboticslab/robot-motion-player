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

"""Pinocchio URDF IK backend wrapper."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from motion_player.core.kinematics.pose_target import PoseTarget


@dataclass
class PinocchioUrdfIKBackend:
    """Thin adapter around a callable Pinocchio IK solve function."""

    dof_names: tuple[str, ...]
    solver: Callable[[np.ndarray, dict[str, PoseTarget]], np.ndarray]

    @staticmethod
    def _normalize_quat(q: np.ndarray) -> np.ndarray:
        quat = np.asarray(q, dtype=np.float64)
        n = np.linalg.norm(quat)
        if n <= 0.0:
            return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        return quat / n

    @classmethod
    def _quat_delta_to_rotvec(cls, q_target_wxyz: np.ndarray, q_current_wxyz: np.ndarray) -> np.ndarray:
        qt = cls._normalize_quat(q_target_wxyz)
        qc = cls._normalize_quat(q_current_wxyz)
        w1, x1, y1, z1 = qt
        w2, x2, y2, z2 = np.array([qc[0], -qc[1], -qc[2], -qc[3]], dtype=np.float64)
        q_err = np.array(
            [
                w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2,
                w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2,
                w1 * y2 - x1 * z2 + y1 * w2 + z1 * x2,
                w1 * z2 + x1 * y2 - y1 * x2 + z1 * w2,
            ],
            dtype=np.float64,
        )
        q_err = cls._normalize_quat(q_err)
        if q_err[0] < 0.0:
            q_err = -q_err
        vec = q_err[1:]
        vec_norm = np.linalg.norm(vec)
        if vec_norm < 1e-10:
            return np.zeros(3, dtype=np.float64)
        angle = 2.0 * np.arctan2(vec_norm, q_err[0])
        return (vec / vec_norm) * angle

    @classmethod
    def _rotmat_to_quat_wxyz(cls, rot: np.ndarray) -> np.ndarray:
        r = np.asarray(rot, dtype=np.float64)
        if r.shape != (3, 3):
            return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        trace = float(np.trace(r))
        if trace > 0.0:
            s = np.sqrt(trace + 1.0) * 2.0
            qw = 0.25 * s
            qx = (r[2, 1] - r[1, 2]) / s
            qy = (r[0, 2] - r[2, 0]) / s
            qz = (r[1, 0] - r[0, 1]) / s
        elif r[0, 0] > r[1, 1] and r[0, 0] > r[2, 2]:
            s = np.sqrt(1.0 + r[0, 0] - r[1, 1] - r[2, 2]) * 2.0
            qw = (r[2, 1] - r[1, 2]) / s
            qx = 0.25 * s
            qy = (r[0, 1] + r[1, 0]) / s
            qz = (r[0, 2] + r[2, 0]) / s
        elif r[1, 1] > r[2, 2]:
            s = np.sqrt(1.0 + r[1, 1] - r[0, 0] - r[2, 2]) * 2.0
            qw = (r[0, 2] - r[2, 0]) / s
            qx = (r[0, 1] + r[1, 0]) / s
            qy = 0.25 * s
            qz = (r[1, 2] + r[2, 1]) / s
        else:
            s = np.sqrt(1.0 + r[2, 2] - r[0, 0] - r[1, 1]) * 2.0
            qw = (r[1, 0] - r[0, 1]) / s
            qx = (r[0, 2] + r[2, 0]) / s
            qy = (r[1, 2] + r[2, 1]) / s
            qz = 0.25 * s
        return cls._normalize_quat(np.array([qw, qx, qy, qz], dtype=np.float64))

    @classmethod
    def from_urdf_path(cls, urdf_path: str | Path) -> PinocchioUrdfIKBackend:
        try:
            import pin  # type: ignore[import]
        except ImportError as exc:
            raise ImportError("URDF IK requires optional dependency 'pin'.") from exc

        model = pin.buildModelFromUrdf(str(Path(urdf_path)))
        data = model.createData()

        joint_names: list[str] = []
        joint_ids: list[int] = []
        q_indices: list[int] = []
        v_indices: list[int] = []

        idx_qs = getattr(model, "idx_qs", None)
        idx_vs = getattr(model, "idx_vs", None)
        for joint_id in range(1, int(getattr(model, "njoints", 0))):
            joint = model.joints[joint_id]
            if int(getattr(joint, "nq", 0)) != 1:
                continue
            if idx_qs is None:
                continue
            q_idx = int(idx_qs[joint_id])
            if q_idx < 0:
                continue
            joint_names.append(str(model.names[joint_id]))
            joint_ids.append(joint_id)
            q_indices.append(q_idx)
            if idx_vs is not None:
                v_indices.append(int(idx_vs[joint_id]))
            else:
                v_indices.append(q_idx)

        if not joint_names:
            raise RuntimeError("URDF IK backend found no 1-DOF joints to solve.")

        q_indices_arr = np.asarray(q_indices, dtype=int)
        v_indices_arr = np.asarray(v_indices, dtype=int)
        joint_id_by_name = dict(zip(joint_names, joint_ids))

        neutral = np.zeros(int(model.nq), dtype=np.float64)
        if hasattr(pin, "neutral"):
            neutral = np.asarray(pin.neutral(model), dtype=np.float64)

        def _to_full_q(q_reduced: np.ndarray) -> np.ndarray:
            q_full = neutral.copy()
            q_full[q_indices_arr] = np.asarray(q_reduced, dtype=np.float64)
            return q_full

        def _forward(q_reduced: np.ndarray) -> np.ndarray:
            q_full = _to_full_q(q_reduced)
            pin.forwardKinematics(model, data, q_full)
            if hasattr(pin, "updateFramePlacements"):
                pin.updateFramePlacements(model, data)
            return q_full

        def _solver(current_qpos: np.ndarray, targets: dict[str, PoseTarget]) -> np.ndarray:
            if len(targets) != 1:
                raise ValueError("IK MVP supports exactly one target per apply action.")
            target_name, target_raw = next(iter(targets.items()))
            if target_name not in joint_id_by_name:
                raise KeyError(f"Unknown IK target '{target_name}'.")

            if isinstance(target_raw, PoseTarget):
                target = target_raw
            else:
                target = PoseTarget(
                    position_m=np.asarray(target_raw, dtype=np.float64),
                    orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
                )

            q_reduced = np.asarray(current_qpos, dtype=np.float64).copy()
            if q_reduced.shape != (len(joint_names),):
                raise ValueError(
                    f"Pinocchio IK input shape mismatch: expected {(len(joint_names),)}, got {q_reduced.shape}"
                )

            damping = 1e-3
            step_size = 0.5
            max_dq_norm = 0.2
            min_condition_eps = 1e-8

            for _ in range(20):
                q_full = _forward(q_reduced)
                joint_id = joint_id_by_name[target_name]
                transform = data.oMi[joint_id]
                p_cur = np.asarray(transform.translation, dtype=np.float64)
                rot_cur = np.asarray(getattr(transform, "rotation", np.eye(3)), dtype=np.float64)
                q_cur = PinocchioUrdfIKBackend._rotmat_to_quat_wxyz(rot_cur)
                pos_err = target.position_m - p_cur
                rot_err = PinocchioUrdfIKBackend._quat_delta_to_rotvec(target.orientation_wxyz, q_cur)
                if np.linalg.norm(pos_err) < 1e-4 and np.linalg.norm(rot_err) < 1e-4:
                    break

                if hasattr(pin, "computeJointJacobian"):
                    jac_full = np.asarray(
                        pin.computeJointJacobian(model, data, q_full, joint_id),
                        dtype=np.float64,
                    )
                else:
                    raise RuntimeError("Pinocchio runtime is missing computeJointJacobian.")
                jac_pos = jac_full[:3, v_indices_arr]
                if jac_full.shape[0] >= 6:
                    jac_rot = jac_full[3:6, v_indices_arr]
                else:
                    jac_rot = np.zeros_like(jac_pos)

                err6 = np.concatenate(
                    [
                        target.position_weight * pos_err,
                        target.rotation_weight * rot_err,
                    ]
                )
                jac6 = np.vstack(
                    [
                        target.position_weight * jac_pos,
                        target.rotation_weight * jac_rot,
                    ]
                )
                jj_t = jac6 @ jac6.T
                a_mat = jj_t + damping * np.eye(6)
                cond = np.linalg.cond(a_mat)
                cond_limit = np.inf if min_condition_eps <= 0.0 else (1.0 / min_condition_eps)
                if not np.isfinite(cond) or cond > cond_limit:
                    break

                dq = jac6.T @ np.linalg.solve(a_mat, err6)
                dq_norm = float(np.linalg.norm(dq))
                if max_dq_norm > 0.0 and dq_norm > max_dq_norm:
                    dq = dq * (max_dq_norm / dq_norm)
                q_reduced = q_reduced + step_size * dq

            return q_reduced

        return cls(dof_names=tuple(joint_names), solver=_solver)

    def solve(self, current_qpos: np.ndarray, targets: dict[str, PoseTarget]) -> np.ndarray:
        target_name = next(iter(targets.keys()))
        if target_name not in self.dof_names:
            raise KeyError(f"Unknown IK target '{target_name}'.")
        current = np.asarray(current_qpos, dtype=np.float64)
        solved = np.asarray(self.solver(current, targets), dtype=np.float64)
        if solved.shape != current.shape:
            raise ValueError("Pinocchio IK output shape mismatch.")
        return solved
