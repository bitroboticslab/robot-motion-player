"""Tests for DearPyGui panel callback wiring."""

from __future__ import annotations

import numpy as np

import motion_player.gui.dearpygui_panel as dearpygui_panel_module
from motion_player.core.ui.state_monitor import PlaybackSnapshot
from motion_player.gui.dearpygui_panel import DearPyGuiPanel
from motion_player.gui.tabs import TAB_IDS


def test_panel_calls_controller_callbacks() -> None:
    calls: list[str] = []

    class StubController:
        def on_play_pause(self) -> None:
            calls.append("play")

        def on_reset(self) -> None:
            calls.append("reset")

        def on_prev_frame(self) -> None:
            calls.append("prev1")

        def on_next_frame(self) -> None:
            calls.append("next1")

        def on_prev_10(self) -> None:
            calls.append("prev10")

        def on_next_10(self) -> None:
            calls.append("next10")

        def on_prev_100(self) -> None:
            calls.append("prev100")

        def on_next_100(self) -> None:
            calls.append("next100")

        def on_toggle_loop(self) -> None:
            calls.append("loop")

        def on_toggle_pingpong(self) -> None:
            calls.append("pingpong")

        def on_mark_keyframe(self) -> None:
            calls.append("mark")

        def on_prev_marked_frame(self) -> None:
            calls.append("prev_mark")

        def on_next_marked_frame(self) -> None:
            calls.append("next_mark")

        def on_jump_marked_frame(self, frame_idx: int) -> None:
            calls.append(f"jump_mark:{frame_idx}")

        def on_toggle_ghost(self) -> None:
            calls.append("ghost")

        def on_toggle_edit(self) -> None:
            calls.append("edit")

        def on_undo_edit(self) -> None:
            calls.append("undo")

        def on_redo_edit(self) -> None:
            calls.append("redo")

        def on_edit_dof_delta(
            self, joint_idx: int, delta: float, propagate_radius: int = 0
        ) -> None:
            calls.append(f"dof:{joint_idx}:{delta:.2f}:{propagate_radius}")

        def on_save_motion(self) -> None:
            calls.append("save")

        def on_toggle_hud(self) -> None:
            calls.append("hud")

        def on_speed_up(self) -> None:
            calls.append("speed+")

        def on_speed_down(self) -> None:
            calls.append("speed-")

        def on_exit(self) -> None:
            calls.append("exit")

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._on_play_button()
    panel._on_reset_button()
    panel._on_prev_button()
    panel._on_next_button()
    panel._on_prev_10_button()
    panel._on_next_10_button()
    panel._on_prev_100_button()
    panel._on_next_100_button()
    panel._on_loop_toggle()
    panel._on_pingpong_toggle()
    panel._on_mark_keyframe_button()
    panel._on_prev_marked_frame_button()
    panel._on_next_marked_frame_button()
    panel._on_ghost_toggle()
    panel._on_edit_toggle()
    panel._on_undo_edit_button()
    panel._on_redo_edit_button()
    panel._dpg = type(
        "_FakeDpg",
        (),
        {
            "get_value": staticmethod(
                lambda tag: {
                    panel._edit_joint_combo_tag: "2 : joint_2",
                    panel._edit_joint_delta_tag: 0.1,
                    panel._edit_propagate_tag: 6,
                    panel._mark_combo_tag: "1: Frame 11",
                }[tag]
            ),
            "set_value": staticmethod(lambda _tag, _value: None),
        },
    )()
    panel._marked_frame_item_to_frame = {"1: Frame 11": 10}
    panel._on_jump_marked_frame_button()
    panel._on_apply_dof_delta_button()
    panel._on_save_button()
    panel._on_hud_toggle()
    panel._on_speed_up_button()
    panel._on_speed_down_button()
    panel._on_exit_button()
    assert calls == [
        "play",
        "reset",
        "prev1",
        "next1",
        "prev10",
        "next10",
        "prev100",
        "next100",
        "loop",
        "pingpong",
        "mark",
        "prev_mark",
        "next_mark",
        "ghost",
        "edit",
        "undo",
        "redo",
        "jump_mark:10",
        "dof:2:0.10:6",
        "save",
        "hud",
        "speed+",
        "speed-",
        "exit",
    ]


def test_panel_language_switch_changes_translation() -> None:
    class StubController:
        def on_play_pause(self) -> None:
            return None

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    assert panel._text("play_pause") == "Play / Pause"
    panel._set_language("zh")
    assert panel._text("play_pause") == "播放 / 暂停"


def test_tab_labels_switch_with_language() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    assert panel._tab_label("play") == "Play"
    panel._set_language("zh")
    assert panel._tab_label("play") == "播放"


def test_mode_buttons_record_last_action_for_feedback() -> None:
    class StubController:
        def on_toggle_loop(self) -> None:
            return None

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._on_loop_toggle()
    assert panel._last_action_key == "toggle_loop"


def test_every_interactive_control_has_tooltip_keys() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    missing = [
        key
        for key in panel._CONTROL_KEYS
        if key not in panel._TOOLTIPS["en"] or key not in panel._TOOLTIPS["zh"]
    ]
    assert missing == []


def test_panel_exposes_status_dock_builder_for_consistent_bottom_layout() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    assert callable(panel._build_status_dock)


def test_panel_viewport_resize_rebuilds_status_dock_and_monitor_layout() -> None:
    calls: list[tuple[str, int | None]] = []

    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = object()
    panel._rebuild_status_dock = lambda width_hint=None: calls.append(("dock", width_hint))
    panel._apply_monitor_card_layout = lambda width_hint=None: calls.append(("monitor", width_hint))

    panel._on_viewport_resized_dpg((960, 540))

    assert calls == [("dock", 960), ("monitor", 960)]


