"""Export tab config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class ExportTabConfig:
    fields: tuple[str, ...] = ("motion_path", "robot_path", "output_path", "fps", "run")


def build_export_tab_config() -> ExportTabConfig:
    return ExportTabConfig()
