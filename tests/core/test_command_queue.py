"""Tests for thread-safe UI command queue."""

from __future__ import annotations

from motion_player.core.ui import PlayerCommand
from motion_player.core.ui.command_queue import CommandQueue


def test_queue_push_pop_order() -> None:
    q = CommandQueue()
    q.push(PlayerCommand.PLAY_PAUSE)
    q.push(PlayerCommand.SEEK_FRAME, 10)
    items = q.drain()
    assert [x.command for x in items] == [
        PlayerCommand.PLAY_PAUSE,
        PlayerCommand.SEEK_FRAME,
    ]
    assert items[1].payload == 10


def test_drain_on_empty_queue_returns_empty_list() -> None:
    q = CommandQueue()
    assert q.drain() == []
