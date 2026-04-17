"""Layout policy for the bottom status dock in the DearPyGui panel."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class StatusDockLayout:
    """Computed status-dock dimensions and section sizing."""

    stacked: bool
    dock_height: int
    row1_height: int
    row2_height: int
    monitor_width: int
    output_width: int
    progress_width: int


def build_status_dock_layout(window_width: int) -> StatusDockLayout:
    """Compute a stable bottom-dock layout from the viewport width."""
    clamped_width = max(520, int(window_width))
    stacked = clamped_width < 760

    if stacked:
        content_width = max(460, clamped_width - 40)
        return StatusDockLayout(
            stacked=True,
            dock_height=394,
            row1_height=112,
            row2_height=64,
            monitor_width=content_width,
            output_width=content_width,
            progress_width=content_width,
        )

    available = max(0, clamped_width - 48)
    monitor_width = max(0, int(available * 0.42))
    output_width = max(0, available - monitor_width)
    progress_width = available

    return StatusDockLayout(
        stacked=False,
        dock_height=312,
        row1_height=146,
        row2_height=81,
        monitor_width=monitor_width,
        output_width=output_width,
        progress_width=progress_width,
    )
