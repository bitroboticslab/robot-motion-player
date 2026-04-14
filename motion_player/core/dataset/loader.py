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

"""DatasetLoader — loads standard motion files and returns StandardMotion objects.

Supported formats
-----------------
* ``.npy`` — ``np.load(path, allow_pickle=True).item()``
* ``.pkl`` — ``pickle.load(f)``

The loader validates required fields, checks shapes, and normalises the
quaternion convention to **xyzw** (matching the rsl-rl-ex standard).

Extension points
----------------
* Subclass ``DatasetLoader`` and override ``_parse_dict`` to support new
  file formats (e.g. HDF5).
* Pass ``quat_fmt="wxyz"`` when loading files that store quaternions in
  wxyz order (rare; the standard is xyzw).
"""

from __future__ import annotations

import pickle
import warnings
from pathlib import Path

import numpy as np

from motion_player.core.dataset.motion import StandardMotion
from motion_player.core.dataset.quat_utils import normalize, wxyz_to_xyzw

# Required keys that every standard motion file must contain.
_REQUIRED_KEYS = {
    "fps",
    "root_pos",
    "root_rot",
    "dof_pos",
    "dof_vel",
    "projected_gravity",
    "root_lin_vel",
    "root_ang_vel",
    "key_body_pos_local",
}


class DatasetLoader:
    """Loads standard motion files produced by rsl-rl-ex dataset_builder.

    Parameters
    ----------
    quat_fmt:
        Quaternion convention used in the file.  Accepted values:
        ``"xyzw"`` (default, rsl-rl-ex standard) or ``"wxyz"`` (MuJoCo
        internal format).  If ``"wxyz"`` the loader will convert to
        xyzw automatically.
    validate:
        If ``True`` (default), call :meth:`StandardMotion.validate` after
        construction to catch shape mismatches early.
    """

    def __init__(
        self,
        quat_fmt: str = "xyzw",
        validate: bool = True,
    ) -> None:
        if quat_fmt not in ("xyzw", "wxyz"):
            raise ValueError(f"quat_fmt must be 'xyzw' or 'wxyz', got '{quat_fmt}'")
        self.quat_fmt = quat_fmt
        self.validate = validate

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def load(self, path: str | Path) -> StandardMotion:
        """Load a single motion file.

        Parameters
        ----------
        path:
            Path to a ``.npy`` or ``.pkl`` standard motion file.

        Returns
        -------
        StandardMotion
            Parsed and validated motion object.
        """
        path = Path(path)
        raw: dict = self._read_file(path)
        motion = self._parse_dict(raw, source_path=str(path))
        if self.validate:
            motion.validate()
        return motion

    def load_folder(self, folder: str | Path) -> list[StandardMotion]:
        """Load all ``.npy`` / ``.pkl`` files in a directory.

        Parameters
        ----------
        folder:
            Directory to search for motion files.

        Returns
        -------
        list of StandardMotion
        """
        folder = Path(folder)
        motions: list[StandardMotion] = []
        for ext in ("*.npy", "*.pkl"):
            for p in sorted(folder.glob(ext)):
                try:
                    motions.append(self.load(p))
                except (
                    FileNotFoundError,
                    KeyError,
                    ValueError,
                    OSError,
                    pickle.UnpicklingError,
                ) as exc:
                    warnings.warn(f"Failed to load {p}: {exc}", stacklevel=2)
        return motions

    def save(
        self,
        motion: StandardMotion,
        path: str | Path,
        fmt: str = "pkl",
    ) -> None:
        """Save a ``StandardMotion`` back to disk.

        Parameters
        ----------
        motion:
            Motion to save.
        path:
            Output file path.  Extension determines format unless ``fmt`` is
            specified.
        fmt:
            ``"pkl"`` (default) or ``"npy"``.
        """
        path = Path(path)
        data = self._to_dict(motion)
        if fmt == "pkl" or path.suffix == ".pkl":
            with open(path, "wb") as f:
                pickle.dump(data, f)
        elif fmt == "npy" or path.suffix == ".npy":
            np.save(str(path), data)  # type: ignore[arg-type]
        else:
            raise ValueError(f"Unknown format '{fmt}'; use 'pkl' or 'npy'.")

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    def _read_file(self, path: Path) -> dict:
        """Read raw dict from disk."""
        if not path.exists():
            raise FileNotFoundError(f"Motion file not found: {path}")
        suffix = path.suffix.lower()
        if suffix == ".npy":
            obj = np.load(str(path), allow_pickle=True)
            # np.load of a pickled dict returns a 0-d object array
            return obj.item() if obj.ndim == 0 else dict(obj)
        elif suffix == ".pkl":
            with open(path, "rb") as f:
                return pickle.load(f)  # noqa: S301
        else:
            raise ValueError(
                f"Unsupported file extension '{suffix}'; expected .npy or .pkl"
            )

    def _parse_dict(
        self, raw: dict, source_path: str | None = None
    ) -> StandardMotion:
        """Convert a raw dict to a ``StandardMotion``."""
        missing = _REQUIRED_KEYS - set(raw.keys())
        if missing:
            raise KeyError(
                f"Motion file is missing required keys: {sorted(missing)}"
            )

        fps = float(raw["fps"])
        root_pos = np.asarray(raw["root_pos"], dtype=np.float32)
        root_rot = np.asarray(raw["root_rot"], dtype=np.float32)
        dof_pos = np.asarray(raw["dof_pos"], dtype=np.float32)
        dof_vel = np.asarray(raw["dof_vel"], dtype=np.float32)
        proj_grav = np.asarray(raw["projected_gravity"], dtype=np.float32)
        root_lin_vel = np.asarray(raw["root_lin_vel"], dtype=np.float32)
        root_ang_vel = np.asarray(raw["root_ang_vel"], dtype=np.float32)
        key_body = np.asarray(raw["key_body_pos_local"], dtype=np.float32)

        # Normalise quaternion convention to xyzw
        if self.quat_fmt == "wxyz":
            root_rot = wxyz_to_xyzw(root_rot).astype(np.float32)

        # Always normalise quaternions to unit length
        root_rot = normalize(root_rot.astype(np.float64)).astype(np.float32)

        joint_names: list[str] | None = (
            list(raw["joint_names"])
            if "joint_names" in raw
            else None
        )
        motion_weight = float(raw.get("motion_weight", 1.0))

        return StandardMotion(
            fps=fps,
            root_pos=root_pos,
            root_rot=root_rot,
            dof_pos=dof_pos,
            dof_vel=dof_vel,
            projected_gravity=proj_grav,
            root_lin_vel=root_lin_vel,
            root_ang_vel=root_ang_vel,
            key_body_pos_local=key_body,
            joint_names=joint_names,
            source_path=source_path,
            motion_weight=motion_weight,
        )

    @staticmethod
    def _to_dict(motion: StandardMotion) -> dict:
        """Serialise a ``StandardMotion`` to a raw dict (rsl-rl-ex format)."""
        d: dict[str, object] = {
            "fps": motion.fps,
            "motion_length": motion.num_frames,
            "motion_weight": motion.motion_weight,
            "root_pos": motion.root_pos,
            "root_rot": motion.root_rot,
            "dof_pos": motion.dof_pos,
            "dof_vel": motion.dof_vel,
            "projected_gravity": motion.projected_gravity,
            "root_lin_vel": motion.root_lin_vel,
            "root_ang_vel": motion.root_ang_vel,
            "key_body_pos_local": motion.key_body_pos_local,
        }
        if motion.joint_names is not None:
            d["joint_names"] = motion.joint_names
        return d
