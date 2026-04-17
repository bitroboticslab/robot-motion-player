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

"""Queue-based IPC adapters between isolated GUI panel and viewer."""

from __future__ import annotations

import queue
from dataclasses import asdict
from typing import Any, Protocol

from motion_player.core.ui import PlayerCommand
from motion_player.core.ui.command_queue import QueuedCommand
from motion_player.core.ui.state_monitor import PlaybackSnapshot


class _QueueLike(Protocol):
    """Minimal queue protocol shared by queue.Queue and multiprocessing.Queue."""

    def put_nowait(self, item: object) -> None: ...

    def get_nowait(self) -> object: ...


def _put_drop_oldest(q: _QueueLike, item: object) -> None:
    """Put item in queue, dropping oldest entries when queue is full."""
    try:
        q.put_nowait(item)
        return
    except queue.Full:
        pass

    while True:
        try:
            q.get_nowait()
        except queue.Empty:
            break
        try:
            q.put_nowait(item)
            return
        except queue.Full:
            continue

    try:
        q.put_nowait(item)
    except queue.Full:
        # If another producer races us, dropping this message is acceptable.
        return


def _decode_command(message: object) -> QueuedCommand | None:
    if not isinstance(message, dict):
        return None
    raw_command = message.get("command")
    if not isinstance(raw_command, str):
        return None
    try:
        command = PlayerCommand(raw_command)
    except ValueError:
        return None
    return QueuedCommand(command=command, payload=message.get("payload"))


def _decode_snapshot(message: object) -> PlaybackSnapshot | None:
    if not isinstance(message, dict):
        return None
    payload = message.get("snapshot")
    if not isinstance(payload, dict):
        return None

    data: dict[str, Any] = dict(payload)
    for key in (
        "marked_frames",
        "mark_history",
        "joint_names",
        "selected_joint_pos_m",
        "selected_joint_quat_wxyz",
    ):
        value = data.get(key)
        if isinstance(value, list):
            data[key] = tuple(value)

    try:
        return PlaybackSnapshot(**data)
    except TypeError:
        return None


class PanelCommandSender:
    """Queue-compatible sender used by GuiController in the panel process."""

    def __init__(self, ipc_queue: _QueueLike) -> None:
        self._queue = ipc_queue

    def push(self, command: PlayerCommand, payload: object | None = None) -> None:
        _put_drop_oldest(
            self._queue,
            {
                "command": command.value,
                "payload": payload,
            },
        )


class PanelCommandReceiver:
    """Viewer-facing command queue adapter with CommandQueue-like API."""

    def __init__(self, ipc_queue: _QueueLike) -> None:
        self._queue = ipc_queue

    def drain(self) -> list[QueuedCommand]:
        drained: list[QueuedCommand] = []
        while True:
            try:
                raw = self._queue.get_nowait()
            except queue.Empty:
                return drained
            decoded = _decode_command(raw)
            if decoded is not None:
                drained.append(decoded)


class PanelMonitorPublisher:
    """Viewer-side snapshot publisher that coalesces to latest state."""

    def __init__(self, ipc_queue: _QueueLike) -> None:
        self._queue = ipc_queue

    def publish(self, snapshot: PlaybackSnapshot) -> None:
        _put_drop_oldest(
            self._queue,
            {
                "snapshot": asdict(snapshot),
            },
        )


class PanelMonitorSubscriber:
    """Panel-side monitor bus adapter with StateMonitorBus-like API."""

    def __init__(self, ipc_queue: _QueueLike) -> None:
        self._queue = ipc_queue
        self._latest: PlaybackSnapshot | None = None

    def latest(self) -> PlaybackSnapshot | None:
        while True:
            try:
                raw = self._queue.get_nowait()
            except queue.Empty:
                return self._latest
            decoded = _decode_snapshot(raw)
            if decoded is not None:
                self._latest = decoded
