"""Tests for backend-connected `motion_player gui` runtime path."""

from __future__ import annotations

import argparse

from motion_player.cli.main import _cmd_gui


def test_cmd_gui_requests_isolated_runtime(monkeypatch) -> None:
    captured: dict[str, object] = {}

    def _fake_runtime(**kwargs):
        captured.update(kwargs)
        return 0

    monkeypatch.setattr("motion_player.cli.gui_runtime.run_backend_connected_gui", _fake_runtime)

    args = argparse.Namespace(
        command="gui",
        motion="walk.pkl",
        robot="robot.xml",
        root_joint="root",
        backend="mujoco",
        font_size="large",
    )

    rc = _cmd_gui(args)

    assert rc == 0
    assert captured["prefer_isolated"] is True
    assert captured["require_panel"] is False
    assert captured["warn_if_panel_unavailable"] is True
    assert captured["initial_font_size_key"] == "large"


def test_cmd_gui_normalizes_sigsegv_like_return_code(monkeypatch, capsys) -> None:
    monkeypatch.setattr(
        "motion_player.cli.gui_runtime.run_backend_connected_gui",
        lambda **_kwargs: 139,
    )

    args = argparse.Namespace(
        command="gui",
        motion="walk.pkl",
        robot="robot.xml",
        root_joint="root",
        backend="mujoco",
        font_size=None,
    )

    rc = _cmd_gui(args)
    captured = capsys.readouterr()

    assert rc == 1
    assert "abnormally" in captured.err.lower()
