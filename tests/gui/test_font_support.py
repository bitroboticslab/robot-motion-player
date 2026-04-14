"""Tests for CJK font resolution used by GUI i18n rendering."""

from __future__ import annotations

from motion_player.gui.font_support import resolve_cjk_font


def test_resolve_cjk_font_returns_first_existing(tmp_path) -> None:
    missing = tmp_path / "missing.ttf"
    found = tmp_path / "NotoSansCJK-Regular.ttc"
    found.write_bytes(b"font")
    assert resolve_cjk_font([missing, found]) == found


def test_resolve_cjk_font_honors_env_override(tmp_path, monkeypatch) -> None:
    custom = tmp_path / "custom.ttf"
    custom.write_bytes(b"font")
    monkeypatch.setenv("RMP_GUI_FONT", str(custom))
    assert resolve_cjk_font([]) == custom
