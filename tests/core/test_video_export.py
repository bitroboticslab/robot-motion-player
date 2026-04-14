from __future__ import annotations

from motion_player.core.export.video_export import _frame_schedule


def test_frame_schedule_matches_duration_and_fps() -> None:
    idx = _frame_schedule(num_frames=30, src_fps=30.0, out_fps=15.0)
    assert idx[0] == 0
    assert idx[-1] == 29
    assert len(idx) == 15
