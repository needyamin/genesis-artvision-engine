"""Fast post-render quality-control checks."""

from __future__ import annotations

import json
import re
import subprocess
import wave
from pathlib import Path
from typing import Any

import numpy as np

from app.video.captions import inspect_caption_file
from app.video.ffmpeg import FFmpegError, find_ffmpeg, find_ffprobe


def inspect_render(
    video_path: Path,
    *,
    expected_duration: float,
    audio_path: Path | None = None,
    config: dict[str, Any] | None = None,
    expected_metadata: dict[str, Any] | None = None,
    caption_path: Path | None = None,
    manifest_path: Path | None = None,
) -> dict[str, Any]:
    """Inspect a delivery while preserving the original call contract."""
    cfg = config or {}
    expected = expected_metadata or {}
    drift_limit = float(cfg.get("max_av_drift_sec", 0.35))
    report: dict[str, Any] = {"passed": True, "errors": [], "warnings": [], "metrics": {}}
    if not video_path.exists() or video_path.stat().st_size < 1024:
        report["passed"] = False
        report["errors"].append("Output video is missing or empty")
        return report

    probe = find_ffprobe()
    if probe:
        proc = subprocess.run(
            [
                probe, "-v", "error",
                "-show_entries",
                (
                    "format=duration,size,format_name:"
                    "stream=index,codec_type,codec_name,width,height,avg_frame_rate,"
                    "r_frame_rate,duration,nb_frames,sample_rate,channels"
                ),
                "-of", "json", str(video_path),
            ],
            capture_output=True,
            text=True,
            timeout=20,
            check=False,
        )
        if proc.returncode == 0:
            data = json.loads(proc.stdout or "{}")
            streams = data.get("streams") or []
            kinds = [str(s.get("codec_type")) for s in streams]
            duration = float((data.get("format") or {}).get("duration") or 0.0)
            video_stream = next((s for s in streams if s.get("codec_type") == "video"), {})
            audio_stream = next((s for s in streams if s.get("codec_type") == "audio"), {})
            fps = _rate(video_stream.get("avg_frame_rate") or video_stream.get("r_frame_rate"))
            video_duration = _float(video_stream.get("duration"))
            audio_duration = _float(audio_stream.get("duration"))
            report["metrics"].update(
                {
                    "duration_sec": duration,
                    "video_duration_sec": video_duration,
                    "audio_duration_sec": audio_duration,
                    "av_duration_drift_sec": (
                        round(abs(video_duration - audio_duration), 6)
                        if video_duration is not None and audio_duration is not None
                        else None
                    ),
                    "streams": kinds,
                    "video_codec": video_stream.get("codec_name"),
                    "audio_codec": audio_stream.get("codec_name"),
                    "width": int(video_stream.get("width") or 0),
                    "height": int(video_stream.get("height") or 0),
                    "fps": round(fps, 6),
                    "frame_count": _int(video_stream.get("nb_frames")),
                    "size_bytes": video_path.stat().st_size,
                }
            )
            if "video" not in kinds:
                report["errors"].append("Encoded file has no video stream")
            if abs(duration - expected_duration) > drift_limit:
                report["warnings"].append(
                    f"Output duration differs by {abs(duration - expected_duration):.2f}s"
                )
            if video_duration is not None and audio_duration is not None:
                if abs(video_duration - audio_duration) > drift_limit:
                    report["errors"].append(
                        f"Muxed audio/video duration drift is {abs(video_duration - audio_duration):.2f}s"
                    )
            _check_expected_stream(video_stream, fps, duration, expected, drift_limit, report)
            if bool(expected.get("audio_included")) and "audio" not in kinds:
                report["errors"].append("Expected muxed audio stream is missing")
        else:
            report["warnings"].append("ffprobe could not inspect the encoded file")
    else:
        report["warnings"].append("ffprobe unavailable; stream checks skipped")

    if caption_path is None and expected.get("caption_path"):
        caption_path = Path(str(expected["caption_path"]))
    if caption_path is not None:
        caption_report = inspect_caption_file(caption_path, expected_duration=expected_duration)
        _merge_report(report, caption_report, "Captions")

    if audio_path and audio_path.exists() and audio_path.suffix.lower() == ".wav":
        _inspect_wav(audio_path, report)
    if "audio" in report["metrics"].get("streams", []):
        _inspect_muxed_audio(video_path, cfg, report)
    _inspect_sampled_frames(video_path, expected_duration, cfg, report)

    if manifest_path is None and expected.get("manifest_path"):
        manifest_path = Path(str(expected["manifest_path"]))
    if manifest_path is not None:
        _inspect_manifest(manifest_path, video_path, caption_path, report)
    report["passed"] = not report["errors"]
    return report


