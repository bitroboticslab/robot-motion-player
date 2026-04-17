"""Version and roadmap consistency checks."""

from __future__ import annotations

from pathlib import Path

try:
    import tomllib
except ModuleNotFoundError:  # pragma: no cover
    tomllib = None


def _project_version() -> str:
    pyproject = Path("pyproject.toml")
    if tomllib is not None:
        data = tomllib.loads(pyproject.read_text(encoding="utf-8"))
        return data["project"]["version"]
    for line in pyproject.read_text(encoding="utf-8").splitlines():
        if line.startswith("version = "):
            return line.partition('"')[2].rpartition('"')[0]
    raise AssertionError("project version not found in pyproject.toml")


def test_version_markers_follow_project_version() -> None:
    project_version = _project_version()
    expected_dev_version = f"{project_version}.dev0"

    init_text = Path("motion_player/__init__.py").read_text(encoding="utf-8")
    cli_text = Path("motion_player/cli/main.py").read_text(encoding="utf-8")

    assert f'__version__ = "{expected_dev_version}"' in init_text
    assert f'return "{expected_dev_version}"' in cli_text


def test_design_and_summary_keep_full_gui_roadmap_order() -> None:
    design = Path("docs/design.md").read_text(encoding="utf-8")
    summary = Path("docs/summary.md").read_text(encoding="utf-8")
    assert "**Version / 版本**: 0.7.0" in design
    assert "| v0.5.0  | Full GUI integration milestone" in design
    assert "| v0.6.0  | IK tuning workflow hardening" in design
    assert "| v0.7.0  | Marked-frame history and quick revisit UX in CLI/GUI" in design
    assert "| v0.8.x  | Font architecture stabilization and reliability hardening" in design
    assert "| v0.9.x  | Physics replay (PD control), deterministic tests" in design
    assert "| v1.0.0  | Isaac/NV backend, HDF5 support, plugin completion" in design
    assert "| v1.1.0  | Web/Jupyter viewer export, packaging/distribution hardening" in design
    assert "Phase 5 — Full GUI Integration (Milestone 0.5.0)" in summary
    assert "Phase 6 — IK Tuning Workflow + Conversion Interop (Milestone 0.6.0)" in summary
    assert "Phase 7 — Marked-Frame UX + Docs/Release Sync (Milestone 0.7.0)" in summary
    assert (
        "Phase 8 — Font Architecture Stabilization + Reliability Hardening (Milestone 0.8.x)"
        in summary
    )
    assert "Phase 9 — Physics Replay + Advanced Evaluation (Milestone 0.9.0)" in summary
    assert "Phase 10 — Multi-Backend & Plugin System (Milestone 1.0.0)" in summary
    assert "Phase 11 — Distribution & Community (Milestone 1.1.0)" in summary


def test_readme_has_professional_banner_and_dual_mode_sections() -> None:
    readme = Path("README.md").read_text(encoding="utf-8")
    readme_cn = Path("README_CN.md").read_text(encoding="utf-8")
    assert "![RMP Banner](docs/assets/banner.svg)" in readme
    assert "## CLI Mode" in readme
    assert "## Full GUI Mode" in readme
    assert "[中文 README](README_CN.md)" in readme
    assert "[English README](README.md)" in readme_cn
    assert "https://github.com/YanjieZe/GMR" in readme
    assert "https://github.com/Mr-tooth/rsl-rl-ex" in readme
    assert "jGMR" not in readme
