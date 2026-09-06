"""Caption and reproducibility sidecar exports."""

from __future__ import annotations

import copy
import hashlib
import json
import re
import textwrap
from pathlib import Path
from typing import Any

import cv2
import numpy as np

from app.core.randomizer import ProjectSpec


_SRT_TIME_RE = re.compile(
    r"(?P<start>\d{2}:\d{2}:\d{2}[,.]\d{3})\s*-->\s*"
    r"(?P<end>\d{2}:\d{2}:\d{2}[,.]\d{3})"
)


def caption_cues(plan: dict[str, Any] | None) -> list[dict[str, Any]]:
    """Normalize an editorial plan into sorted, valid caption cues."""
    cues: list[dict[str, Any]] = []
    for shot in (plan or {}).get("shots") or []:
        text = " ".join(str(shot.get("caption") or "").split())
        if not text:
            continue
        start = max(0.0, float(shot.get("caption_start", shot.get("start", 0.0))))
        end = float(shot.get("caption_end", shot.get("end", start + 1.0)))
        if end <= start:
            end = float(shot.get("end", start + 1.0))
        if end <= start:
            end = start + 1.0
        cues.append({"start": start, "end": end, "text": text})
    return sorted(cues, key=lambda cue: (cue["start"], cue["end"]))


def overlay_caption_frame(
    frame: np.ndarray,
    plan: dict[str, Any] | list[dict[str, Any]] | None,
    time_seconds: float,
) -> np.ndarray:
    """Burn the active cue into an RGB frame using the existing OpenCV stack."""
    cues = caption_cues(plan) if isinstance(plan, dict) else (plan or [])
    active = next(
        (cue for cue in cues if float(cue["start"]) <= time_seconds < float(cue["end"])),
        None,
    )
    if not active:
        return frame

    height, width = frame.shape[:2]
    font = cv2.FONT_HERSHEY_DUPLEX
    font_scale = max(0.48, min(1.35, width / 1100.0))
    thickness = max(1, int(round(font_scale * 2)))
    margin = max(12, int(width * 0.055))
    max_chars = max(16, int((width - 2 * margin) / max(7.0, 18.0 * font_scale)))
    lines = textwrap.wrap(str(active["text"]), width=max_chars, break_long_words=True)[:3]
    if not lines:
        return frame

    line_sizes = [cv2.getTextSize(line, font, font_scale, thickness)[0] for line in lines]
    line_height = max(size[1] for size in line_sizes) + max(8, int(10 * font_scale))
    pad = max(10, int(14 * font_scale))
    box_height = line_height * len(lines) + pad * 2
    bottom = height - max(12, int(height * 0.065))
    top = max(0, bottom - box_height)
    out = frame.copy()
    overlay = out.copy()
    cv2.rectangle(overlay, (margin, top), (width - margin, bottom), (0, 0, 0), -1)
    cv2.addWeighted(overlay, 0.62, out, 0.38, 0.0, dst=out)
    for index, (line, size) in enumerate(zip(lines, line_sizes)):
        x = max(margin + pad, (width - size[0]) // 2)
        y = top + pad + line_height * index + size[1]
        cv2.putText(out, line, (x, y), font, font_scale, (255, 255, 255), thickness, cv2.LINE_AA)
    return np.ascontiguousarray(out)


def inspect_caption_file(path: Path, *, expected_duration: float | None = None) -> dict[str, Any]:
    """Validate SRT timing and overlap without third-party subtitle parsers."""
    result: dict[str, Any] = {"passed": True, "errors": [], "warnings": [], "metrics": {}}
    if not path.exists():
        result["passed"] = False
        result["errors"].append("Caption file is missing")
        return result
    text = path.read_text(encoding="utf-8-sig")
    matches = list(_SRT_TIME_RE.finditer(text))
    previous_end = -1.0
    overlaps = 0
    for match in matches:
        start = _parse_timestamp(match.group("start"))
        end = _parse_timestamp(match.group("end"))
        if end <= start:
            result["errors"].append(f"Caption cue ends before it starts at {match.group('start')}")
        if start < previous_end - 0.001:
            overlaps += 1
        previous_end = max(previous_end, end)
        if expected_duration is not None and end > expected_duration + 0.05:
            result["warnings"].append(
                f"Caption cue exceeds expected duration by {end - expected_duration:.2f}s"
            )
    if not matches and text.strip():
        result["errors"].append("Caption file contains no valid SRT timing")
    if overlaps:
        result["errors"].append(f"Caption file has {overlaps} overlapping cue(s)")
    result["metrics"] = {
        "caption_cues": len(matches),
        "caption_last_end_sec": round(max(previous_end, 0.0), 3),
        "caption_overlaps": overlaps,
    }
    result["passed"] = not result["errors"]
    return result


def export_srt(video_path: Path, plan: dict[str, Any]) -> Path | None:
    cues: list[str] = []
    for number, cue in enumerate(caption_cues(plan), start=1):
        cues.append(
            f"{number}\n{_timestamp(cue['start'])} --> {_timestamp(cue['end'])}\n{cue['text']}\n"
        )
    if not cues:
        return None
    path = video_path.with_suffix(".srt")
    path.write_text("\n".join(cues), encoding="utf-8")
    return path


def export_manifest(
    video_path: Path,
    spec: ProjectSpec,
    *,
    caption_path: Path | None,
    qc: dict[str, Any] | None = None,
) -> Path:
    prompt = str(spec.params.get("user_prompt") or "")
    safe_spec = copy.deepcopy(spec.to_dict())
    if isinstance(safe_spec.get("params"), dict):
        safe_spec["params"].pop("user_prompt", None)
    payload = {
        "schema_version": 1,
        "video": video_path.name,
        "caption": caption_path.name if caption_path else None,
        "spec": safe_spec,
        "editorial_plan": spec.params.get("editorial_plan") or {},
        "ai": {
            "applied": bool(spec.params.get("ai_applied")),
            "model": spec.params.get("ai_model"),
            "prompt_sha256": hashlib.sha256(prompt.encode("utf-8")).hexdigest() if prompt else None,
        },
        "sources": spec.params.get("sources") or [],
        "delivery": spec.params.get("render_metadata") or {},
        "qc": qc or {},
    }
    path = video_path.with_suffix(".json")
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=False, default=str), encoding="utf-8")
    return path


def _timestamp(seconds: float) -> str:
    millis = max(0, int(round(float(seconds) * 1000.0)))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def _parse_timestamp(value: str) -> float:
    hours, minutes, rest = value.replace(".", ",").split(":")
    seconds, millis = rest.split(",")
    return int(hours) * 3600 + int(minutes) * 60 + int(seconds) + int(millis) / 1000.0
