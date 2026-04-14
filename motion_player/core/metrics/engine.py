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

"""MetricEngine — computes and aggregates quality metrics on StandardMotion.

Priority order (aligned with requirements.md §5.4):
  1. AMP training friendliness (highest)
  2. Physical plausibility
  3. Visual smoothness (lowest)

GMR Retargeting Loss Parity
---------------------------
The metric terms below are designed to be *directly comparable* to the loss
terms used in the GMR retargeting optimisation pipeline (Mr-tooth/GMR).  The
intent is that the same quality bar used to *produce* a dataset can also be
used to *evaluate* it after production.

Specifically:

* ``term_joint_limit_violation`` mirrors GMR's ``joint_limit_penalty`` term.
* ``term_foot_penetration`` mirrors GMR's ``foot_ground_penalty`` term.
* ``term_joint_acc`` mirrors GMR's ``smoothness_penalty`` (second-order).

To compare a metric score with a GMR loss value, set the corresponding
weight in ``MetricConfig`` to match the GMR loss weight.

Extension Points
----------------
* Register custom metric terms via :meth:`MetricEngine.register_term`.
* Subclass ``MetricEngine`` and override any ``term_*`` method.
* The ``MetricConfig`` dataclass controls weights, thresholds, and reference
  ranges; update it without subclassing.
"""

from __future__ import annotations

import csv
import json
import warnings
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

import numpy as np

from motion_player.core.dataset.motion import StandardMotion
from motion_player.core.metrics.per_frame_score import PerFrameScore


@dataclass
class MetricConfig:
    """Configuration for :class:`MetricEngine`.

    All weight values default to 1.0 and can be tuned to match GMR loss
    weights for a fair comparison.

    Parameters
    ----------
    joint_lower_limits / joint_upper_limits:
        Per-DOF joint angle limits in radians.  Shape ``(D,)``.  If ``None``
        the limit-violation term returns zeros.
    foot_body_indices:
        Indices into ``key_body_pos_local`` (flat, groups of 3) that
        correspond to foot end-effectors.  Used by ``term_foot_penetration``.
    root_height_range:
        ``(min, max)`` root height in metres for the COM height term.
    amp_feature_fields:
        List of ``StandardMotion`` attribute names to include in AMP feature
        stability computation.  Defaults to the standard AMP input vector.
    """

    # --- Weights (mirror GMR loss weights for parity) ---
    w_amp_feature_stability: float = 1.0
    w_dof_vel_distribution: float = 1.0
    w_joint_limit_violation: float = 1.0  # matches GMR w_joint_limit
    w_foot_penetration: float = 1.0       # matches GMR w_foot_ground
    w_com_height: float = 0.5
    w_joint_acc: float = 0.5             # matches GMR w_smoothness
    w_joint_jerk: float = 0.2

    # --- Thresholds (for PerFrameScore.bad_frames) ---
    joint_limit_threshold: float = 0.01   # radians
    foot_penetration_threshold: float = 0.01  # metres below ground
    joint_acc_threshold: float = 50.0     # rad/s²

    # --- Joint limits ---
    joint_lower_limits: np.ndarray | None = None  # (D,)
    joint_upper_limits: np.ndarray | None = None  # (D,)

    # --- Foot body indices into key_body_pos_local ---
    # Each index corresponds to the start of a 3-element block (body * 3).
    foot_body_indices: list[int] = field(default_factory=list)

    # --- Root height range ---
    root_height_range: tuple[float, float] = (0.2, 2.0)  # metres

    # --- AMP feature fields ---
    amp_feature_fields: list[str] = field(
        default_factory=lambda: [
            "root_lin_vel",
            "root_ang_vel",
            "projected_gravity",
            "dof_pos",
            "dof_vel",
            "key_body_pos_local",
        ]
    )

    # --- DOF velocity reference distribution ---
    dof_vel_mean: np.ndarray | None = None   # (D,)
    dof_vel_std: np.ndarray | None = None    # (D,)
    dof_vel_sigma_threshold: float = 3.0


