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
    parser.add_argument(
        "--edit-preset",
        choices=("draft", "standard", "master"),
        default=None,
        help="Automatic editing and delivery quality preset",
    )
    parser.add_argument(
        "--captions",
        choices=("off", "sidecar", "burn", "both"),
        default=None,
        help="Caption delivery mode",
    )
    parser.add_argument(
        "--edit-intensity",
        type=float,
        default=None,
        help="Motion intensity from 0.25 to 2.0",
    )
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
        "--prompt",
        type=str,
        default=None,
        help="Generate one video from this prompt (offline plan; add --ai for OpenRouter)",
    )
    parser.add_argument(
        "--curate",
        action="store_true",
        help="Expand offline catalogs via OpenRouter (no video render)",
    )
    parser.add_argument(
        "--youtube",
        action="store_true",
        help="After generating, upload to your connected YouTube channel",
    )
    parser.add_argument(
        "--letters",
        type=str,
        default=None,
        help="Comma-separated letters for --curate (default: full alphabet)",
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
            "edit_preset": args.edit_preset,
            "caption_mode": args.captions,
            "edit_intensity": args.edit_intensity,
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
            "edit_preset": args.edit_preset,
            "caption_mode": args.captions,
            "edit_intensity": args.edit_intensity,
            "audio_enabled": not args.no_audio,
        }
        if args.output:
            overrides["output_dir"] = args.output
    if args.prompt:
        overrides["user_prompt"] = args.prompt
        overrides["prompt_mode"] = "ai" if args.ai else "offline"
        overrides["count"] = args.count or 1
    if args.youtube:
        overrides["youtube_upload"] = True

    factory = VideoFactory(config)
    results = factory.generate_batch(**{k: v for k, v in overrides.items() if v is not None})
    ok = sum(1 for r in results if r.success)
    print(f"Generated {ok}/{len(results)} video(s).")
    for r in results:
        status = "OK" if r.success else "FAIL"
        print(f"  [{status}] seed={r.seed} engine={r.engine} -> {r.output_path}")
        if getattr(r, "youtube_url", None):
            print(f"         youtube: {r.youtube_url}")
        if getattr(r, "youtube_error", None):
            print(f"         youtube error: {r.youtube_error}")
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
    from app.gui.styles import APP_STYLE

    apply_windows_app_id()
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setApplicationName("Genesis Artvision Engine")
    app.setOrganizationName("ANSNEW TECH")
    app.setStyleSheet(APP_STYLE)
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
    if args.generate or args.test or args.prompt:
        return run_cli(args)
    return run_gui(args)


if __name__ == "__main__":
    raise SystemExit(main())
