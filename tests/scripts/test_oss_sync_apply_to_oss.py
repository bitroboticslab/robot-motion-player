from pathlib import Path

import pytest

from scripts.oss_sync.apply_to_oss import apply_staging_to_oss, validate_oss_target


def test_validate_oss_target_rejects_main_branch(tmp_path: Path) -> None:
    oss = tmp_path / "oss"
    oss.mkdir(parents=True)
    (oss / ".git").mkdir()

    with pytest.raises(RuntimeError, match="main"):
        validate_oss_target(oss, branch_name="main")


def test_validate_oss_target_requires_git_metadata(tmp_path: Path) -> None:
    oss = tmp_path / "oss"
    oss.mkdir(parents=True)

    with pytest.raises(RuntimeError, match="git"):
        validate_oss_target(oss, branch_name="feat/oss-sync")


def test_validate_oss_target_rejects_unsafe_target_path_intent(tmp_path: Path) -> None:
    oss = tmp_path / "oss"
    oss.mkdir(parents=True)
    (oss / ".git").mkdir()
    unsafe_target = oss / ".." / "oss"

    with pytest.raises(RuntimeError, match="unsafe target path intent"):
        validate_oss_target(unsafe_target, branch_name="feat/oss-sync")


def test_apply_staging_to_oss_dry_run_by_default(tmp_path: Path) -> None:
    staging = tmp_path / "stage"
    oss = tmp_path / "oss"
    (staging / "motion_player").mkdir(parents=True)
    (staging / "motion_player/__init__.py").write_text("__version__ = 'x'", encoding="utf-8")
    oss.mkdir(parents=True)
    (oss / ".git").mkdir()

    report = apply_staging_to_oss(staging, oss, apply=False, branch_name="feat/oss-sync")

    assert report["mode"] == "dry-run"
    assert report["copied"] == []
    assert report["planned"] == ["motion_player/__init__.py"]
    assert not (oss / "motion_player/__init__.py").exists()


def test_apply_staging_to_oss_rejects_unsafe_relative_paths(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    staging = tmp_path / "stage"
    oss = tmp_path / "oss"
    staging.mkdir(parents=True)
    oss.mkdir(parents=True)
    (oss / ".git").mkdir()

    monkeypatch.setattr(
        "scripts.oss_sync.apply_to_oss.collect_staged_relative_paths",
        lambda _: [Path("../outside.txt")],
    )

    with pytest.raises(RuntimeError, match="relative"):
        apply_staging_to_oss(staging, oss, apply=True, branch_name="feat/oss-sync")


def test_apply_staging_to_oss_applies_only_explicit_report_paths(tmp_path: Path) -> None:
    staging = tmp_path / "stage"
    oss = tmp_path / "oss"
    (staging / "docs").mkdir(parents=True)
    (staging / "docs/keep.md").write_text("keep", encoding="utf-8")
    (staging / "docs/unlisted.md").write_text("unlisted", encoding="utf-8")
    (staging / "report.json").write_text(
        '{"copied":["docs/keep.md","report.json","apply_report.md","docs/keep.md"]}',
        encoding="utf-8",
    )
    (staging / "apply_report.md").write_text("artifact", encoding="utf-8")

    oss.mkdir(parents=True)
    (oss / ".git").mkdir()

    report = apply_staging_to_oss(staging, oss, apply=True, branch_name="feat/oss-sync")

    assert report["planned"] == ["docs/keep.md"]
    assert report["copied"] == ["docs/keep.md"]
    assert (oss / "docs/keep.md").exists()
    assert not (oss / "docs/unlisted.md").exists()
    assert not (oss / "report.json").exists()
    assert not (oss / "apply_report.md").exists()


def test_apply_staging_to_oss_fallback_excludes_report_artifacts(tmp_path: Path) -> None:
    staging = tmp_path / "stage"
    oss = tmp_path / "oss"
    (staging / "motion_player").mkdir(parents=True)
    (staging / "motion_player/__init__.py").write_text("__version__ = 'x'", encoding="utf-8")
    (staging / "report.txt").write_text("artifact", encoding="utf-8")
    (staging / "apply_report.json").write_text("{}", encoding="utf-8")
    oss.mkdir(parents=True)
    (oss / ".git").mkdir()

    report = apply_staging_to_oss(staging, oss, apply=False, branch_name="feat/oss-sync")

    assert report["planned"] == ["motion_player/__init__.py"]


def test_apply_staging_to_oss_expands_directory_entries_from_report(tmp_path: Path) -> None:
    staging = tmp_path / "stage"
    oss = tmp_path / "oss"
    (staging / "docs/sub").mkdir(parents=True)
    (staging / "docs/root.md").write_text("root", encoding="utf-8")
    (staging / "docs/sub/nested.md").write_text("nested", encoding="utf-8")
    (staging / "report.json").write_text('{"copied":["docs"]}', encoding="utf-8")

    oss.mkdir(parents=True)
    (oss / ".git").mkdir()

    report = apply_staging_to_oss(staging, oss, apply=True, branch_name="feat/oss-sync")

    assert report["planned"] == ["docs/root.md", "docs/sub/nested.md"]
    assert report["copied"] == ["docs/root.md", "docs/sub/nested.md"]
    assert (oss / "docs/root.md").exists()
    assert (oss / "docs/sub/nested.md").exists()


def test_apply_staging_to_oss_rejects_direct_symlink_file(tmp_path: Path) -> None:
    staging = tmp_path / "stage"
    oss = tmp_path / "oss"
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    staging.mkdir(parents=True)
    (staging / "payload.txt").symlink_to(outside)
    oss.mkdir(parents=True)
    (oss / ".git").mkdir()

    with pytest.raises(RuntimeError, match="symlink"):
        apply_staging_to_oss(staging, oss, apply=True, branch_name="feat/oss-sync")

    assert not (oss / "payload.txt").exists()


def test_apply_staging_to_oss_rejects_symlink_in_report_directory(tmp_path: Path) -> None:
    staging = tmp_path / "stage"
    oss = tmp_path / "oss"
    outside = tmp_path / "outside.txt"
    outside.write_text("secret", encoding="utf-8")
    (staging / "docs").mkdir(parents=True)
    (staging / "docs/keep.md").write_text("keep", encoding="utf-8")
    (staging / "docs/leak.txt").symlink_to(outside)
    (staging / "report.json").write_text('{"copied":["docs"]}', encoding="utf-8")
    oss.mkdir(parents=True)
    (oss / ".git").mkdir()

    with pytest.raises(RuntimeError, match="symlink"):
        apply_staging_to_oss(staging, oss, apply=True, branch_name="feat/oss-sync")

    assert not (oss / "docs/leak.txt").exists()
    assert not (oss / "docs/keep.md").exists()
