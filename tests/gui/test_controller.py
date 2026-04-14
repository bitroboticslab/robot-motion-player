"""Tests for framework-agnostic GUI controller callbacks."""

from __future__ import annotations

import pytest

from motion_player.core.ui import PlayerCommand
from motion_player.core.ui.command_queue import CommandQueue
from motion_player.gui.controller import GuiController


@pytest.mark.parametrize(
    ("method_name", "expected_command"),
    [
        ("on_play_pause", PlayerCommand.PLAY_PAUSE),
        ("on_reset", PlayerCommand.RESET),
        ("on_prev_frame", PlayerCommand.STEP_BWD_1),
        ("on_next_frame", PlayerCommand.STEP_FWD_1),
        ("on_prev_10", PlayerCommand.STEP_BWD_10),
        ("on_next_10", PlayerCommand.STEP_FWD_10),
        ("on_prev_100", PlayerCommand.STEP_BWD_100),
        ("on_next_100", PlayerCommand.STEP_FWD_100),
        ("on_toggle_loop", PlayerCommand.TOGGLE_LOOP),
        ("on_toggle_pingpong", PlayerCommand.TOGGLE_PINGPONG),
        ("on_mark_keyframe", PlayerCommand.MARK_KEYFRAME),
        ("on_prev_marked_frame", PlayerCommand.PREV_MARKED_FRAME),
        ("on_next_marked_frame", PlayerCommand.NEXT_MARKED_FRAME),
        ("on_toggle_ghost", PlayerCommand.TOGGLE_GHOST),
        ("on_toggle_edit", PlayerCommand.TOGGLE_EDIT),
        ("on_save_motion", PlayerCommand.SAVE_MOTION),
        ("on_toggle_hud", PlayerCommand.TOGGLE_HUD),
        ("on_speed_up", PlayerCommand.SPEED_UP),
        ("on_speed_down", PlayerCommand.SPEED_DOWN),
        ("on_exit", PlayerCommand.EXIT),
    ],
)
def test_button_callbacks_enqueue_expected_commands(
    method_name: str,
    expected_command: PlayerCommand,
) -> None:
    q = CommandQueue()
    c = GuiController(q)
    getattr(c, method_name)()
    drained = q.drain()
    assert drained[0].command is expected_command


def test_speed_slider_enqueues_set_speed() -> None:
    q = CommandQueue()
    c = GuiController(q)
    c.on_speed_changed(2.5)
    drained = q.drain()
    assert drained[0].command is PlayerCommand.SET_SPEED
    assert drained[0].payload == 2.5


def test_seek_and_clip_callbacks_enqueue_expected_payloads() -> None:
    q = CommandQueue()
    c = GuiController(q)
    c.on_seek_frame(12)
    c.on_jump_marked_frame(21)
    c.on_clip_selected(3)
    drained = q.drain()
    assert drained[0].command is PlayerCommand.SEEK_FRAME
    assert drained[0].payload == 12
    assert drained[1].command is PlayerCommand.SEEK_FRAME
    assert drained[1].payload == 21
    assert drained[2].command is PlayerCommand.CLIP_SELECT
    assert drained[2].payload == 3


def test_editor_callbacks_enqueue_commands() -> None:
    q = CommandQueue()
    c = GuiController(q)
    c.on_edit_dof_delta(joint_idx=2, delta=0.1, propagate_radius=8)
    c.on_undo_edit()
    c.on_redo_edit()
    drained = q.drain()
    assert drained[0].command is PlayerCommand.EDIT_DOF_DELTA
    assert drained[1].command is PlayerCommand.UNDO_EDIT
    assert drained[2].command is PlayerCommand.REDO_EDIT


def test_joint_selector_enqueues_set_edit_joint() -> None:
    q = CommandQueue()
    c = GuiController(q)
    c.on_select_edit_joint(4)
    drained = q.drain()
    assert drained[0].command is PlayerCommand.SET_EDIT_JOINT
    assert drained[0].payload == 4


def test_ik_button_enqueues_apply_ik_target() -> None:
    q = CommandQueue()
    c = GuiController(q)
    c.on_apply_ik_target("joint_1", 0.1, 0.0, -0.1)
    drained = q.drain()
    assert drained[0].command is PlayerCommand.APPLY_IK_TARGET
    assert drained[0].payload["target_joint"] == "joint_1"


def test_ik_pose_callback_enqueues_full_pose_payload() -> None:
    q = CommandQueue()
    c = GuiController(q)
    c.on_apply_ik_pose(
        target_joint="left_foot",
        position=(0.1, 0.0, -0.02),
        rotation=(0.0, 10.0, 0.0),
        position_unit="m",
        angle_unit="deg",
    )
    item = q.drain()[0]
    assert item.command is PlayerCommand.APPLY_IK_TARGET
    assert item.payload["rotation"]["unit"] == "deg"
    assert item.payload["reference_frame"] == "world"
    assert item.payload["propagate_radius"] == 0


def test_apply_ik_pose_keeps_undo_redo_flow_intact() -> None:
    q = CommandQueue()
    c = GuiController(q)
    c.on_apply_ik_pose("left_hand", (0.1, 0.0, 0.0), (0.0, 0.0, 0.0), "m", "deg")
    c.on_undo_edit()
    c.on_redo_edit()
    drained = q.drain()
    assert drained[1].command is PlayerCommand.UNDO_EDIT
    assert drained[2].command is PlayerCommand.REDO_EDIT
