"""Tests for read-only playback state monitor bus."""

from __future__ import annotations

from motion_player.core.ui.state_monitor import PlaybackSnapshot, StateMonitorBus


def test_latest_is_none_before_publish() -> None:
    bus = StateMonitorBus()
    assert bus.latest() is None


def test_publish_and_latest_roundtrip() -> None:
    bus = StateMonitorBus()
    snap = PlaybackSnapshot(
        frame=41,
        total_frames=120,
        clip=1,
        total_clips=3,
        speed=1.5,
        playing=True,
        loop=True,
        pingpong=False,
        edit_mode=False,
        show_hud=True,
        show_ghost=False,
        keyframe_count=2,
        joint_names=("joint_0", "joint_1"),
        selected_joint_idx=1,
    )
    bus.publish(snap)

    latest = bus.latest()
    assert latest is not None
    assert latest.frame == 41
    assert latest.total_frames == 120
    assert latest.speed == 1.5
    assert latest.playing is True
    assert latest.selected_joint_idx == 1
    assert latest.joint_names[0] == "joint_0"
