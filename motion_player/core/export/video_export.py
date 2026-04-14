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

"""Video export helpers."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import numpy as np


def _frame_schedule(num_frames: int, src_fps: float, out_fps: float) -> list[int]:
    """Build sampled source frame indices for output FPS."""
    if num_frames <= 0:
        return []
    if src_fps <= 0.0:
        raise ValueError("src_fps must be > 0.")
    if out_fps <= 0.0:
        raise ValueError("out_fps must be > 0.")
    duration = (num_frames - 1) / src_fps
    out_count = max(1, int(round(duration * out_fps)) + 1)
    idx = np.linspace(0, num_frames - 1, out_count).round().astype(int)
    idx[0] = 0
    idx[-1] = num_frames - 1
    return idx.tolist()


def export_video_with_renderer(
    *,
    num_frames: int,
    src_fps: float,
    out_fps: float,
    render_frame: Callable[[int], np.ndarray],
    output_path: str | Path,
) -> Path:
    """Render sampled frames and encode to gif/mp4."""
    path = Path(output_path)
    frame_ids = _frame_schedule(num_frames=num_frames, src_fps=src_fps, out_fps=out_fps)
    if not frame_ids:
        raise ValueError("No source frames available for export.")
    _encode_video(path=path, frame_ids=frame_ids, render_frame=render_frame, fps=out_fps)
    return path


def _encode_video(
    *,
    path: Path,
    frame_ids: list[int],
    render_frame: Callable[[int], np.ndarray],
    fps: float,
) -> None:
    suffix = path.suffix.lower()
    if suffix not in (".gif", ".mp4"):
        raise ValueError("Output extension must be .gif or .mp4.")
    try:
        import imageio.v2 as imageio  # type: ignore[import]
    except ImportError as exc:
        raise ImportError(
            "imageio is required for video export. Install with: pip install -e '.[video]'"
        ) from exc
    path.parent.mkdir(parents=True, exist_ok=True)
    writer_kwargs: dict[str, object] = {"fps": fps}
    if suffix == ".gif":
        writer_kwargs["format"] = "GIF"
    writer = imageio.get_writer(str(path), **writer_kwargs)
    try:
        for frame_idx in frame_ids:
            frame = np.asarray(render_frame(frame_idx), dtype=np.uint8)
            if frame.ndim != 3 or frame.shape[2] not in (3, 4):
                raise ValueError(
                    f"render_frame({frame_idx}) must return HxWx3/4 uint8 image, got {frame.shape}"
                )
            writer.append_data(frame[:, :, :3])
    finally:
        writer.close()