def test_status_dock_output_menu_label_switches_with_language() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    assert panel._text("status_dock_output_menu") == "Output"
    panel._set_language("zh")
    assert panel._text("status_dock_output_menu") == "输出"


def test_status_dock_rebuild_preserves_tool_state() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self, panel: DearPyGuiPanel) -> None:
            self.values: dict[str, object] = {
                panel._tool_result_tag: "export: rc=0\nstdout:\nDone",
                panel._tool_progress_bar_tag: 0.65,
                panel._tool_progress_text_tag: "export: 13/20 frames",
            }
            self.deleted: list[str] = []
            self.viewport_width = 920

        def does_item_exist(self, tag: str) -> bool:
            return tag in self.values or tag == panel._status_dock_container_tag

        def get_value(self, tag: str) -> object:
            return self.values[tag]

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

        def delete_item(self, tag: str) -> None:
            self.deleted.append(tag)
            self.values.pop(tag, None)

        def get_viewport_client_width(self) -> int:
            return self.viewport_width

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    fake_dpg = FakeDpg(panel)
    panel._dpg = fake_dpg
    panel._tool_progress_ratio = 0.65

    def _fake_build_status_dock(
        _dpg: object, window_width: int = 760, parent: str | None = None
    ) -> None:
        assert window_width == 920
        assert parent == panel._status_dock_container_tag
        fake_dpg.values[panel._tool_result_tag] = panel._text("tool_ready")
        fake_dpg.values[panel._tool_progress_bar_tag] = 0.0
        fake_dpg.values[panel._tool_progress_text_tag] = ""

    panel._build_status_dock = _fake_build_status_dock

    panel._rebuild_status_dock(width_hint=920)

    assert fake_dpg.deleted == [panel._status_dock_tag]
    assert fake_dpg.values[panel._tool_result_tag] == "export: rc=0\nstdout:\nDone"
    assert fake_dpg.values[panel._tool_progress_bar_tag] == 0.65
    assert fake_dpg.values[panel._tool_progress_text_tag] == "export: 13/20 frames"
    assert panel._tool_progress_ratio == 0.65


def test_status_dock_rebuild_passes_explicit_parent_container() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self, panel: DearPyGuiPanel) -> None:
            self.values: dict[str, object] = {
                panel._tool_result_tag: "ready",
                panel._tool_progress_bar_tag: 0.0,
                panel._tool_progress_text_tag: "",
            }
            self.viewport_width = 900

        def does_item_exist(self, tag: str) -> bool:
            return tag in self.values or tag == panel._status_dock_container_tag

        def get_value(self, tag: str) -> object:
            return self.values[tag]

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

        def delete_item(self, tag: str) -> None:
            self.values.pop(tag, None)

        def get_viewport_client_width(self) -> int:
            return self.viewport_width

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    fake_dpg = FakeDpg(panel)
    panel._dpg = fake_dpg

    called: dict[str, object] = {}

    def _fake_build_status_dock(
        _dpg: object, window_width: int = 760, parent: str | None = None
    ) -> None:
        called["window_width"] = window_width
        called["parent"] = parent

    panel._build_status_dock = _fake_build_status_dock

    panel._rebuild_status_dock(width_hint=900)

    assert called["window_width"] == 900
    assert called["parent"] == panel._status_dock_container_tag


def test_status_dock_rebuild_noops_when_container_missing() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self, panel: DearPyGuiPanel) -> None:
            self.values: dict[str, object] = {
                panel._tool_result_tag: "ready",
                panel._tool_progress_bar_tag: 0.0,
                panel._tool_progress_text_tag: "",
            }
            self.viewport_width = 860

        def does_item_exist(self, tag: str) -> bool:
            return tag in self.values

        def get_value(self, tag: str) -> object:
            return self.values[tag]

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

        def delete_item(self, tag: str) -> None:
            self.values.pop(tag, None)

        def get_viewport_client_width(self) -> int:
            return self.viewport_width

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    fake_dpg = FakeDpg(panel)
    panel._dpg = fake_dpg

    called = False

    def _fake_build_status_dock(
        _dpg: object, window_width: int = 760, parent: str | None = None
    ) -> None:
        nonlocal called
        called = True

    panel._build_status_dock = _fake_build_status_dock

    panel._rebuild_status_dock(width_hint=860)

    assert called is False


def test_status_dock_rebuild_fail_open_when_build_raises() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self, panel: DearPyGuiPanel) -> None:
            self.values: dict[str, object] = {
                panel._tool_result_tag: "export: rc=0",
                panel._tool_progress_bar_tag: 0.5,
                panel._tool_progress_text_tag: "export: running",
            }
            self.deleted: list[str] = []
            self.viewport_width = 880

        def does_item_exist(self, tag: str) -> bool:
            return tag in self.values or tag == panel._status_dock_container_tag

        def get_value(self, tag: str) -> object:
            return self.values[tag]

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

        def delete_item(self, tag: str) -> None:
            self.deleted.append(tag)
            self.values.pop(tag, None)

        def get_viewport_client_width(self) -> int:
            return self.viewport_width

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    fake_dpg = FakeDpg(panel)
    panel._dpg = fake_dpg

    def _fake_build_status_dock(
        _dpg: object, window_width: int = 760, parent: str | None = None
    ) -> None:
        raise RuntimeError("status dock build failure")

    panel._build_status_dock = _fake_build_status_dock

    panel._rebuild_status_dock(width_hint=880)

    assert fake_dpg.deleted == [panel._status_dock_tag]
    assert panel._tool_progress_ratio == 0.5


