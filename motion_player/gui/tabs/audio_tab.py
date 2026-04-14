"""Audio tab config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AudioTabConfig:
    fields: tuple[str, ...] = ("status", "play", "pause", "stop")


def build_audio_tab_config() -> AudioTabConfig:
    return AudioTabConfig()
