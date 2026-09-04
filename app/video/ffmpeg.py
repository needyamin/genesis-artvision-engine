"""FFmpeg discovery and command builders."""

from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Sequence


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
) -> list[str]:
    """
    Build an FFmpeg command that reads raw RGB24 frames from stdin
    and encodes an H.264 MP4 (optionally muxing AAC audio).
    """
    cmd: list[str] = [
        ffmpeg,
        "-y",
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
        "libx264",
        "-pix_fmt",
        "yuv420p",
        "-preset",
        "veryfast",
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
