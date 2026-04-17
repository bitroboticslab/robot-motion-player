from pathlib import Path


def test_oss_docs_and_changelog_exist() -> None:
    for path in (
        Path("CHANGELOG.md"),
        Path("docs/QUICKSTART_en.md"),
        Path("docs/QUICKSTART_zh.md"),
        Path("docs/IK_USAGE.md"),
        Path("docs/OSS_SYNC_AUDIT.md"),
    ):
        assert path.exists(), f"missing required OSS document: {path}"


def test_changelog_and_docs_are_v080_aligned() -> None:
    changelog = Path("CHANGELOG.md").read_text(encoding="utf-8")
    quickstart_en = Path("docs/QUICKSTART_en.md").read_text(encoding="utf-8")
    quickstart_zh = Path("docs/QUICKSTART_zh.md").read_text(encoding="utf-8")
    ik_usage = Path("docs/IK_USAGE.md").read_text(encoding="utf-8")

    assert "## [0.8.0]" in changelog
    assert "font-size" in changelog
    assert "v0.8.0" in quickstart_en
    assert "v0.8.0" in quickstart_zh
    assert "RMP_GUI_FONT_SIZE" in ik_usage
