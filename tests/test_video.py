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
    assert "veryfast" in cmd
    assert "-thread_queue_size" in cmd


def test_resolve_workers_uses_many_cores():
    from app.utils.performance import resolve_workers

    n = resolve_workers({"performance": {"workers": "auto"}}, width=1920, height=1080)
    assert n >= 2
    capped = resolve_workers({"performance": {"workers": 99}}, width=3840, height=2160)
    assert capped <= 8


def test_ffmpeg_command_can_use_qsv_args():
    cmd = build_raw_video_encode_cmd(
        ffmpeg="ffmpeg",
        width=1920,
        height=1080,
        fps=30,
        output=Path("out.mp4"),
        audio_path=None,
        video_codec="h264_qsv",
        codec_args=("-pix_fmt", "nv12", "-preset", "veryfast"),
    )
    assert "h264_qsv" in cmd
    assert "nv12" in cmd


def test_ffmpeg_available():
    ok, msg = check_ffmpeg()
    assert ok, f"FFmpeg required for full tests: {msg}"
