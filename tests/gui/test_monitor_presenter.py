"""Tests for monitor presenter view model formatting."""

from __future__ import annotations

from motion_player.core.ui.state_monitor import PlaybackSnapshot
from motion_player.gui.monitor_presenter import MonitorViewModel, build_monitor_view_model


def test_build_monitor_view_model_for_playing_state() -> None:
    snap = PlaybackSnapshot(
        frame=14,
        total_frames=120,
        clip=1,
        total_clips=3,
        speed=1.3,
        playing=True,
        loop=True,
        pingpong=False,
        edit_mode=False,
        show_hud=True,
        show_ghost=False,
        keyframe_count=4,
    )

    vm = build_monitor_view_model(snap)

    assert isinstance(vm, MonitorViewModel)
    assert vm.headline == "Clip 2/3  Frame 15/120"
    assert vm.subline == "PLAY  1.3x"
    assert "LOOP ON" in vm.flags_line
    assert "HUD ON" in vm.flags_line


def test_build_monitor_view_model_for_paused_state() -> None:
    snap = PlaybackSnapshot(
        frame=0,
        total_frames=88,
        clip=0,
        total_clips=1,
        speed=0.8,
        playing=False,
        loop=False,
        pingpong=True,
        edit_mode=True,
        show_hud=False,
        show_ghost=True,
        keyframe_count=2,
    )

    vm = build_monitor_view_model(snap)

    assert vm.subline == "PAUSE  0.8x"
    assert "PING ON" in vm.flags_line
    assert "EDIT ON" in vm.flags_line
    assert "GHOST ON" in vm.flags_line
