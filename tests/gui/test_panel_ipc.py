"""Tests for queue-based panel IPC adapters."""

from __future__ import annotations

import queue

from motion_player.core.ui import PlayerCommand
from motion_player.core.ui.state_monitor import PlaybackSnapshot
from motion_player.gui.panel_ipc import (
    PanelCommandReceiver,
    PanelCommandSender,
    PanelMonitorPublisher,
    PanelMonitorSubscriber,
)


def _snapshot(frame: int) -> PlaybackSnapshot:
    return PlaybackSnapshot(
        frame=frame,
        total_frames=12,
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
    )


def test_panel_command_round_trip_preserves_payload() -> None:
    q: queue.Queue[dict[str, object]] = queue.Queue(maxsize=8)
    sender = PanelCommandSender(q)
    receiver = PanelCommandReceiver(q)

    sender.push(PlayerCommand.APPLY_IK_TARGET, {"target_joint": "hip", "dx": 0.1})
    drained = receiver.drain()

    assert len(drained) == 1
    assert drained[0].command is PlayerCommand.APPLY_IK_TARGET
    assert drained[0].payload == {"target_joint": "hip", "dx": 0.1}


def test_panel_monitor_subscriber_returns_latest_snapshot_after_coalescing() -> None:
    q: queue.Queue[dict[str, object]] = queue.Queue(maxsize=1)
    publisher = PanelMonitorPublisher(q)
    subscriber = PanelMonitorSubscriber(q)

    publisher.publish(_snapshot(frame=1))
    publisher.publish(_snapshot(frame=9))

    latest = subscriber.latest()
    assert latest is not None
    assert latest.frame == 9


def test_panel_command_sender_drops_oldest_when_queue_is_full() -> None:
    q: queue.Queue[dict[str, object]] = queue.Queue(maxsize=1)
    sender = PanelCommandSender(q)
    receiver = PanelCommandReceiver(q)

    sender.push(PlayerCommand.PLAY_PAUSE)
    sender.push(PlayerCommand.RESET)
    drained = receiver.drain()

    assert [item.command for item in drained] == [PlayerCommand.RESET]
