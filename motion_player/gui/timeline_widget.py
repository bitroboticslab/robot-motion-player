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

"""Timeline presentation helpers for GUI display."""

from __future__ import annotations


def format_keyframe_line(total_frames: int, keyframes: list[int], current_frame: int) -> str:
    """Format a compact keyframe/timeline summary line for the control deck."""
    if total_frames <= 0:
        return "K: none | Current [0] / 0 | KeyCount 0 | Span -"
    keys = sorted({int(k) for k in keyframes if 0 <= int(k) < int(total_frames)})
    key_label = ",".join(str(k + 1) for k in keys[:12]) or "none"
    return (
        f"K: {key_label} | Current [{current_frame + 1}] / {total_frames} | "
        f"KeyCount {len(keys)} | Span 1..{total_frames}"
    )