def test_panel_language_switch_changes_tooltip_translation() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    assert panel._tooltip_text("toggle_loop") == "Loop playback when reaching the last frame."
    panel._set_language("zh")
    assert panel._tooltip_text("toggle_loop") == "到达末帧后自动回到开头循环播放。"


def test_tune_state_defaults_from_snapshot_selected_joint_pose() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    snap = PlaybackSnapshot(
        frame=0,
        total_frames=100,
        clip=0,
        total_clips=1,
        speed=1.0,
        playing=False,
        loop=True,
        pingpong=False,
        edit_mode=False,
        show_hud=True,
        show_ghost=False,
        keyframe_count=0,
        joint_names=("joint_0",),
        selected_joint_idx=0,
        ik_target_joint="joint_0",
        selected_joint_pos_m=(0.4, 0.1, 0.9),
        selected_joint_quat_wxyz=(1.0, 0.0, 0.0, 0.0),
    )

    panel._refresh_tune_state_from_snapshot(snap)

    pos = panel._tune_state.display_position()
    assert tuple(round(float(v), 6) for v in pos) == (0.4, 0.1, 0.9)
    assert tuple(round(float(v), 6) for v in panel._tune_state.current_position_m) == (
        0.4,
        0.1,
        0.9,
    )
    assert panel._tune_state.target_joint == "joint_0"


def test_language_switch_updates_tool_section_labels() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._set_language("zh")
    assert panel._text("convert_run") == "执行转换"


def test_tune_i18n_includes_reference_frame_and_pose_sections() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    assert "Reference Frame" in panel._text("ik_reference_frame")
    assert "Current Pose" in panel._text("ik_current_pose")
    assert "Target Pose" in panel._text("ik_target_pose")


def test_font_size_option_mapping_supports_en_and_zh_labels() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    en_items = panel._font_size_items()
    assert "Medium (18)" in en_items

    panel._set_language("zh")
    zh_items = panel._font_size_items()
    assert "中 (18)" in zh_items

    assert panel._font_size_key_from_label("Large (22)") == "large"
    assert panel._font_size_key_from_label("大 (22)") == "large"


def test_font_size_changed_binds_selected_font_when_available() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.bound = None

        def bind_font(self, font: int) -> None:
            self.bound = font

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"medium": 101, "large": 202}

    panel._on_font_size_changed("Large (22)")
    panel._process_font_intents()

    assert panel._font_size_key == "large"
    assert panel._dpg.bound == 202


def test_font_size_changed_accepts_index_like_payload() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.bound = None

        def bind_font(self, font: int) -> None:
            self.bound = font

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"medium": 101, "large": 202}

    panel._on_font_size_changed(2)
    panel._process_font_intents()

    assert panel._font_size_key == "large"
    assert panel._dpg.bound == 202


def test_font_size_changed_ignores_invalid_payload_without_polling_combo_value() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.bound = None
            self.values: dict[str, object] = {}

        def bind_font(self, font: int) -> None:
            self.bound = font

        def get_value(self, _tag: str) -> object:
            raise AssertionError("get_value should not be called")

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"medium": 101, "large": 202}

    panel._on_font_size_changed({"selected": "??"})

    assert not panel._font_intents
    assert panel._font_size_key == "medium"
    assert panel._dpg.bound is None
    assert panel._dpg.values[panel._status_text_tag] == "Font selection ignored: invalid payload."


def test_font_size_changed_uses_payload_key_even_if_combo_value_is_stale() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.bound = None

        def bind_font(self, font: int) -> None:
            self.bound = font

        def get_value(self, _tag: str) -> object:
            raise AssertionError("get_value should not be called")

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"small": 101, "large": 202}
    panel._font_size_key = "small"
    panel._applied_font_size_key = "small"

    panel._on_font_size_changed("Large (22)")
    panel._process_font_intents()

    assert panel._font_size_key == "large"
    assert panel._applied_font_size_key == "large"
    assert panel._dpg.bound == 202


def test_font_size_callback_increase_not_reverted_by_stale_combo_display() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.bound: list[int] = []
            self.combo_value = "Small (14)"
            self.values: dict[str, object] = {}

        def get_value(self, tag: str) -> object:
            assert tag == panel._font_size_combo_tag
            return self.combo_value

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value
            if tag == panel._font_size_combo_tag:
                self.combo_value = str(value)

        def bind_font(self, font: int) -> None:
            self.bound.append(font)

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"small": 11, "medium": 22}
    panel._font_size_key = "small"
    panel._font_requested_key = "small"
    panel._applied_font_size_key = "small"

    panel._on_font_size_changed("Medium (18)")
    panel._process_font_intents()
    assert panel._font_size_key == "medium"

    panel._dpg.combo_value = "Small (14)"
    panel._reconcile_font_size_combo_display()

    assert panel._font_size_key == "medium"
    assert panel._applied_font_size_key == "medium"


def test_value_callback_enqueues_command_until_ui_bus_drained() -> None:
    panel = DearPyGuiPanel(controller=type("Stub", (), {})(), title="Test")
    seen: list[object] = []
    cb = panel._make_dpg_value_callback(lambda value: seen.append(value))

    cb("sender", "Medium (18)", None)

    assert seen == []
    assert len(panel._ui_commands) == 1
    panel._drain_ui_commands()
    assert seen == ["Medium (18)"]


