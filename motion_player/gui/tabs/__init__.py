"""Tab registry and shared constants for GUI workbench."""

from __future__ import annotations

from motion_player.gui.tabs.layout_spec import TAB_CONTROL_KEYS

TAB_IDS: tuple[str, ...] = (
    "play",
    "tune",
    "metrics",
    "audit",
    "convert",
    "export",
    "audio",
)

__all__ = ["TAB_IDS", "TAB_CONTROL_KEYS"]
