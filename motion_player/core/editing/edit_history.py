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

"""EditHistory — undo/redo stack for motion editing operations."""

from __future__ import annotations

from motion_player.core.dataset.motion import StandardMotion


class EditHistory:
    """Undo/redo stack for :class:`~motion_player.core.editing.frame_editor.FrameEditor`.

    Each push stores a *clone* of the current motion state.  Undo restores
    the previous state; redo re-applies it.

    Parameters
    ----------
    max_depth:
        Maximum number of snapshots to retain.  Older snapshots are discarded
        when the stack exceeds this depth.  ``0`` means unlimited.
    """

    def __init__(self, max_depth: int = 50) -> None:
        self.max_depth = max_depth
        self._undo_stack: list[StandardMotion] = []
        self._redo_stack: list[StandardMotion] = []

    def push(self, snapshot: StandardMotion) -> None:
        """Push a clone of the current motion onto the undo stack.

        Clears the redo stack (any redo history is invalidated by new edits).
        """
        self._undo_stack.append(snapshot.clone())
        self._redo_stack.clear()
        if self.max_depth > 0:
            while len(self._undo_stack) > self.max_depth:
                self._undo_stack.pop(0)

    def undo(self, current: StandardMotion | None = None) -> StandardMotion:
        """Pop and return the most recent snapshot from the undo stack.

        Raises
        ------
        IndexError
            If there is nothing to undo.
        """
        if not self._undo_stack:
            raise IndexError("Nothing to undo.")
        snapshot = self._undo_stack.pop()
        if current is None:
            self._redo_stack.append(snapshot)
        else:
            self._redo_stack.append(current.clone())
        return snapshot.clone()

    def redo(self, current: StandardMotion | None = None) -> StandardMotion:
        """Pop and return the most recent snapshot from the redo stack.

        Raises
        ------
        IndexError
            If there is nothing to redo.
        """
        if not self._redo_stack:
            raise IndexError("Nothing to redo.")
        snapshot = self._redo_stack.pop()
        if current is None:
            self._undo_stack.append(snapshot)
        else:
            self._undo_stack.append(current.clone())
        return snapshot.clone()

    def can_undo(self) -> bool:
        """Return ``True`` if an undo operation is available."""
        return bool(self._undo_stack)

    def can_redo(self) -> bool:
        """Return ``True`` if a redo operation is available."""
        return bool(self._redo_stack)

    def clear(self) -> None:
        """Clear both undo and redo stacks."""
        self._undo_stack.clear()
        self._redo_stack.clear()
