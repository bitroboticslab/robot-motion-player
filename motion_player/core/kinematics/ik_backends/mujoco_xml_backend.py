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

"""MuJoCo XML IK backend core loop."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable

import numpy as np

from motion_player.core.kinematics.pose_target import PoseTarget


@dataclass
class MujocoXmlIKBackend:
    """Damped least-squares IK backend for XML robot models."""

    dof_names: tuple[str, ...]
    fk: Callable[[np.ndarray, str], np.ndarray]
    jac: Callable[[np.ndarray, str], np.ndarray]
    fk_rot: Callable[[np.ndarray, str], np.ndarray] | None = None
    jac_rot: Callable[[np.ndarray, str], np.ndarray] | None = None
    damping: float = 1e-3
    step_size: float = 0.5
    max_iters: int = 20
    max_dq_norm: float = 0.2
    min_condition_eps: float = 1e-8

    @classmethod
    def from_runtime_driver(cls, driver: object) -> MujocoXmlIKBackend:
        """Build a MuJoCo-backed IK backend from a live state driver."""
        model = getattr(driver, "model", None)
        data = getattr(driver, "data", None)
        mj = getattr(driver, "_mujoco", None)
        if model is None or data is None:
            raise RuntimeError("Runtime driver is missing model/data for XML IK backend.")
        if mj is None:
            try:
                import mujoco as mj  # type: ignore[import]
            except ImportError as exc:
                raise ImportError("mujoco runtime is required for XML IK backend.") from exc

        qpos_addrs = np.asarray(driver.dof_qpos_addresses(), dtype=int)
        vel_addrs = np.asarray(driver.dof_velocity_addresses(), dtype=int)
        if qpos_addrs.size == 0 or vel_addrs.size == 0:
            raise RuntimeError("Driver has no non-free DOFs for XML IK backend.")
        if qpos_addrs.shape != vel_addrs.shape:
            raise RuntimeError("Driver DOF qpos/velocity address shape mismatch.")

        dof_names = tuple(str(driver.dof_joint_name(i)) for i in range(int(qpos_addrs.size)))
        body_ids = {name: int(driver.dof_joint_body_id(i)) for i, name in enumerate(dof_names)}

        def _apply_qpos(q: np.ndarray) -> None:
            data.qpos[qpos_addrs] = np.asarray(q, dtype=np.float64)
            mj.mj_forward(model, data)

        def _fk(q: np.ndarray, target_name: str) -> np.ndarray:
            _apply_qpos(q)
            return np.asarray(data.xpos[body_ids[target_name]], dtype=np.float64).copy()

        def _jac(q: np.ndarray, target_name: str) -> np.ndarray:
            _apply_qpos(q)
            jacp = np.zeros((3, int(model.nv)), dtype=np.float64)
            jacr = np.zeros((3, int(model.nv)), dtype=np.float64)
            mj.mj_jacBody(model, data, jacp, jacr, int(body_ids[target_name]))
            return np.asarray(jacp[:, vel_addrs], dtype=np.float64).copy()

        def _fk_rot(q: np.ndarray, target_name: str) -> np.ndarray:
            _apply_qpos(q)
            body_id = int(body_ids[target_name])
            xquat = getattr(data, "xquat", None)
            if xquat is None:
                return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
            return np.asarray(xquat[body_id], dtype=np.float64).copy()

        def _jac_rot(q: np.ndarray, target_name: str) -> np.ndarray:
            _apply_qpos(q)
            jacp = np.zeros((3, int(model.nv)), dtype=np.float64)
            jacr = np.zeros((3, int(model.nv)), dtype=np.float64)
            mj.mj_jacBody(model, data, jacp, jacr, int(body_ids[target_name]))
            return np.asarray(jacr[:, vel_addrs], dtype=np.float64).copy()

        return cls(
            dof_names=dof_names,
            fk=_fk,
            jac=_jac,
            fk_rot=_fk_rot,
            jac_rot=_jac_rot,
        )

    @classmethod
    def from_xml_path(cls, model_path: str | Path) -> MujocoXmlIKBackend:
        del model_path
        raise RuntimeError(
            "Runtime MuJoCo-backed constructor must be implemented with model-specific FK/Jacobian wiring."
        )

    @staticmethod
    def _normalize_quat(q: np.ndarray) -> np.ndarray:
        quat = np.asarray(q, dtype=np.float64)
        norm = np.linalg.norm(quat)
        if norm <= 0.0:
            return np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        return quat / norm

    @classmethod
    def _quat_delta_to_rotvec(
        cls, q_target_wxyz: np.ndarray, q_current_wxyz: np.ndarray
    ) -> np.ndarray:
        qt = cls._normalize_quat(q_target_wxyz)
        qc = cls._normalize_quat(q_current_wxyz)

        # q_err = q_target * conj(q_current)
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
        axis = vec / vec_norm
        return axis * angle

    def solve(self, current_qpos: np.ndarray, targets: dict[str, PoseTarget]) -> np.ndarray:
        if len(targets) != 1:
            raise ValueError("IK MVP supports exactly one target per apply action.")
        target_name, target_raw = next(iter(targets.items()))
        if target_name not in self.dof_names:
            raise KeyError(f"Unknown IK target '{target_name}'.")

        if isinstance(target_raw, PoseTarget):
            target = target_raw
        else:
            target = PoseTarget(
                position_m=np.asarray(target_raw, dtype=np.float64),
                orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
            )

        q = np.asarray(current_qpos, dtype=np.float64).copy()

        for _ in range(self.max_iters):
            p_cur = np.asarray(self.fk(q, target_name), dtype=np.float64)
            if self.fk_rot is None:
                q_cur = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
            else:
                q_cur = np.asarray(self.fk_rot(q, target_name), dtype=np.float64)

            pos_err = target.position_m - p_cur
            rot_err = self._quat_delta_to_rotvec(target.orientation_wxyz, q_cur)
            if np.linalg.norm(pos_err) < 1e-4 and np.linalg.norm(rot_err) < 1e-4:
                break

            j_pos = np.asarray(self.jac(q, target_name), dtype=np.float64)
            if self.jac_rot is None:
                j_rot = np.zeros_like(j_pos)
            else:
                j_rot = np.asarray(self.jac_rot(q, target_name), dtype=np.float64)

            err6 = np.concatenate(
                [
                    target.position_weight * pos_err,
                    target.rotation_weight * rot_err,
                ]
            )
            j6 = np.vstack(
                [
                    target.position_weight * j_pos,
                    target.rotation_weight * j_rot,
                ]
            )
            jj_t = j6 @ j6.T
            a_mat = jj_t + self.damping * np.eye(6)
            cond = np.linalg.cond(a_mat)
            cond_limit = np.inf if self.min_condition_eps <= 0.0 else (1.0 / self.min_condition_eps)
            if not np.isfinite(cond) or cond > cond_limit:
                break

            dq = j6.T @ np.linalg.solve(a_mat, err6)
            dq_norm = float(np.linalg.norm(dq))
            if self.max_dq_norm > 0.0 and dq_norm > self.max_dq_norm:
                dq = dq * (self.max_dq_norm / dq_norm)
            q = q + self.step_size * dq

        return q
