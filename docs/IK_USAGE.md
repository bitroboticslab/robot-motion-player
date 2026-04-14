# IK Usage Guide

## Status

`robot-motion-player` now supports **full pose** IK targets for end-effectors:

- Position: `x, y, z`
- Orientation: `roll, pitch, yaw` (UI-facing Euler)
- Internal canonical form: position in meters + normalized quaternion (`wxyz`)

Both runtime backend paths (`.xml` MuJoCo and `.urdf` Pinocchio when installed) consume the same canonical target shape.

## Unit Model

- Position units in GUI: `m / cm / mm`
- Orientation units in GUI: `rad / deg`
- Solver internals always run in one canonical representation:
  - position in `m`
  - rotation in quaternion `wxyz`

Unit conversion is done only at the UI/payload boundary.

## GUI Workflow

Use either:

- `motion_player play --motion <clip.pkl> --robot <robot.xml> --gui`
- `motion_player gui --motion <clip.pkl> --robot <robot.xml>`

### Tune tab (full-pose)

1. Select target joint (`joint_id : joint_name`).
2. Choose `Reference Frame` (`world` or local frame).
3. Set position/angle units.
4. Inspect `Current Pose` (live measured 6D state).
5. Edit `Target Pose` (numeric 6D values).
6. Adjust step increments.
7. Use nudge buttons for incremental refinement.
8. Click `Apply Full Pose IK`.

Undo/redo remains available through the existing editor command path.

## Reference Frame

- `Reference Frame = world`: values are interpreted in world coordinates.
- `Reference Frame = local`: values are interpreted in joint-local coordinates and converted internally before solve.
- Solver internals still use canonical meters + normalized quaternion (`wxyz`).

## Current Pose vs Target Pose

- `Current Pose`: read-only, refreshed from backend runtime state for the selected joint.
- `Target Pose`: editable numeric inputs used to build the IK request payload.
- This dual-level flow prevents accidental overwrite of observed state while preserving precise editing control.

## Cross-Frame Smoothing

When an IK edit is applied at one frame, optional cross-frame smoothing can propagate the solved delta to subsequent frames with decay. This reduces visible joint jumps and keeps adjacent motion continuity for beginner and production tuning workflows.

### Workbench tabs

- `Play`: playback controls
- `Tune`: IK and edit refinement
- `Metrics`: run metrics command path
- `Audit`: run joint-order audit
- `Convert`: extension-aware URDF/XML conversion routing
- `Export`: gif/mp4 export
- `Audio`: reserved placeholder

## Developer API Example

```python
import numpy as np

from motion_player.core.editing.editor_session import EditorSession
from motion_player.core.kinematics.pose_target import PoseTarget


class MyIKBackend:
    def solve(self, current_qpos: np.ndarray, targets: dict[str, PoseTarget]) -> np.ndarray:
        solved = current_qpos.copy()
        # insert custom solve logic
        return solved


session = EditorSession(motion, ik_solver=MyIKBackend())
session.apply_eef_edit(
    frame=120,
    targets={
        "left_foot": PoseTarget(
            position_m=np.array([0.1, 0.0, 0.0], dtype=np.float64),
            orientation_wxyz=np.array([1.0, 0.0, 0.0, 0.0], dtype=np.float64),
        )
    },
)
```

## Key Design Choices

- Internal canonical state: meters + normalized quaternion.
- UI-facing controls: Euler + selectable units.
- Conversion occurs only at the boundary layer.
- Command model stays backend-agnostic through `APPLY_IK_TARGET`.
