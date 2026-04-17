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

"""Font resolution helpers for GUI i18n rendering."""

from __future__ import annotations

import os
from collections.abc import Iterable
from pathlib import Path


def resolve_cjk_font(candidates: Iterable[Path]) -> Path | None:
    """Return first existing CJK-capable font path.

    Resolution order:
    1. `RMP_GUI_FONT` env override when it points to an existing file.
    2. First existing path from caller-provided candidates.
    """
    override = os.getenv("RMP_GUI_FONT")
    if override:
        path = Path(override)
        if path.exists():
            return path
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return None


def resolve_ui_font(
    cjk_candidates: Iterable[Path], fallback_candidates: Iterable[Path]
) -> Path | None:
    cjk = resolve_cjk_font(cjk_candidates)
    if cjk is not None:
        return cjk
    for candidate in fallback_candidates:
        if candidate.exists():
            return candidate
    return None
