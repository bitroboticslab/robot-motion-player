"""Tests for import safety of all modules (no mujoco/pinocchio required)."""

from __future__ import annotations


def test_top_level_import():
    import motion_player

    assert hasattr(motion_player, "__version__")


def test_core_dataset_import():
    from motion_player.core.dataset import DatasetLoader, StandardMotion

    assert StandardMotion is not None
    assert DatasetLoader is not None


def test_core_kinematics_import():
    from motion_player.core.kinematics import JointMapper, JointOrderAuditor

    assert JointMapper is not None
    assert JointOrderAuditor is not None


def test_core_metrics_import():
    from motion_player.core.metrics import MetricEngine

    assert MetricEngine is not None


def test_core_editing_import():
    from motion_player.core.editing import FrameEditor

    assert FrameEditor is not None


def test_core_ui_import():
    from motion_player.core.ui import PlayerCommand

    assert PlayerCommand is not None


def test_backends_import():
    """Backends package can be imported without mujoco installed."""
    import motion_player.backends  # noqa: F401


def test_cli_import():
    from motion_player.cli import main

    assert callable(main)
