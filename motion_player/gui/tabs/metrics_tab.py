"""Metrics tab config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class MetricsTabConfig:
    fields: tuple[str, ...] = ("motion_path", "output_path", "run")


def build_metrics_tab_config() -> MetricsTabConfig:
    return MetricsTabConfig()
