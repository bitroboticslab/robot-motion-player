# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Web documentation site (planned)
- Conda package distribution (planned)

## [0.7.0] - 2026-04-14

### Highlights

First public release! Robot Motion Player is now open-source under Apache 2.0 license.

### Added

#### Core Features
- **Playback Module** - Real-time motion playback with MuJoCo backend
  - Keyboard controls (play/pause, step forward/backward)
  - Frame-by-frame navigation
  - Marked frame support
- **IK Tuning Module** - 6D end-effector pose adjustment
  - Jacobian-based inverse kinematics
  - Unit-aware controls (meters, degrees)
  - Real-time visualization
  - Cross-frame propagation
- **Metrics Module** - AMP-aligned quality evaluation
  - Joint velocity/acceleration limits
  - GMR loss parity checking
  - JSON/CSV report export
- **Editing Module** - Keyframe-safe trajectory editing
  - Frame/segment editing
  - Undo/redo support
  - Edit history tracking
- **Convert Module** - URDF/XML format conversion
  - MuJoCo XML support
  - URDF to XML conversion
- **Export Module** - GIF/Video output
  - GIF export
  - MP4 export
  - Frame sequence export
- **GUI Workbench** - Full graphical interface
  - Play/Tune/Metrics/Audit tabs
  - Timeline widget
  - Real-time visualization

#### Integration
- MuJoCo backend (primary)
- Isaac backend (experimental)
- Pinocchio IK backend (optional)

#### Documentation
- Quick Start Guide (English/Chinese)
- IK Usage Guide
- Example robot model (Booster T1)
- Sample motion data

#### Testing
- 80+ unit tests
- Pytest configuration
- CI workflow (GitHub Actions)

### Technical Details

- **Python Support**: 3.9, 3.10, 3.11, 3.12
- **Primary Backend**: MuJoCo 3.0+
- **GUI Framework**: Dear PyGui
- **License**: Apache 2.0

[unreleased]: https://github.com/bitroboticslab/robot-motion-player/compare/v0.7.0...HEAD
[0.7.0]: https://github.com/bitroboticslab/robot-motion-player/releases/tag/v0.7.0
