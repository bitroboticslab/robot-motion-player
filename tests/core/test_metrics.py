"""Tests for quality metrics engine."""

from __future__ import annotations

import numpy as np

from motion_player.core.metrics.engine import MetricConfig, MetricEngine
from motion_player.core.metrics.per_frame_score import PerFrameScore
from tests.conftest import make_motion


class TestPerFrameScore:
    def test_summary_defaults_to_mean(self):
        values = np.array([1.0, 2.0, 3.0])
        score = PerFrameScore("test", values)
        assert abs(score.summary - 2.0) < 1e-9

    def test_bad_frames_with_threshold(self):
        values = np.array([0.5, 1.5, 0.3, 2.0])
        score = PerFrameScore("test", values, threshold=1.0)
        assert set(score.bad_frames.tolist()) == {1, 3}

    def test_bad_frames_no_threshold(self):
        values = np.array([1.0, 2.0])
        score = PerFrameScore("test", values)
        assert len(score.bad_frames) == 0

    def test_worst_frame(self):
        values = np.array([0.1, 5.0, 0.2])
        score = PerFrameScore("test", values)
        assert score.worst_frame == 1


class TestMetricEngine:
    def test_all_terms_return_correct_shape(self):
        m = make_motion(num_frames=60, num_dofs=12)
        engine = MetricEngine(m)
        scores = engine.compute_all()
        for name, score in scores.items():
            assert score.values.shape == (60,), (
                f"Term '{name}' returned shape {score.values.shape}, expected (60,)"
            )

    def test_joint_limit_violation_no_limits(self):
        """Without limits set, the term should return all zeros."""
        m = make_motion()
        engine = MetricEngine(m, MetricConfig())
        score = engine.term_joint_limit_violation()
        assert np.allclose(score.values, 0.0)

    def test_joint_limit_violation_with_limits(self):
        """Synthetic violations should be detected."""
        m = make_motion(num_frames=10, num_dofs=4)
        # Force all joints to +2 rad (well beyond ±1 rad limit)
        m.dof_pos[:] = 2.0
        config = MetricConfig(
            joint_lower_limits=np.full(4, -1.0),
            joint_upper_limits=np.full(4, 1.0),
        )
        engine = MetricEngine(m, config)
        score = engine.term_joint_limit_violation()
        assert np.all(score.values > 0), "Expected violations on every frame"

    def test_foot_penetration_no_indices(self):
        """Without foot indices, penetration is zero."""
        m = make_motion()
        engine = MetricEngine(m, MetricConfig())
        score = engine.term_foot_penetration()
        assert np.allclose(score.values, 0.0)

    def test_foot_penetration_with_penetrating_foot(self):
        """Synthetic foot below ground should be detected."""
        m = make_motion(num_frames=10, num_dofs=4, num_bodies=4)
        # Set body 0 Z coordinate (index 2 in flat layout) to -0.5 m
        m.key_body_pos_local[:, 2] = -0.5
        config = MetricConfig(foot_body_indices=[0])
        engine = MetricEngine(m, config)
        score = engine.term_foot_penetration()
        assert np.all(score.values > 0)

    def test_penetration_extreme_is_capped(self):
        m = make_motion(num_frames=10, num_dofs=4, num_bodies=4)
        # Extreme negative height should be capped at 1m per body.
        m.key_body_pos_local[:, 2] = -10.0
        config = MetricConfig(foot_body_indices=[0])
        engine = MetricEngine(m, config)
        score = engine.term_foot_penetration()
        assert np.all(score.values <= 1.0 + 1e-6)

    def test_com_height_in_range(self):
        """COM within range should give zero penalty."""
        m = make_motion()  # root_pos z = 0.9 m
        config = MetricConfig(root_height_range=(0.5, 1.5))
        engine = MetricEngine(m, config)
        score = engine.term_com_height()
        assert np.allclose(score.values, 0.0)

    def test_com_height_out_of_range(self):
        """COM below minimum should be penalised."""
        m = make_motion()
        m.root_pos[:, 2] = 0.1  # below 0.5 m minimum
        config = MetricConfig(root_height_range=(0.5, 1.5))
        engine = MetricEngine(m, config)
        score = engine.term_com_height()
        assert np.all(score.values > 0)

    def test_joint_acc_shape(self):
        m = make_motion(num_frames=60)
        engine = MetricEngine(m)
        score = engine.term_joint_acc()
        assert score.values.shape == (60,)

    def test_overall_score_is_finite(self):
        m = make_motion()
        engine = MetricEngine(m)
        s = engine.overall_score()
        assert np.isfinite(s)

    def test_custom_term_registration(self):
        """Custom terms should be included in compute_all."""
        m = make_motion(num_frames=30)

        def my_term(motion):
            return PerFrameScore(
                "my_custom",
                np.ones(motion.num_frames),
                weight=2.0,
            )

        engine = MetricEngine(m)
        engine.register_term("my_custom", my_term, weight=2.0)
        scores = engine.compute_all()
        assert "my_custom" in scores
        assert abs(scores["my_custom"].summary - 1.0) < 1e-9

    def test_export_json(self, tmp_path):
        import json

        m = make_motion()
        engine = MetricEngine(m)
        out = tmp_path / "report.json"
        engine.export_report(str(out), fmt="json")
        assert out.exists()
        data = json.loads(out.read_text())
        assert "overall_score" in data
        assert "terms" in data

    def test_export_csv(self, tmp_path):
        m = make_motion()
        engine = MetricEngine(m)
        out = tmp_path / "report.csv"
        engine.export_report(str(out), fmt="csv")
        assert out.exists()
        lines = out.read_text().splitlines()
        # Header + N frame rows
        assert len(lines) == m.num_frames + 1

    def test_amp_feature_stability_shape(self):
        m = make_motion(num_frames=50)
        engine = MetricEngine(m)
        score = engine.term_amp_feature_stability()
        assert score.values.shape == (50,)
        # First frame is zero (padding)
        assert score.values[0] == 0.0
