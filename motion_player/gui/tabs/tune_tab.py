"""Tune tab config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class TuneTabConfig:
    fields: tuple[str, ...]


def build_tune_tab_config(language: str) -> TuneTabConfig:
    del language
    return TuneTabConfig(
        fields=(
            "target_joint",
            "position_x",
            "position_y",
            "position_z",
            "position_unit",
            "rotation_roll",
            "rotation_pitch",
            "rotation_yaw",
            "angle_unit",
            "step_position",
            "step_angle",
        )
    )
