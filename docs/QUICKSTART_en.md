# Quickstart (5 Minutes)

This guide is the fastest path to verify `robot-motion-player` is working.

## 1) Create and activate environment

```bash
conda create -y -n rmp python=3.11 pip
conda activate rmp
pip install -e ".[dev,mujoco]"
pip install -e ".[dev,mujoco,gui]"
pip install -e ".[video]"
```

## 2) Play one motion clip

```bash
motion_player play --motion path/to/clip.pkl --robot path/to/robot.xml

# Optional: launch the bilingual control panel (English/中文)
motion_player play --motion path/to/clip.pkl --robot path/to/robot.xml --gui

# Optional: launch standalone GUI workbench
motion_player gui --motion path/to/clip.pkl --robot path/to/robot.xml
```

`motion_player gui` now prefers an isolated panel process mode. If panel startup fails,
the runtime prints a warning and continues in MuJoCo keyboard-only mode.

## 3) Essential keys

- `Space`: play/pause
- `←/→`: prev/next frame
- `Shift+←/→`: ±10 frames
- `Ctrl+←/→`: ±100 frames
- `1..9`: switch clip
- `[` / `]`: speed -/+ 0.1x (clamped `0.1x..4.0x`)
- `S`: save edited clip
- `Q`: toggle HUD
- `Esc`: exit

When GUI is enabled (`play --gui` or `gui`), the workbench provides tabbed tools:
`Play`, `Tune`, `Metrics`, `Audit`, `Convert`, `Export`, `Audio`.
The control deck still exposes all keyboard-mapped actions
(`±1/10/100` stepping, loop/ping-pong, save, HUD toggle, speed ±, clip select, exit).
Each interactive control also provides a hover tooltip that explains the action.
The status dock groups the runtime monitor, output log, and progress display for quick
state checks while controlling playback.
The Tune tab exposes full-pose IK numeric editing (position + orientation), unit switching
(`m / cm / mm`, `rad / deg`), and step-based nudge controls for precise refinement.
Tune workflow uses a dual-level data flow: `Current Pose` (runtime read-only) and
`Target Pose` (editable fields), with explicit `Reference Frame` selection (`world` / local).
For high-resolution displays, use the GUI header `Font Size` selector (next to `Language`);
if no CJK font is available, the panel falls back to the best readable platform font.
The output menu provides a `Clear` action, and export progress advances per rendered frame.
For details, see [IK Usage Guide](IK_USAGE.md).

GUI visual QA command (desktop session):

```bash
RMP_GUI_SNAPSHOT_OUT=/tmp/rmp-monitor-card.png \
RMP_GUI_LAYOUT_REPORT_OUT=/tmp/rmp-monitor-card-layout.json \
motion_player play --motion path/to/clip.pkl --robot path/to/robot.xml --gui
```

Expected report field in `/tmp/rmp-monitor-card-layout.json`: `"fits_all_lines": true`.

## 4) Generate quality report

```bash
motion_player metrics --motion path/to/clip.pkl --output report.json
motion_player metrics --motion path/to/clip.pkl --output report.csv
```

## 5) Audit joint ordering

```bash
motion_player audit --motion path/to/clip.pkl --robot path/to/robot.xml --output joint_order.yaml
```

## 6) Convert model files

```bash
# Supported conversion
motion_player convert --input path/to/robot.urdf --output path/to/robot.xml

# XML input is routed as no-op when output is also .xml
motion_player convert --input path/to/robot.xml --output path/to/robot.xml

# XML -> URDF when external backend is installed (example)
motion_player convert --input path/to/robot.xml --output path/to/robot.urdf
```

Notes:
- `.urdf -> .xml`: supported
- `.xml -> .xml`: no-op with explicit hint
- `.xml -> .urdf`: supported via external backend (e.g., `mjcf2urdf`) or `RMP_XML_TO_URDF_CMD`

## 7) Export playback artifact

```bash
motion_player export \
  --motion path/to/clip.pkl \
  --robot path/to/robot.xml \
  --output /tmp/clip.gif \
  --fps 20
```

## Troubleshooting

- `mujoco package is required`: install extras with `pip install -e ".[mujoco]"`.
- `Isaac backend is not available`: use `--backend mujoco` for v0.1.
- `Motion path not found` / `Robot model path not found`: verify absolute file paths.
- Chinese labels show as `???`: install a CJK font and set `RMP_GUI_FONT=/absolute/path/to/font.ttf`.
- If GUI startup reports a DearPyGui font-range error, upgrade to latest patch version and keep `RMP_GUI_FONT` pointing to a valid CJK font file.
- If GUI startup warns that panel process could not start, playback is still running in viewer-only fallback mode.
