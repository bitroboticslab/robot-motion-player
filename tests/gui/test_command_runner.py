from __future__ import annotations

from motion_player.gui.command_models import ExportRequest, MetricsRequest
from motion_player.gui.command_runner import CommandRunner


def test_command_runner_dispatches_metrics_handler() -> None:
    seen: dict[str, object] = {}

    def _fake_metrics(args):
        seen["command"] = args.command
        seen["motion"] = args.motion
        return 0

    runner = CommandRunner(metrics_handler=_fake_metrics)
    rc = runner.run_metrics(MetricsRequest(motion="walk.pkl", output="report.json"))
    assert rc.return_code == 0
    assert seen["command"] == "metrics"
    assert seen["motion"] == "walk.pkl"


def test_command_runner_reports_staged_progress_for_metrics() -> None:
    seen: list[tuple[float, str]] = []

    def _fake_metrics(_args):
        return 0

    runner = CommandRunner(metrics_handler=_fake_metrics)
    rc = runner.run_metrics(
        MetricsRequest(motion="walk.pkl", output="report.json"),
        progress_callback=lambda ratio, msg: seen.append((ratio, msg)),
    )
    assert rc.return_code == 0
    assert seen[0][0] == 0.0
    assert seen[-1][0] == 1.0
    assert "complete" in seen[-1][1]


def test_command_runner_forwards_export_progress_callback() -> None:
    seen: list[tuple[float, str]] = []

    def _fake_export(args):
        cb = getattr(args, "progress_callback", None)
        assert cb is not None
        cb(2, 10)
        cb(10, 10)
        return 0

    runner = CommandRunner(export_handler=_fake_export)
    rc = runner.run_export(
        ExportRequest(
            motion="walk.pkl",
            robot="robot.xml",
            output="out.gif",
            fps=30.0,
        ),
        progress_callback=lambda ratio, msg: seen.append((ratio, msg)),
    )
    assert rc.return_code == 0
    assert seen[-1][0] == 1.0
    assert any("10/10" in message for _ratio, message in seen)


def test_export_progress_is_frame_driven_without_synthetic_running_ratio() -> None:
    seen: list[tuple[float, str]] = []

    def _fake_export(args):
        cb = getattr(args, "progress_callback", None)
        assert cb is not None
        cb(1, 4)
        cb(4, 4)
        return 0

    runner = CommandRunner(export_handler=_fake_export)
    rc = runner.run_export(
        ExportRequest(
            motion="walk.pkl",
            robot="robot.xml",
            output="out.gif",
            fps=30.0,
        ),
        progress_callback=lambda ratio, msg: seen.append((ratio, msg)),
    )

    assert rc.return_code == 0
    assert [ratio for ratio, _message in seen] == [0.0, 0.25, 1.0, 1.0]
    assert all("running" not in message for _ratio, message in seen)


def test_export_progress_reports_preparing_for_empty_total() -> None:
    seen: list[tuple[float, str]] = []

    def _fake_export(args):
        cb = getattr(args, "progress_callback", None)
        assert cb is not None
        cb(0, 0)
        return 0

    runner = CommandRunner(export_handler=_fake_export)
    rc = runner.run_export(
        ExportRequest(
            motion="walk.pkl",
            robot="robot.xml",
            output="out.gif",
            fps=30.0,
        ),
        progress_callback=lambda ratio, msg: seen.append((ratio, msg)),
    )

    assert rc.return_code == 0
    assert (0.0, "export: preparing") in seen


def test_command_runner_failure_path_emits_failed_state_and_rc1() -> None:
    seen: list[tuple[float, str]] = []

    def _boom(_args):
        raise RuntimeError("boom")

    runner = CommandRunner(metrics_handler=_boom)
    rc = runner.run_metrics(
        MetricsRequest(motion="walk.pkl", output="report.json"),
        progress_callback=lambda ratio, msg: seen.append((ratio, msg)),
    )

    assert rc.return_code == 1
    assert seen[0] == (0.0, "metrics: queued")
    assert seen[-1] == (1.0, "metrics: failed")
    assert "boom" in rc.stderr
