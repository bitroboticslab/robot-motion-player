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

"""Command-line interface for robot-motion-player.

Sub-commands
------------
play      Launch the interactive MuJoCo viewer for one or more motion files.
audit     Inspect joint ordering between a dataset and a robot model.
metrics   Compute quality metrics and export a report.
convert   Convert models with extension-aware URDF/XML routing.
export    Export playback to gif/mp4.

Examples
--------
::

    # Play a motion file on a robot
    motion_player play --motion walk.pkl --robot booster_t1/scene.xml

    # Audit joint ordering
    motion_player audit --motion walk.pkl --robot booster_t1/scene.xml

    # Export quality metrics as JSON
    motion_player metrics --motion walk.pkl --robot booster_t1/scene.xml --output report.json

    # Convert model description
    motion_player convert --input robot.urdf --output robot.xml

    # Export playback
    motion_player export --motion walk.pkl --robot booster_t1/scene.xml --output walk.gif
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

logger = logging.getLogger(__name__)


def _cmd_play(args: argparse.Namespace) -> int:
    """Launch the interactive MuJoCo viewer."""
    from motion_player.core.dataset.loader import DatasetLoader

    loader = DatasetLoader()
    motion_path = Path(args.motion)
    robot_path = Path(args.robot)
    if not motion_path.exists():
        print(f"Motion path not found: '{motion_path}'", file=sys.stderr)
        return 1
    if not robot_path.exists():
        print(f"Robot model path not found: '{robot_path}'", file=sys.stderr)
        return 1
    if motion_path.is_dir():
        motions = loader.load_folder(motion_path)
        if not motions:
            print(f"No motion files found in '{motion_path}'.", file=sys.stderr)
            return 1
    else:
        try:
            motions = [loader.load(motion_path)]
        except (FileNotFoundError, KeyError, ValueError) as exc:
            print(f"Failed to load motion file '{motion_path}': {exc}", file=sys.stderr)
            return 1

    selected_backend = args.backend
    if selected_backend == "isaac":
        from motion_player.backends.isaac_backend import IsaacBackend

        if not IsaacBackend.is_available():
            print(
                "Isaac backend is not available in this environment; "
                "falling back to MuJoCo.",
                file=sys.stderr,
            )
            selected_backend = "mujoco"
        else:
            try:
                backend = IsaacBackend()
                backend.bind_motion(motions[0])
                backend.apply_frame(0)
                print(
                    "Isaac backend frame apply succeeded in minimal mode.",
                    file=sys.stderr,
                )
                return 0
            except NotImplementedError:
                print(
                    "Isaac backend is v0.1-minimal and does not provide full "
                    "playback yet. Please use --backend mujoco.",
                    file=sys.stderr,
                )
                return 1
            except (ImportError, RuntimeError, ValueError, OSError) as exc:
                print(f"Failed to launch Isaac backend: {exc}", file=sys.stderr)
                return 1

    if selected_backend == "mujoco":
        from motion_player.cli.gui_runtime import run_backend_connected_gui

        try:
            if getattr(args, "gui", False):
                return run_backend_connected_gui(
                    motion=str(motion_path),
                    robot=str(robot_path),
                    root_joint=args.root_joint or "root",
                    backend=selected_backend,
                    require_panel=False,
                    warn_if_panel_unavailable=True,
                )

            from motion_player.backends.mujoco_backend.state_driver import MuJoCoStateDriver
            from motion_player.backends.mujoco_backend.viewer import MuJoCoViewer

            driver = MuJoCoStateDriver(
                model_path=robot_path,
                root_joint_name=args.root_joint or "root",
            )
            driver.bind_motion(motions[0])
            viewer = MuJoCoViewer(driver, motions)
            viewer.run()
        except (ImportError, RuntimeError, ValueError, OSError, FileNotFoundError, KeyError) as exc:
            print(f"Failed to launch player: {exc}", file=sys.stderr)
            return 1
    else:
        print(f"Unsupported backend '{selected_backend}'.", file=sys.stderr)
        return 1
    return 0


def _cmd_audit(args: argparse.Namespace) -> int:
    """Inspect joint ordering."""
    from motion_player.core.dataset.loader import DatasetLoader
    from motion_player.core.kinematics.joint_order_auditor import JointOrderAuditor

    loader = DatasetLoader()
    motion = loader.load(args.motion)
    auditor = JointOrderAuditor(model_path=args.robot)
    report = auditor.audit(motion)

    print(f"Dataset DOF count : {report.dataset_dof_count}")
    print(f"Model joint count : {report.model_joint_count}")
    print(f"Count mismatch    : {report.count_mismatch}")
    if report.unmatched_model:
        print(f"Unmatched (model) : {report.unmatched_model}")
    if report.unmatched_dataset:
        print(f"Unmatched (data)  : {report.unmatched_dataset}")

    if args.output:
        auditor.generate_sidecar_yaml(motion, args.output)
        print(f"Sidecar written to {args.output}")

    return 0 if report.is_ok() else 1


def _cmd_metrics(args: argparse.Namespace) -> int:
    """Compute quality metrics."""
    from motion_player.core.dataset.loader import DatasetLoader
    from motion_player.core.metrics.engine import MetricEngine

    loader = DatasetLoader()
    motion = loader.load(args.motion)
    engine = MetricEngine(motion)

    scores = engine.compute_all()
    print(f"Overall score: {engine.overall_score():.4f}  (lower is better)")
    for name, score in scores.items():
        bad = len(score.bad_frames)
        print(
            f"  {name:<35} summary={score.summary:.4f}  "
            f"bad_frames={bad}"
        )

    if args.output:
        fmt = "csv" if args.output.endswith(".csv") else "json"
        engine.export_report(args.output, fmt=fmt)
        print(f"Report written to {args.output}")

    return 0


def _cmd_convert(args: argparse.Namespace) -> int:
    """Convert model descriptions with extension-aware routing."""
    from motion_player.core.convert.router import convert_model

    input_path = Path(args.input)
    output_path = Path(args.output)

    if not input_path.exists():
        print(f"Input path not found: '{input_path}'", file=sys.stderr)
        return 1

    rc, out, err = convert_model(input_path=input_path, output_path=output_path)
    if out:
        print(out)
    if err:
        print(err, file=sys.stderr)
    return int(rc)


def _cmd_export(args: argparse.Namespace) -> int:
    """Export playback to gif/mp4 using MuJoCo offscreen renderer."""
    from motion_player.backends.mujoco_backend.state_driver import MuJoCoStateDriver
    from motion_player.core.dataset.loader import DatasetLoader
    from motion_player.core.export.video_export import export_video_with_renderer

    motion_path = Path(args.motion)
    robot_path = Path(args.robot)
    output_path = Path(args.output)
    if not motion_path.exists():
        print(f"Motion path not found: '{motion_path}'", file=sys.stderr)
        return 1
    if not robot_path.exists():
        print(f"Robot model path not found: '{robot_path}'", file=sys.stderr)
        return 1

    loader = DatasetLoader()
    try:
        motion = loader.load(motion_path)
    except (FileNotFoundError, KeyError, ValueError) as exc:
        print(f"Failed to load motion file '{motion_path}': {exc}", file=sys.stderr)
        return 1

    try:
        import mujoco  # type: ignore[import]
    except ImportError:
        print("mujoco package is required for export.", file=sys.stderr)
        return 1

    try:
        driver = MuJoCoStateDriver(
            model_path=robot_path,
            root_joint_name=args.root_joint or "root",
        )
        driver.bind_motion(motion)
        offwidth = int(driver.model.vis.global_.offwidth)
        offheight = int(driver.model.vis.global_.offheight)
        width = min(int(args.width), offwidth)
        height = min(int(args.height), offheight)
        if width != int(args.width) or height != int(args.height):
            print(
                f"Requested export size {args.width}x{args.height} exceeds model offscreen "
                f"framebuffer {offwidth}x{offheight}; using {width}x{height}.",
                file=sys.stderr,
            )
        renderer = mujoco.Renderer(driver.model, width=width, height=height)
        try:
            out = export_video_with_renderer(
                num_frames=motion.num_frames,
                src_fps=motion.fps,
                out_fps=float(args.fps),
                output_path=output_path,
                render_frame=lambda frame_idx: _render_frame(
                    renderer=renderer,
                    driver=driver,
                    frame_idx=frame_idx,
                ),
            )
        finally:
            if hasattr(renderer, "close"):
                renderer.close()
        print(f"Export written to {out}")
        return 0
    except (ImportError, RuntimeError, ValueError, OSError) as exc:
        print(f"Failed to export playback: {exc}", file=sys.stderr)
        return 1


def _cmd_gui(args: argparse.Namespace) -> int:
    """Launch backend-connected full GUI runtime."""
    from motion_player.cli.gui_runtime import run_backend_connected_gui

    if not args.motion or not args.robot:
        print(
            "Full GUI mode requires both --motion and --robot paths.",
            file=sys.stderr,
        )
        return 1

    try:
        return run_backend_connected_gui(
            motion=str(args.motion),
            robot=str(args.robot),
            root_joint=args.root_joint or "root",
            backend=args.backend,
            require_panel=True,
        )
    except (ImportError, RuntimeError, ValueError, OSError, FileNotFoundError, KeyError) as exc:
        print(f"Failed to launch full GUI mode: {exc}", file=sys.stderr)
        return 1


def _render_frame(*, renderer: object, driver: object, frame_idx: int):
    driver.apply_frame(frame_idx)
    renderer.update_scene(driver.data)
    return renderer.render()


def build_parser() -> argparse.ArgumentParser:
    """Build CLI parser for testing and runtime entry points."""
    parser = argparse.ArgumentParser(
        prog="motion_player",
        description=(
            "robot-motion-player — cross-platform AMP motion dataset "
            "visualiser & editor."
        ),
    )
    parser.add_argument(
        "--version",
        action="version",
        version="%(prog)s " + _get_version(),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # --- play ---
    p_play = subparsers.add_parser("play", help="Launch interactive MuJoCo viewer.")
    p_play.add_argument("--motion", required=True, help="Path to motion file or folder.")
    p_play.add_argument("--robot", required=True, help="Path to MJCF .xml file.")
    p_play.add_argument("--mapping", default=None, help="Path to mapping.yaml.")
    p_play.add_argument("--root-joint", default="root", help="Name of the root free joint.")
    p_play.add_argument(
        "--gui",
        action="store_true",
        help="Launch beginner-friendly control panel window.",
    )
    p_play.add_argument(
        "--backend",
        choices=["mujoco", "isaac"],
        default="mujoco",
        help=(
            "Rendering backend. 'isaac' is minimal in v0.1 and "
            "falls back to MuJoCo if unavailable."
        ),
    )

    # --- audit ---
    p_audit = subparsers.add_parser("audit", help="Inspect joint ordering.")
    p_audit.add_argument("--motion", required=True, help="Path to motion file.")
    p_audit.add_argument("--robot", required=True, help="Path to MJCF .xml file.")
    p_audit.add_argument("--output", default=None, help="Write sidecar YAML to this path.")

    # --- metrics ---
    p_metrics = subparsers.add_parser("metrics", help="Compute quality metrics.")
    p_metrics.add_argument("--motion", required=True, help="Path to motion file.")
    p_metrics.add_argument("--robot", default=None, help="Path to MJCF .xml file (optional).")
    p_metrics.add_argument(
        "--output",
        default=None,
        help="Write report to this path (.json or .csv).",
    )

    # --- convert ---
    p_conv = subparsers.add_parser(
        "convert",
        help="Convert model descriptions between URDF/XML with extension-aware routing.",
    )
    p_conv.add_argument("--input", required=True, help="Input model path (.urdf or .xml).")
    p_conv.add_argument("--output", required=True, help="Output model path (.xml or .urdf).")

    # --- export ---
    p_export = subparsers.add_parser("export", help="Export playback to mp4/gif.")
    p_export.add_argument("--motion", required=True, help="Path to motion file.")
    p_export.add_argument("--robot", required=True, help="Path to MJCF .xml file.")
    p_export.add_argument("--output", required=True, help="Output path (.mp4 or .gif).")
    p_export.add_argument("--fps", type=float, default=30.0, help="Output FPS.")
    p_export.add_argument("--root-joint", default="root", help="Name of the root free joint.")
    p_export.add_argument("--width", type=int, default=640, help="Output width in pixels.")
    p_export.add_argument("--height", type=int, default=480, help="Output height in pixels.")

    # --- gui ---
    p_gui = subparsers.add_parser("gui", help="Launch full-feature GUI workbench.")
    p_gui.add_argument("--motion", default=None, help="Optional default motion path for GUI tool tabs.")
    p_gui.add_argument("--robot", default=None, help="Optional default robot path for GUI tool tabs.")
    p_gui.add_argument("--root-joint", default="root", help="Name of the root free joint.")
    p_gui.add_argument(
        "--backend",
        choices=["mujoco"],
        default="mujoco",
        help="Rendering backend for full GUI mode.",
    )

    return parser


def main(argv: list[str] | None = None) -> int:
    """Entry point for the ``motion_player`` CLI."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(levelname)s %(name)s: %(message)s",
    )
    parser = build_parser()
    args = parser.parse_args(argv)

    dispatch = {
        "play": _cmd_play,
        "audit": _cmd_audit,
        "metrics": _cmd_metrics,
        "convert": _cmd_convert,
        "export": _cmd_export,
        "gui": _cmd_gui,
    }
    return dispatch[args.command](args)


def _get_version() -> str:
    try:
        from importlib.metadata import PackageNotFoundError, version

        return version("robot-motion-player")
    except PackageNotFoundError:
        logger.debug("Package metadata not found, using dev version.")
        return "0.7.0.dev0"


if __name__ == "__main__":
    sys.exit(main())
