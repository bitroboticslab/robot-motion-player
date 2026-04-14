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

"""Layout policy for monitor card geometry in DearPyGui panel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MonitorCardLayout:
    """Computed monitor-card dimensions and wrapping strategy."""

    card_height: int
    line_wrap_px: int
    needs_compact_spacing: bool


def build_monitor_card_layout(window_width: int, language: str) -> MonitorCardLayout:
    """Compute stable monitor-card layout from viewport width and language."""
    clamped_width = max(420, int(window_width))
    compact = clamped_width < 620

    line_wrap_px = max(260, clamped_width - 56)

    base_height = 124
    compact_extra = 24 if compact else 0
    zh_extra = 8 if language == "zh" else 0

    return MonitorCardLayout(
        card_height=base_height + compact_extra + zh_extra,
        line_wrap_px=line_wrap_px,
        needs_compact_spacing=compact,
    )
