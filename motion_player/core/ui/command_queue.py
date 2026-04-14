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

"""Thread-safe queue for external UI commands."""

from __future__ import annotations

import queue
from dataclasses import dataclass

from motion_player.core.ui import PlayerCommand


@dataclass(frozen=True)
class QueuedCommand:
    """A command and optional payload pending dispatch."""

    command: PlayerCommand
    payload: object | None = None


class CommandQueue:
    """Simple thread-safe FIFO queue used between GUI and viewer loop."""

    def __init__(self) -> None:
        self._queue: queue.Queue[QueuedCommand] = queue.Queue()

    def push(self, command: PlayerCommand, payload: object | None = None) -> None:
        """Push a command into queue."""
        self._queue.put(QueuedCommand(command=command, payload=payload))

    def drain(self) -> list[QueuedCommand]:
        """Drain all currently queued commands in FIFO order."""
        drained: list[QueuedCommand] = []
        while True:
            try:
                drained.append(self._queue.get_nowait())
            except queue.Empty:
                return drained