def _check_expected_stream(
    stream: dict[str, Any],
    fps: float,
    duration: float,
    expected: dict[str, Any],
    drift_limit: float,
    report: dict[str, Any],
) -> None:
    width = _int(expected.get("width"))
    height = _int(expected.get("height"))
    resolution = expected.get("resolution")
    if resolution and (width is None or height is None):
        try:
            width, height = (int(part) for part in str(resolution).lower().split("x", 1))
        except (TypeError, ValueError):
            report["warnings"].append("Expected resolution metadata is invalid")
    if width is not None and int(stream.get("width") or 0) != width:
        report["errors"].append(f"Output width is not the expected {width}px")
    if height is not None and int(stream.get("height") or 0) != height:
        report["errors"].append(f"Output height is not the expected {height}px")
    expected_fps = _float(expected.get("fps"))
    if expected_fps is not None and abs(fps - expected_fps) > 0.01:
        report["errors"].append(f"Output frame rate {fps:.3f} does not match {expected_fps:.3f}")
    expected_frames = _int(expected.get("frame_count"))
    actual_frames = _int(stream.get("nb_frames"))
    if expected_frames is not None and actual_frames is not None and actual_frames != expected_frames:
        report["errors"].append(
            f"Output has {actual_frames} frames; expected exactly {expected_frames}"
        )
    metadata_duration = _float(expected.get("duration_sec"))
    if metadata_duration is not None and abs(duration - metadata_duration) > drift_limit:
        report["errors"].append("Output duration does not match render metadata")


def _inspect_wav(path: Path, report: dict[str, Any]) -> None:
    try:
        with wave.open(str(path), "rb") as wav:
            raw = wav.readframes(wav.getnframes())
            width = wav.getsampwidth()
            channels = wav.getnchannels()
            sample_rate = wav.getframerate()
            frame_count = wav.getnframes()
        if width != 2:
            report["warnings"].append("Audio QC supports 16-bit WAV only")
            return
        samples = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
        if channels > 1:
            samples = samples.reshape(-1, channels).mean(axis=1)
        peak = float(np.max(np.abs(samples))) if len(samples) else 0.0
        rms = float(np.sqrt(np.mean(samples * samples))) if len(samples) else 0.0
        report["metrics"].update(
            {
                "source_audio_duration_sec": round(frame_count / max(1, sample_rate), 6),
                "source_audio_peak_dbfs": _db(peak),
                "source_audio_rms_dbfs": _db(rms),
            }
        )
        if rms < 0.003:
            report["warnings"].append("Audio is effectively silent")
        if peak >= 0.995:
            report["warnings"].append("Audio is at risk of clipping")
    except Exception as exc:  # noqa: BLE001
        report["warnings"].append(f"Audio QC skipped: {exc}")


def _inspect_muxed_audio(path: Path, cfg: dict[str, Any], report: dict[str, Any]) -> None:
    try:
        ffmpeg = find_ffmpeg()
    except FFmpegError:
        report["warnings"].append("FFmpeg unavailable; muxed audio analysis skipped")
        return
    silence_db = float(cfg.get("silence_db", -50.0))
    silence_min = float(cfg.get("silence_min_sec", 1.0))
    filters = (
        f"ebur128=peak=true,silencedetect=noise={silence_db}dB:d={silence_min},"
        "astats=metadata=0:reset=0"
    )
    proc = subprocess.run(
        [ffmpeg, "-hide_banner", "-nostats", "-i", str(path), "-vn", "-af", filters, "-f", "null", "-"],
        capture_output=True,
        text=True,
        timeout=float(cfg.get("audio_qc_timeout_sec", 120)),
        check=False,
    )
    text = proc.stderr or ""
    integrated = _last_float(r"\bI:\s*(-?[\d.]+)\s+LUFS", text)
    true_peak = _last_float(r"\bPeak:\s*(-?[\d.]+)\s+dBFS", text)
    peak = _last_float(r"Peak level dB:\s*(-?[\d.]+)", text)
    silence = sum(float(value) for value in re.findall(r"silence_duration:\s*([\d.]+)", text))
    report["metrics"].update(
        {
            "audio_integrated_lufs": integrated,
            "audio_true_peak_dbfs": true_peak,
            "audio_peak_dbfs": peak,
            "audio_silence_sec": round(silence, 3),
        }
    )
    if proc.returncode != 0:
        report["warnings"].append("Muxed audio analysis did not complete")
    if integrated is not None and integrated < float(cfg.get("min_lufs", -35.0)):
        report["warnings"].append("Muxed audio is effectively silent")
    clipping_limit = float(cfg.get("clipping_peak_dbfs", -0.1))
    measured_peak = true_peak if true_peak is not None else peak
    if measured_peak is not None and measured_peak >= clipping_limit:
        report["warnings"].append("Muxed audio is at risk of clipping")
    duration = _float(report["metrics"].get("audio_duration_sec")) or 0.0
    if duration and silence / duration > float(cfg.get("max_silence_fraction", 0.8)):
        report["warnings"].append("Muxed audio contains excessive silence")


