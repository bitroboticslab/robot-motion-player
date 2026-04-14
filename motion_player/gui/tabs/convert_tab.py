"""Convert tab config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ConvertTabConfig:
    fields: tuple[str, ...] = ("input_path", "output_path", "run")


def build_convert_tab_config() -> ConvertTabConfig:
    return ConvertTabConfig()
