from motion_player.gui.timeline_widget import format_keyframe_line


def test_format_keyframe_line_with_dense_markers() -> None:
    line = format_keyframe_line(total_frames=30, keyframes=[0, 5, 6, 12, 29], current_frame=6)
    assert "K:" in line
    assert "[7]" in line
    assert line.count("|") >= 3