class MetricEngine:
    """Computes quality metrics on a :class:`~motion_player.core.dataset.motion.StandardMotion`.

    Parameters
    ----------
    motion:
        The motion to evaluate.
    config:
        Metric configuration (weights, thresholds, limits).
    """

    def __init__(
        self,
        motion: StandardMotion,
        config: MetricConfig | None = None,
    ) -> None:
        self.motion = motion
        self.config = config or MetricConfig()
        self._custom_terms: dict[
            str, tuple[Callable[[StandardMotion], PerFrameScore], float]
        ] = {}

    # ------------------------------------------------------------------
    # Extension point: custom terms
    # ------------------------------------------------------------------

    def register_term(
        self,
        name: str,
        fn: Callable[[StandardMotion], PerFrameScore],
        weight: float = 1.0,
    ) -> None:
        """Register a custom metric term.

        Parameters
        ----------
        name:
            Unique term identifier.
        fn:
            Callable that takes a ``StandardMotion`` and returns a
            ``PerFrameScore``.
        weight:
            Weight in the aggregated overall score.
        """
        self._custom_terms[name] = (fn, weight)

    # ------------------------------------------------------------------
    # 1. AMP training friendliness (highest priority)
    # ------------------------------------------------------------------

    def term_amp_feature_stability(self) -> PerFrameScore:
        """Per-frame L2 norm of the AMP feature vector delta.

        Measures frame-to-frame change in the concatenated AMP discriminator
        input feature.  High values indicate unstable features that will make
        the AMP discriminator training harder.

        AMP feature vector (configurable via ``MetricConfig.amp_feature_fields``):
          root_lin_vel | root_ang_vel | projected_gravity |
          dof_pos | dof_vel | key_body_pos_local
        """
        m = self.motion
        parts = []
        for attr in self.config.amp_feature_fields:
            arr = getattr(m, attr, None)
            if arr is not None:
                parts.append(arr.reshape(m.num_frames, -1))
        if not parts:
            return PerFrameScore(
                "amp_feature_stability",
                np.zeros(m.num_frames),
                weight=self.config.w_amp_feature_stability,
            )
        feat = np.concatenate(parts, axis=1)  # (N, F)
        delta = np.diff(feat, axis=0)          # (N-1, F)
        norms = np.linalg.norm(delta, axis=1)  # (N-1,)
        # Pad first frame with zero for uniform length
        values = np.concatenate([[0.0], norms])
        return PerFrameScore(
            "amp_feature_stability",
            values,
            weight=self.config.w_amp_feature_stability,
        )

    def term_dof_vel_distribution(self) -> PerFrameScore:
        """Per-frame DOF velocity outlier count (z-score > threshold).

        Frames with many joints exceeding the reference DOF velocity
        distribution will corrupt the AMP reward signal.

        If no reference distribution is configured
        (``MetricConfig.dof_vel_mean/std``), the clip's own mean/std is used.
        """
        dv = self.motion.dof_vel  # (N, D)
        mean = (
            self.config.dof_vel_mean
            if self.config.dof_vel_mean is not None
            else dv.mean(axis=0)
        )
        std = (
            self.config.dof_vel_std
            if self.config.dof_vel_std is not None
            else dv.std(axis=0)
        )
        # Avoid division by zero
        safe_std = np.where(std < 1e-6, 1.0, std)
        z = np.abs(dv - mean) / safe_std       # (N, D)
        # Count outlier joints per frame
        outlier_count = (z > self.config.dof_vel_sigma_threshold).sum(axis=1)
        return PerFrameScore(
            "dof_vel_distribution",
            outlier_count.astype(np.float32),
            weight=self.config.w_dof_vel_distribution,
        )

    # ------------------------------------------------------------------
    # 2. Physical plausibility
    # ------------------------------------------------------------------

    def term_joint_limit_violation(self) -> PerFrameScore:
        """Per-frame sum of joint angle limit violations in radians.

        Mirrors GMR retargeting loss term ``joint_limit_penalty``.
        Set ``MetricConfig.w_joint_limit_violation`` to match GMR's
        ``w_joint_limit`` weight for a comparable score.

        Extension point: replace ``MetricConfig.joint_lower_limits /
        joint_upper_limits`` with arrays loaded from your robot MJCF to get
        robot-specific limits.
        """
        dof = self.motion.dof_pos  # (N, D)
        lo = self.config.joint_lower_limits
        hi = self.config.joint_upper_limits

        if lo is None or hi is None:
            return PerFrameScore(
                "joint_limit_violation",
                np.zeros(self.motion.num_frames, dtype=np.float32),
                weight=self.config.w_joint_limit_violation,
                threshold=self.config.joint_limit_threshold,
            )

        lo = np.asarray(lo)
        hi = np.asarray(hi)
        violation_lo = np.maximum(0.0, lo - dof)   # (N, D)
        violation_hi = np.maximum(0.0, dof - hi)   # (N, D)
        per_frame = (violation_lo + violation_hi).sum(axis=1)  # (N,)
        return PerFrameScore(
            "joint_limit_violation",
            per_frame.astype(np.float32),
            weight=self.config.w_joint_limit_violation,
            threshold=self.config.joint_limit_threshold,
        )

    def term_foot_penetration(self) -> PerFrameScore:
        """Per-frame foot penetration depth below ground plane (z = 0).

        Mirrors GMR retargeting loss term ``foot_ground_penalty``.

        Requires ``MetricConfig.foot_body_indices`` to be set with the flat
        body indices (into ``key_body_pos_local``) of the foot end-effectors.

        Extension point: replace the ``z = 0`` ground plane with a terrain
        height function by subclassing and overriding this method.
        """
        kbl = self.motion.key_body_pos_local  # (N, K*3)
        indices = self.config.foot_body_indices

        if not indices:
            return PerFrameScore(
                "foot_penetration",
                np.zeros(self.motion.num_frames, dtype=np.float32),
                weight=self.config.w_foot_penetration,
                threshold=self.config.foot_penetration_threshold,
            )

        # Extract Z coordinates of each foot body
        per_frame = np.zeros(self.motion.num_frames, dtype=np.float32)
        for body_idx in indices:
            # body_idx is the body ordinal; Z is at column body_idx*3 + 2
            z_col = body_idx * 3 + 2
            if z_col < kbl.shape[1]:
                z = kbl[:, z_col]
                per_frame += np.clip(-z, 0.0, 1.0)  # cap extreme values at 1m

        return PerFrameScore(
            "foot_penetration",
            per_frame,
            weight=self.config.w_foot_penetration,
            threshold=self.config.foot_penetration_threshold,
        )

    def term_com_height(self) -> PerFrameScore:
        """Per-frame absolute deviation of root height from reference range.

        Penalises root heights outside ``MetricConfig.root_height_range``.
        """
        z = self.motion.root_pos[:, 2]  # (N,)
        lo, hi = self.config.root_height_range
        violation = np.maximum(0.0, lo - z) + np.maximum(0.0, z - hi)
        return PerFrameScore(
            "com_height",
            violation.astype(np.float32),
            weight=self.config.w_com_height,
        )

    # ------------------------------------------------------------------
    # 3. Visual smoothness (lowest priority)
    # ------------------------------------------------------------------

    def term_joint_acc(self) -> PerFrameScore:
        """Per-frame RMS joint acceleration (second finite difference of dof_pos).

        High values indicate jitter that degrades both AMP discriminator
        performance and visual quality.  Mirrors GMR ``smoothness_penalty``.
        """
        dof = self.motion.dof_pos        # (N, D)
        dt = self.motion.dt
        vel = np.diff(dof, axis=0) / dt  # (N-1, D)
        acc = np.diff(vel, axis=0) / dt  # (N-2, D)
        rms = np.sqrt((acc ** 2).mean(axis=1))  # (N-2,)
        # Pad to length N
        values = np.concatenate([[0.0, 0.0], rms]).astype(np.float32)
        return PerFrameScore(
            "joint_acc",
            values,
            weight=self.config.w_joint_acc,
            threshold=self.config.joint_acc_threshold,
        )

    def term_joint_jerk(self) -> PerFrameScore:
        """Per-frame RMS joint jerk (third finite difference of dof_pos)."""
        dof = self.motion.dof_pos
        dt = self.motion.dt
        vel = np.diff(dof, axis=0) / dt
        acc = np.diff(vel, axis=0) / dt
        jerk = np.diff(acc, axis=0) / dt   # (N-3, D)
        rms = np.sqrt((jerk ** 2).mean(axis=1))
        values = np.concatenate([[0.0, 0.0, 0.0], rms]).astype(np.float32)
        return PerFrameScore(
            "joint_jerk",
            values,
            weight=self.config.w_joint_jerk,
        )

    # ------------------------------------------------------------------
    # Aggregation
    # ------------------------------------------------------------------

    def compute_all(self) -> dict[str, PerFrameScore]:
        """Compute all built-in metric terms.

        Returns
        -------
        dict
            Mapping from term name to :class:`PerFrameScore`.
        """
        results: dict[str, PerFrameScore] = {}
        for method_name in [
            "term_amp_feature_stability",
            "term_dof_vel_distribution",
            "term_joint_limit_violation",
            "term_foot_penetration",
            "term_com_height",
            "term_joint_acc",
            "term_joint_jerk",
        ]:
            try:
                score = getattr(self, method_name)()
                results[score.term_name] = score
            except (AttributeError, ValueError, RuntimeError, FloatingPointError) as exc:
                warnings.warn(
                    f"MetricEngine: failed to compute {method_name}: {exc}",
                    stacklevel=2,
                )

        # Custom terms
        for name, (fn, _weight) in self._custom_terms.items():
            try:
                score = fn(self.motion)
                results[score.term_name] = score
            except (AttributeError, ValueError, RuntimeError, FloatingPointError) as exc:
                warnings.warn(
                    f"MetricEngine: failed to compute custom term '{name}': {exc}",
                    stacklevel=2,
                )

        return results

    def overall_score(self) -> float:
        """Weighted mean of all per-frame summary scores.

        Lower is better (all terms are penalty-style).
        """
        scores = self.compute_all()
        if not scores:
            return 0.0
        total_weight = sum(s.weight for s in scores.values())
        if total_weight < 1e-12:
            return 0.0
        weighted_sum = sum(
            s.weight * (s.summary or 0.0) for s in scores.values()
        )
        return weighted_sum / total_weight

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def export_report(
        self,
        path: str | Path,
        fmt: str = "json",
    ) -> None:
        """Export a quality report to disk.

        Parameters
        ----------
        path:
            Output file path.
        fmt:
            ``"json"`` (default) or ``"csv"``.
        """
        scores = self.compute_all()
        path = Path(path)

        if fmt == "json":
            data = {
                "source": self.motion.source_path,
                "overall_score": self.overall_score(),
                "num_frames": self.motion.num_frames,
                "fps": self.motion.fps,
                "terms": {
                    name: {
                        "summary": float(score.summary or 0.0),
                        "weight": score.weight,
                        "worst_frame": int(score.worst_frame),
                        "bad_frame_count": int(len(score.bad_frames)),
                    }
                    for name, score in scores.items()
                },
            }
            with open(path, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2)

        elif fmt == "csv":
            with open(path, "w", encoding="utf-8", newline="") as f:
                writer = csv.writer(f)
                writer.writerow(["frame"] + list(scores.keys()))
                for i in range(self.motion.num_frames):
                    row = [i] + [
                        float(score.values[i]) for score in scores.values()
                    ]
                    writer.writerow(row)
        else:
            raise ValueError(f"Unknown format '{fmt}'; use 'json' or 'csv'.")