def _inspect_sampled_frames(
    path: Path,
    duration: float,
    cfg: dict[str, Any],
    report: dict[str, Any],
) -> None:
    try:
        ffmpeg = find_ffmpeg()
    except FFmpegError:
        return
    sample_count = max(2, int(cfg.get("frame_samples", min(24, max(6, round(duration / 2))))))
    sample_fps = sample_count / max(duration, 0.001)
    width, height = 160, 90
    proc = subprocess.run(
        [
            ffmpeg, "-v", "error", "-i", str(path), "-an",
            "-vf", f"fps={sample_fps:.8f},scale={width}:{height},format=gray",
            "-frames:v", str(sample_count), "-f", "rawvideo", "-",
        ],
        capture_output=True,
        timeout=float(cfg.get("frame_qc_timeout_sec", 120)),
        check=False,
    )
    frame_size = width * height
    count = len(proc.stdout) // frame_size
    if proc.returncode != 0 or count == 0:
        report["warnings"].append("Sampled frame analysis could not run")
        return
    frames = np.frombuffer(proc.stdout[: count * frame_size], dtype=np.uint8).reshape(count, height, width)
    black = [
        bool(float(np.mean(frame)) < 8.0 and float(np.percentile(frame, 95)) < 18.0)
        for frame in frames
    ]
    frozen = [
        bool(float(np.mean(np.abs(frames[i].astype(np.int16) - frames[i - 1]))) < 0.35)
        for i in range(1, count)
    ]
    black_fraction = sum(black) / count
    frozen_fraction = sum(frozen) / max(1, count - 1)
    report["metrics"].update(
        {
            "sampled_frames": count,
            "sampled_black_frames": sum(black),
            "sampled_frozen_transitions": sum(frozen),
            "sampled_black_fraction": round(black_fraction, 4),
            "sampled_frozen_fraction": round(frozen_fraction, 4),
        }
    )
    if black_fraction > float(cfg.get("max_black_fraction", 0.25)):
        report["warnings"].append("Excessive sampled black frames detected")
    if frozen_fraction > float(cfg.get("max_frozen_fraction", 0.75)):
        report["warnings"].append("Excessive sampled frozen frames detected")


def _inspect_manifest(
    path: Path,
    video_path: Path,
    caption_path: Path | None,
    report: dict[str, Any],
) -> None:
    if not path.exists():
        report["errors"].append("Expected manifest sidecar is missing")
        return
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        report["errors"].append(f"Manifest sidecar is invalid: {exc}")
        return
    if data.get("video") != video_path.name:
        report["errors"].append("Manifest video filename does not match output")
    expected_caption = caption_path.name if caption_path else None
    if data.get("caption") != expected_caption:
        report["errors"].append("Manifest caption filename does not match caption sidecar")
    if not isinstance(data.get("spec"), dict):
        report["errors"].append("Manifest has no project specification")
    report["metrics"]["manifest_schema_version"] = data.get("schema_version")


def _merge_report(
    target: dict[str, Any],
    source: dict[str, Any],
    label: str,
) -> None:
    target["errors"].extend(f"{label}: {message}" for message in source.get("errors") or [])
    target["warnings"].extend(f"{label}: {message}" for message in source.get("warnings") or [])
    target["metrics"].update(source.get("metrics") or {})


def _rate(value: Any) -> float:
    try:
        numerator, denominator = str(value or "0/1").split("/", 1)
        return float(numerator) / max(float(denominator), 1e-12)
    except (TypeError, ValueError):
        return 0.0


def _float(value: Any) -> float | None:
    try:
        return float(value) if value not in (None, "", "N/A") else None
    except (TypeError, ValueError):
        return None


def _int(value: Any) -> int | None:
    try:
        return int(value) if value not in (None, "", "N/A") else None
    except (TypeError, ValueError):
        return None


def _last_float(pattern: str, text: str) -> float | None:
    matches = re.findall(pattern, text)
    return float(matches[-1]) if matches else None


def _db(value: float) -> float:
    return round(float(20.0 * np.log10(max(value, 1e-9))), 2)
