"""Tests for DearPyGui panel callback wiring."""

from __future__ import annotations

import numpy as np

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

        def on_edit_dof_delta(self, joint_idx: int, delta: float, propagate_radius: int = 0) -> None:
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
    assert tuple(round(float(v), 6) for v in panel._tune_state.current_position_m) == (0.4, 0.1, 0.9)
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
