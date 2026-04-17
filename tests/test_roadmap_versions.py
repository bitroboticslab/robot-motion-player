from __future__ import annotations

from pathlib import Path


def test_design_roadmap_marks_v050_as_full_gui_and_shifts_future_versions() -> None:
    text = Path("docs/design.md").read_text(encoding="utf-8")
    assert "| v0.5.0  | Full GUI integration" in text
    assert "| v0.6.0  | IK tuning workflow hardening" in text
    assert "| v0.7.0  | Marked-frame history and quick revisit UX in CLI/GUI" in text
    assert "| v0.8.x  | Font architecture stabilization and reliability hardening" in text
    assert "| v0.9.x  | Physics replay (PD control), deterministic tests" in text
    assert "| v1.0.0  | Isaac/NV backend, HDF5 support, plugin completion" in text
    assert "| v1.1.0  | Web/Jupyter viewer export, packaging/distribution hardening" in text


def test_summary_roadmap_phase_numbers_shifted_by_one_after_full_gui() -> None:
    text = Path("docs/summary.md").read_text(encoding="utf-8")
    assert "Phase 5 — Full GUI Integration" in text
    assert "Phase 6 — IK Tuning Workflow + Conversion Interop (Milestone 0.6.0)" in text
    assert "Phase 7 — Marked-Frame UX + Docs/Release Sync (Milestone 0.7.0)" in text
    assert (
        "Phase 8 — Font Architecture Stabilization + Reliability Hardening (Milestone 0.8.x)"
        in text
    )
    assert "Phase 9 — Physics Replay + Advanced Evaluation (Milestone 0.9.0)" in text
    assert "Phase 10 — Multi-Backend & Plugin System (Milestone 1.0.0)" in text
    assert "Phase 11 — Distribution & Community (Milestone 1.1.0)" in text


def test_readme_documents_dual_usage_model() -> None:
    text = Path("README.md").read_text(encoding="utf-8")
    assert "CLI Mode" in text
    assert "Full GUI Mode" in text
    assert "motion_player gui --motion" in text
