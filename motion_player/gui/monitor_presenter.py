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

"""Presentation helpers for GUI status monitor rendering."""

from __future__ import annotations

from dataclasses import dataclass

from motion_player.core.ui.state_monitor import PlaybackSnapshot


@dataclass(frozen=True)
class MonitorViewModel:
    """Formatted monitor text lines for the control deck card."""

    headline: str
    subline: str
    flags_line: str


def _on_off(value: bool) -> str:
    return "ON" if value else "OFF"


def build_monitor_view_model(snap: PlaybackSnapshot) -> MonitorViewModel:
    """Build a stable monitor view model from a playback snapshot."""
    headline = (
        f"Clip {snap.clip + 1}/{snap.total_clips}  Frame {snap.frame + 1}/{snap.total_frames}"
    )
    subline = f"{'PLAY' if snap.playing else 'PAUSE'}  {snap.speed:.1f}x"
    flags_line = (
        f"LOOP {_on_off(snap.loop)}  "
        f"PING {_on_off(snap.pingpong)}  "
        f"EDIT {_on_off(snap.edit_mode)}  "
        f"HUD {_on_off(snap.show_hud)}  "
        f"GHOST {_on_off(snap.show_ghost)}  "
        f"KEY {snap.keyframe_count}"
    )
    return MonitorViewModel(headline=headline, subline=subline, flags_line=flags_line)