def test_queued_font_event_applies_upward_after_ui_bus_drain() -> None:
    class FakeDpg:
        def bind_font(self, _font: int) -> None:
            return None

    panel = DearPyGuiPanel(controller=type("Stub", (), {})(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"small": 11, "medium": 22}
    panel._font_size_key = "small"
    panel._applied_font_size_key = "small"

    cb = panel._make_dpg_value_callback(panel._on_font_size_changed)
    cb("sender", "Medium (18)", None)
    panel._drain_ui_commands()
    panel._process_font_intents()

    assert panel._font_size_key == "medium"


def test_font_size_unparseable_callback_does_not_poison_future_upscale() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.bound: list[int] = []
            self.values: dict[str, object] = {}

        def bind_font(self, font: int) -> None:
            self.bound.append(font)

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"small": 11, "medium": 22}
    panel._font_size_key = "small"
    panel._applied_font_size_key = "small"

    panel._on_font_size_changed({"opaque": "payload"})
    assert panel._font_size_key == "small"

    panel._on_font_size_changed("Medium (18)")
    panel._process_font_intents()

    assert panel._font_size_key == "medium"
    assert panel._applied_font_size_key == "medium"
    assert panel._dpg.bound == [22]


def test_font_intent_stale_ack_does_not_revert_latest_applied_font() -> None:
    class FakeDpg:
        def __init__(self) -> None:
            self.bound: list[int] = []

        def bind_font(self, font: int) -> None:
            self.bound.append(font)

    panel = DearPyGuiPanel(controller=type("Stub", (), {})(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"small": 11, "medium": 22, "large": 33}
    panel._font_size_key = "small"
    panel._applied_font_size_key = "small"
    panel._enqueue_font_intent("medium")
    panel._process_font_intents()
    panel._enqueue_font_intent("large")
    panel._process_font_intents()
    panel._ack_font_apply(intent_id=1, applied_key="medium")
    assert panel._font_size_key == "large"
    assert panel._applied_font_size_key == "large"


def test_stale_failure_ack_does_not_block_later_upward_font_event() -> None:
    class FakeDpg:
        def __init__(self) -> None:
            self.bound: list[int] = []
            self.values: dict[str, object] = {}

        def bind_font(self, font: int) -> None:
            self.bound.append(font)

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

    panel = DearPyGuiPanel(controller=type("Stub", (), {})(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"small": 11, "medium": 22, "large": 33}
    panel._font_size_key = "small"
    panel._font_requested_key = "small"
    panel._applied_font_size_key = "small"

    panel._on_font_size_changed("Medium (18)")
    panel._process_font_intents()

    panel._ack_font_apply(intent_id=999, applied_key="small", ok=False, reason="stale")

    assert panel._font_size_key == "medium"
    assert panel._applied_font_size_key == "medium"
    assert panel._dpg.bound == [22]

    panel._on_font_size_changed("Large (22)")
    panel._process_font_intents()

    assert panel._font_size_key == "large"
    assert panel._applied_font_size_key == "large"
    assert panel._dpg.bound == [22, 33]
    assert panel._last_font_status_message != "Font apply failed for 'small': stale"


def test_font_intent_queue_latest_wins() -> None:
    panel = DearPyGuiPanel(controller=type("Stub", (), {})(), title="Test")
    panel._enqueue_font_intent("medium")
    panel._enqueue_font_intent("large")

    assert len(panel._font_intents) == 1
    assert next(iter(panel._font_intents)).target_key == "large"
    assert panel._font_requested_key == "large"


def test_font_apply_failure_preserves_latest_requested_key_when_pending() -> None:
    class FakeDpg:
        def __init__(self) -> None:
            self.values: dict[str, object] = {}

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

    panel = DearPyGuiPanel(controller=type("Stub", (), {})(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"small": 11, "medium": 22, "large": 33}
    panel._font_size_key = "small"
    panel._font_requested_key = "small"
    panel._applied_font_size_key = "small"

    panel._enqueue_font_intent("medium")
    intent = panel._font_intents.popleft()
    panel._font_inflight_intent_id = intent.intent_id

    panel._enqueue_font_intent("large")
    panel._ack_font_apply(
        intent_id=intent.intent_id,
        applied_key=intent.target_key,
        ok=False,
        reason="simulated bind failure",
    )

    assert panel._font_size_key == "small"
    assert panel._applied_font_size_key == "small"
    assert panel._font_requested_key == "large"
    assert (
        panel._dpg.values[panel._status_text_tag]
        == "Font apply failed for 'medium': simulated bind failure"
    )
    assert panel._font_size_combo_tag not in panel._dpg.values


def test_font_apply_success_preserves_latest_requested_key_when_pending() -> None:
    class FakeDpg:
        def __init__(self) -> None:
            self.bound: list[int] = []

        def bind_font(self, font: int) -> None:
            self.bound.append(font)

    panel = DearPyGuiPanel(controller=type("Stub", (), {})(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"small": 11, "medium": 22, "large": 33}
    panel._font_size_key = "small"
    panel._font_requested_key = "small"
    panel._applied_font_size_key = "small"

    panel._enqueue_font_intent("medium")
    intent = panel._font_intents.popleft()
    panel._font_inflight_intent_id = intent.intent_id

    panel._enqueue_font_intent("large")
    panel._ack_font_apply(intent_id=intent.intent_id, applied_key=intent.target_key, ok=True)

    assert panel._font_size_key == "medium"
    assert panel._applied_font_size_key == "medium"
    assert panel._font_requested_key == "large"
    assert len(panel._font_intents) == 1
    assert panel._font_intents[-1].target_key == "large"
    assert panel._dpg.bound == [22]


def test_font_apply_intent_fast_path_avoids_rebinding_same_key() -> None:
    class FakeDpg:
        def __init__(self) -> None:
            self.bind_calls = 0

        def bind_font(self, _font: int) -> None:
            self.bind_calls += 1

    panel = DearPyGuiPanel(controller=type("Stub", (), {})(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"medium": 22}
    panel._font_size_key = "medium"
    panel._font_requested_key = "medium"
    panel._applied_font_size_key = "medium"

    panel._enqueue_font_intent("medium")
    panel._process_font_intents()

    assert panel._dpg.bind_calls == 0


def test_font_size_combo_poll_no_longer_mutates_font_state() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.combo_value = "XLarge (26)"

        def get_value(self, tag: str) -> object:
            assert tag == panel._font_size_combo_tag
            return self.combo_value

        def set_value(self, tag: str, value: object) -> None:
            assert tag == panel._font_size_combo_tag
            self.combo_value = str(value)

        def bind_font(self, _font: int) -> None:
            raise AssertionError("bind_font should not be called")

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"small": 11, "medium": 22, "large": 33, "xlarge": 44}
    panel._font_size_key = "medium"
    panel._font_requested_key = "medium"
    panel._applied_font_size_key = "medium"

    panel._reconcile_font_size_combo_display()

    assert panel._font_size_key == "medium"
    assert panel._applied_font_size_key == "medium"


def test_font_size_items_marks_unavailable_variants() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._font_unavailable_reasons = {"large": "simulated install failure"}

    items = panel._font_size_items()

    assert "Large (22) [Unavailable]" in items


def test_font_size_changed_rejects_unavailable_choice_and_keeps_applied_font() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.bound = None
            self.status_values: dict[str, object] = {}

        def bind_font(self, font: int) -> None:
            self.bound = font

        def get_value(self, tag: str) -> object:
            assert tag == panel._font_size_combo_tag
            return "Large (22) [Unavailable]"

        def set_value(self, tag: str, value: object) -> None:
            self.status_values[tag] = value

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"small": 101}
    panel._font_unavailable_reasons = {"large": "simulated install failure"}
    panel._font_size_key = "small"
    panel._applied_font_size_key = "small"

    panel._on_font_size_changed("Large (22) [Unavailable]")
    panel._process_font_intents()

    assert panel._font_size_key == "small"
    assert panel._applied_font_size_key == "small"
    assert panel._dpg.bound is None
    assert panel._dpg.status_values[panel._status_text_tag] == "Font size 'large' unavailable."
    assert panel._last_font_status_message == "Font size 'large' unavailable."
    assert panel._dpg.status_values[panel._font_size_combo_tag] == "Small (14)"


def test_font_apply_failure_surfaces_reason_and_keeps_applied_font() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.status_values: dict[str, object] = {}

        def bind_font(self, _font: int) -> None:
            raise RuntimeError("simulated bind failure")

        def set_value(self, tag: str, value: object) -> None:
            self.status_values[tag] = value

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"small": 11, "medium": 22}
    panel._font_size_key = "small"
    panel._font_requested_key = "small"
    panel._applied_font_size_key = "small"

    panel._on_font_size_changed("Medium (18)")
    panel._process_font_intents()

    assert panel._font_size_key == "small"
    assert panel._applied_font_size_key == "small"
    assert (
        panel._dpg.status_values[panel._status_text_tag]
        == "Font apply failed for 'medium': simulated bind failure"
    )
    assert panel._dpg.status_values[panel._font_size_combo_tag] == "Small (14)"


def test_font_apply_is_idempotent_for_same_key() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.bind_calls = 0

        def bind_font(self, _font: int) -> None:
            self.bind_calls += 1

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()
    panel._font_handles = {"large": 33}
    panel._font_size_key = "large"

    panel._apply_font_size_if_needed()
    panel._apply_font_size_if_needed()

    assert panel._dpg.bind_calls == 1


def test_clear_tool_output_resets_to_ready_message() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.values: dict[str, object] = {}

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()

    panel._set_tool_result("export: rc=0\nstdout:\nDone")
    panel._on_clear_tool_output_button()

    assert panel._dpg.values[panel._tool_result_tag] == panel._text("tool_ready")


def test_tool_progress_widget_updates_with_event_payload() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.values: dict[str, object] = {}

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()

    panel._apply_tool_progress(0.42, "Exporting frames 42%")

    assert panel._dpg.values[panel._tool_progress_bar_tag] == 0.42
    assert panel._dpg.values[panel._tool_progress_text_tag] == "Exporting frames 42%"


def test_tool_progress_ratio_never_regresses_for_same_task() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.values: dict[str, object] = {}

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()

    panel._apply_tool_progress(0.7, "export: 7/10 frames")
    panel._apply_tool_progress(0.2, "export: 2/10 frames")

    assert panel._dpg.values[panel._tool_progress_bar_tag] == 0.7
    assert panel._dpg.values[panel._tool_progress_text_tag] == "export: 7/10 frames"


def test_tool_progress_ratio_resets_per_task() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.values: dict[str, object] = {}

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

    class FakeThread:
        def __init__(self, target, daemon: bool = False) -> None:
            self.target = target
            self.daemon = daemon

        def start(self) -> None:
            return None

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = FakeDpg()
    panel._tool_progress_ratio = 0.7

    original_thread = dearpygui_panel_module.threading.Thread
    dearpygui_panel_module.threading.Thread = FakeThread
    try:
        panel._launch_tool_task(task_name="export", execute=lambda _cb: "export: rc=0")
    finally:
        dearpygui_panel_module.threading.Thread = original_thread

    assert panel._tool_progress_ratio == 0.0
    assert panel._dpg.values[panel._tool_progress_bar_tag] == 0.0
    assert panel._dpg.values[panel._tool_progress_text_tag] == "export: queued"


def test_tune_action_sets_short_running_progress_state() -> None:
    calls: list[tuple[str, float, float, float]] = []

    class StubController:
        def on_apply_ik_target(self, target_joint: str, dx: float, dy: float, dz: float) -> None:
            calls.append((target_joint, dx, dy, dz))

    class FakeDpg:
        def __init__(self, panel: DearPyGuiPanel) -> None:
            self.values: dict[str, object] = {
                panel._edit_joint_combo_tag: "0 : joint_0",
                panel._ik_dx_tag: 0.0,
                panel._ik_dy_tag: 0.0,
                panel._ik_dz_tag: 0.0,
            }

        def get_value(self, tag: str) -> object:
            return self.values[tag]

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    fake = FakeDpg(panel)
    panel._dpg = fake

    panel._on_apply_ik_button()

    assert calls == [("joint_0", 0.0, 0.0, 0.0)]
    assert float(fake.values[panel._tool_progress_bar_tag]) > 0.0


def test_primary_monitor_line_formats_core_playback_state() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    snap = PlaybackSnapshot(
        frame=9,
        total_frames=88,
        clip=0,
        total_clips=1,
        speed=1.2,
        playing=True,
        loop=True,
        pingpong=False,
        edit_mode=False,
        show_hud=True,
        show_ghost=False,
        keyframe_count=3,
    )
    line = panel._format_monitor_line_primary(snap)
    assert "Clip 1/1" in line
    assert "Frame 10/88" in line
    assert "PLAY" in line
    assert "1.2x" in line


def test_secondary_monitor_line_formats_modes() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    snap = PlaybackSnapshot(
        frame=0,
        total_frames=88,
        clip=0,
        total_clips=1,
        speed=1.0,
        playing=False,
        loop=False,
        pingpong=True,
        edit_mode=True,
        show_hud=False,
        show_ghost=True,
        keyframe_count=5,
    )
    line = panel._format_monitor_line_secondary(snap)
    assert "LOOP OFF" in line
    assert "PING ON" in line
    assert "EDIT ON" in line
    assert "HUD OFF" in line
    assert "GHOST ON" in line
    assert "KEY 5" in line


def test_mark_combo_items_include_marked_frames() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    snap = PlaybackSnapshot(
        frame=0,
        total_frames=50,
        clip=0,
        total_clips=1,
        speed=1.0,
        playing=False,
        loop=True,
        pingpong=False,
        edit_mode=False,
        show_hud=True,
        show_ghost=False,
        keyframe_count=3,
        marked_frames=(2, 10, 30),
        mark_history=(2, 10, 30),
    )
    items, mapping = panel._mark_combo_items(snap)
    assert len(items) == 3
    assert mapping[items[0]] == 2
    assert mapping[items[-1]] == 30


def test_mark_history_text_shows_recent_stack() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    snap = PlaybackSnapshot(
        frame=0,
        total_frames=50,
        clip=0,
        total_clips=1,
        speed=1.0,
        playing=False,
        loop=True,
        pingpong=False,
        edit_mode=False,
        show_hud=True,
        show_ghost=False,
        keyframe_count=3,
        marked_frames=(2, 10, 30),
        mark_history=(2, 10, 30),
    )
    text = panel._format_mark_history_text(snap)
    assert "Marked Frames:" in text
    assert "3" in text
    assert "31" in text


def test_monitor_card_primary_line_is_short_and_prominent() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    snap = PlaybackSnapshot(
        frame=10,
        total_frames=100,
        clip=0,
        total_clips=1,
        speed=1.0,
        playing=True,
        loop=True,
        pingpong=False,
        edit_mode=False,
        show_hud=True,
        show_ghost=False,
        keyframe_count=0,
    )
    headline, subline, flags = panel._format_monitor_card_lines(snap)
    assert headline.startswith("Clip 1/1")
    assert "Frame 11/100" in headline
    assert subline.startswith("PLAY")
    assert "LOOP ON" in flags


def test_monitor_card_paused_state_text() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    snap = PlaybackSnapshot(
        frame=0,
        total_frames=100,
        clip=0,
        total_clips=1,
        speed=0.7,
        playing=False,
        loop=False,
        pingpong=True,
        edit_mode=True,
        show_hud=False,
        show_ghost=True,
        keyframe_count=3,
    )
    _headline, subline, flags = panel._format_monitor_card_lines(snap)
    assert subline.startswith("PAUSE")
    assert "0.7x" in subline
    assert "PING ON" in flags


def test_panel_registers_all_workbench_tabs() -> None:
    assert TAB_IDS == (
        "play",
        "tune",
        "metrics",
        "audit",
        "convert",
        "export",
        "audio",
    )


def test_panel_builds_layout_for_wide_window() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    layout = panel._build_monitor_card_layout_for_width(780)

    assert layout.card_height >= 124
    assert layout.line_wrap_px >= 650


def test_panel_builds_layout_for_narrow_window_zh() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._set_language("zh")
    layout = panel._build_monitor_card_layout_for_width(520)

    assert layout.card_height >= 156
    assert layout.needs_compact_spacing is True


def test_panel_ik_apply_uses_selected_joint_and_xyz_offsets() -> None:
    calls: list[tuple[str, float, float, float]] = []

    class StubController:
        def on_apply_ik_target(self, target_joint: str, dx: float, dy: float, dz: float) -> None:
            calls.append((target_joint, dx, dy, dz))

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._dpg = type(
        "_FakeDpg",
        (),
        {
            "get_value": staticmethod(
                lambda tag: {
                    panel._edit_joint_combo_tag: "2 : right_knee",
                    panel._ik_dx_tag: 0.05,
                    panel._ik_dy_tag: 0.0,
                    panel._ik_dz_tag: -0.02,
                }[tag]
            ),
            "set_value": staticmethod(lambda _tag, _value: None),
        },
    )()

    panel._on_apply_ik_button()
    assert calls == [("right_knee", 0.05, 0.0, -0.02)]


def test_panel_has_tab_builder_methods_for_isolated_layout() -> None:
    class StubController:
        pass

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    assert hasattr(panel, "_build_play_tab")
    assert hasattr(panel, "_build_tune_tab")
    assert hasattr(panel, "_build_metrics_tab")
    assert hasattr(panel, "_build_audit_tab")
    assert hasattr(panel, "_build_convert_tab")
    assert hasattr(panel, "_build_export_tab")
    assert hasattr(panel, "_build_audio_tab")


def test_panel_exposes_single_row_tune_nudge_builder() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.events: list[tuple[str, object]] = []

        class _GroupCtx:
            def __init__(self, events: list[tuple[str, object]], horizontal: bool) -> None:
                self._events = events
                self._horizontal = horizontal

            def __enter__(self) -> FakeDpg._GroupCtx:
                self._events.append(("group_enter", self._horizontal))
                return self

            def __exit__(self, exc_type, exc, tb) -> bool:
                self._events.append(("group_exit", self._horizontal))
                return False

        def group(self, horizontal: bool = False) -> FakeDpg._GroupCtx:
            return self._GroupCtx(self.events, horizontal)

        def add_text(self, label: str, tag: str | None = None) -> None:
            self.events.append(("text", label))

        def add_spacer(self, width: int) -> None:
            self.events.append(("spacer", width))

        def add_button(self, label: str, callback=None) -> None:
            self.events.append(("button", label))

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    assert callable(panel._build_tune_nudge_row)

    fake = FakeDpg()
    panel._build_tune_nudge_row(fake)

    assert [event[1] for event in fake.events if event[0] == "text"] == [
        "Position Nudge",
        "Rotation Nudge",
    ]
    assert [event[1] for event in fake.events if event[0] == "spacer"] == [24]
    assert [event[1] for event in fake.events if event[0] == "button"] == [
        "-X",
        "+X",
        "-Y",
        "+Y",
        "-Z",
        "+Z",
        "-R",
        "+R",
        "-P",
        "+P",
        "-Y",
        "+Y",
    ]
    assert fake.events[0] == ("group_enter", True)


def test_panel_tune_tab_invokes_single_row_tune_nudge_builder() -> None:
    class StubController:
        pass

    class FakeDpg:
        class _Ctx:
            def __init__(self, events: list[tuple[str, object]], name: str, value: object) -> None:
                self._events = events
                self._name = name
                self._value = value

            def __enter__(self) -> FakeDpg._Ctx:
                self._events.append((self._name, self._value))
                return self

            def __exit__(self, exc_type, exc, tb) -> bool:
                self._events.append((f"{self._name}_exit", self._value))
                return False

        def __init__(self) -> None:
            self.events: list[tuple[str, object]] = []

        def group(self, horizontal: bool = False) -> FakeDpg._Ctx:
            return self._Ctx(self.events, "group", horizontal)

        def tooltip(self, item_tag: str) -> FakeDpg._Ctx:
            return self._Ctx(self.events, "tooltip", item_tag)

        def add_combo(self, **kwargs) -> None:
            self.events.append(("combo", kwargs["label"]))

        def add_text(self, text: str, tag: str | None = None, **kwargs) -> None:
            self.events.append(("text", text))

        def add_button(self, **kwargs) -> None:
            self.events.append(("button", kwargs["label"]))

        def add_slider_float(self, **kwargs) -> None:
            self.events.append(("slider_float", kwargs["label"]))

        def add_input_int(self, **kwargs) -> None:
            self.events.append(("input_int", kwargs["label"]))

        def add_input_float(self, **kwargs) -> None:
            self.events.append(("input_float", kwargs["label"]))

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    called: list[object] = []
    panel._build_tune_nudge_row = lambda dpg: called.append(dpg)

    panel._build_tune_tab(FakeDpg())

    assert len(called) == 1


def test_panel_tune_nudge_button_callbacks_preserve_axis_sign_mapping() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.buttons: list[tuple[str, object]] = []

        class _GroupCtx:
            def __enter__(self) -> FakeDpg._GroupCtx:
                return self

            def __exit__(self, exc_type, exc, tb) -> bool:
                return False

        def group(self, horizontal: bool = False) -> FakeDpg._GroupCtx:
            return self._GroupCtx()

        def add_text(self, label: str, tag: str | None = None) -> None:
            return None

        def add_spacer(self, width: int) -> None:
            return None

        def add_button(self, label: str, callback=None) -> None:
            self.buttons.append((label, callback))

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    fake = FakeDpg()
    panel._build_tune_nudge_row(fake)

    expected = [
        ("-X", ("position", 0, -1)),
        ("+X", ("position", 0, 1)),
        ("-Y", ("position", 1, -1)),
        ("+Y", ("position", 1, 1)),
        ("-Z", ("position", 2, -1)),
        ("+Z", ("position", 2, 1)),
        ("-R", ("rotation", 0, -1)),
        ("+R", ("rotation", 0, 1)),
        ("-P", ("rotation", 1, -1)),
        ("+P", ("rotation", 1, 1)),
        ("-Y", ("rotation", 2, -1)),
        ("+Y", ("rotation", 2, 1)),
    ]

    assert [label for label, _ in fake.buttons] == [label for label, _ in expected]
    assert len(fake.buttons) == len(expected), "Button mapping mismatch"
    for (_label, callback), (_expected_label, (kind, axis, sign)) in zip(fake.buttons, expected):
        panel._tune_state.target_position_m = np.zeros(3, dtype=np.float64)
        panel._tune_state.target_euler_rad = np.zeros(3, dtype=np.float64)
        callback(None, None, None)
        panel._drain_ui_commands()
        if kind == "position":
            assert np.isclose(
                panel._tune_state.target_position_m[axis],
                float(sign) * panel._tune_state.step_position_m,
            )
        else:
            assert np.isclose(
                panel._tune_state.target_euler_rad[axis],
                float(sign) * panel._tune_state.step_angle_rad,
            )


def test_panel_tune_nudge_row_renders_in_zh_language_mode() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self) -> None:
            self.texts: list[str] = []

        class _GroupCtx:
            def __enter__(self) -> FakeDpg._GroupCtx:
                return self

            def __exit__(self, exc_type, exc, tb) -> bool:
                return False

        def group(self, horizontal: bool = False) -> FakeDpg._GroupCtx:
            return self._GroupCtx()

        def add_text(self, label: str, tag: str | None = None) -> None:
            self.texts.append(label)

        def add_spacer(self, width: int) -> None:
            return None

        def add_button(self, label: str, callback=None) -> None:
            return None

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._set_language("zh")
    fake = FakeDpg()

    panel._build_tune_nudge_row(fake)

    assert "位置微调" in fake.texts
    assert "旋转微调" in fake.texts


def test_position_unit_switch_preserves_internal_target_and_step_si() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self, values: dict[str, object]) -> None:
            self.values = dict(values)

        def get_value(self, tag: str) -> object:
            return self.values[tag]

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._tune_state.set_reference_frame("world")
    panel._tune_state.set_position_display((20.0, 0.0, 0.0), unit="cm")
    panel._tune_state.set_rotation_display((90.0, 0.0, 0.0), unit="deg")
    panel._tune_state.set_step_position_display(1.0)  # 1 cm
    panel._tune_state.set_step_angle_display(5.0)  # 5 deg

    fake = FakeDpg(
        {
            panel._ik_pos_unit_tag: "mm",
            panel._ik_angle_unit_tag: "deg",
            panel._ik_reference_frame_tag: panel._reference_frame_label("world"),
            panel._ik_pos_x_tag: 20.0,
            panel._ik_pos_y_tag: 0.0,
            panel._ik_pos_z_tag: 0.0,
            panel._ik_rot_roll_tag: 90.0,
            panel._ik_rot_pitch_tag: 0.0,
            panel._ik_rot_yaw_tag: 0.0,
            panel._ik_step_pos_tag: 1.0,
            panel._ik_step_angle_tag: 5.0,
            panel._ik_current_pose_line_tag: "",
        }
    )
    panel._dpg = fake

    panel._on_tune_position_unit_changed("mm")

    assert np.isclose(panel._tune_state.target_position_m[0], 0.2)
    assert np.isclose(panel._tune_state.step_position_m, 0.01)
    assert np.isclose(float(fake.values[panel._ik_pos_x_tag]), 200.0)
    assert np.isclose(float(fake.values[panel._ik_step_pos_tag]), 10.0)


