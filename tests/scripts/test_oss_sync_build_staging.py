from pathlib import Path

import pytest

from scripts.oss_sync.build_staging import build_staging


def test_build_staging_blocks_allow_path_under_denylist(tmp_path: Path) -> None:
    src = tmp_path / "src"
    stage = tmp_path / "stage"
    (src / "docs/superpowers").mkdir(parents=True)
    (src / "docs/superpowers/secret.md").write_text("secret", encoding="utf-8")

    allow = [Path("docs/superpowers/secret.md")]
    deny = [Path("docs/superpowers")]

    report = build_staging(src, stage, allow, deny)
    assert report["blocked"] == ["docs/superpowers/secret.md"]
    assert report["copied"] == []
    assert not (stage / "docs/superpowers/secret.md").exists()


def test_build_staging_skips_denied_descendants_for_allowed_parent(tmp_path: Path) -> None:
    src = tmp_path / "src"
    stage = tmp_path / "stage"
    (src / "docs/public").mkdir(parents=True)
    (src / "docs/public/readme.md").write_text("ok", encoding="utf-8")
    (src / "docs/superpowers").mkdir(parents=True)
    (src / "docs/superpowers/secret.md").write_text("secret", encoding="utf-8")

    report = build_staging(src, stage, [Path("docs")], [Path("docs/superpowers")])

    assert report["copied"] == ["docs"]
    assert report["blocked"] == []
    assert report["skipped"] == ["docs/superpowers"]
    assert (stage / "docs/public/readme.md").exists()
    assert not (stage / "docs/superpowers/secret.md").exists()


