"""Regression checks for IK usage documentation."""

from __future__ import annotations

from pathlib import Path


def test_ik_usage_mentions_full_pose_and_units() -> None:
    path = Path("docs/IK_USAGE.md")
    assert path.exists()
    text = path.read_text(encoding="utf-8")
    assert "full pose" in text.lower()
    assert "m / cm / mm" in text
    assert "rad / deg" in text
    assert "quaternion" in text.lower()
    assert "Reference Frame" in text
    assert "Current Pose" in text
    assert "Target Pose" in text
    assert "cross-frame smoothing" in text.lower()