def test_angle_unit_switch_preserves_internal_target_and_step_si() -> None:
    class StubController:
        pass

    class FakeDpg:
        def __init__(self, values: dict[str, object]) -> None:
            self.values = dict(values)

        def get_value(self, tag: str) -> object:
            return self.values[tag]

        def set_value(self, tag: str, value: object) -> None:
            self.values[tag] = value

    panel = DearPyGuiPanel(controller=StubController(), title="Test")
    panel._tune_state.set_reference_frame("world")
    panel._tune_state.set_position_display((20.0, 0.0, 0.0), unit="cm")
    panel._tune_state.set_rotation_display((90.0, 0.0, 0.0), unit="deg")
    panel._tune_state.set_step_position_display(1.0)
    panel._tune_state.set_step_angle_display(5.0)  # 5 deg

    fake = FakeDpg(
        {
            panel._ik_pos_unit_tag: "cm",
            panel._ik_angle_unit_tag: "rad",
            panel._ik_reference_frame_tag: panel._reference_frame_label("world"),
            panel._ik_pos_x_tag: 20.0,
            panel._ik_pos_y_tag: 0.0,
            panel._ik_pos_z_tag: 0.0,
            panel._ik_rot_roll_tag: 90.0,
            panel._ik_rot_pitch_tag: 0.0,
            panel._ik_rot_yaw_tag: 0.0,
            panel._ik_step_pos_tag: 1.0,
            panel._ik_step_angle_tag: 5.0,
            panel._ik_current_pose_line_tag: "",
        }
    )
    panel._dpg = fake

    panel._on_tune_angle_unit_changed("rad")

    assert np.isclose(panel._tune_state.target_euler_rad[0], np.pi / 2.0)
    assert np.isclose(panel._tune_state.step_angle_rad, np.deg2rad(5.0))
    assert np.isclose(float(fake.values[panel._ik_rot_roll_tag]), np.pi / 2.0)
    assert np.isclose(float(fake.values[panel._ik_step_angle_tag]), np.deg2rad(5.0))
