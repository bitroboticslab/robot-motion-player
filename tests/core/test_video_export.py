from __future__ import annotations

import numpy as np
import pytest

from motion_player.core.export.video_export import _frame_schedule, export_video_with_renderer


def test_frame_schedule_matches_duration_and_fps() -> None:
    idx = _frame_schedule(num_frames=30, src_fps=30.0, out_fps=15.0)
    assert idx[0] == 0
    assert idx[-1] == 29
    assert len(idx) == 15


def test_export_video_progress_callback_reaches_completion(tmp_path) -> None:
    pytest.importorskip("imageio.v2")

    seen: list[tuple[int, int]] = []
    output = tmp_path / "clip.gif"
    export_video_with_renderer(
        num_frames=5,
        src_fps=5.0,
        out_fps=5.0,
        output_path=output,
        render_frame=lambda _idx: np.zeros((8, 8, 3), dtype=np.uint8),
        progress_callback=lambda done, total: seen.append((done, total)),
    )

    assert output.exists()
    assert seen
    assert seen[-1][0] == seen[-1][1]
