"""OSS release governance checks."""

from pathlib import Path

PRIVATE_RELEASE_PATHS = (
    Path("docs/releases"),
    Path("scripts/release/backfill_releases.sh"),
)


def test_private_release_artifacts_are_not_present_in_oss() -> None:
    for path in PRIVATE_RELEASE_PATHS:
        assert not path.exists(), f"private-only artifact should be absent in OSS: {path}"


def test_releasing_guide_targets_oss_artifacts() -> None:
    text = Path("RELEASING.md").read_text(encoding="utf-8")

    assert "CHANGELOG.md" in text
    assert "docs/QUICKSTART_en.md" in text
    assert "docs/QUICKSTART_zh.md" in text
    assert "docs/IK_USAGE.md" in text
    assert "docs/releases" not in text
    assert "backfill_releases.sh" not in text


def test_make_release_check_uses_oss_tests() -> None:
    text = Path("Makefile").read_text(encoding="utf-8")

    assert "release-check" in text
    assert "tests/test_docs_version_state.py" in text
    assert "tests/test_release_backfill_state.py" in text
    assert "tests/test_roadmap_versions.py" in text
    assert "scripts/release/check_release_markers.py" not in text
