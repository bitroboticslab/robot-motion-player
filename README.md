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

## Demo

<table>
<tr>
<td width="50%" align="center"><b>Playback + Control</b></td>
<td width="50%" align="center"><b>IK Tuning</b></td>
</tr>
<tr>
<td><img src="assets/demo/playback.gif" width="100%"></td>
<td><img src="assets/demo/ik_tuning.gif" width="100%"></td>
</tr>
<tr>
<td align="center"><b>Metrics Report</b></td>
<td align="center"><b>GUI Workbench</b></td>
</tr>
<tr>
<td><img src="assets/demo/metrics.gif" width="100%"></td>
<td><img src="assets/demo/audit.gif" width="100%"></td>
</tr>
</table>

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

### Installation

```bash
# Core + MuJoCo
pip install robot-motion-player[mujoco]

# With GUI support
pip install robot-motion-player[mujoco,gui]

# All features
pip install robot-motion-player[all]
```

### Try with Example Data

```bash
# Clone repository
git clone https://github.com/bitroboticslab/robot-motion-player.git
cd robot-motion-player

# Basic playback
motion_player play \
  --motion example/standard_dataset/run1_subject5_standard.pkl \
  --robot example/robots/booster_t1/T1_23dof.xml

# GUI mode
motion_player gui \
  --motion example/standard_dataset/run1_subject5_standard.pkl \
  --robot example/robots/booster_t1/T1_23dof.xml

# Quality metrics
motion_player metrics \
  --motion example/standard_dataset/run1_subject5_standard.pkl \
  --output report.json
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
pip install -e ".[all]"
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
  author = {Lai, Junhang and contributors},
  title = {Robot Motion Player: A Visualizer and Editor for Robot Motion Data},
  howpublished = {https://github.com/bitroboticslab/robot-motion-player},
  year = {2026}
}
```

---

## Contributing

We welcome contributions! Please see [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines.

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
