"""Tests for monitor-card visual QA report generation."""

from __future__ import annotations

from motion_player.gui.dearpygui_panel import DearPyGuiPanel


class _StubController:
    pass


class _FakeDpg:
    def __init__(self, sizes: dict[str, tuple[int, int]]) -> None:
        self._sizes = sizes

    def get_item_rect_size(self, tag: str) -> tuple[int, int]:
        return self._sizes[tag]


def test_monitor_layout_report_marks_fit_true() -> None:
    panel = DearPyGuiPanel(controller=_StubController(), title="Test")
    panel._dpg = _FakeDpg(
        {
            panel._monitor_card_tag: (740, 150),
            panel._monitor_line_1_tag: (700, 22),
            panel._monitor_line_2_tag: (700, 22),
            panel._monitor_line_3_tag: (700, 44),
        }
    )

    report = panel._build_monitor_card_layout_report()
    assert report["fits_all_lines"] is True


def test_monitor_layout_report_marks_fit_false_when_card_too_short() -> None:
    panel = DearPyGuiPanel(controller=_StubController(), title="Test")
    panel._dpg = _FakeDpg(
        {
            panel._monitor_card_tag: (740, 92),
            panel._monitor_line_1_tag: (700, 22),
            panel._monitor_line_2_tag: (700, 22),
            panel._monitor_line_3_tag: (700, 44),
        }
    )

    report = panel._build_monitor_card_layout_report()
    assert report["fits_all_lines"] is False
