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

"""Shared backend-connected runtime launcher for GUI-enabled sessions."""

from __future__ import annotations

import sys
from pathlib import Path

from motion_player.core.dataset.loader import DatasetLoader


def run_backend_connected_gui(
    *,
    motion: str,
    robot: str,
    root_joint: str,
    backend: str,
    require_panel: bool,
    warn_if_panel_unavailable: bool = False,
) -> int:
    """Run a backend-connected playback session with optional DearPyGui panel.

    When ``require_panel`` is True, DearPyGui availability is treated as required.
    """
    motion_path = Path(motion)
    robot_path = Path(robot)
    if not motion_path.exists():
        raise FileNotFoundError(f"Motion path not found: '{motion_path}'")
    if not robot_path.exists():
        raise FileNotFoundError(f"Robot model path not found: '{robot_path}'")

    loader = DatasetLoader()
    if motion_path.is_dir():
        motions = loader.load_folder(motion_path)
        if not motions:
            raise ValueError(f"No motion files found in '{motion_path}'.")
    else:
        motions = [loader.load(motion_path)]

    if backend != "mujoco":
        raise ValueError(f"Unsupported backend '{backend}'.")

    from motion_player.backends.mujoco_backend.state_driver import MuJoCoStateDriver
    from motion_player.backends.mujoco_backend.viewer import MuJoCoViewer

    driver = MuJoCoStateDriver(
        model_path=robot_path,
        root_joint_name=root_joint or "root",
    )
    driver.bind_motion(motions[0])

    external_queue = None
    monitor_bus = None

    from motion_player.gui.dearpygui_panel import DearPyGuiPanel

    if DearPyGuiPanel.is_available():
        from motion_player.core.ui.command_queue import CommandQueue
        from motion_player.core.ui.state_monitor import StateMonitorBus
        from motion_player.gui.command_runner import CommandRunner
        from motion_player.gui.controller import GuiController

        external_queue = CommandQueue()
        monitor_bus = StateMonitorBus()
        panel = DearPyGuiPanel(
            controller=GuiController(external_queue),
            monitor_bus=monitor_bus,
            command_runner=CommandRunner(),
            default_motion_path=str(motion_path),
            default_robot_path=str(robot_path),
        )
        panel.launch_non_blocking()
    elif require_panel:
        raise ImportError(
            "DearPyGui is not installed. Install GUI extras with: "
            "pip install 'robot-motion-player[gui]'"
        )
    elif warn_if_panel_unavailable:
        print(
            "--gui was requested but DearPyGui is not installed. "
            "Install GUI extras with: pip install 'robot-motion-player[gui]'. "
            "Continuing with MuJoCo keyboard controls only.",
            file=sys.stderr,
        )

    if external_queue is None:
        viewer = MuJoCoViewer(driver, motions)
    else:
        viewer = MuJoCoViewer(
            driver,
            motions,
            external_queue=external_queue,
            monitor_bus=monitor_bus,
        )
    viewer.run()
    return 0
