"""Audit tab config."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class AuditTabConfig:
    fields: tuple[str, ...] = ("motion_path", "robot_path", "output_path", "run")


def build_audit_tab_config() -> AuditTabConfig:
    return AuditTabConfig()