def test_build_staging_rejects_src_stage_overlap(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir(parents=True)
    (src / "motion_player").mkdir(parents=True)
    (src / "motion_player/__init__.py").write_text("", encoding="utf-8")

    stage = src / "stage"
    allow = [Path("motion_player")]
    deny: list[Path] = []

    with pytest.raises(ValueError, match="overlap"):
        build_staging(src, stage, allow, deny)


def test_build_staging_rebuilds_fresh_stage_tree(tmp_path: Path) -> None:
    src = tmp_path / "src"
    stage = tmp_path / "stage"
    (src / "docs/public").mkdir(parents=True)
    (src / "docs/public/readme.md").write_text("ok", encoding="utf-8")
    (src / "docs/superpowers").mkdir(parents=True)
    (src / "docs/superpowers/secret.md").write_text("secret", encoding="utf-8")

    build_staging(src, stage, [Path("docs")], [])
    assert (stage / "docs/superpowers/secret.md").exists()

    report = build_staging(src, stage, [Path("docs")], [Path("docs/superpowers")])
    assert report["skipped"] == ["docs/superpowers"]
    assert not (stage / "docs/superpowers/secret.md").exists()
    assert (stage / "docs/public/readme.md").exists()


def test_build_staging_rejects_allowlisted_symlink_file(tmp_path: Path) -> None:
    src = tmp_path / "src"
    stage = tmp_path / "stage"
    src.mkdir(parents=True)
    external = tmp_path / "external.txt"
    external.write_text("outside", encoding="utf-8")
    (src / "link.txt").symlink_to(external)

    report = build_staging(src, stage, [Path("link.txt")], [])
    assert report["copied"] == []
    assert report["skipped"] == ["link.txt"]
    assert not (stage / "link.txt").exists()


def test_build_staging_rejects_symlinks_while_walking_allowlisted_dir(tmp_path: Path) -> None:
    src = tmp_path / "src"
    stage = tmp_path / "stage"
    (src / "docs").mkdir(parents=True)
    (src / "docs/readme.md").write_text("ok", encoding="utf-8")

    external = tmp_path / "external.txt"
    external.write_text("outside", encoding="utf-8")
    (src / "docs/link.txt").symlink_to(external)

    external_dir = tmp_path / "external_dir"
    external_dir.mkdir(parents=True)
    (external_dir / "secret.md").write_text("secret", encoding="utf-8")
    (src / "docs/linkdir").symlink_to(external_dir, target_is_directory=True)

    report = build_staging(src, stage, [Path("docs")], [])
    assert report["copied"] == ["docs"]
    assert report["skipped"] == ["docs/linkdir", "docs/link.txt"]
    assert (stage / "docs/readme.md").exists()
    assert not (stage / "docs/link.txt").exists()
    assert not (stage / "docs/linkdir").exists()


def test_build_staging_rejects_symlink_stage_root_before_resolution(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir(parents=True)
    (src / "docs").mkdir(parents=True)
    (src / "docs/readme.md").write_text("ok", encoding="utf-8")

    stage_target = tmp_path / "victim"
    stage_target.mkdir(parents=True)
    target_file = stage_target / "keep.txt"
    target_file.write_text("do not delete", encoding="utf-8")

    stage_symlink = tmp_path / "stage-link"
    stage_symlink.symlink_to(stage_target, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink"):
        build_staging(src, stage_symlink, [Path("docs")], [])

    assert target_file.exists()
    assert target_file.read_text(encoding="utf-8") == "do not delete"


def test_build_staging_rejects_dangling_symlink_stage_root(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir(parents=True)
    (src / "docs").mkdir(parents=True)
    (src / "docs/readme.md").write_text("ok", encoding="utf-8")

    dangling_target = tmp_path / "missing-stage-target"
    stage_symlink = tmp_path / "dangling-stage-link"
    stage_symlink.symlink_to(dangling_target, target_is_directory=True)

    with pytest.raises(ValueError, match="symlink"):
        build_staging(src, stage_symlink, [Path("docs")], [])

    assert not dangling_target.exists()
    assert stage_symlink.is_symlink()


def test_build_staging_rejects_symlink_ancestor_in_stage_path(tmp_path: Path) -> None:
    src = tmp_path / "src"
    src.mkdir(parents=True)
    (src / "docs").mkdir(parents=True)
    (src / "docs/readme.md").write_text("ok", encoding="utf-8")

    victim_root = tmp_path / "victim-root"
    victim_stage = victim_root / "stage"
    victim_stage.mkdir(parents=True)
    keep = victim_stage / "keep.txt"
    keep.write_text("do not delete", encoding="utf-8")

    symlink_parent = tmp_path / "stage-parent-link"
    symlink_parent.symlink_to(victim_root, target_is_directory=True)
    stage_path = symlink_parent / "stage"

    with pytest.raises(ValueError, match="symlink"):
        build_staging(src, stage_path, [Path("docs")], [])

    assert keep.exists()
    assert keep.read_text(encoding="utf-8") == "do not delete"


def test_build_staging_rejects_allowlisted_file_under_symlinked_source_ancestor(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    stage = tmp_path / "stage"
    outside = tmp_path / "outside"
    (outside / "nested").mkdir(parents=True)
    (outside / "nested/secret.md").write_text("secret", encoding="utf-8")
    (src / "docs").mkdir(parents=True)
    (src / "docs/link").symlink_to(outside, target_is_directory=True)

    report = build_staging(src, stage, [Path("docs/link/nested/secret.md")], [])

    assert report["copied"] == []
    assert report["skipped"] == ["docs/link/nested/secret.md"]
    assert not (stage / "docs/link/nested/secret.md").exists()


def test_build_staging_rejects_allowlisted_dir_under_symlinked_source_ancestor(
    tmp_path: Path,
) -> None:
    src = tmp_path / "src"
    stage = tmp_path / "stage"
    outside = tmp_path / "outside"
    (outside / "nested/deep").mkdir(parents=True)
    (outside / "nested/deep/secret.md").write_text("secret", encoding="utf-8")
    (src / "docs").mkdir(parents=True)
    (src / "docs/link").symlink_to(outside, target_is_directory=True)

    report = build_staging(src, stage, [Path("docs/link/nested")], [])

    assert report["copied"] == []
    assert report["skipped"] == ["docs/link/nested"]
    assert not (stage / "docs/link/nested/deep/secret.md").exists()
