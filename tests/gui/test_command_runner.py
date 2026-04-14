from __future__ import annotations

from motion_player.gui.command_models import MetricsRequest
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
