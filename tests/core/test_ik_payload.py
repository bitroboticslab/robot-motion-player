from __future__ import annotations

import numpy as np

from motion_player.core.ui.ik_payload import build_pose_target_from_payload


def test_build_pose_target_from_payload_converts_units() -> None:
    payload = {
        "target_joint": "left_hand",
        "position": {"x": 10.0, "y": 0.0, "z": -5.0, "unit": "cm"},
        "rotation": {"roll": 90.0, "pitch": 0.0, "yaw": 0.0, "unit": "deg"},
    }
    name, target = build_pose_target_from_payload(payload)
    assert name == "left_hand"
    np.testing.assert_allclose(target.position_m, np.array([0.1, 0.0, -0.05]))
