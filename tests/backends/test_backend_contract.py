"""Tests for backend protocol parity across MuJoCo and Isaac backends."""

from __future__ import annotations

import warnings

import pytest

from motion_player.backends import BackendProtocol
from motion_player.backends.isaac_backend import IsaacBackend
from motion_player.backends.mujoco_backend.state_driver import MuJoCoStateDriver
from tests.conftest import make_motion


def test_backend_protocol_has_required_methods() -> None:
    required = {"bind_motion", "apply_frame", "reset", "close", "is_available"}
    assert required.issubset(set(dir(BackendProtocol)))


def test_isaac_backend_matches_protocol_shape() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        backend = IsaacBackend()
    assert isinstance(backend, BackendProtocol)
    assert isinstance(backend.is_available(), bool)


def test_mujoco_class_exposes_protocol_methods() -> None:
    for name in ("bind_motion", "apply_frame", "reset", "close", "is_available"):
        assert callable(getattr(MuJoCoStateDriver, name))
    assert isinstance(MuJoCoStateDriver.is_available(), bool)


def test_isaac_apply_frame_validates_bounds() -> None:
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        backend = IsaacBackend()
    backend.bind_motion(make_motion(num_frames=5))
    with warnings.catch_warnings():
        warnings.simplefilter("ignore")
        with pytest.raises(IndexError):
            backend.apply_frame(-1)
