# Copyright 2026 Mr-tooth
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""DearPyGui control panel for beginner-friendly playback controls."""

from __future__ import annotations

import importlib.util
import json
import logging
import os
import threading
import time
from pathlib import Path
from typing import TYPE_CHECKING, Callable

import numpy as np

from motion_player.core.kinematics.unit_conversion import AngleUnit, quat_wxyz_to_euler_xyz
from motion_player.core.ui.state_monitor import PlaybackSnapshot, StateMonitorBus
from motion_player.gui.command_models import (
    AudioRequest,
    AuditRequest,
    ConvertRequest,
    ExportRequest,
    MetricsRequest,
)
from motion_player.gui.command_runner import CommandRunner
from motion_player.gui.font_support import resolve_cjk_font
from motion_player.gui.layout_policy import MonitorCardLayout, build_monitor_card_layout
from motion_player.gui.monitor_presenter import build_monitor_view_model
from motion_player.gui.tabs import TAB_IDS
from motion_player.gui.timeline_widget import format_keyframe_line
from motion_player.gui.tune_state import IkTuneState

if TYPE_CHECKING:
    from motion_player.gui.controller import GuiController

logger = logging.getLogger(__name__)


class DearPyGuiPanel:
    """Lightweight non-blocking control panel."""

    _I18N: dict[str, dict[str, str]] = {
        "en": {
            "window_title": "Robot Motion Player Control Deck",
            "hero_title": "Playback Console",
            "hero_subtitle": "Use buttons/sliders here or keyboard shortcuts in MuJoCo.",
            "language_label": "Language",
            "status_label": "Last Action",
            "status_idle": "Waiting for interaction",
            "status_prefix": "Executed: ",
            "monitor_label": "Runtime State",
            "monitor_line_1_placeholder": "Clip --/--  Frame --/--",
            "monitor_line_2_placeholder": "PAUSE  --x",
            "monitor_line_3_placeholder": "LOOP --  PING --  EDIT --  HUD --  GHOST --  KEY --",
            "section_transport": "Transport",
            "section_navigation": "Frame Navigation",
            "section_modes": "Mode Toggles",
            "section_editor": "Editor Tools",
            "section_io": "Persistence and Visibility",
            "section_speed": "Speed and Timeline",
            "play_pause": "Play / Pause",
            "reset": "Reset",
            "prev_1": "Prev 1",
            "next_1": "Next 1",
            "prev_10": "Prev 10",
            "next_10": "Next 10",
            "prev_100": "Prev 100",
            "next_100": "Next 100",
            "toggle_loop": "Loop",
            "toggle_pingpong": "Ping-Pong",
            "mark_keyframe": "Mark Keyframe",
            "prev_marked_frame": "Prev Mark",
            "next_marked_frame": "Next Mark",
            "jump_marked_frame": "Jump Mark",
            "mark_history_label": "Marked Frames",
            "mark_history_none": "No marks yet",
            "toggle_ghost": "Ghost",
            "toggle_edit": "Edit Mode",
            "undo_edit": "Undo Edit",
            "redo_edit": "Redo Edit",
            "apply_dof_delta": "Apply DOF Delta",
            "apply_ik_target": "Apply IK Target",
            "joint_selector": "Joint",
            "joint_delta": "Joint Delta",
            "propagate_radius": "Propagate Radius",
            "ik_dx": "IK dx",
            "ik_dy": "IK dy",
            "ik_dz": "IK dz",
            "toggle_hud": "HUD",
            "save_motion": "Save Motion",
            "speed_down": "Speed -",
            "speed_up": "Speed +",
            "exit": "Exit Player",
            "speed_slider": "Speed",
            "frame_slider": "Frame",
            "clip_slider": "Clip",
            "timeline_line_placeholder": "K: none | Current [1] / -- | KeyCount 0 | Span -",
            "tab_play": "Play",
            "tab_tune": "Tune",
            "tab_metrics": "Metrics",
            "tab_audit": "Audit",
            "tab_convert": "Convert",
            "tab_export": "Export",
            "tab_audio": "Audio",
            "ik_pos_unit": "Position Unit",
            "ik_angle_unit": "Angle Unit",
            "ik_reference_frame": "Reference Frame",
            "ik_reference_world": "World",
            "ik_reference_local": "Local (Joint)",
            "ik_current_pose": "Current Pose",
            "ik_target_pose": "Target Pose",
            "ik_dual_state_hint": "Current Pose is monitor-only. Edit Target Pose below, then apply IK.",
            "ik_current_pose_line_placeholder": "Current Pose: (x --, y --, z --) | (roll --, pitch --, yaw --)",
            "ik_pos_x": "Pos X",
            "ik_pos_y": "Pos Y",
            "ik_pos_z": "Pos Z",
            "ik_roll": "Roll",
            "ik_pitch": "Pitch",
            "ik_yaw": "Yaw",
            "ik_step_position": "Step Position",
            "ik_step_angle": "Step Angle",
            "tune_position_nudge": "Position Nudge",
            "tune_rotation_nudge": "Rotation Nudge",
            "ik_apply_full_pose": "Apply Full Pose IK",
            "metrics_motion": "Motion",
            "metrics_output": "Output (.json/.csv)",
            "metrics_run": "Run Metrics",
            "tool_output": "Tool Output",
            "tool_ready": "Ready.",
            "audit_motion": "Motion",
            "audit_robot": "Robot (.xml)",
            "audit_output": "Output Sidecar (optional)",
            "audit_run": "Run Audit",
            "convert_input": "Input URDF or XML",
            "convert_output": "Output XML or URDF",
            "convert_run": "Run Convert",
            "export_motion": "Motion",
            "export_robot": "Robot (.xml)",
            "export_output": "Output (.gif/.mp4)",
            "export_fps": "FPS",
            "export_run": "Run Export",
            "audio_placeholder": "Audio module placeholder.",
            "audio_play": "Play",
            "audio_pause": "Pause",
            "audio_stop": "Stop",
        },
        "zh": {
            "window_title": "机器人动作播放器控制台",
            "hero_title": "播放控制面板",
            "hero_subtitle": "可在此使用按钮/滑条，也可在 MuJoCo 使用键盘快捷键。",
            "language_label": "语言",
            "status_label": "最近操作",
            "status_idle": "等待交互",
            "status_prefix": "已执行：",
            "monitor_label": "运行状态",
            "monitor_line_1_placeholder": "片段 --/--  帧 --/--",
            "monitor_line_2_placeholder": "暂停  --x",
            "monitor_line_3_placeholder": "循环 --  乒乓 --  编辑 --  HUD --  残影 --  关键帧 --",
            "section_transport": "传输控制",
            "section_navigation": "帧导航",
            "section_modes": "模式开关",
            "section_editor": "编辑工具",
            "section_io": "保存与显示",
            "section_speed": "速度与时间轴",
            "play_pause": "播放 / 暂停",
            "reset": "重置",
            "prev_1": "后退 1 帧",
            "next_1": "前进 1 帧",
            "prev_10": "后退 10 帧",
            "next_10": "前进 10 帧",
            "prev_100": "后退 100 帧",
            "next_100": "前进 100 帧",
            "toggle_loop": "循环",
            "toggle_pingpong": "乒乓播放",
            "mark_keyframe": "关键帧标记",
            "prev_marked_frame": "上一个标记",
            "next_marked_frame": "下一个标记",
            "jump_marked_frame": "跳转标记",
            "mark_history_label": "已标记帧",
            "mark_history_none": "暂无标记",
            "toggle_ghost": "残影",
            "toggle_edit": "编辑模式",
            "undo_edit": "撤销编辑",
            "redo_edit": "重做编辑",
            "apply_dof_delta": "应用关节增量",
            "apply_ik_target": "应用 IK 目标",
            "joint_selector": "关节",
            "joint_delta": "关节增量",
            "propagate_radius": "传播半径",
            "ik_dx": "IK dx",
            "ik_dy": "IK dy",
            "ik_dz": "IK dz",
            "toggle_hud": "HUD 显示",
            "save_motion": "保存动作",
            "speed_down": "减速",
            "speed_up": "加速",
            "exit": "退出播放器",
            "speed_slider": "速度",
            "frame_slider": "帧",
            "clip_slider": "片段",
            "timeline_line_placeholder": "K: none | Current [1] / -- | KeyCount 0 | Span -",
            "tab_play": "播放",
            "tab_tune": "调参",
            "tab_metrics": "指标",
            "tab_audit": "审计",
            "tab_convert": "转换",
            "tab_export": "导出",
            "tab_audio": "音频",
            "ik_pos_unit": "位置单位",
            "ik_angle_unit": "角度单位",
            "ik_reference_frame": "参考坐标系",
            "ik_reference_world": "世界坐标",
            "ik_reference_local": "局部（关节）",
            "ik_current_pose": "当前姿态",
            "ik_target_pose": "目标姿态",
            "ik_dual_state_hint": "当前姿态仅用于监看。请在下方编辑目标姿态后再应用 IK。",
            "ik_current_pose_line_placeholder": "当前姿态：(x --, y --, z --) | (roll --, pitch --, yaw --)",
            "ik_pos_x": "位置 X",
            "ik_pos_y": "位置 Y",
            "ik_pos_z": "位置 Z",
            "ik_roll": "横滚",
            "ik_pitch": "俯仰",
            "ik_yaw": "偏航",
            "ik_step_position": "位置步长",
            "ik_step_angle": "角度步长",
            "tune_position_nudge": "位置微调",
            "tune_rotation_nudge": "旋转微调",
            "ik_apply_full_pose": "应用全姿态 IK",
            "metrics_motion": "动作文件",
            "metrics_output": "输出路径 (.json/.csv)",
            "metrics_run": "执行指标",
            "tool_output": "工具输出",
            "tool_ready": "就绪。",
            "audit_motion": "动作文件",
            "audit_robot": "机器人模型 (.xml)",
            "audit_output": "旁路输出 (可选)",
            "audit_run": "执行审计",
            "convert_input": "输入 URDF 或 XML",
            "convert_output": "输出 XML 或 URDF",
            "convert_run": "执行转换",
            "export_motion": "动作文件",
            "export_robot": "机器人模型 (.xml)",
            "export_output": "输出文件 (.gif/.mp4)",
            "export_fps": "帧率",
            "export_run": "执行导出",
            "audio_placeholder": "音频模块占位功能。",
            "audio_play": "播放",
            "audio_pause": "暂停",
            "audio_stop": "停止",
        },
    }
    _LANGUAGE_OPTIONS: dict[str, str] = {
        "English": "en",
        "中文": "zh",
    }
    _CONTROL_KEYS: tuple[str, ...] = (
        "play_pause",
        "reset",
        "prev_1",
        "next_1",
        "prev_10",
        "next_10",
        "prev_100",
        "next_100",
        "toggle_loop",
        "toggle_pingpong",
        "mark_keyframe",
        "prev_marked_frame",
        "next_marked_frame",
        "jump_marked_frame",
        "toggle_ghost",
        "toggle_edit",
        "undo_edit",
        "redo_edit",
        "apply_dof_delta",
        "ik_dx",
        "ik_dy",
        "ik_dz",
        "apply_ik_target",
        "save_motion",
        "toggle_hud",
        "speed_down",
        "speed_up",
        "speed_slider",
        "frame_slider",
        "clip_slider",
        "ik_reference_frame",
        "exit",
    )
    _TOOLTIPS: dict[str, dict[str, str]] = {
        "en": {
            "play_pause": "Toggle playback state between running and paused.",
            "reset": "Jump to frame 1 of the current clip.",
            "prev_1": "Step backward by one frame.",
            "next_1": "Step forward by one frame.",
            "prev_10": "Step backward by ten frames.",
            "next_10": "Step forward by ten frames.",
            "prev_100": "Step backward by one hundred frames.",
            "next_100": "Step forward by one hundred frames.",
            "toggle_loop": "Loop playback when reaching the last frame.",
            "toggle_pingpong": "Reverse direction at clip boundaries.",
            "mark_keyframe": "Mark or unmark the current frame as keyframe.",
            "prev_marked_frame": "Jump to the previous marked frame (wraps around).",
            "next_marked_frame": "Jump to the next marked frame (wraps around).",
            "jump_marked_frame": "Jump directly to the frame selected in the marked-frame list.",
            "toggle_ghost": "Toggle ghost overlay state flag.",
            "toggle_edit": "Toggle edit mode state flag.",
            "undo_edit": "Restore the previous editable motion snapshot.",
            "redo_edit": "Re-apply the previously undone editable motion snapshot.",
            "apply_dof_delta": "Apply a joint delta at current frame with optional propagation.",
            "ik_dx": "X-axis offset for IK target in world coordinates.",
            "ik_dy": "Y-axis offset for IK target in world coordinates.",
            "ik_dz": "Z-axis offset for IK target in world coordinates.",
            "apply_ik_target": "Solve IK for selected joint target using the configured backend.",
            "save_motion": "Save current clip to a versioned edited file.",
            "toggle_hud": "Show or hide the MuJoCo HUD overlay.",
            "speed_down": "Decrease speed by 0.1x.",
            "speed_up": "Increase speed by 0.1x.",
            "speed_slider": "Set playback speed directly between 0.1x and 4.0x.",
            "frame_slider": "Seek directly to a target frame index.",
            "clip_slider": "Select clip index (0-based).",
            "ik_reference_frame": "Choose whether target values are interpreted in world or joint-local frame.",
            "exit": "Exit the player loop safely.",
        },
        "zh": {
            "play_pause": "在播放与暂停之间切换。",
            "reset": "跳转到当前片段第 1 帧。",
            "prev_1": "向后步进 1 帧。",
            "next_1": "向前步进 1 帧。",
            "prev_10": "向后步进 10 帧。",
            "next_10": "向前步进 10 帧。",
            "prev_100": "向后步进 100 帧。",
            "next_100": "向前步进 100 帧。",
            "toggle_loop": "到达末帧后自动回到开头循环播放。",
            "toggle_pingpong": "到达边界后反向播放，不直接跳回。",
            "mark_keyframe": "将当前帧标记或取消为关键帧。",
            "prev_marked_frame": "跳转到上一个已标记帧（支持循环）。",
            "next_marked_frame": "跳转到下一个已标记帧（支持循环）。",
            "jump_marked_frame": "跳转到下方列表中选中的标记帧。",
            "toggle_ghost": "切换残影视图状态标记。",
            "toggle_edit": "切换编辑模式状态标记。",
            "undo_edit": "恢复上一次编辑前的动作快照。",
            "redo_edit": "重新应用刚刚撤销的编辑快照。",
            "apply_dof_delta": "在当前帧应用关节增量，并可向后传播。",
            "ik_dx": "设置 IK 目标在世界坐标系 X 方向的偏移量。",
            "ik_dy": "设置 IK 目标在世界坐标系 Y 方向的偏移量。",
            "ik_dz": "设置 IK 目标在世界坐标系 Z 方向的偏移量。",
            "apply_ik_target": "使用已配置后端对所选关节目标执行 IK 求解。",
            "save_motion": "将当前片段保存为带版本号的编辑文件。",
            "toggle_hud": "显示或隐藏 MuJoCo HUD 信息。",
            "speed_down": "播放速度降低 0.1x。",
            "speed_up": "播放速度提高 0.1x。",
            "speed_slider": "在 0.1x 到 4.0x 之间直接设置播放速度。",
            "frame_slider": "直接跳转到目标帧索引。",
            "clip_slider": "选择片段索引（从 0 开始）。",
            "ik_reference_frame": "选择目标值按世界坐标还是关节局部坐标解释。",
            "exit": "安全退出播放器循环。",
        },
    }

    def __init__(
        self,
        controller: GuiController,
        title: str = "Robot Motion Player Controls",
        monitor_bus: StateMonitorBus | None = None,
        command_runner: CommandRunner | None = None,
        default_motion_path: str = "",
        default_robot_path: str = "",
    ) -> None:
        self._controller = controller
        self._title = title
        self._monitor_bus = monitor_bus
        self._command_runner = command_runner or CommandRunner()
        self._default_motion_path = default_motion_path
        self._default_robot_path = default_robot_path
        self._tune_state = IkTuneState()
        self._language = "en"
        self._last_action_key: str | None = None
        self._worker: threading.Thread | None = None
        self._dpg = None
        self._label_keys: dict[str, str] = {}
        self._text_keys: dict[str, str] = {}
        self._window_tag = "rmp_gui_window"
        self._language_combo_tag = "rmp_gui_language_combo"
        self._hero_title_tag = "rmp_gui_hero_title"
        self._hero_subtitle_tag = "rmp_gui_hero_subtitle"
        self._language_text_tag = "rmp_gui_language_text"
        self._status_text_tag = "rmp_gui_status_text"
        self._monitor_title_tag = "rmp_gui_monitor_title"
        self._monitor_card_tag = "rmp_gui_monitor_card"
        self._monitor_line_1_tag = "rmp_gui_monitor_line_1"
        self._monitor_line_2_tag = "rmp_gui_monitor_line_2"
        self._monitor_line_3_tag = "rmp_gui_monitor_line_3"
        self._timeline_line_tag = "rmp_gui_timeline_line"
        self._mark_combo_tag = "rmp_gui_mark_combo"
        self._mark_history_text_tag = "rmp_gui_mark_history_text"
        self._workbench_tabbar_tag = "rmp_gui_workbench_tabs"
        self._tool_result_tag = "rmp_gui_tool_result"
        self._metrics_motion_tag = "rmp_gui_metrics_motion"
        self._metrics_output_tag = "rmp_gui_metrics_output"
        self._audit_motion_tag = "rmp_gui_audit_motion"
        self._audit_robot_tag = "rmp_gui_audit_robot"
        self._audit_output_tag = "rmp_gui_audit_output"
        self._convert_input_tag = "rmp_gui_convert_input"
        self._convert_output_tag = "rmp_gui_convert_output"
        self._export_motion_tag = "rmp_gui_export_motion"
        self._export_robot_tag = "rmp_gui_export_robot"
        self._export_output_tag = "rmp_gui_export_output"
        self._export_fps_tag = "rmp_gui_export_fps"
        self._ik_pose_joint_tag = "rmp_gui_ik_pose_joint"
        self._ik_pos_unit_tag = "rmp_gui_ik_pos_unit"
        self._ik_angle_unit_tag = "rmp_gui_ik_angle_unit"
        self._ik_reference_frame_tag = "rmp_gui_ik_reference_frame"
        self._ik_current_pose_line_tag = "rmp_gui_ik_current_pose_line"
        self._ik_pos_x_tag = "rmp_gui_ik_pos_x"
        self._ik_pos_y_tag = "rmp_gui_ik_pos_y"
        self._ik_pos_z_tag = "rmp_gui_ik_pos_z"
        self._ik_rot_roll_tag = "rmp_gui_ik_rot_roll"
        self._ik_rot_pitch_tag = "rmp_gui_ik_rot_pitch"
        self._ik_rot_yaw_tag = "rmp_gui_ik_rot_yaw"
        self._ik_step_pos_tag = "rmp_gui_ik_step_pos"
        self._ik_step_angle_tag = "rmp_gui_ik_step_angle"
        self._edit_joint_combo_tag = "rmp_gui_edit_joint_combo"
        self._edit_joint_delta_tag = "rmp_gui_edit_joint_delta"
        self._edit_propagate_tag = "rmp_gui_edit_propagate"
        self._ik_dx_tag = "rmp_gui_ik_dx"
        self._ik_dy_tag = "rmp_gui_ik_dy"
        self._ik_dz_tag = "rmp_gui_ik_dz"
        self._joint_selector_items: list[str] = ["0 : joint_0"]
        self._marked_frame_items: list[str] = []
        self._marked_frame_item_to_frame: dict[str, int] = {}
        self._last_monitor_refresh = 0.0
        self._monitor_refresh_interval_s = 0.12
        self._tooltip_text_tags: dict[str, str] = {}
        self._visual_qa_snapshot_out = os.environ.get("RMP_GUI_SNAPSHOT_OUT")
        self._visual_qa_layout_report_out = os.environ.get("RMP_GUI_LAYOUT_REPORT_OUT")
        self._visual_qa_exported = False
        self._last_tune_sync_key: tuple[int, int] | None = None

    @staticmethod
    def is_available() -> bool:
        """Return True when DearPyGui can be imported in this environment."""
        return importlib.util.find_spec("dearpygui.dearpygui") is not None

    def _text(self, key: str) -> str:
        table = self._I18N.get(self._language, self._I18N["en"])
        return table.get(key, self._I18N["en"].get(key, key))

    def _tooltip_text(self, key: str) -> str:
        table = self._TOOLTIPS.get(self._language, self._TOOLTIPS["en"])
        return table.get(key, self._TOOLTIPS["en"].get(key, key))

    def _set_language(self, language: str) -> None:
        self._language = "zh" if language == "zh" else "en"
        self._refresh_translations()

    def _on_language_changed(
        self,
        value: object,
    ) -> None:
        if isinstance(value, str):
            mapped = self._LANGUAGE_OPTIONS.get(value)
            if mapped is not None:
                self._set_language(mapped)

    def _make_dpg_callback(
        self,
        fn: Callable[[], None],
    ) -> Callable[[object, object, object | None], None]:
        def _callback(_sender: object, _app_data: object, _user_data: object | None = None) -> None:
            del _sender, _app_data, _user_data
            fn()

        return _callback

    def _make_dpg_value_callback(
        self,
        fn: Callable[[object], None],
    ) -> Callable[[object, object, object | None], None]:
        def _callback(_sender: object, app_data: object, _user_data: object | None = None) -> None:
            del _sender, _user_data
            fn(app_data)

        return _callback

    def _register_label(self, tag: str, key: str) -> str:
        self._label_keys[tag] = key
        return tag

    def _register_text(self, tag: str, key: str) -> str:
        self._text_keys[tag] = key
        return tag

    def _refresh_translations(self) -> None:
        if self._dpg is None:
            return
        dpg = self._dpg
        dpg.configure_item(self._window_tag, label=self._text("window_title"))
        dpg.set_value(self._hero_title_tag, self._text("hero_title"))
        dpg.set_value(self._hero_subtitle_tag, self._text("hero_subtitle"))
        dpg.set_value(self._language_text_tag, self._text("language_label"))
        dpg.set_value(self._monitor_title_tag, self._text("monitor_label"))
        for tag, key in self._label_keys.items():
            dpg.configure_item(tag, label=self._text(key))
        for tag, key in self._text_keys.items():
            dpg.set_value(tag, self._text(key))
        dpg.configure_item(self._ik_reference_frame_tag, items=self._reference_frame_items())
        dpg.set_value(self._ik_reference_frame_tag, self._reference_frame_label(self._tune_state.reference_frame))
        for tab_id in TAB_IDS:
            dpg.configure_item(f"rmp_tab_{tab_id}", label=self._tab_label(tab_id))
        self._refresh_status_text()
        self._refresh_tooltips()
        self._refresh_monitor_lines(force=True)
        self._apply_monitor_card_layout()

    def _refresh_status_text(self) -> None:
        if self._dpg is None:
            return
        if self._last_action_key is None:
            self._dpg.set_value(self._status_text_tag, self._text("status_idle"))
            return
        self._dpg.set_value(
            self._status_text_tag,
            self._text("status_prefix") + self._text(self._last_action_key),
        )

    def _dispatch_action(self, action_key: str, callback: Callable[[], None]) -> None:
        callback()
        self._last_action_key = action_key
        self._refresh_status_text()

    def _tab_label(self, tab_id: str) -> str:
        labels = {
            "play": self._text("tab_play"),
            "tune": self._text("tab_tune"),
            "metrics": self._text("tab_metrics"),
            "audit": self._text("tab_audit"),
            "convert": self._text("tab_convert"),
            "export": self._text("tab_export"),
            "audio": self._text("tab_audio"),
        }
        return labels.get(tab_id, tab_id.title())

    def _reference_frame_items(self) -> list[str]:
        return [self._text("ik_reference_world"), self._text("ik_reference_local")]

    def _reference_frame_label(self, value: str) -> str:
        return self._text("ik_reference_local") if value == "local" else self._text("ik_reference_world")

    def _reference_frame_value_from_label(self, value: object) -> str:
        if not isinstance(value, str):
            return "world"
        token = value.strip().lower()
        if token in {"world", "local"}:
            return token
        if value == self._text("ik_reference_local"):
            return "local"
        if value == self._text("ik_reference_world"):
            return "world"
        # fallback for cross-language values while toggling UI language
        zh_local = self._I18N["zh"]["ik_reference_local"]
        zh_world = self._I18N["zh"]["ik_reference_world"]
        en_local = self._I18N["en"]["ik_reference_local"]
        en_world = self._I18N["en"]["ik_reference_world"]
        if value in {zh_local, en_local}:
            return "local"
        if value in {zh_world, en_world}:
            return "world"
        return "world"

    def _get_text_input(self, tag: str) -> str:
        if self._dpg is None:
            return ""
        value = self._dpg.get_value(tag)
        return str(value).strip() if value is not None else ""

    def _set_tool_result(self, result_text: str) -> None:
        if self._dpg is not None:
            try:
                self._dpg.set_value(self._tool_result_tag, result_text)
            except Exception:  # noqa: BLE001
                return

    def _format_command_result(self, title: str, rc: int, stdout: str, stderr: str) -> str:
        lines = [f"{title}: rc={rc}"]
        if stdout.strip():
            lines.append("stdout:")
            lines.append(stdout.strip())
        if stderr.strip():
            lines.append("stderr:")
            lines.append(stderr.strip())
        return "\n".join(lines)

    def _run_metrics_tool(self) -> None:
        req = MetricsRequest(
            motion=self._get_text_input(self._metrics_motion_tag),
            output=self._get_text_input(self._metrics_output_tag) or None,
        )
        result = self._command_runner.run_metrics(req)
        self._set_tool_result(
            self._format_command_result("metrics", result.return_code, result.stdout, result.stderr)
        )

    def _run_audit_tool(self) -> None:
        req = AuditRequest(
            motion=self._get_text_input(self._audit_motion_tag),
            robot=self._get_text_input(self._audit_robot_tag),
            output=self._get_text_input(self._audit_output_tag) or None,
        )
        result = self._command_runner.run_audit(req)
        self._set_tool_result(
            self._format_command_result("audit", result.return_code, result.stdout, result.stderr)
        )

    def _run_convert_tool(self) -> None:
        req = ConvertRequest(
            input_path=self._get_text_input(self._convert_input_tag),
            output_path=self._get_text_input(self._convert_output_tag),
        )
        result = self._command_runner.run_convert(req)
        self._set_tool_result(
            self._format_command_result("convert", result.return_code, result.stdout, result.stderr)
        )

    def _run_export_tool(self) -> None:
        fps_text = self._get_text_input(self._export_fps_tag)
        try:
            fps = float(fps_text) if fps_text else 30.0
        except ValueError:
            self._set_tool_result("export: rc=1\nstderr:\nInvalid FPS value.")
            return
        req = ExportRequest(
            motion=self._get_text_input(self._export_motion_tag),
            robot=self._get_text_input(self._export_robot_tag),
            output=self._get_text_input(self._export_output_tag),
            fps=fps,
        )
        result = self._command_runner.run_export(req)
        self._set_tool_result(
            self._format_command_result("export", result.return_code, result.stdout, result.stderr)
        )

    def _run_audio_tool(self, action: str) -> None:
        result = self._command_runner.run_audio(AudioRequest(action=action))
        self._set_tool_result(
            self._format_command_result(f"audio:{action}", result.return_code, result.stdout, result.stderr)
        )

    def _safe_float_input(self, tag: str, fallback: float) -> float:
        if self._dpg is None:
            return float(fallback)
        try:
            value = float(self._dpg.get_value(tag))
        except Exception:  # noqa: BLE001
            return float(fallback)
        if not np.isfinite(value):
            return float(fallback)
        return float(value)

    def _sync_tune_inputs_from_state(self) -> None:
        if self._dpg is None:
            return
        pos = self._tune_state.display_target_position()
        rot = self._tune_state.display_target_rotation()
        self._dpg.set_value(self._ik_pos_unit_tag, self._tune_state.position_unit.value)
        self._dpg.set_value(self._ik_angle_unit_tag, self._tune_state.angle_unit.value)
        self._dpg.set_value(self._ik_reference_frame_tag, self._reference_frame_label(self._tune_state.reference_frame))
        self._dpg.set_value(self._ik_pos_x_tag, float(pos[0]))
        self._dpg.set_value(self._ik_pos_y_tag, float(pos[1]))
        self._dpg.set_value(self._ik_pos_z_tag, float(pos[2]))
        self._dpg.set_value(self._ik_rot_roll_tag, float(rot[0]))
        self._dpg.set_value(self._ik_rot_pitch_tag, float(rot[1]))
        self._dpg.set_value(self._ik_rot_yaw_tag, float(rot[2]))
        self._dpg.set_value(self._ik_step_pos_tag, self._tune_state.display_step_position())
        self._dpg.set_value(self._ik_step_angle_tag, self._tune_state.display_step_angle())
        self._refresh_current_pose_line()

    def _format_current_pose_line(self) -> str:
        pos = self._tune_state.display_current_position()
        quat = np.asarray(self._tune_state.current_quat_wxyz, dtype=np.float64)
        if quat.shape != (4,):
            quat = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        rot = quat_wxyz_to_euler_xyz(quat, AngleUnit(self._tune_state.angle_unit.value))
        return (
            f"{self._text('ik_current_pose')}: "
            f"(x {float(pos[0]):.3f}, y {float(pos[1]):.3f}, z {float(pos[2]):.3f}) | "
            f"(roll {float(rot[0]):.2f}, pitch {float(rot[1]):.2f}, yaw {float(rot[2]):.2f})"
        )

    def _refresh_current_pose_line(self) -> None:
        if self._dpg is None:
            return
        self._dpg.set_value(self._ik_current_pose_line_tag, self._format_current_pose_line())

    def _read_tune_inputs_into_state(
        self,
        *,
        position_unit_override: str | None = None,
        angle_unit_override: str | None = None,
    ) -> None:
        if self._dpg is None:
            return
        pos_unit = str(position_unit_override or self._dpg.get_value(self._ik_pos_unit_tag) or self._tune_state.position_unit.value)
        angle_unit = str(
            angle_unit_override or self._dpg.get_value(self._ik_angle_unit_tag) or self._tune_state.angle_unit.value
        )
        self._tune_state.set_reference_frame(
            self._reference_frame_value_from_label(
                self._dpg.get_value(self._ik_reference_frame_tag) or self._tune_state.reference_frame
            )
        )
        self._tune_state.set_position_display(
            (
                self._safe_float_input(self._ik_pos_x_tag, float(self._tune_state.display_position()[0])),
                self._safe_float_input(self._ik_pos_y_tag, float(self._tune_state.display_position()[1])),
                self._safe_float_input(self._ik_pos_z_tag, float(self._tune_state.display_position()[2])),
            ),
            unit=pos_unit,
        )
        self._tune_state.set_rotation_display(
            (
                self._safe_float_input(self._ik_rot_roll_tag, float(self._tune_state.display_rotation()[0])),
                self._safe_float_input(self._ik_rot_pitch_tag, float(self._tune_state.display_rotation()[1])),
                self._safe_float_input(self._ik_rot_yaw_tag, float(self._tune_state.display_rotation()[2])),
            ),
            unit=angle_unit,
        )
        self._tune_state.set_step_position_display(
            self._safe_float_input(self._ik_step_pos_tag, self._tune_state.display_step_position())
        )
        self._tune_state.set_step_angle_display(
            self._safe_float_input(self._ik_step_angle_tag, self._tune_state.display_step_angle())
        )

    def _on_tune_reference_frame_changed(self, value: object) -> None:
        mode = self._reference_frame_value_from_label(value)
        self._tune_state.set_reference_frame(mode)
        if mode == "local":
            self._tune_state.target_position_m = np.zeros(3, dtype=np.float64)
            self._tune_state.target_euler_rad = np.zeros(3, dtype=np.float64)
        else:
            self._tune_state.target_position_m = self._tune_state.current_position_m.copy()
            quat = np.asarray(self._tune_state.current_quat_wxyz, dtype=np.float64)
            euler = quat_wxyz_to_euler_xyz(quat, AngleUnit(self._tune_state.angle_unit.value))
            self._tune_state.set_rotation_display((float(euler[0]), float(euler[1]), float(euler[2])), unit=self._tune_state.angle_unit.value)
        self._sync_tune_inputs_from_state()

    def _on_tune_position_unit_changed(self, value: object) -> None:
        previous_pos_unit = self._tune_state.position_unit.value
        previous_angle_unit = self._tune_state.angle_unit.value
        self._read_tune_inputs_into_state(
            position_unit_override=previous_pos_unit,
            angle_unit_override=previous_angle_unit,
        )
        self._tune_state.switch_position_unit(str(value))
        self._sync_tune_inputs_from_state()

    def _on_tune_angle_unit_changed(self, value: object) -> None:
        previous_pos_unit = self._tune_state.position_unit.value
        previous_angle_unit = self._tune_state.angle_unit.value
        self._read_tune_inputs_into_state(
            position_unit_override=previous_pos_unit,
            angle_unit_override=previous_angle_unit,
        )
        self._tune_state.switch_angle_unit(str(value))
        self._sync_tune_inputs_from_state()

    def _on_tune_nudge_position(self, axis: int, sign: int) -> None:
        self._read_tune_inputs_into_state()
        self._tune_state.nudge_position(axis=axis, sign=sign)
        self._sync_tune_inputs_from_state()

    def _on_tune_nudge_rotation(self, axis: int, sign: int) -> None:
        self._read_tune_inputs_into_state()
        self._tune_state.nudge_rotation(axis=axis, sign=sign)
        self._sync_tune_inputs_from_state()

    def _current_tune_joint_name(self) -> str:
        if self._dpg is not None:
            try:
                combo_value = self._dpg.get_value(self._edit_joint_combo_tag)
                return self._joint_name_from_combo_value(combo_value)
            except Exception:  # noqa: BLE001
                pass
        return "joint_0"

    def _on_apply_ik_pose_button(self) -> None:
        self._read_tune_inputs_into_state()
        pos = self._tune_state.display_position()
        rot = self._tune_state.display_rotation()
        propagate_radius = 0
        if self._dpg is not None:
            try:
                propagate_radius = int(self._dpg.get_value(self._edit_propagate_tag))
            except Exception:  # noqa: BLE001
                propagate_radius = 0
        self._dispatch_action(
            "apply_ik_target",
            lambda: self._controller.on_apply_ik_pose(
                target_joint=self._current_tune_joint_name(),
                position=(float(pos[0]), float(pos[1]), float(pos[2])),
                rotation=(float(rot[0]), float(rot[1]), float(rot[2])),
                position_unit=self._tune_state.position_unit.value,
                angle_unit=self._tune_state.angle_unit.value,
                reference_frame=self._tune_state.reference_frame,
                propagate_radius=propagate_radius,
            ),
        )

    def _monitor_placeholder_line_primary(self) -> str:
        return self._text("monitor_line_1_placeholder")

    def _monitor_placeholder_line_secondary(self) -> str:
        return self._text("monitor_line_2_placeholder")

    def _monitor_placeholder_line_flags(self) -> str:
        return self._text("monitor_line_3_placeholder")

    def _timeline_placeholder_line(self) -> str:
        return self._text("timeline_line_placeholder")

    def _format_monitor_card_lines(self, snap: PlaybackSnapshot) -> tuple[str, str, str]:
        vm = build_monitor_view_model(snap)
        return vm.headline, vm.subline, vm.flags_line

    def _joint_combo_items(self, names: tuple[str, ...]) -> list[str]:
        if not names:
            return ["0 : joint_0"]
        return [f"{idx} : {name}" for idx, name in enumerate(names)]

    @staticmethod
    def _joint_index_from_combo_value(value: object) -> int:
        if isinstance(value, str):
            head = value.split(":", 1)[0].strip()
            if head.isdigit():
                return int(head)
        if isinstance(value, int):
            return value
        return 0

    def _joint_name_from_combo_value(self, value: object) -> str:
        if isinstance(value, str) and ":" in value:
            return value.split(":", 1)[1].strip()
        idx = self._joint_index_from_combo_value(value)
        idx = max(0, min(idx, len(self._joint_selector_items) - 1))
        item = self._joint_selector_items[idx]
        if ":" in item:
            return item.split(":", 1)[1].strip()
        return f"joint_{idx}"

    def _mark_combo_items(self, snap: PlaybackSnapshot) -> tuple[list[str], dict[str, int]]:
        if not snap.marked_frames:
            label = self._text("mark_history_none")
            return [label], {}
        items: list[str] = []
        mapping: dict[str, int] = {}
        frame_label = self._text("frame_slider")
        for idx, frame in enumerate(snap.marked_frames):
            item = f"{idx + 1}: {frame_label} {int(frame) + 1}"
            items.append(item)
            mapping[item] = int(frame)
        return items, mapping

    def _selected_marked_frame(self) -> int | None:
        if self._dpg is None:
            return None
        value = self._dpg.get_value(self._mark_combo_tag)
        if not isinstance(value, str):
            return None
        return self._marked_frame_item_to_frame.get(value)

    def _format_mark_history_text(self, snap: PlaybackSnapshot) -> str:
        if not snap.mark_history:
            return f"{self._text('mark_history_label')}: {self._text('mark_history_none')}"
        history_tail = [int(frame) + 1 for frame in snap.mark_history[-12:]]
        arrow = " -> "
        return f"{self._text('mark_history_label')}: " + arrow.join(str(frame) for frame in history_tail)

    def _reset_marked_frames_widgets(self) -> None:
        if self._dpg is None:
            return
        empty_label = self._text("mark_history_none")
        self._marked_frame_items = [empty_label]
        self._marked_frame_item_to_frame = {}
        try:
            self._dpg.configure_item(self._mark_combo_tag, items=self._marked_frame_items)
            self._dpg.set_value(self._mark_combo_tag, empty_label)
            self._dpg.set_value(
                self._mark_history_text_tag,
                f"{self._text('mark_history_label')}: {empty_label}",
            )
        except Exception:  # noqa: BLE001
            return

    def _on_joint_selected_dpg(self, value: object) -> None:
        self._controller.on_select_edit_joint(self._joint_index_from_combo_value(value))

    def _refresh_joint_selector_from_snapshot(self, snap: PlaybackSnapshot) -> None:
        if self._dpg is None:
            return
        items = self._joint_combo_items(snap.joint_names)
        if items != self._joint_selector_items:
            self._joint_selector_items = items
            self._dpg.configure_item(self._edit_joint_combo_tag, items=items)
        idx = max(0, min(int(snap.selected_joint_idx), len(self._joint_selector_items) - 1))
        selected_value = self._joint_selector_items[idx]
        self._dpg.set_value(self._edit_joint_combo_tag, selected_value)
        self._refresh_tune_current_state_from_snapshot(snap)
        sync_key = (int(snap.clip), int(snap.selected_joint_idx))
        if self._last_tune_sync_key != sync_key:
            self._refresh_tune_target_state_from_snapshot(snap)
            self._last_tune_sync_key = sync_key

    def _refresh_marked_frames_from_snapshot(self, snap: PlaybackSnapshot) -> None:
        if self._dpg is None:
            return
        items, mapping = self._mark_combo_items(snap)
        if items != self._marked_frame_items:
            self._marked_frame_items = items
            self._marked_frame_item_to_frame = mapping
            self._dpg.configure_item(self._mark_combo_tag, items=items)
        if self._marked_frame_items:
            current = self._dpg.get_value(self._mark_combo_tag)
            if current not in self._marked_frame_items:
                self._dpg.set_value(self._mark_combo_tag, self._marked_frame_items[0])
        self._dpg.set_value(self._mark_history_text_tag, self._format_mark_history_text(snap))

    def _refresh_tune_current_state_from_snapshot(self, snap: PlaybackSnapshot) -> None:
        self._tune_state.set_current_position_m(
            (
                float(snap.selected_joint_pos_m[0]),
                float(snap.selected_joint_pos_m[1]),
                float(snap.selected_joint_pos_m[2]),
            )
        )
        self._tune_state.set_current_quat_wxyz(snap.selected_joint_quat_wxyz)
        self._refresh_current_pose_line()

    def _refresh_tune_target_state_from_snapshot(self, snap: PlaybackSnapshot) -> None:
        if snap.joint_names:
            idx = max(0, min(int(snap.selected_joint_idx), len(snap.joint_names) - 1))
            target_joint = snap.ik_target_joint or str(snap.joint_names[idx])
        else:
            target_joint = snap.ik_target_joint or ""
        self._tune_state.target_joint = str(target_joint)
        self._tune_state.target_position_m = self._tune_state.current_position_m.copy()
        quat = np.asarray(self._tune_state.current_quat_wxyz, dtype=np.float64)
        if quat.shape != (4,):
            quat = np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64)
        euler = quat_wxyz_to_euler_xyz(quat, AngleUnit(self._tune_state.angle_unit.value))
        if self._tune_state.reference_frame == "local":
            self._tune_state.target_euler_rad = np.zeros(3, dtype=np.float64)
            self._tune_state.target_position_m = np.zeros(3, dtype=np.float64)
        else:
            self._tune_state.set_rotation_display(
                (float(euler[0]), float(euler[1]), float(euler[2])),
                unit=self._tune_state.angle_unit.value,
            )
        self._sync_tune_inputs_from_state()

    def _refresh_tune_state_from_snapshot(self, snap: PlaybackSnapshot) -> None:
        """Backward-compatible wrapper used by existing tests."""
        self._refresh_tune_current_state_from_snapshot(snap)
        self._refresh_tune_target_state_from_snapshot(snap)

    def _build_monitor_card_layout_for_width(self, window_width: int) -> MonitorCardLayout:
        return build_monitor_card_layout(window_width=window_width, language=self._language)

    def _apply_monitor_card_layout(self, width_hint: int | None = None) -> None:
        if self._dpg is None:
            return

        width = width_hint
        if width is None:
            width = int(self._dpg.get_viewport_client_width())

        layout = self._build_monitor_card_layout_for_width(width)
        self._dpg.configure_item(self._monitor_card_tag, height=layout.card_height)
        self._dpg.configure_item(self._monitor_line_1_tag, wrap=layout.line_wrap_px)
        self._dpg.configure_item(self._monitor_line_2_tag, wrap=layout.line_wrap_px)
        self._dpg.configure_item(self._monitor_line_3_tag, wrap=layout.line_wrap_px)

    def _on_viewport_resized_dpg(self, app_data: object) -> None:
        width = None
        if isinstance(app_data, (list, tuple)) and len(app_data) >= 1:
            width = int(app_data[0])
        self._apply_monitor_card_layout(width_hint=width)

    def _build_monitor_card_layout_report(self) -> dict[str, object]:
        if self._dpg is None:
            return {"fits_all_lines": False, "reason": "dpg-unavailable"}

        card_w, card_h = self._dpg.get_item_rect_size(self._monitor_card_tag)
        _w1, h1 = self._dpg.get_item_rect_size(self._monitor_line_1_tag)
        _w2, h2 = self._dpg.get_item_rect_size(self._monitor_line_2_tag)
        _w3, h3 = self._dpg.get_item_rect_size(self._monitor_line_3_tag)

        estimated_title_h = 22
        estimated_padding = 16
        required_h = estimated_title_h + estimated_padding + h1 + h2 + h3

        return {
            "card_width": card_w,
            "card_height": card_h,
            "line_heights": [h1, h2, h3],
            "required_height": required_h,
            "fits_all_lines": required_h <= card_h,
        }

    def _maybe_export_visual_qa_artifacts(self) -> None:
        if self._dpg is None or self._visual_qa_exported:
            return
        if not self._visual_qa_snapshot_out and not self._visual_qa_layout_report_out:
            return

        try:
            if self._visual_qa_snapshot_out:
                self._dpg.output_frame_buffer(file=self._visual_qa_snapshot_out)

            if self._visual_qa_layout_report_out:
                report = self._build_monitor_card_layout_report()
                Path(self._visual_qa_layout_report_out).write_text(
                    json.dumps(report, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
        except Exception as exc:  # noqa: BLE001
            logger.warning("GUI visual QA export failed: %s", exc)
        finally:
            self._visual_qa_exported = True

    def _format_monitor_line_primary(self, snap: PlaybackSnapshot) -> str:
        headline, subline, _flags = self._format_monitor_card_lines(snap)
        return f"{headline} | {subline}"

    def _format_monitor_line_secondary(self, snap: PlaybackSnapshot) -> str:
        _headline, _subline, flags = self._format_monitor_card_lines(snap)
        return flags

    def _refresh_monitor_lines(self, force: bool = False) -> None:
        if self._dpg is None:
            return
        now = time.monotonic()
        if not force and (now - self._last_monitor_refresh) < self._monitor_refresh_interval_s:
            return
        self._last_monitor_refresh = now
        if self._monitor_bus is None:
            self._dpg.set_value(self._monitor_line_1_tag, self._monitor_placeholder_line_primary())
            self._dpg.set_value(self._monitor_line_2_tag, self._monitor_placeholder_line_secondary())
            self._dpg.set_value(self._monitor_line_3_tag, self._monitor_placeholder_line_flags())
            self._dpg.set_value(self._timeline_line_tag, self._timeline_placeholder_line())
            self._reset_marked_frames_widgets()
            return
        snap = self._monitor_bus.latest()
        if snap is None:
            self._dpg.set_value(self._monitor_line_1_tag, self._monitor_placeholder_line_primary())
            self._dpg.set_value(self._monitor_line_2_tag, self._monitor_placeholder_line_secondary())
            self._dpg.set_value(self._monitor_line_3_tag, self._monitor_placeholder_line_flags())
            self._dpg.set_value(self._timeline_line_tag, self._timeline_placeholder_line())
            self._reset_marked_frames_widgets()
            return
        headline, subline, flags = self._format_monitor_card_lines(snap)
        self._dpg.set_value(self._monitor_line_1_tag, headline)
        self._dpg.set_value(self._monitor_line_2_tag, subline)
        self._dpg.set_value(self._monitor_line_3_tag, flags)
        self._refresh_joint_selector_from_snapshot(snap)
        self._refresh_marked_frames_from_snapshot(snap)
        self._dpg.set_value(
            self._timeline_line_tag,
            format_keyframe_line(
                total_frames=snap.total_frames,
                keyframes=list(snap.marked_frames),
                current_frame=snap.frame,
            ),
        )

    def _default_cjk_candidates(self) -> list[Path]:
        return [
            Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc"),
            Path("/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc"),
            Path("/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"),
            Path("/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc"),
            Path("/System/Library/Fonts/PingFang.ttc"),
            Path("/System/Library/Fonts/Hiragino Sans GB.ttc"),
            Path("C:/Windows/Fonts/msyh.ttc"),
            Path("C:/Windows/Fonts/simhei.ttf"),
        ]

    def _install_fonts(self, dpg: object) -> None:
        font_path = resolve_cjk_font(self._default_cjk_candidates())
        if font_path is None:
            return
        try:
            with dpg.font_registry():
                font = dpg.add_font(str(font_path), 18)
                dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full, parent=font)
                dpg.bind_font(font)
        except Exception as exc:  # noqa: BLE001
            logger.warning("GUI CJK font setup failed for %s: %s", font_path, exc)

    def _attach_tooltip(self, dpg: object, item_tag: str, tip_key: str) -> None:
        text_tag = f"tooltip_text_{item_tag}"
        with dpg.tooltip(item_tag):
            dpg.add_text(self._tooltip_text(tip_key), tag=text_tag)
        self._tooltip_text_tags[tip_key] = text_tag

    def _refresh_tooltips(self) -> None:
        if self._dpg is None:
            return
        for tip_key, text_tag in self._tooltip_text_tags.items():
            self._dpg.set_value(text_tag, self._tooltip_text(tip_key))

    def _create_theme(self, dpg: object) -> int:
        theme = dpg.add_theme()
        with dpg.theme_component(dpg.mvAll, parent=theme):
            dpg.add_theme_color(dpg.mvThemeCol_WindowBg, (14, 24, 35), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (20, 34, 48), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(dpg.mvThemeCol_Button, (33, 79, 112), category=dpg.mvThemeCat_Core)
            dpg.add_theme_color(
                dpg.mvThemeCol_ButtonHovered,
                (47, 114, 161),
                category=dpg.mvThemeCat_Core,
            )
            dpg.add_theme_color(
                dpg.mvThemeCol_ButtonActive,
                (26, 140, 173),
                category=dpg.mvThemeCat_Core,
            )
            dpg.add_theme_color(dpg.mvThemeCol_FrameBg, (23, 40, 57), category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FrameRounding, 6, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 8, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowRounding, 10, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_FramePadding, 8, 6, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ItemSpacing, 8, 8, category=dpg.mvThemeCat_Core)
        return theme

    def _create_monitor_card_theme(self, dpg: object) -> int:
        theme = dpg.add_theme()
        with dpg.theme_component(dpg.mvChildWindow, parent=theme):
            dpg.add_theme_color(dpg.mvThemeCol_ChildBg, (17, 37, 50), category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_ChildRounding, 10, category=dpg.mvThemeCat_Core)
            dpg.add_theme_style(dpg.mvStyleVar_WindowPadding, 10, 8, category=dpg.mvThemeCat_Core)
        return theme

    def _on_play_button(self) -> None:
        self._dispatch_action("play_pause", self._controller.on_play_pause)

    def _on_reset_button(self) -> None:
        self._dispatch_action("reset", self._controller.on_reset)

    def _on_prev_button(self) -> None:
        self._dispatch_action("prev_1", self._controller.on_prev_frame)

    def _on_next_button(self) -> None:
        self._dispatch_action("next_1", self._controller.on_next_frame)

    def _on_prev_10_button(self) -> None:
        self._dispatch_action("prev_10", self._controller.on_prev_10)

    def _on_next_10_button(self) -> None:
        self._dispatch_action("next_10", self._controller.on_next_10)

    def _on_prev_100_button(self) -> None:
        self._dispatch_action("prev_100", self._controller.on_prev_100)

    def _on_next_100_button(self) -> None:
        self._dispatch_action("next_100", self._controller.on_next_100)

    def _on_loop_toggle(self) -> None:
        self._dispatch_action("toggle_loop", self._controller.on_toggle_loop)

    def _on_pingpong_toggle(self) -> None:
        self._dispatch_action("toggle_pingpong", self._controller.on_toggle_pingpong)

    def _on_mark_keyframe_button(self) -> None:
        self._dispatch_action("mark_keyframe", self._controller.on_mark_keyframe)

    def _on_prev_marked_frame_button(self) -> None:
        self._dispatch_action("prev_marked_frame", self._controller.on_prev_marked_frame)

    def _on_next_marked_frame_button(self) -> None:
        self._dispatch_action("next_marked_frame", self._controller.on_next_marked_frame)

    def _on_jump_marked_frame_button(self) -> None:
        frame = self._selected_marked_frame()
        if frame is None:
            return
        self._dispatch_action("jump_marked_frame", lambda: self._controller.on_jump_marked_frame(int(frame)))

    def _on_ghost_toggle(self) -> None:
        self._dispatch_action("toggle_ghost", self._controller.on_toggle_ghost)

    def _on_edit_toggle(self) -> None:
        self._dispatch_action("toggle_edit", self._controller.on_toggle_edit)

    def _on_undo_edit_button(self) -> None:
        self._dispatch_action("undo_edit", self._controller.on_undo_edit)

    def _on_redo_edit_button(self) -> None:
        self._dispatch_action("redo_edit", self._controller.on_redo_edit)

    def _on_apply_dof_delta_button(self) -> None:
        if self._dpg is None:
            return
        joint_idx = self._joint_index_from_combo_value(self._dpg.get_value(self._edit_joint_combo_tag))
        delta = float(self._dpg.get_value(self._edit_joint_delta_tag))
        propagate_radius = int(self._dpg.get_value(self._edit_propagate_tag))
        self._dispatch_action(
            "apply_dof_delta",
            lambda: self._controller.on_edit_dof_delta(
                joint_idx=joint_idx,
                delta=delta,
                propagate_radius=propagate_radius,
            ),
        )

    def _on_apply_ik_button(self) -> None:
        if self._dpg is None:
            return
        joint_value = self._dpg.get_value(self._edit_joint_combo_tag)
        target_joint = self._joint_name_from_combo_value(joint_value)
        dx = float(self._dpg.get_value(self._ik_dx_tag))
        dy = float(self._dpg.get_value(self._ik_dy_tag))
        dz = float(self._dpg.get_value(self._ik_dz_tag))
        self._dispatch_action(
            "apply_ik_target",
            lambda: self._controller.on_apply_ik_target(target_joint, dx, dy, dz),
        )

    def _on_hud_toggle(self) -> None:
        self._dispatch_action("toggle_hud", self._controller.on_toggle_hud)

    def _on_save_button(self) -> None:
        self._dispatch_action("save_motion", self._controller.on_save_motion)

    def _on_speed_up_button(self) -> None:
        self._dispatch_action("speed_up", self._controller.on_speed_up)

    def _on_speed_down_button(self) -> None:
        self._dispatch_action("speed_down", self._controller.on_speed_down)

    def _on_exit_button(self) -> None:
        self._dispatch_action("exit", self._controller.on_exit)

    def _on_speed_changed(self, speed: float) -> None:
        self._last_action_key = "speed_slider"
        self._refresh_status_text()
        self._controller.on_speed_changed(float(speed))

    def _on_speed_changed_dpg(self, value: object) -> None:
        self._on_speed_changed(float(value))

    def _on_frame_changed(self, frame_idx: int) -> None:
        self._last_action_key = "frame_slider"
        self._refresh_status_text()
        self._controller.on_seek_frame(int(frame_idx))

    def _on_frame_changed_dpg(self, value: object) -> None:
        self._on_frame_changed(int(value))

    def _on_clip_changed(self, clip_idx: int) -> None:
        self._last_action_key = "clip_slider"
        self._refresh_status_text()
        self._controller.on_clip_selected(int(clip_idx))

    def _on_clip_changed_dpg(self, value: object) -> None:
        self._on_clip_changed(int(value))

    def _build_play_tab(self, dpg: object) -> None:
        dpg.add_text(
            self._text("section_transport"),
            tag=self._register_text("txt_transport", "section_transport"),
        )
        with dpg.group(horizontal=True):
            dpg.add_button(
                label=self._text("play_pause"),
                width=130,
                callback=self._make_dpg_callback(self._on_play_button),
                tag=self._register_label("btn_play", "play_pause"),
            )
            self._attach_tooltip(dpg, "btn_play", "play_pause")
            dpg.add_button(
                label=self._text("reset"),
                width=120,
                callback=self._make_dpg_callback(self._on_reset_button),
                tag=self._register_label("btn_reset", "reset"),
            )
            self._attach_tooltip(dpg, "btn_reset", "reset")
            dpg.add_button(
                label=self._text("exit"),
                width=120,
                callback=self._make_dpg_callback(self._on_exit_button),
                tag=self._register_label("btn_exit", "exit"),
            )
            self._attach_tooltip(dpg, "btn_exit", "exit")

        dpg.add_text(
            self._text("section_navigation"),
            tag=self._register_text("txt_navigation", "section_navigation"),
        )
        with dpg.group(horizontal=True):
            dpg.add_button(
                label=self._text("prev_1"),
                width=90,
                callback=self._make_dpg_callback(self._on_prev_button),
                tag=self._register_label("btn_prev_1", "prev_1"),
            )
            self._attach_tooltip(dpg, "btn_prev_1", "prev_1")
            dpg.add_button(
                label=self._text("next_1"),
                width=90,
                callback=self._make_dpg_callback(self._on_next_button),
                tag=self._register_label("btn_next_1", "next_1"),
            )
            self._attach_tooltip(dpg, "btn_next_1", "next_1")
            dpg.add_button(
                label=self._text("prev_10"),
                width=100,
                callback=self._make_dpg_callback(self._on_prev_10_button),
                tag=self._register_label("btn_prev_10", "prev_10"),
            )
            self._attach_tooltip(dpg, "btn_prev_10", "prev_10")
            dpg.add_button(
                label=self._text("next_10"),
                width=100,
                callback=self._make_dpg_callback(self._on_next_10_button),
                tag=self._register_label("btn_next_10", "next_10"),
            )
            self._attach_tooltip(dpg, "btn_next_10", "next_10")
            dpg.add_button(
                label=self._text("prev_100"),
                width=110,
                callback=self._make_dpg_callback(self._on_prev_100_button),
                tag=self._register_label("btn_prev_100", "prev_100"),
            )
            self._attach_tooltip(dpg, "btn_prev_100", "prev_100")
            dpg.add_button(
                label=self._text("next_100"),
                width=110,
                callback=self._make_dpg_callback(self._on_next_100_button),
                tag=self._register_label("btn_next_100", "next_100"),
            )
            self._attach_tooltip(dpg, "btn_next_100", "next_100")

        dpg.add_text(self._text("section_modes"), tag=self._register_text("txt_modes", "section_modes"))
        with dpg.group(horizontal=True):
            dpg.add_button(
                label=self._text("toggle_loop"),
                width=110,
                callback=self._make_dpg_callback(self._on_loop_toggle),
                tag=self._register_label("btn_loop", "toggle_loop"),
            )
            self._attach_tooltip(dpg, "btn_loop", "toggle_loop")
            dpg.add_button(
                label=self._text("toggle_pingpong"),
                width=120,
                callback=self._make_dpg_callback(self._on_pingpong_toggle),
                tag=self._register_label("btn_pingpong", "toggle_pingpong"),
            )
            self._attach_tooltip(dpg, "btn_pingpong", "toggle_pingpong")
            dpg.add_button(
                label=self._text("toggle_hud"),
                width=120,
                callback=self._make_dpg_callback(self._on_hud_toggle),
                tag=self._register_label("btn_hud", "toggle_hud"),
            )
            self._attach_tooltip(dpg, "btn_hud", "toggle_hud")

        dpg.add_text(self._text("section_speed"), tag=self._register_text("txt_speed", "section_speed"))
        with dpg.group(horizontal=True):
            dpg.add_button(
                label=self._text("speed_down"),
                width=100,
                callback=self._make_dpg_callback(self._on_speed_down_button),
                tag=self._register_label("btn_speed_down", "speed_down"),
            )
            self._attach_tooltip(dpg, "btn_speed_down", "speed_down")
            dpg.add_button(
                label=self._text("speed_up"),
                width=100,
                callback=self._make_dpg_callback(self._on_speed_up_button),
                tag=self._register_label("btn_speed_up", "speed_up"),
            )
            self._attach_tooltip(dpg, "btn_speed_up", "speed_up")
        dpg.add_slider_float(
            label=self._text("speed_slider"),
            default_value=1.0,
            min_value=0.1,
            max_value=4.0,
            callback=self._make_dpg_value_callback(self._on_speed_changed_dpg),
            tag=self._register_label("slider_speed", "speed_slider"),
        )
        self._attach_tooltip(dpg, "slider_speed", "speed_slider")
        dpg.add_slider_int(
            label=self._text("frame_slider"),
            default_value=0,
            min_value=0,
            max_value=10000,
            callback=self._make_dpg_value_callback(self._on_frame_changed_dpg),
            tag=self._register_label("slider_frame", "frame_slider"),
        )
        self._attach_tooltip(dpg, "slider_frame", "frame_slider")
        dpg.add_slider_int(
            label=self._text("clip_slider"),
            default_value=0,
            min_value=0,
            max_value=8,
            callback=self._make_dpg_value_callback(self._on_clip_changed_dpg),
            tag=self._register_label("slider_clip", "clip_slider"),
        )
        self._attach_tooltip(dpg, "slider_clip", "clip_slider")

    def _build_tune_tab(self, dpg: object) -> None:
        dpg.add_combo(
            label=self._text("joint_selector"),
            items=self._joint_selector_items,
            default_value=self._joint_selector_items[0],
            width=300,
            tag=self._register_label(self._edit_joint_combo_tag, "joint_selector"),
            callback=self._make_dpg_value_callback(self._on_joint_selected_dpg),
        )
        dpg.add_combo(
            label=self._text("ik_reference_frame"),
            items=self._reference_frame_items(),
            default_value=self._reference_frame_label(self._tune_state.reference_frame),
            width=220,
            tag=self._register_label(self._ik_reference_frame_tag, "ik_reference_frame"),
            callback=self._make_dpg_value_callback(self._on_tune_reference_frame_changed),
        )
        self._attach_tooltip(dpg, self._ik_reference_frame_tag, "ik_reference_frame")
        dpg.add_text(self._text("ik_current_pose"), tag=self._register_text("txt_ik_current_pose", "ik_current_pose"))
        dpg.add_text(
            self._text("ik_current_pose_line_placeholder"),
            tag=self._register_text(self._ik_current_pose_line_tag, "ik_current_pose_line_placeholder"),
            wrap=700,
        )
        dpg.add_text(
            self._text("ik_dual_state_hint"),
            tag=self._register_text("txt_ik_dual_state_hint", "ik_dual_state_hint"),
            wrap=700,
            color=(170, 200, 220),
        )
        dpg.add_text(self._text("ik_target_pose"), tag=self._register_text("txt_ik_target_pose", "ik_target_pose"))
        with dpg.group(horizontal=True):
            dpg.add_button(
                label=self._text("mark_keyframe"),
                width=140,
                callback=self._make_dpg_callback(self._on_mark_keyframe_button),
                tag=self._register_label("btn_mark", "mark_keyframe"),
            )
            self._attach_tooltip(dpg, "btn_mark", "mark_keyframe")
            dpg.add_button(
                label=self._text("toggle_ghost"),
                width=110,
                callback=self._make_dpg_callback(self._on_ghost_toggle),
                tag=self._register_label("btn_ghost", "toggle_ghost"),
            )
            self._attach_tooltip(dpg, "btn_ghost", "toggle_ghost")
            dpg.add_button(
                label=self._text("toggle_edit"),
                width=110,
                callback=self._make_dpg_callback(self._on_edit_toggle),
                tag=self._register_label("btn_edit", "toggle_edit"),
            )
            self._attach_tooltip(dpg, "btn_edit", "toggle_edit")
            dpg.add_button(
                label=self._text("save_motion"),
                width=140,
                callback=self._make_dpg_callback(self._on_save_button),
                tag=self._register_label("btn_save", "save_motion"),
            )
            self._attach_tooltip(dpg, "btn_save", "save_motion")
        with dpg.group(horizontal=True):
            dpg.add_button(
                label=self._text("prev_marked_frame"),
                width=130,
                callback=self._make_dpg_callback(self._on_prev_marked_frame_button),
                tag=self._register_label("btn_prev_marked_frame", "prev_marked_frame"),
            )
            self._attach_tooltip(dpg, "btn_prev_marked_frame", "prev_marked_frame")
            dpg.add_button(
                label=self._text("next_marked_frame"),
                width=130,
                callback=self._make_dpg_callback(self._on_next_marked_frame_button),
                tag=self._register_label("btn_next_marked_frame", "next_marked_frame"),
            )
            self._attach_tooltip(dpg, "btn_next_marked_frame", "next_marked_frame")
            dpg.add_combo(
                label=self._text("mark_history_label"),
                items=[self._text("mark_history_none")],
                default_value=self._text("mark_history_none"),
                width=220,
                tag=self._register_label(self._mark_combo_tag, "mark_history_label"),
            )
            dpg.add_button(
                label=self._text("jump_marked_frame"),
                width=120,
                callback=self._make_dpg_callback(self._on_jump_marked_frame_button),
                tag=self._register_label("btn_jump_marked_frame", "jump_marked_frame"),
            )
            self._attach_tooltip(dpg, "btn_jump_marked_frame", "jump_marked_frame")
        dpg.add_text(
            f"{self._text('mark_history_label')}: {self._text('mark_history_none')}",
            tag=self._mark_history_text_tag,
            wrap=720,
        )

        dpg.add_text(self._text("section_editor"), tag=self._register_text("txt_editor", "section_editor"))
        with dpg.group(horizontal=True):
            dpg.add_button(
                label=self._text("undo_edit"),
                width=130,
                callback=self._make_dpg_callback(self._on_undo_edit_button),
                tag=self._register_label("btn_undo_edit", "undo_edit"),
            )
            self._attach_tooltip(dpg, "btn_undo_edit", "undo_edit")
            dpg.add_button(
                label=self._text("redo_edit"),
                width=130,
                callback=self._make_dpg_callback(self._on_redo_edit_button),
                tag=self._register_label("btn_redo_edit", "redo_edit"),
            )
            self._attach_tooltip(dpg, "btn_redo_edit", "redo_edit")
        dpg.add_slider_float(
            label=self._text("joint_delta"),
            default_value=0.05,
            min_value=-0.5,
            max_value=0.5,
            tag=self._register_label(self._edit_joint_delta_tag, "joint_delta"),
        )
        dpg.add_input_int(
            label=self._text("propagate_radius"),
            default_value=0,
            min_value=0,
            min_clamped=True,
            max_value=300,
            max_clamped=True,
            width=180,
            tag=self._register_label(self._edit_propagate_tag, "propagate_radius"),
        )
        dpg.add_button(
            label=self._text("apply_dof_delta"),
            width=220,
            callback=self._make_dpg_callback(self._on_apply_dof_delta_button),
            tag=self._register_label("btn_apply_dof_delta", "apply_dof_delta"),
        )
        self._attach_tooltip(dpg, "btn_apply_dof_delta", "apply_dof_delta")
        with dpg.group(horizontal=True):
            dpg.add_slider_float(
                label=self._text("ik_dx"),
                default_value=0.0,
                min_value=-0.5,
                max_value=0.5,
                width=180,
                tag=self._register_label(self._ik_dx_tag, "ik_dx"),
            )
            self._attach_tooltip(dpg, self._ik_dx_tag, "ik_dx")
            dpg.add_slider_float(
                label=self._text("ik_dy"),
                default_value=0.0,
                min_value=-0.5,
                max_value=0.5,
                width=180,
                tag=self._register_label(self._ik_dy_tag, "ik_dy"),
            )
            self._attach_tooltip(dpg, self._ik_dy_tag, "ik_dy")
            dpg.add_slider_float(
                label=self._text("ik_dz"),
                default_value=0.0,
                min_value=-0.5,
                max_value=0.5,
                width=180,
                tag=self._register_label(self._ik_dz_tag, "ik_dz"),
            )
            self._attach_tooltip(dpg, self._ik_dz_tag, "ik_dz")
        dpg.add_button(
            label=self._text("apply_ik_target"),
            width=220,
            callback=self._make_dpg_callback(self._on_apply_ik_button),
            tag=self._register_label("btn_apply_ik_target", "apply_ik_target"),
        )
        self._attach_tooltip(dpg, "btn_apply_ik_target", "apply_ik_target")
        dpg.add_text(self._timeline_placeholder_line(), tag=self._timeline_line_tag, wrap=720)

        with dpg.group(horizontal=True):
            dpg.add_combo(
                label=self._text("ik_pos_unit"),
                items=["m", "cm", "mm"],
                default_value=self._tune_state.position_unit.value,
                width=120,
                tag=self._register_label(self._ik_pos_unit_tag, "ik_pos_unit"),
                callback=self._make_dpg_value_callback(self._on_tune_position_unit_changed),
            )
            dpg.add_combo(
                label=self._text("ik_angle_unit"),
                items=["deg", "rad"],
                default_value=self._tune_state.angle_unit.value,
                width=120,
                tag=self._register_label(self._ik_angle_unit_tag, "ik_angle_unit"),
                callback=self._make_dpg_value_callback(self._on_tune_angle_unit_changed),
            )
        with dpg.group(horizontal=True):
            dpg.add_input_float(
                label=self._text("ik_pos_x"),
                default_value=0.0,
                width=170,
                tag=self._register_label(self._ik_pos_x_tag, "ik_pos_x"),
            )
            dpg.add_input_float(
                label=self._text("ik_pos_y"),
                default_value=0.0,
                width=170,
                tag=self._register_label(self._ik_pos_y_tag, "ik_pos_y"),
            )
            dpg.add_input_float(
                label=self._text("ik_pos_z"),
                default_value=0.0,
                width=170,
                tag=self._register_label(self._ik_pos_z_tag, "ik_pos_z"),
            )
        with dpg.group(horizontal=True):
            dpg.add_input_float(
                label=self._text("ik_roll"),
                default_value=0.0,
                width=170,
                tag=self._register_label(self._ik_rot_roll_tag, "ik_roll"),
            )
            dpg.add_input_float(
                label=self._text("ik_pitch"),
                default_value=0.0,
                width=170,
                tag=self._register_label(self._ik_rot_pitch_tag, "ik_pitch"),
            )
            dpg.add_input_float(
                label=self._text("ik_yaw"),
                default_value=0.0,
                width=170,
                tag=self._register_label(self._ik_rot_yaw_tag, "ik_yaw"),
            )
        with dpg.group(horizontal=True):
            dpg.add_input_float(
                label=self._text("ik_step_position"),
                default_value=self._tune_state.display_step_position(),
                width=170,
                tag=self._register_label(self._ik_step_pos_tag, "ik_step_position"),
            )
            dpg.add_input_float(
                label=self._text("ik_step_angle"),
                default_value=self._tune_state.display_step_angle(),
                width=170,
                tag=self._register_label(self._ik_step_angle_tag, "ik_step_angle"),
            )
        dpg.add_text(self._text("tune_position_nudge"), tag=self._register_text("txt_tune_pos_nudge", "tune_position_nudge"))
        with dpg.group(horizontal=True):
            dpg.add_button(label="-X", callback=self._make_dpg_callback(lambda: self._on_tune_nudge_position(0, -1)))
            dpg.add_button(label="+X", callback=self._make_dpg_callback(lambda: self._on_tune_nudge_position(0, 1)))
            dpg.add_button(label="-Y", callback=self._make_dpg_callback(lambda: self._on_tune_nudge_position(1, -1)))
            dpg.add_button(label="+Y", callback=self._make_dpg_callback(lambda: self._on_tune_nudge_position(1, 1)))
            dpg.add_button(label="-Z", callback=self._make_dpg_callback(lambda: self._on_tune_nudge_position(2, -1)))
            dpg.add_button(label="+Z", callback=self._make_dpg_callback(lambda: self._on_tune_nudge_position(2, 1)))
        dpg.add_text(
            self._text("tune_rotation_nudge"),
            tag=self._register_text("txt_tune_rot_nudge", "tune_rotation_nudge"),
        )
        with dpg.group(horizontal=True):
            dpg.add_button(label="-R", callback=self._make_dpg_callback(lambda: self._on_tune_nudge_rotation(0, -1)))
            dpg.add_button(label="+R", callback=self._make_dpg_callback(lambda: self._on_tune_nudge_rotation(0, 1)))
            dpg.add_button(label="-P", callback=self._make_dpg_callback(lambda: self._on_tune_nudge_rotation(1, -1)))
            dpg.add_button(label="+P", callback=self._make_dpg_callback(lambda: self._on_tune_nudge_rotation(1, 1)))
            dpg.add_button(label="-Y", callback=self._make_dpg_callback(lambda: self._on_tune_nudge_rotation(2, -1)))
            dpg.add_button(label="+Y", callback=self._make_dpg_callback(lambda: self._on_tune_nudge_rotation(2, 1)))
        dpg.add_button(
            label=self._text("ik_apply_full_pose"),
            callback=self._make_dpg_callback(self._on_apply_ik_pose_button),
            tag=self._register_label("btn_apply_ik_pose_full", "ik_apply_full_pose"),
        )

    def _build_metrics_tab(self, dpg: object) -> None:
        dpg.add_input_text(
            label=self._text("metrics_motion"),
            default_value=self._default_motion_path,
            width=690,
            tag=self._register_label(self._metrics_motion_tag, "metrics_motion"),
        )
        dpg.add_input_text(
            label=self._text("metrics_output"),
            default_value="report.json",
            width=690,
            tag=self._register_label(self._metrics_output_tag, "metrics_output"),
        )
        dpg.add_button(
            label=self._text("metrics_run"),
            callback=self._make_dpg_callback(self._run_metrics_tool),
            tag=self._register_label("btn_run_metrics", "metrics_run"),
        )

    def _build_audit_tab(self, dpg: object) -> None:
        dpg.add_input_text(
            label=self._text("audit_motion"),
            default_value=self._default_motion_path,
            width=690,
            tag=self._register_label(self._audit_motion_tag, "audit_motion"),
        )
        dpg.add_input_text(
            label=self._text("audit_robot"),
            default_value=self._default_robot_path,
            width=690,
            tag=self._register_label(self._audit_robot_tag, "audit_robot"),
        )
        dpg.add_input_text(
            label=self._text("audit_output"),
            default_value="",
            width=690,
            tag=self._register_label(self._audit_output_tag, "audit_output"),
        )
        dpg.add_button(
            label=self._text("audit_run"),
            callback=self._make_dpg_callback(self._run_audit_tool),
            tag=self._register_label("btn_run_audit", "audit_run"),
        )

    def _build_convert_tab(self, dpg: object) -> None:
        dpg.add_input_text(
            label=self._text("convert_input"),
            default_value=self._default_robot_path,
            width=690,
            tag=self._register_label(self._convert_input_tag, "convert_input"),
        )
        dpg.add_input_text(
            label=self._text("convert_output"),
            default_value="robot.xml",
            width=690,
            tag=self._register_label(self._convert_output_tag, "convert_output"),
        )
        dpg.add_button(
            label=self._text("convert_run"),
            callback=self._make_dpg_callback(self._run_convert_tool),
            tag=self._register_label("btn_run_convert", "convert_run"),
        )

    def _build_export_tab(self, dpg: object) -> None:
        dpg.add_input_text(
            label=self._text("export_motion"),
            default_value=self._default_motion_path,
            width=690,
            tag=self._register_label(self._export_motion_tag, "export_motion"),
        )
        dpg.add_input_text(
            label=self._text("export_robot"),
            default_value=self._default_robot_path,
            width=690,
            tag=self._register_label(self._export_robot_tag, "export_robot"),
        )
        dpg.add_input_text(
            label=self._text("export_output"),
            default_value="export.gif",
            width=690,
            tag=self._register_label(self._export_output_tag, "export_output"),
        )
        dpg.add_input_text(
            label=self._text("export_fps"),
            default_value="30.0",
            width=200,
            tag=self._register_label(self._export_fps_tag, "export_fps"),
        )
        dpg.add_button(
            label=self._text("export_run"),
            callback=self._make_dpg_callback(self._run_export_tool),
            tag=self._register_label("btn_run_export", "export_run"),
        )

    def _build_audio_tab(self, dpg: object) -> None:
        dpg.add_text(self._text("audio_placeholder"), tag=self._register_text("txt_audio_placeholder", "audio_placeholder"))
        with dpg.group(horizontal=True):
            dpg.add_button(
                label=self._text("audio_play"),
                callback=self._make_dpg_callback(lambda: self._run_audio_tool("play")),
                tag=self._register_label("btn_audio_play", "audio_play"),
            )
            dpg.add_button(
                label=self._text("audio_pause"),
                callback=self._make_dpg_callback(lambda: self._run_audio_tool("pause")),
                tag=self._register_label("btn_audio_pause", "audio_pause"),
            )
            dpg.add_button(
                label=self._text("audio_stop"),
                callback=self._make_dpg_callback(lambda: self._run_audio_tool("stop")),
                tag=self._register_label("btn_audio_stop", "audio_stop"),
            )

    def _build_tool_output_panel(self, dpg: object) -> None:
        dpg.add_separator()
        dpg.add_text(self._text("tool_output"), tag=self._register_text("txt_tool_output", "tool_output"))
        dpg.add_input_text(
            multiline=True,
            readonly=True,
            width=730,
            height=120,
            tag=self._tool_result_tag,
            default_value=self._text("tool_ready"),
        )

    def _run_blocking(self) -> None:
        try:
            import dearpygui.dearpygui as dpg  # type: ignore[import]
        except ImportError:
            return

        self._dpg = dpg
        context_created = False
        try:
            dpg.create_context()
            context_created = True
            self._install_fonts(dpg)
            dpg.bind_theme(self._create_theme(dpg))
            monitor_card_theme = self._create_monitor_card_theme(dpg)

            with dpg.window(
                label=self._text("window_title"),
                width=760,
                height=640,
                tag=self._window_tag,
            ):
                with dpg.group(horizontal=True):
                    dpg.add_text(self._text("hero_title"), tag=self._hero_title_tag)
                    dpg.add_spacer(width=60)
                    dpg.add_text(self._text("language_label"), tag=self._language_text_tag)
                    dpg.add_combo(
                        items=list(self._LANGUAGE_OPTIONS.keys()),
                        default_value="English",
                        width=120,
                        tag=self._language_combo_tag,
                        callback=self._make_dpg_value_callback(self._on_language_changed),
                    )
                dpg.add_text(self._text("hero_subtitle"), tag=self._hero_subtitle_tag)
                with dpg.group(horizontal=True):
                    dpg.add_text(
                        self._text("status_label"),
                        tag=self._register_text("txt_status_label", "status_label"),
                    )
                    dpg.add_text(self._text("status_idle"), tag=self._status_text_tag)
                with dpg.child_window(
                    height=124,
                    border=True,
                    tag=self._monitor_card_tag,
                ):
                    dpg.add_text(self._text("monitor_label"), tag=self._monitor_title_tag, color=(95, 200, 255))
                    dpg.add_text(self._text("monitor_line_1_placeholder"), tag=self._monitor_line_1_tag, wrap=650)
                    dpg.add_text(self._text("monitor_line_2_placeholder"), tag=self._monitor_line_2_tag, wrap=650)
                    dpg.add_text(self._text("monitor_line_3_placeholder"), tag=self._monitor_line_3_tag, wrap=650)
                dpg.add_separator()

                with dpg.tab_bar(tag=self._workbench_tabbar_tag):
                    for tab_id in TAB_IDS:
                        with dpg.tab(label=self._tab_label(tab_id), tag=f"rmp_tab_{tab_id}"):
                            if tab_id == "play":
                                self._build_play_tab(dpg)
                            elif tab_id == "tune":
                                self._build_tune_tab(dpg)
                            elif tab_id == "metrics":
                                self._build_metrics_tab(dpg)
                            elif tab_id == "audit":
                                self._build_audit_tab(dpg)
                            elif tab_id == "convert":
                                self._build_convert_tab(dpg)
                            elif tab_id == "export":
                                self._build_export_tab(dpg)
                            else:
                                self._build_audio_tab(dpg)
                self._build_tool_output_panel(dpg)

                dpg.bind_item_theme(self._monitor_card_tag, monitor_card_theme)

            dpg.create_viewport(title=self._text("window_title"), width=780, height=680)
            dpg.setup_dearpygui()
            dpg.set_viewport_resize_callback(
                self._make_dpg_value_callback(self._on_viewport_resized_dpg)
            )
            self._refresh_translations()
            self._sync_tune_inputs_from_state()
            self._apply_monitor_card_layout()
            dpg.show_viewport()
            while dpg.is_dearpygui_running():
                self._refresh_monitor_lines()
                dpg.render_dearpygui_frame()
                self._maybe_export_visual_qa_artifacts()
        except Exception as exc:  # noqa: BLE001
            logger.exception("DearPyGui panel loop crashed: %s", exc)
        finally:
            if context_created:
                dpg.destroy_context()
            self._dpg = None

    def launch_non_blocking(self) -> None:
        """Start panel loop in a background daemon thread."""
        if self._worker is not None and self._worker.is_alive():
            return
        worker = threading.Thread(target=self._run_blocking, daemon=True)
        worker.start()
        self._worker = worker

    def run_blocking(self) -> None:
        """Run panel loop in foreground thread until window is closed."""
        self._run_blocking()
