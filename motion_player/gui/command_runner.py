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

"""Execute non-play tool commands through existing CLI handlers."""

from __future__ import annotations

import argparse
import io
from contextlib import redirect_stderr, redirect_stdout
from typing import Callable

from motion_player.cli.main import _cmd_audit, _cmd_convert, _cmd_export, _cmd_metrics
from motion_player.gui.command_models import (
    AudioRequest,
    AuditRequest,
    CommandResult,
    ConvertRequest,
    ExportRequest,
    MetricsRequest,
)

ProgressCallback = Callable[[float, str], None]


class CommandRunner:
    """Wrapper over CLI command handlers for GUI parity."""

    def __init__(
        self,
        metrics_handler: Callable[[argparse.Namespace], int] = _cmd_metrics,
        audit_handler: Callable[[argparse.Namespace], int] = _cmd_audit,
        convert_handler: Callable[[argparse.Namespace], int] = _cmd_convert,
        export_handler: Callable[[argparse.Namespace], int] = _cmd_export,
    ) -> None:
        self._metrics_handler = metrics_handler
        self._audit_handler = audit_handler
        self._convert_handler = convert_handler
        self._export_handler = export_handler

    def _run_handler(
        self,
        handler: Callable[[argparse.Namespace], int],
        args: argparse.Namespace,
        *,
        progress_callback: ProgressCallback | None = None,
        title: str = "task",
        emit_running_ratio: bool = True,
    ) -> CommandResult:
        if progress_callback is not None:
            progress_callback(0.0, f"{title}: queued")
        out = io.StringIO()
        err = io.StringIO()
        try:
            if progress_callback is not None and emit_running_ratio:
                progress_callback(0.15, f"{title}: running")
            with redirect_stdout(out), redirect_stderr(err):
                rc = int(handler(args))
        except Exception as exc:  # noqa: BLE001
            if progress_callback is not None:
                progress_callback(1.0, f"{title}: failed")
            return CommandResult(
                return_code=1, stdout=out.getvalue(), stderr=err.getvalue() + f"{exc}\n"
            )
        if progress_callback is not None:
            progress_callback(1.0, f"{title}: complete")
        return CommandResult(return_code=rc, stdout=out.getvalue(), stderr=err.getvalue())

    def run_metrics(
        self, req: MetricsRequest, progress_callback: ProgressCallback | None = None
    ) -> CommandResult:
        args = argparse.Namespace(
            command="metrics", motion=req.motion, robot=req.robot, output=req.output
        )
        return self._run_handler(
            self._metrics_handler,
            args,
            progress_callback=progress_callback,
            title="metrics",
        )

    def run_audit(
        self, req: AuditRequest, progress_callback: ProgressCallback | None = None
    ) -> CommandResult:
        args = argparse.Namespace(
            command="audit", motion=req.motion, robot=req.robot, output=req.output
        )
        return self._run_handler(
            self._audit_handler,
            args,
            progress_callback=progress_callback,
            title="audit",
        )

    def run_convert(
        self, req: ConvertRequest, progress_callback: ProgressCallback | None = None
    ) -> CommandResult:
        args = argparse.Namespace(command="convert", input=req.input_path, output=req.output_path)
        return self._run_handler(
            self._convert_handler,
            args,
            progress_callback=progress_callback,
            title="convert",
        )

    def run_export(
        self, req: ExportRequest, progress_callback: ProgressCallback | None = None
    ) -> CommandResult:
        def _emit_export_progress(done: int, total: int) -> None:
            if progress_callback is None:
                return
            if total <= 0:
                progress_callback(0.0, "export: preparing")
                return
            ratio = max(0.0, min(1.0, float(done) / float(total)))
            progress_callback(ratio, f"export: {done}/{total} frames")

        args = argparse.Namespace(
            command="export",
            motion=req.motion,
            robot=req.robot,
            output=req.output,
            fps=float(req.fps),
            root_joint=req.root_joint,
            width=int(req.width),
            height=int(req.height),
            progress_callback=_emit_export_progress,
        )
        return self._run_handler(
            self._export_handler,
            args,
            progress_callback=progress_callback,
            title="export",
            emit_running_ratio=False,
        )

    def run_audio(self, req: AudioRequest) -> CommandResult:
        del req
        return CommandResult(
            return_code=1,
            stderr="Audio tools are not implemented in this version. Use playback controls in Play tab.\n",
        )
