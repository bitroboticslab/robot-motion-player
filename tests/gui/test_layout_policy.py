"""Tests for monitor card layout sizing policy."""

from __future__ import annotations

from motion_player.gui.layout_policy import MonitorCardLayout, build_monitor_card_layout


def test_layout_policy_wide_window_keeps_three_lines_visible() -> None:
    layout = build_monitor_card_layout(window_width=780, language="en")

    assert isinstance(layout, MonitorCardLayout)
    assert layout.card_height >= 124
    assert layout.line_wrap_px >= 650
    assert layout.needs_compact_spacing is False


def test_layout_policy_narrow_window_adds_height_and_tighter_wrap() -> None:
    layout = build_monitor_card_layout(window_width=520, language="en")

    assert layout.card_height >= 148
    assert layout.line_wrap_px <= 470
    assert layout.needs_compact_spacing is True


def test_layout_policy_zh_reserves_extra_vertical_space() -> None:
    en_layout = build_monitor_card_layout(window_width=780, language="en")
    zh_layout = build_monitor_card_layout(window_width=780, language="zh")

    assert zh_layout.card_height == en_layout.card_height + 8
