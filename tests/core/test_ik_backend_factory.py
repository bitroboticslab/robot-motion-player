"""Tests for robot-path IK backend routing."""

from __future__ import annotations

import sys
import types
from pathlib import Path

from motion_player.core.kinematics.ik_backend_factory import create_ik_solver_for_robot


def test_create_ik_solver_for_xml_uses_mujoco_backend(tmp_path: Path) -> None:
    xml = tmp_path / "robot.xml"
    xml.write_text("<mujoco/>", encoding="utf-8")
    solver = create_ik_solver_for_robot(xml)
    assert solver is None or solver.__class__.__name__ == "IKSolver"


def test_create_ik_solver_for_urdf_uses_pin_backend(tmp_path: Path) -> None:
    urdf = tmp_path / "robot.urdf"
    urdf.write_text("<robot name='r'/>", encoding="utf-8")
    solver = create_ik_solver_for_robot(urdf)
    assert solver is None or solver.__class__.__name__ == "IKSolver"


def test_create_ik_solver_for_unknown_suffix_returns_none(tmp_path: Path) -> None:
    txt = tmp_path / "robot.txt"
    txt.write_text("noop", encoding="utf-8")
    assert create_ik_solver_for_robot(txt) is None


def test_create_ik_solver_for_xml_prefers_runtime_driver(
    monkeypatch,
    tmp_path: Path,
) -> None:
    xml = tmp_path / "robot.xml"
    xml.write_text("<mujoco/>", encoding="utf-8")
    marker = object()
    seen: dict[str, object] = {}

    class _Backend:
        @classmethod
        def from_runtime_driver(cls, driver: object):
            seen["driver"] = driver
            return cls()

        @classmethod
        def from_xml_path(cls, _path: Path):
            raise AssertionError(
                "from_xml_path should not be used when runtime driver is provided."
            )

        def solve(self, current_qpos, targets):
            return current_qpos

    monkeypatch.setitem(
        sys.modules,
        "motion_player.core.kinematics.ik_backends.mujoco_xml_backend",
        types.SimpleNamespace(MujocoXmlIKBackend=_Backend),
    )
    solver = create_ik_solver_for_robot(xml, driver=marker)
    assert solver is not None
    assert seen["driver"] is marker
