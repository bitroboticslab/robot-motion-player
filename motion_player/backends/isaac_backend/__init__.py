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

"""Optional Isaac / NV HumanoidViewMotion backend.

This backend allows the same :class:`~motion_player.core.dataset.motion.StandardMotion`
to be replayed via the ASE/CALM ``HumanoidViewMotion`` task inside IsaacGym or
IsaacLab.

Installation
------------
This backend requires an Isaac SDK installation, which is **not** included in
the default robot-motion-player dependencies.  Enable it with::

    pip install robot-motion-player[isaac]

Status: **placeholder / not yet implemented**.  The interface is defined here
so that downstream users can register their own Isaac adapter without waiting
for an official implementation.
"""

from __future__ import annotations

import warnings

from motion_player.core.dataset.motion import StandardMotion


class IsaacBackend:
    """Placeholder Isaac / NV HumanoidViewMotion backend.

    To implement a custom Isaac backend, subclass this class and override
    :meth:`apply_frame`.

    Parameters
    ----------
    task_class:
        The Isaac ``HumanoidViewMotion`` task class (or compatible).  Pass
        ``None`` to defer initialisation.
    """

    def __init__(self, task_class: object = None) -> None:
        warnings.warn(
            "IsaacBackend is a placeholder and not yet implemented. "
            "Subclass it and override apply_frame() to add Isaac support.",
            stacklevel=2,
        )
        self._task_class = task_class
        self._motion: StandardMotion | None = None

    def bind_motion(self, motion: StandardMotion) -> None:
        """Bind a motion clip."""
        self._motion = motion

    def reset(self) -> None:
        """Reset backend state for a new playback sequence."""
        return None

    def close(self) -> None:
        """Release backend resources (placeholder no-op in v0.1)."""
        return None

    @staticmethod
    def is_available() -> bool:
        """Return whether Isaac runtime packages are importable."""
        try:
            import isaacgym  # type: ignore[import]  # noqa: F401

            return True
        except ImportError:
            pass
        try:
            import isaaclab  # type: ignore[import]  # noqa: F401

            return True
        except ImportError:
            return False

    def apply_frame(self, frame_idx: int) -> None:
        """Apply a single frame.  Override in subclass."""
        if self._motion is None:
            raise RuntimeError("No motion bound; call bind_motion() first.")
        if not isinstance(frame_idx, int):
            raise TypeError(f"frame_idx must be int, got {type(frame_idx).__name__}.")
        if frame_idx < 0 or frame_idx >= self._motion.num_frames:
            raise IndexError(
                f"Frame {frame_idx} out of range [0, {self._motion.num_frames})."
            )
        raise NotImplementedError(
            "IsaacBackend.apply_frame is not implemented. "
            "Subclass IsaacBackend and implement this method."
        )
