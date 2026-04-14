# Copyright 2026 Mr-tooth
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""Factory for selecting IK backend by robot model suffix."""

from __future__ import annotations

import logging
from pathlib import Path

from motion_player.core.kinematics.ik_solver import IKSolver

logger = logging.getLogger(__name__)


def create_ik_solver_for_robot(
    robot_path: str | Path,
    driver: object | None = None,
) -> IKSolver | None:
    """Create an IK solver based on robot model suffix (`.xml` or `.urdf`)."""
    path = Path(robot_path)
    suffix = path.suffix.lower()

    if suffix == ".xml":
        try:
            from motion_player.core.kinematics.ik_backends.mujoco_xml_backend import (
                MujocoXmlIKBackend,
            )

            if driver is not None:
                return IKSolver(backend=MujocoXmlIKBackend.from_runtime_driver(driver))
            return IKSolver(backend=MujocoXmlIKBackend.from_xml_path(path))
        except (ImportError, RuntimeError, ValueError) as exc:
            logger.info("XML IK backend unavailable: %s", exc)
            return None

    if suffix == ".urdf":
        try:
            from motion_player.core.kinematics.ik_backends.pinocchio_urdf_backend import (
                PinocchioUrdfIKBackend,
            )

            return IKSolver(backend=PinocchioUrdfIKBackend.from_urdf_path(path))
        except (ImportError, RuntimeError, ValueError) as exc:
            logger.info("URDF IK backend unavailable: %s", exc)
            return None

    logger.info("IK backend skipped: unsupported robot suffix '%s'", suffix)
    return None
