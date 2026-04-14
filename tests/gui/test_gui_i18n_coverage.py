"""Coverage tests for GUI i18n keys."""

from __future__ import annotations

from motion_player.gui.dearpygui_panel import DearPyGuiPanel


class _StubController:
    pass


def test_all_required_gui_i18n_keys_have_en_and_zh_entries() -> None:
    panel = DearPyGuiPanel(controller=_StubController(), title="Test")
    required = [
        "tab_play",
        "tab_tune",
        "tab_metrics",
        "tab_audit",
        "tab_convert",
        "tab_export",
        "tab_audio",
        "ik_pos_unit",
        "ik_angle_unit",
        "ik_reference_frame",
        "ik_reference_world",
        "ik_reference_local",
        "ik_current_pose",
        "ik_target_pose",
        "ik_dual_state_hint",
        "ik_current_pose_line_placeholder",
        "ik_pos_x",
        "ik_pos_y",
        "ik_pos_z",
        "ik_roll",
        "ik_pitch",
        "ik_yaw",
        "ik_step_position",
        "ik_step_angle",
        "ik_apply_full_pose",
        "metrics_motion",
        "metrics_output",
        "metrics_run",
        "tool_output",
        "audit_motion",
        "audit_robot",
        "audit_output",
        "audit_run",
        "convert_input",
        "convert_output",
        "convert_run",
        "export_motion",
        "export_robot",
        "export_output",
        "export_fps",
        "export_run",
        "audio_placeholder",
        "audio_play",
        "audio_pause",
        "audio_stop",
        "tune_position_nudge",
        "tune_rotation_nudge",
    ]
    missing = [k for k in required if k not in panel._I18N["en"] or k not in panel._I18N["zh"]]
    assert missing == []
