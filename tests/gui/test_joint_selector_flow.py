"""Tests for joint-selector callback flow."""

from __future__ import annotations

from motion_player.gui.dearpygui_panel import DearPyGuiPanel


def test_panel_extracts_joint_index_from_combo_label() -> None:
    class StubController:
        def __init__(self) -> None:
            self.calls: list[int] = []

        def on_select_edit_joint(self, idx: int) -> None:
            self.calls.append(idx)

    ctrl = StubController()
    panel = DearPyGuiPanel(controller=ctrl, title="Test")
    panel._on_joint_selected_dpg("1 : left_knee")
    assert ctrl.calls == [1]


def test_joint_combo_items_use_space_colon_space_format() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    assert panel._joint_combo_items(("hip", "knee")) == ["0 : hip", "1 : knee"]
