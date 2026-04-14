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

"""Request/response models for GUI tool-command execution."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class CommandResult:
    return_code: int
    stdout: str = ""
    stderr: str = ""


@dataclass(frozen=True)
class MetricsRequest:
    motion: str
    output: str | None = None
    robot: str | None = None


@dataclass(frozen=True)
class AuditRequest:
    motion: str
    robot: str
    output: str | None = None


@dataclass(frozen=True)
class ConvertRequest:
    input_path: str
    output_path: str


@dataclass(frozen=True)
class ExportRequest:
    motion: str
    robot: str
    output: str
    fps: float = 30.0
    root_joint: str = "root"
    width: int = 640
    height: int = 480


@dataclass(frozen=True)
class AudioRequest:
    action: str
