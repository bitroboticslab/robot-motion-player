"""Tests for abstract UI layer (PlayerCommand, PlayerState, CommandDispatcher)."""

from __future__ import annotations

from motion_player.core.ui import CommandDispatcher, PlayerCommand, PlayerState


class TestPlayerState:
    def test_toggle_play(self):
        s = PlayerState(playing=False)
        s.toggle_play()
        assert s.playing
        s.toggle_play()
        assert not s.playing

    def test_step_forward_with_loop(self):
        s = PlayerState(frame=28, loop=True)
        s.step(3, total_frames=30)
        assert s.frame == 1  # wraps around: (28+3) % 30 = 1

    def test_step_no_loop_clamps(self):
        s = PlayerState(frame=28, loop=False)
        s.step(100, total_frames=30)
        assert s.frame == 29  # clamped to max

    def test_pingpong_direction_flip(self):
        s = PlayerState(frame=28, pingpong=True, direction=1)
        s.step(3, total_frames=30)  # 28+3 = 31 >= 30 → flip
        assert s.direction == -1

    def test_mark_unmark_keyframe(self):
        s = PlayerState(frame=5)
        s.toggle_mark_keyframe()
        assert 5 in s.keyframes
        assert s.mark_history == [5]
        s.toggle_mark_keyframe()
        assert 5 not in s.keyframes
        assert s.mark_history == []

    def test_adjust_speed_clamps_min(self):
        s = PlayerState(speed=0.2)
        s.adjust_speed(-1.0)
        assert s.speed == 0.1

    def test_adjust_speed_clamps_max(self):
        s = PlayerState(speed=3.9)
        s.adjust_speed(1.0)
        assert s.speed == 4.0

    def test_set_speed_clamps_min(self):
        s = PlayerState(speed=1.0)
        s.set_speed(0.01)
        assert s.speed == 0.1

    def test_set_speed_clamps_max(self):
        s = PlayerState(speed=1.0)
        s.set_speed(10.0)
        assert s.speed == 4.0


class TestCommandDispatcher:
    def test_dispatch_calls_handler(self):
        calls = []
        s = PlayerState()
        d = CommandDispatcher(s)
        d.register(PlayerCommand.PLAY_PAUSE, lambda state, _: calls.append("called"))
        d.dispatch(PlayerCommand.PLAY_PAUSE)
        assert calls == ["called"]

    def test_dispatch_unregistered_is_silent(self):
        s = PlayerState()
        d = CommandDispatcher(s)
        d.dispatch(PlayerCommand.EXIT)  # should not raise

    def test_play_pause_via_dispatch(self):
        s = PlayerState(playing=False)
        d = CommandDispatcher(s)
        d.register(PlayerCommand.PLAY_PAUSE, lambda state, _: state.toggle_play())
        d.dispatch(PlayerCommand.PLAY_PAUSE)
        assert s.playing

    def test_all_commands_enumerable(self):
        """Ensure the enum has the expected members."""
        expected = {
            "PLAY_PAUSE",
            "STEP_FWD_1",
            "STEP_BWD_1",
            "SEEK_FRAME",
            "SET_SPEED",
            "SPEED_UP",
            "SPEED_DOWN",
            "RESET",
            "TOGGLE_LOOP",
            "PREV_MARKED_FRAME",
            "NEXT_MARKED_FRAME",
            "EXIT",
        }
        names = {cmd.name for cmd in PlayerCommand}
        assert expected.issubset(names)
