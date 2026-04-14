<div align="center">
  <img src="assets/banner.png" alt="Robot Motion Player" width="100%"/>
  
  # Robot Motion Player
  
  **Visualize • Tune • Validate Robot Motion Data**
  
  [![License][license-badge]](LICENSE)
  [![Python][python-badge]](https://www.python.org/)
  
  [English](README.md) | [中文](docs/QUICKSTART_zh.md)
</div>

---

## Overview

Robot Motion Player is a standalone, cross-platform Python tool for visualizing, editing, and quality assessment of robot motion datasets. It supports AMP-format data and whole-body trajectory optimization results.

**Key capabilities:**
- 🎬 **Playback** — MuJoCo-first real-time motion playback
- 🎚️ **IK Tuning** — 6D end-effector pose adjustment
- 📊 **Metrics** — AMP-aligned quality evaluation
- ✏️ **Editing** — Keyframe-safe trajectory editing
- 🔄 **Convert** — URDF/XML format conversion
- 📤 **Export** — GIF/Video output

**Use cases:**
- AMP locomotion learning pipeline (GMR → rsl-rl-ex → training)
- Trajectory optimization visualization and debugging
- Motion data quality control before expensive GPU training
- Robot motion algorithm development

---

## Features

| Module | Features | Status |
|--------|----------|--------|
| 📽️ **Playback** | Real-time playback, keyboard control, marked frames | ✅ |
| 🎚️ **IK Tuning** | 6D target pose, unit-aware controls, Jacobian-based | ✅ |
| 📊 **Metrics** | AMP quality terms, GMR loss parity, JSON/CSV export | ✅ |
| ✏️ **Editing** | Frame/segment editing, undo/redo, cross-frame propagation | ✅ |
| 🔄 **Convert** | URDF↔XML, MuJoCo format support | ✅ |
| 📤 **Export** | GIF, MP4, frame sequences | ✅ |
| 🖥️ **GUI** | Full workbench with tabs (Play/Tune/Metrics/Audit) | ✅ |

---

## Quick Start

```bash
# Install
pip install robot-motion-player[mujoco]

# Or with GUI support
pip install robot-motion-player[mujoco,gui]

# Basic playback
motion_player play --motion walk.pkl --robot robot.xml

# GUI mode
motion_player gui --motion walk.pkl --robot robot.xml

# Quality metrics
motion_player metrics --motion walk.pkl --output report.json
```

---

## Installation

### pip (Linux/macOS/Windows)

```bash
# Core + MuJoCo
pip install robot-motion-player[mujoco]

# With optional dependencies
pip install robot-motion-player[mujoco,gui,video]
```

### From Source

```bash
git clone https://github.com/bitroboticslab/robot-motion-player.git
cd robot-motion-player
pip install -e ".[mujoco]"
```

---

## Documentation

- 📖 [Quick Start Guide](docs/QUICKSTART_en.md)
- 📖 [快速上手](docs/QUICKSTART_zh.md)
- 📖 [IK Usage Guide](docs/IK_USAGE.md)

---

## Integration

Robot Motion Player is designed to integrate with:

| Project | Role |
|---------|------|
| [GMR](https://github.com/YanjieZe/GMR) | Human-to-robot motion retargeting |
| [rsl-rl-ex](https://github.com/Mr-tooth/rsl-rl-ex) | AMP dataset building and training |
| [Pinocchio](https://github.com/stack-of-tasks/pinocchio) | IK backend (optional) |

---

## Citing

If you use Robot Motion Player in your research, please cite:

```bibtex
@software{rmp2026,
  author = {junhang and contributors},
  title = {Robot Motion Player: A Visualizer and Editor for Robot Motion Data},
  howpublished = {https://github.com/bitroboticslab/robot-motion-player},
  year = {2026}
}
```

---

## License

Apache 2.0 — see [LICENSE](LICENSE).

---

## Acknowledgments

Built upon the shoulders of:
- [Pinocchio](https://github.com/stack-of-tasks/pinocchio) — Rigid body dynamics
- [MuJoCo](https://github.com/google-deepmind/mujoco) — Physics simulation
- [GMR](https://github.com/YanjieZe/GMR) — Motion retargeting

<!-- Links -->
[license-badge]: https://img.shields.io/badge/License-Apache%202.0-blue.svg
[python-badge]: https://img.shields.io/badge/Python-3.9%2B-blue
