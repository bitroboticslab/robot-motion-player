# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.0] - 2026-04-16

### Added
- Added startup font-size controls for GUI entry commands via `--font-size` (`small|medium|large|xlarge`) with environment fallback `RMP_GUI_FONT_SIZE`.
- Added OSS governance baseline guidance via `CLAUDE.md` and OSS-focused release checks.

### Changed
- Refactored GUI font-size handling to track per-size availability and reject unavailable selections with explicit status feedback.
- Updated OSS quickstart and IK docs to align with v0.8.0 font-size startup behavior.

### Fixed
- Fixed persistent runtime font-size issue where only `small` effectively applied when higher-size font handles were unavailable.
- Hardened font installation to fail per size instead of aborting the full font registry initialization path.
- Updated OSS docs/release tests to validate OSS-owned artifacts only.

## [0.7.9] - 2026-04-15

### Fixed
- Fixed directional font sync so startup and runtime GUI font sizing stay aligned.
- Increased the progress row depth to improve readability and reduce clipping.

## [0.7.7] - 2026-04-15

### Fixed
- Enforced GUI font authority so panel font settings remain the single source of truth.
- Tuned the Runtime State and Tool Call dock area to a 2:1 height balance for clearer status scanning.

## [0.7.6] - 2026-04-15

### Fixed
- Font-size dropdown now applies all size options reliably across callback payload variants.
- Replaced the redundant top Runtime State block with a unified top status dock.
- Reworked status display into a balanced 2-row layout:
  - Row 1: Runtime State + Tool Call
  - Row 2: Progress
- Increased default Runtime State / Tool Call panel heights to reduce routine scrolling.

## [0.7.5] - 2026-04-14

### Added
- Isolated panel runtime mode for `motion_player gui`, with viewer-path fallback behavior.
- Queue-based IPC adapters for panel command transport and monitor snapshots.
- Regression coverage for runtime fallback paths, IPC behavior, and panel process entry hardening.

### Changed
- Full GUI startup now prefers isolated panel process mode on Linux desktop sessions.

### Fixed
- DearPyGui status-dock rebuild parent-chain handling in callback paths.
- Guarded fail-open status-dock rebuild logic to avoid panel-loop aborts during rebuild errors.
