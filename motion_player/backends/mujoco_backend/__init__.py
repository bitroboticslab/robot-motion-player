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

"""MuJoCo rendering backend.

This package provides kinematic replay of a
:class:`~motion_player.core.dataset.motion.StandardMotion` using the official
MuJoCo Python bindings (``mujoco >= 3.0``).

Import guard
-----------
MuJoCo is a runtime dependency (not available in headless CI).  All MuJoCo
imports are deferred to runtime inside the module functions; this package can
be *imported* safely without MuJoCo installed — you will only get an
``ImportError`` when you actually try to use :class:`MuJoCoStateDriver` or
:class:`MuJoCoViewer`.
"""

from motion_player.backends.mujoco_backend.state_driver import MuJoCoStateDriver
from motion_player.backends.mujoco_backend.viewer import MuJoCoViewer

__all__ = ["MuJoCoStateDriver", "MuJoCoViewer"]
