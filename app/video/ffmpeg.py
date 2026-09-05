"""FFmpeg discovery and command builders."""

from __future__ import annotations

import os
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path
from typing import Sequence

from app.utils.logger import get_logger

logger = get_logger("ffmpeg")


class FFmpegError(RuntimeError):
    """Raised when FFmpeg is missing or a command fails."""


def find_ffmpeg() -> str:
    """Locate the ffmpeg executable on PATH or common Windows install paths."""
    found = shutil.which("ffmpeg")
    if found:
        return found

    candidates = [
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Links" / "ffmpeg.exe",
        Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "WinGet" / "Packages",
        Path("C:/ffmpeg/bin/ffmpeg.exe"),
        Path("C:/Program Files/ffmpeg/bin/ffmpeg.exe"),
        Path(os.environ.get("USERPROFILE", "")) / "scoop" / "shims" / "ffmpeg.exe",
    ]
    for c in candidates:
        if c.is_file():
            return str(c)
        if c.is_dir():
            # Search winget package folder
            for match in c.rglob("ffmpeg.exe"):
                return str(match)
    raise FFmpegError(
        "FFmpeg was not found. Install FFmpeg and ensure it is on PATH, "
        "then restart the application."
    )


def find_ffprobe() -> str | None:
    ff = shutil.which("ffprobe")
    if ff:
        return ff
    try:
        ffmpeg = Path(find_ffmpeg())
        probe = ffmpeg.with_name("ffprobe.exe" if os.name == "nt" else "ffprobe")
        if probe.exists():
            return str(probe)
    except FFmpegError:
        return None
    return None


def check_ffmpeg() -> tuple[bool, str]:
    """Return (ok, message) describing FFmpeg availability."""
    try:
        path = find_ffmpeg()
        proc = subprocess.run(
            [path, "-version"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        first = (proc.stdout or proc.stderr or "").splitlines()[:1]
        return True, f"{path} ({first[0] if first else 'ok'})"
    except Exception as exc:  # noqa: BLE001
        return False, str(exc)


def _listed_h264_encoders(ffmpeg: str) -> set[str]:
    try:
        proc = subprocess.run(
            [ffmpeg, "-hide_banner", "-encoders"],
            capture_output=True,
            timeout=8,
            check=False,
        )
        text = (proc.stdout or b"").decode("utf-8", errors="replace")
    except Exception:
        return {"libx264"}
    found = {"libx264"} if "libx264" in text else set()
    for name in ("h264_qsv", "h264_nvenc", "h264_amf"):
        if name in text:
            found.add(name)
    return found


def _probe_encoder(ffmpeg: str, codec: str, extra: Sequence[str]) -> bool:
    """Encode two tiny raw frames to confirm this H.264 encoder actually works."""
    w, h, frames = 128, 64, 2
    raw = bytes(w * h * 3 * frames)
    cmd = [
        ffmpeg,
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{w}x{h}",
        "-r",
        "10",
        "-i",
        "-",
        "-frames:v",
        str(frames),
        "-c:v",
        codec,
        *list(extra),
        "-f",
        "null",
        "-",
    ]
    try:
        proc = subprocess.run(
            cmd,
            input=raw,
            capture_output=True,
            timeout=6,
            check=False,
        )
        return proc.returncode == 0
    except Exception:
        return False


@lru_cache(maxsize=4)
def detect_h264_encoder(ffmpeg: str, *, hardware: bool = True) -> tuple[str, tuple[str, ...], str]:
    """
    Pick the fastest working H.264 encoder.

    Returns (codec, extra_args, label). Result is cached per ffmpeg path.
    """
    software = (
        "libx264",
        (
            "-pix_fmt",
            "yuv420p",
            "-preset",
            "veryfast",
            "-tune",
            "animation",
            "-threads",
            "0",
        ),
        "CPU x264",
    )
    if not hardware:
        return software

    available = _listed_h264_encoders(ffmpeg)
    candidates: list[tuple[str, tuple[str, ...], str]] = [
        (
            "h264_qsv",
            ("-vf", "format=nv12", "-preset", "veryfast", "-look_ahead", "0"),
            "Intel Quick Sync",
        ),
        (
            "h264_qsv",
            ("-pix_fmt", "nv12", "-preset", "veryfast", "-look_ahead", "0"),
            "Intel Quick Sync",
        ),
        (
            "h264_nvenc",
            ("-pix_fmt", "yuv420p", "-preset", "p4", "-tune", "ll", "-rc", "vbr"),
            "NVIDIA NVENC",
        ),
        (
            "h264_amf",
            ("-pix_fmt", "yuv420p", "-quality", "speed"),
            "AMD AMF",
        ),
    ]
    for codec, extra, label in candidates:
        if codec not in available:
            continue
        if _probe_encoder(ffmpeg, codec, extra):
            logger.info("Hardware encoder ready: %s (%s)", label, codec)
            return codec, extra, label
        logger.debug("Encoder listed but probe failed: %s", codec)
    logger.info("Using software libx264 (no working GPU encoder)")
    return software


def build_raw_video_encode_cmd(
    *,
    ffmpeg: str,
    width: int,
    height: int,
    fps: int,
    output: Path,
    audio_path: Path | None = None,
    video_bitrate: str = "8M",
    audio_bitrate: str = "192k",
    video_codec: str = "libx264",
    codec_args: Sequence[str] | None = None,
) -> list[str]:
    """
    Build an FFmpeg command that reads raw RGB24 frames from stdin
    and encodes an H.264 MP4 (optionally muxing AAC audio).
    """
    extra = list(codec_args) if codec_args is not None else [
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
        "-tune",
        "animation",
        "-threads",
        "0",
    ]
    cmd: list[str] = [
        ffmpeg,
        "-y",
        "-hide_banner",
        "-thread_queue_size",
        "512",
        "-f",
        "rawvideo",
        "-vcodec",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{width}x{height}",
        "-r",
        str(fps),
        "-i",
        "-",
    ]
    if audio_path is not None and audio_path.exists():
        cmd += ["-i", str(audio_path)]
    cmd += [
        "-c:v",
        video_codec,
        *extra,
        "-b:v",
        video_bitrate,
        "-movflags",
        "+faststart",
    ]
    if audio_path is not None and audio_path.exists():
        cmd += ["-c:a", "aac", "-b:a", audio_bitrate, "-shortest"]
    else:
        cmd += ["-an"]
    cmd.append(str(output))
    return cmd


def run_ffmpeg(cmd: Sequence[str], *, stdin_data: bytes | None = None) -> None:
    """Execute an FFmpeg command, raising FFmpegError on failure."""
    proc = subprocess.run(
        list(cmd),
        input=stdin_data,
        capture_output=True,
        check=False,
    )
    if proc.returncode != 0:
        err = (proc.stderr or b"").decode("utf-8", errors="replace")[-2000:]
        raise FFmpegError(f"FFmpeg failed ({proc.returncode}): {err}")


def extract_thumbnail(
    video_path: Path,
    thumb_path: Path,
    *,
    time_seconds: float | None = None,
) -> None:
    """Extract a JPEG thumbnail from a video around the midpoint."""
    ffmpeg = find_ffmpeg()
    ss = f"{max(0.0, time_seconds or 0.0):.3f}"
    cmd = [
        ffmpeg,
        "-y",
        "-ss",
        ss,
        "-i",
        str(video_path),
        "-frames:v",
        "1",
        "-q:v",
        "3",
        str(thumb_path),
    ]
    run_ffmpeg(cmd)
