"""Tests for FFmpeg command building and config."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.utils.validation import load_config, parse_resolution, validate_config
from app.video.ffmpeg import build_raw_video_encode_cmd, check_ffmpeg


def test_parse_resolution():
    assert parse_resolution("1920x1080") == (1920, 1080)
    assert parse_resolution("1080X1920") == (1080, 1920)


def test_config_loads():
    cfg = load_config()
    validate_config(cfg)
    assert "engines" in cfg
    assert cfg["fps"] >= 1


def test_ffmpeg_command_shape():
    cmd = build_raw_video_encode_cmd(
        ffmpeg="ffmpeg",
        width=320,
        height=180,
        fps=10,
        output=Path("out.mp4"),
        audio_path=None,
    )
    assert "libx264" in cmd
    assert "yuv420p" in cmd
    assert "-an" in cmd
    assert "320x180" in cmd


def test_ffmpeg_available():
    ok, msg = check_ffmpeg()
    assert ok, f"FFmpeg required for full tests: {msg}"
