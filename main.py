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
    parser.add_argument(
        "--ai",
        action="store_true",
        help="Enable OpenRouter creative advisor for this run (per-video suggestions)",
    )
    parser.add_argument(
        "--curate",
        action="store_true",
        help="Expand offline education catalogs via OpenRouter (no video render)",
    )
    parser.add_argument(
        "--letters",
        type=str,
        default=None,
        help="Comma-separated letters for --curate (default: full alphabet)",
    )
    parser.add_argument(
        "--complete-az",
        action="store_true",
        help="With --engine alphabet_cartoon: teach every letter A–Z (CLI only)",
    )
    return parser


def _apply_ai_cli_flags(config: dict, *, enable_ai: bool) -> None:
    if not enable_ai:
        return
    ai = config.setdefault("ai", {})
    ai["enabled"] = True
    ai["per_video"] = True


def run_curate(args: argparse.Namespace) -> int:
    from app.ai.client import AIClientError
    from app.ai.curate import curate_letters
    from app.utils.logger import setup_logging
    from app.utils.paths import ensure_directories
    from app.utils.validation import load_config

    config = load_config(args.config)
    ensure_directories(config)
    setup_logging(config)
    config.setdefault("ai", {})["enabled"] = True

    letters = None
    if args.letters:
        letters = [c.strip().upper() for c in args.letters.split(",") if c.strip()]

    try:
        path = curate_letters(config, letters)
    except AIClientError as exc:
        print(f"Curate failed: {exc}")
        return 1
    print(f"Wrote education catalog: {path}")
    return 0


def run_cli(args: argparse.Namespace) -> int:
    from app.core.generator import VideoFactory
    from app.utils.logger import setup_logging
    from app.utils.paths import ensure_directories
    from app.utils.validation import load_config

    config = load_config(args.config)
    _apply_ai_cli_flags(config, enable_ai=args.ai)
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

    if getattr(args, "complete_az", False):
        overrides["complete_alphabet"] = True

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
    _apply_ai_cli_flags(config, enable_ai=args.ai)
    ensure_directories(config)
    setup_logging(config)

    from PySide6.QtWidgets import QApplication
    from app.gui.branding import apply_app_icon, apply_windows_app_id
    from app.gui.main_window import MainWindow

    apply_windows_app_id()
    app = QApplication(sys.argv)
    app.setApplicationName("Genesis Artvision Engine")
    app.setOrganizationName("ANSNEW TECH")
    apply_app_icon(app)
    window = MainWindow(config)
    apply_app_icon(window)
    window.showMaximized()
    return app.exec()


def main() -> int:
    from app.utils.dotenv import load_dotenv

    load_dotenv()
    parser = build_parser()
    args = parser.parse_args()
    if args.curate:
        return run_curate(args)
    if args.generate or args.test:
        return run_cli(args)
    return run_gui(args)


if __name__ == "__main__":
    raise SystemExit(main())
