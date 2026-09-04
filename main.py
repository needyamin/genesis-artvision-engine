"""Genesis Artvision Engine — entry point."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

# Ensure package root is on sys.path when run as script
ROOT = Path(__file__).resolve().parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Genesis Artvision Engine by ANSNEW TECH — offline procedural art video generator",
    )
    parser.add_argument(
        "--generate",
        action="store_true",
        help="Generate videos in CLI mode (no GUI)",
    )
    parser.add_argument("--count", type=int, default=1, help="Number of videos to generate")
    parser.add_argument("--duration", type=int, default=None, help="Duration in seconds")
    parser.add_argument("--resolution", type=str, default=None, help="e.g. 1920x1080")
    parser.add_argument("--fps", type=int, default=None, help="Frames per second")
    parser.add_argument("--seed", type=int, default=None, help="Deterministic seed")
    parser.add_argument("--engine", type=str, default=None, help="Force art engine name")
    parser.add_argument("--style", type=str, default=None, help="Force style name")
    parser.add_argument("--no-audio", action="store_true", help="Disable procedural audio")
    parser.add_argument(
        "--test",
        action="store_true",
        help="Fast low-res test render (320x180, 10fps, 3s)",
    )
    parser.add_argument("--config", type=str, default=None, help="Path to config.yaml")
    parser.add_argument("--output", type=str, default=None, help="Output directory")
    return parser


def run_cli(args: argparse.Namespace) -> int:
    from app.core.generator import VideoFactory
    from app.utils.logger import setup_logging
    from app.utils.paths import ensure_directories
    from app.utils.validation import load_config

    config = load_config(args.config)
    ensure_directories(config)
    setup_logging(config)

    if args.test:
        overrides = {
            "resolution": "320x180",
            "fps": 10,
            "duration": 3,
            "count": args.count or 1,
            "seed": args.seed,
            "engine": args.engine,
            "style": args.style,
            "audio_enabled": not args.no_audio,
            "thumbnail": True,
        }
    else:
        overrides = {
            "resolution": args.resolution,
            "fps": args.fps,
            "duration": args.duration,
            "count": args.count,
            "seed": args.seed,
            "engine": args.engine,
            "style": args.style,
            "audio_enabled": not args.no_audio,
        }
        if args.output:
            overrides["output_dir"] = args.output

    factory = VideoFactory(config)
    results = factory.generate_batch(**{k: v for k, v in overrides.items() if v is not None})
    ok = sum(1 for r in results if r.success)
    print(f"Generated {ok}/{len(results)} video(s).")
    for r in results:
        status = "OK" if r.success else "FAIL"
        print(f"  [{status}] seed={r.seed} engine={r.engine} -> {r.output_path}")
        if r.error:
            print(f"         error: {r.error}")
    return 0 if ok == len(results) else 1


def run_gui(args: argparse.Namespace) -> int:
    from app.utils.logger import setup_logging
    from app.utils.paths import ensure_directories
    from app.utils.validation import load_config

    config = load_config(args.config)
    ensure_directories(config)
    setup_logging(config)

    from PySide6.QtWidgets import QApplication
    from app.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    app.setApplicationName("Genesis Artvision Engine")
    app.setOrganizationName("ANSNEW TECH")
    window = MainWindow(config)
    window.showMaximized()
    return app.exec()


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    if args.generate or args.test:
        return run_cli(args)
    return run_gui(args)


if __name__ == "__main__":
    raise SystemExit(main())
