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

"""Extension-aware model conversion routing."""

from __future__ import annotations

from pathlib import Path

from motion_player.core.convert.backends import (
    convert_urdf_to_xml_mujoco,
    convert_xml_to_urdf_external,
)


def convert_model(*, input_path: Path, output_path: Path) -> tuple[int, str, str]:
    in_ext = input_path.suffix.lower()
    out_ext = output_path.suffix.lower()

    if in_ext == ".xml" and out_ext == ".xml":
        return 0, f"Input '{input_path}' is already XML; no conversion performed.", ""

    if in_ext == ".urdf" and out_ext == ".urdf":
        return 0, f"Input '{input_path}' is already URDF; no conversion performed.", ""

    if in_ext == ".urdf" and out_ext == ".xml":
        return convert_urdf_to_xml_mujoco(input_path, output_path)

    if in_ext == ".xml" and out_ext == ".urdf":
        return convert_xml_to_urdf_external(input_path, output_path)

    if in_ext not in {".xml", ".urdf"}:
        return 1, "", f"Unsupported input extension '{in_ext}'. Use .urdf or .xml."

    return 1, "", f"Unsupported conversion: {in_ext} -> {out_ext}."
