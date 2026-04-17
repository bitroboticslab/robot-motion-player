"""Release tag map and backfill-script consistency checks."""

from __future__ import annotations

from pathlib import Path


def test_release_map_covers_v040_to_v052() -> None:
    text = Path("docs/releases/RELEASE_TAG_MAP.md").read_text(encoding="utf-8")
    for tag in ("v0.4.0", "v0.4.1", "v0.5.0", "v0.5.1", "v0.5.2"):
        assert f"| {tag} |" in text


def test_backfill_script_lists_v040_to_v052() -> None:
    text = Path("scripts/release/backfill_releases.sh").read_text(encoding="utf-8")
    for tag in ("v0.4.0", "v0.4.1", "v0.5.0", "v0.5.1", "v0.5.2"):
        assert tag in text


def test_release_note_files_exist_for_v040_to_v052() -> None:
    for tag in ("v0.4.0", "v0.4.1", "v0.5.0", "v0.5.1", "v0.5.2"):
        path = Path(f"docs/releases/{tag}.md")
        assert path.exists()
