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

"""Concrete conversion backends used by model-conversion router."""

from __future__ import annotations

import os
import shlex
import shutil
import subprocess
import sys
from pathlib import Path


def convert_urdf_to_xml_mujoco(input_path: Path, output_path: Path) -> tuple[int, str, str]:
    try:
        import mujoco  # type: ignore[import]
    except ImportError:
        return 1, "", "mujoco package is required for URDF->XML conversion."

    save_last_xml = getattr(mujoco, "mj_saveLastXML", None)
    if not callable(save_last_xml):
        return 1, "", "Current mujoco runtime does not expose mj_saveLastXML."

    try:
        model = mujoco.MjModel.from_xml_path(str(input_path))
        save_last_xml(str(output_path), model)
        return 0, f"Converted '{input_path}' -> '{output_path}'", ""
    except (ValueError, RuntimeError, OSError, TypeError) as exc:
        return 1, "", f"Conversion failed: {exc}"


def _run_external_command(cmd: list[str]) -> tuple[int, str, str]:
    try:
        proc = subprocess.run(  # noqa: S603
            cmd,
            check=False,
            capture_output=True,
            text=True,
        )
    except OSError as exc:
        return 1, "", str(exc)
    return int(proc.returncode), proc.stdout.strip(), proc.stderr.strip()


def _build_env_command(input_path: Path, output_path: Path) -> list[str] | None:
    template = os.environ.get("RMP_XML_TO_URDF_CMD", "").strip()
    if not template:
        return None
    if "{input}" in template or "{output}" in template:
        rendered = template.format(input=str(input_path), output=str(output_path))
        return shlex.split(rendered)
    cmd = shlex.split(template)
    cmd.extend([str(input_path), str(output_path)])
    return cmd


def convert_xml_to_urdf_external(input_path: Path, output_path: Path) -> tuple[int, str, str]:
    attempted: list[str] = []

    env_cmd = _build_env_command(input_path, output_path)
    if env_cmd:
        attempted.append(" ".join(env_cmd))
        rc, out, err = _run_external_command(env_cmd)
        if rc == 0 and output_path.exists():
            return 0, out or f"Converted '{input_path}' -> '{output_path}'", ""

    candidates: list[list[str]] = []
    if shutil.which("mjcf2urdf"):
        candidates.append(["mjcf2urdf", str(input_path), str(output_path)])

    # module path fallback for environments where executable wrapper is absent
    candidates.append([sys.executable, "-m", "mjcf2urdf", str(input_path), str(output_path)])

    for cmd in candidates:
        attempted.append(" ".join(cmd))
        rc, out, err = _run_external_command(cmd)
        if rc == 0 and output_path.exists():
            return 0, out or f"Converted '{input_path}' -> '{output_path}'", ""

    hint = (
        "XML->URDF conversion requires an external backend. "
        "Install one (for example `mjcf2urdf`) or set RMP_XML_TO_URDF_CMD."
    )
    if attempted:
        hint = hint + " Tried: " + " | ".join(attempted)
    return 1, "", hint
