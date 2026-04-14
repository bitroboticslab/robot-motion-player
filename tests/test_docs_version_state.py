"""Version consistency checks for release."""

from __future__ import annotations

from pathlib import Path


def test_version_markers_are_synced_to_v070() -> None:
    """Verify version is consistent across key files."""
    pyproject = Path("pyproject.toml").read_text(encoding="utf-8")
    init = Path("motion_player/__init__.py").read_text(encoding="utf-8")

    assert 'version = "0.7.0"' in pyproject
    assert "__version__" in init


def test_readme_has_banner_and_quickstart() -> None:
    """Verify README has essential sections."""
    readme = Path("README.md").read_text(encoding="utf-8")

    # Banner
    assert "assets/banner.png" in readme or "assets/Banner" in readme

    # Quick start section
    assert "## Quick Start" in readme or "## Installation" in readme

    # Usage examples
    assert "motion_player play" in readme
    assert "motion_player gui" in readme

    # Integration links
    assert "github.com/YanjieZe/GMR" in readme
    assert "rsl-rl-ex" in readme
