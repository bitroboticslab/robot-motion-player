"""Play tab config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlayTabConfig:
    fields: tuple[str, ...] = ("transport", "navigation", "modes", "speed", "timeline")


def build_play_tab_config() -> PlayTabConfig:
    return PlayTabConfig()
