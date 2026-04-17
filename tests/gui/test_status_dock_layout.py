"""Tests for the bottom status dock layout policy."""

from __future__ import annotations

from motion_player.gui.status_dock_layout import StatusDockLayout, build_status_dock_layout


def test_status_dock_layout_wide_uses_two_row_policy() -> None:
    layout = build_status_dock_layout(window_width=980)
    available = 980 - 48

    assert isinstance(layout, StatusDockLayout)
    assert layout.stacked is False
    assert layout.monitor_width > 0
    assert layout.output_width > 0
    assert layout.progress_width > 0
    assert layout.monitor_width + layout.output_width == available
    assert layout.progress_width == available
    assert layout.row1_height == 146
    assert layout.row2_height == 81
    assert layout.row1_height > layout.row2_height
    assert layout.dock_height >= 280


def test_status_dock_layout_wide_allocates_taller_first_row() -> None:
    layout = build_status_dock_layout(window_width=760)
    available = 760 - 48

    assert layout.stacked is False
    assert layout.monitor_width >= 0
    assert layout.output_width >= 0
    assert layout.progress_width >= 0
    assert layout.monitor_width <= available
    assert layout.output_width <= available
    assert layout.progress_width <= available
    assert layout.monitor_width + layout.output_width == available
    assert layout.progress_width == available
    assert layout.row1_height > layout.row2_height
    assert layout.dock_height >= 280


def test_status_dock_layout_wide_keeps_row1_taller_than_row2() -> None:
    layout = build_status_dock_layout(window_width=980)

    assert layout.stacked is False
    assert layout.row1_height > layout.row2_height


def test_status_dock_layout_narrow_stacks_cards() -> None:
    layout = build_status_dock_layout(window_width=560)

    assert layout.stacked is True
    assert layout.monitor_width == layout.output_width == layout.progress_width
    assert layout.row1_height == 112
    assert layout.row2_height == 64
    assert layout.row1_height > layout.row2_height
    assert layout.dock_height >= 320


def test_status_dock_layout_stacked_keeps_progress_shorter_than_row1() -> None:
    layout = build_status_dock_layout(window_width=560)

    assert layout.stacked is True
    assert layout.row1_height > layout.row2_height
