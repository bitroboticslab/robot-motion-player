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

"""Process-isolated runtime launcher for full GUI workbench mode."""

from __future__ import annotations

import multiprocessing
import queue
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from motion_player.core.dataset.loader import DatasetLoader
from motion_player.gui.panel_ipc import PanelCommandReceiver, PanelMonitorPublisher


@dataclass
class _PanelRuntime:
    command_receiver: PanelCommandReceiver
    monitor_publisher: PanelMonitorPublisher
    process: Any
    stop_event: Any

    def close(self) -> None:
        try:
            self.stop_event.set()
        except Exception:  # noqa: BLE001
            pass

        try:
            if self.process.is_alive():
                self.process.join(timeout=0.8)
            if self.process.is_alive():
                self.process.terminate()
                self.process.join(timeout=1.0)
        except Exception:  # noqa: BLE001
            return


def _status_put(status_queue: Any, message: str) -> None:
    try:
        status_queue.put_nowait(message)
    except Exception:  # noqa: BLE001
        return


def _panel_process_entry(
    command_queue: Any,
    monitor_queue: Any,
    status_queue: Any,
    stop_event: Any,
    default_motion_path: str,
    default_robot_path: str,
    initial_font_size_key: str,
) -> None:
    from motion_player.gui.command_runner import CommandRunner
    from motion_player.gui.controller import GuiController
    from motion_player.gui.dearpygui_panel import DearPyGuiPanel
    from motion_player.gui.panel_ipc import PanelCommandSender, PanelMonitorSubscriber

    try:
        controller = GuiController(PanelCommandSender(command_queue))
        monitor_bus = PanelMonitorSubscriber(monitor_queue)
        panel = DearPyGuiPanel(
            controller=controller,
            monitor_bus=monitor_bus,
            command_runner=CommandRunner(),
            default_motion_path=default_motion_path,
            default_robot_path=default_robot_path,
            initial_font_size_key=initial_font_size_key,
        )
    except Exception as exc:  # noqa: BLE001
        _status_put(status_queue, f"failed:{exc}")
        return

    rc = panel.run_process_entry(lambda msg: _status_put(status_queue, msg))
    if rc != 0 and not stop_event.is_set():
        _status_put(status_queue, f"failed:exit-{rc}")


def _start_panel_runtime(
    *,
    default_motion_path: str,
    default_robot_path: str,
    initial_font_size_key: str,
    startup_timeout_s: float = 2.0,
) -> _PanelRuntime:
    ctx = multiprocessing.get_context("spawn")
    command_queue = ctx.Queue(maxsize=256)
    monitor_queue = ctx.Queue(maxsize=1)
    status_queue = ctx.Queue(maxsize=16)
    stop_event = ctx.Event()

    process = ctx.Process(
        target=_panel_process_entry,
        args=(
            command_queue,
            monitor_queue,
            status_queue,
            stop_event,
            default_motion_path,
            default_robot_path,
            initial_font_size_key,
        ),
        daemon=True,
    )
    process.start()

    deadline = time.monotonic() + max(0.2, float(startup_timeout_s))
    while time.monotonic() < deadline:
        if not process.is_alive():
            break
        try:
            message = status_queue.get(timeout=0.05)
        except queue.Empty:
            continue
        msg = str(message)
        if msg == "ready":
            return _PanelRuntime(
                command_receiver=PanelCommandReceiver(command_queue),
                monitor_publisher=PanelMonitorPublisher(monitor_queue),
                process=process,
                stop_event=stop_event,
            )
        if msg.startswith("failed:"):
            process.join(timeout=0.2)
            raise RuntimeError(msg.partition(":")[2] or "panel process failed")

    if process.is_alive():
        process.terminate()
        process.join(timeout=1.0)
    raise RuntimeError("panel process startup timeout")


def _warn_fallback(message: str) -> None:
    print(message, file=sys.stderr)


def run_backend_connected_gui_isolated(
    *,
    motion: str,
    robot: str,
    root_joint: str,
    backend: str,
    require_panel: bool,
    warn_if_panel_unavailable: bool = False,
    initial_font_size_key: str = "medium",
) -> int:
    """Run backend-connected playback with panel in isolated subprocess."""
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

    panel_runtime: _PanelRuntime | None = None

    from motion_player.gui.dearpygui_panel import DearPyGuiPanel

    if DearPyGuiPanel.is_available():
        try:
            panel_runtime = _start_panel_runtime(
                default_motion_path=str(motion_path),
                default_robot_path=str(robot_path),
                initial_font_size_key=initial_font_size_key,
            )
        except Exception as exc:  # noqa: BLE001
            if require_panel:
                raise RuntimeError("DearPyGui panel process startup failed.") from exc
            if warn_if_panel_unavailable:
                _warn_fallback(
                    "--gui was requested but DearPyGui panel process failed to start. "
                    "Continuing with MuJoCo keyboard controls only. "
                    f"Reason: {exc}"
                )
    elif require_panel:
        raise ImportError(
            "DearPyGui is not installed. Install GUI extras with: "
            "pip install 'robot-motion-player[gui]'"
        )
    elif warn_if_panel_unavailable:
        _warn_fallback(
            "--gui was requested but DearPyGui is not installed. "
            "Install GUI extras with: pip install 'robot-motion-player[gui]'. "
            "Continuing with MuJoCo keyboard controls only."
        )

    if panel_runtime is None:
        viewer = MuJoCoViewer(driver, motions)
    else:
        viewer = MuJoCoViewer(
            driver,
            motions,
            external_queue=panel_runtime.command_receiver,
            monitor_bus=panel_runtime.monitor_publisher,
        )
    try:
        viewer.run()
    finally:
        if panel_runtime is not None:
            panel_runtime.close()
    return 0
