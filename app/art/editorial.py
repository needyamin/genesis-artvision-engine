"""Deterministic editorial planning shared by every visual engine."""

from __future__ import annotations

from typing import Any

from app.art.edit_brain import clamp01, ease_in_out_cubic, ease_out_cubic

_MIN_SHOT_DURATION = 0.40
_MAX_CAPTION_WORDS_PER_SECOND = 4.5


def build_editorial_plan(
    segments: list[dict[str, Any]],
    *,
    engine: str,
    duration: float,
    params: dict[str, Any],
) -> dict[str, Any]:
    """Normalize content beats into a serializable automatic edit decision list."""
    weights = params.get("segment_weights")
    if not isinstance(weights, list):
        weights = []
    transitions = {
        "kids_storybook": ("page_turn", "dissolve"),
        "how_it_works": ("dissolve", "push"),
        "trend_brief": ("flash", "push"),
    }.get(engine, ("dissolve",))
    shots: list[dict[str, Any]] = []
    for i, segment in enumerate(segments):
        try:
            weight = float(weights[i]) if i < len(weights) else float(segment.get("emphasis_weight", 1.0))
        except (TypeError, ValueError):
            weight = 1.0
        weight = max(0.5, min(2.0, weight))
        segment["emphasis_weight"] = weight
        requested_transition = str(
            segment.get("transition_intent") or segment.get("transition") or ""
        ).strip().lower().replace("-", "_")
        allowed = {"fade", "dissolve", "push", "flash", "page_turn"}
        segment["transition"] = (
            requested_transition
            if requested_transition in allowed
            else (transitions[i % len(transitions)] if i else "fade")
        )
        segment["shot_id"] = f"{engine}_{i + 1:02d}"
        shots.append(_shot_from_segment(segment, i, duration))
    plan = {
        "version": 2,
        "engine": engine,
        "duration": float(duration),
        "shots": shots,
        "safe_margin": 0.06,
        "caption_mode": str(params.get("caption_mode") or "sidecar"),
    }
    if "audio_enabled" in params:
        plan["audio_enabled"] = bool(params["audio_enabled"])
    params["editorial_plan"] = plan
    return plan


def finalize_editorial_plan(plan: dict[str, Any], segments: list[dict[str, Any]], duration: float) -> dict[str, Any]:
    """Refresh shot timings after measured narration has locked the picture."""
    shots = [_shot_from_segment(seg, i, duration) for i, seg in enumerate(segments)]
    plan["duration"] = float(duration)
    plan["shots"] = shots
    return plan


def validate_editorial_plan(plan: dict[str, Any]) -> list[str]:
    """Return actionable pre-render timeline/readability errors."""
    errors: list[str] = []
    duration = max(0.0, _number(plan.get("duration"), 0.0))
    shots = list(plan.get("shots") or [])
    if not shots:
        return ["Editorial plan contains no shots"]
    min_shot_duration = max(0.0, _number(plan.get("min_shot_duration"), _MIN_SHOT_DURATION))
    max_wps = max(0.1, _number(plan.get("max_caption_words_per_second"), _MAX_CAPTION_WORDS_PER_SECOND))
    previous_start = -1.0
    previous_end = -1.0
    previous_caption_end = -1.0
    for i, shot in enumerate(shots):
        start = _number(shot.get("start"), 0.0)
        end = _number(shot.get("end"), 0.0)
        shot_duration = end - start
        if end <= start:
            errors.append(f"Shot {i + 1} has no visible duration")
        elif shot_duration + 1e-6 < min_shot_duration:
            errors.append(
                f"Shot {i + 1} is too short ({shot_duration:.2f}s; minimum {min_shot_duration:.2f}s)"
            )
        if start + 1e-6 < previous_start:
            errors.append(f"Shot {i + 1} starts before the previous shot")
        if previous_end >= 0.0 and start + 0.02 < previous_end:
            errors.append(f"Shot {i + 1} overlaps the previous shot")
        if end > duration + 0.05:
            errors.append(f"Shot {i + 1} exceeds the project duration")
        caption = str(shot.get("caption") or "")
        if len(caption) > 500:
            errors.append(f"Shot {i + 1} caption is too long")
        if _caption_timing_applies(plan, shot):
            caption_start = _number(shot.get("caption_start"), 0.0)
            caption_end = _number(shot.get("caption_end"), 0.0)
            if caption_start < 0.0 or caption_end <= caption_start:
                errors.append(f"Shot {i + 1} caption timing must be nonzero and ordered")
            else:
                if caption_start + 0.05 < start or caption_end > end + 0.05:
                    errors.append(f"Shot {i + 1} caption timing falls outside the shot")
                if previous_caption_end >= 0.0 and caption_start + 0.02 < previous_caption_end:
                    errors.append(f"Shot {i + 1} caption overlaps the previous caption")
                caption_seconds = caption_end - caption_start
                words = len(caption.split())
                if words and words / caption_seconds > max_wps + 1e-6:
                    errors.append(
                        f"Shot {i + 1} caption is too fast "
                        f"({words / caption_seconds:.1f} words/s; maximum {max_wps:.1f})"
                    )
                previous_caption_end = max(previous_caption_end, caption_end)
        previous_start = max(previous_start, start)
        previous_end = max(previous_end, end)
    return errors


def segment_state(segment: dict[str, Any], t: float, *, easing: str = "smooth") -> dict[str, float]:
    """Return local shot progress and transition envelopes for a global 0..1 time."""
    t0 = float(segment.get("t0", 0.0))
    t1 = max(t0 + 1e-6, float(segment.get("t1", 1.0)))
    local = clamp01((t - t0) / (t1 - t0))
    key = str(easing or "smooth").lower()
    eased = local if key == "linear" else (ease_out_cubic(local) if key == "snappy" else ease_in_out_cubic(local))
    transition_fraction = max(0.04, min(0.18, float(segment.get("transition_fraction", 0.10))))
    enter = clamp01(local / transition_fraction)
    leave = clamp01((1.0 - local) / transition_fraction)
    return {"local": local, "eased": eased, "enter": ease_out_cubic(enter), "leave": ease_in_out_cubic(leave)}


def reveal_progress(
    segment: dict[str, Any],
    t: float,
    *,
    duration: float | None = None,
    easing: str = "smooth",
) -> float:
    """Return 0..1 reveal progress aligned to speech when timing is available.

    ``t`` uses the same normalized project timeline as :func:`segment_state`
    for segment records. Shot records (``start``/``end``) accept seconds.
    Untimed and audio-disabled records gracefully fall back to visual progress.
    """
    if "start" in segment or "end" in segment:
        start = _number(segment.get("start"), 0.0)
        end = max(start + 1e-6, _number(segment.get("end"), start + 1.0))
        local = clamp01((_number(t, start) - start) / (end - start))
        caption_start = _number(segment.get("caption_start"), start)
        caption_end = _number(segment.get("caption_end"), caption_start)
        if caption_end > caption_start:
            raw = clamp01((_number(t, start) - caption_start) / (caption_end - caption_start))
            return _ease_progress(raw, easing)
        return _ease_progress(local, easing)

    t0 = _number(segment.get("t0"), 0.0)
    t1 = max(t0 + 1e-6, _number(segment.get("t1"), 1.0))
    local = clamp01((_number(t, t0) - t0) / (t1 - t0))
    speech = max(0.0, _number(segment.get("speech_seconds"), 0.0))
    if speech <= 0.0:
        return _ease_progress(local, easing)
    lead = max(0.0, _number(segment.get("speech_lead"), 0.0))
    span = _number(segment.get("hold_seconds"), 0.0)
    if span <= 0.0 and duration is not None:
        span = max(0.0, float(duration) * (t1 - t0))
    if span <= 0.0:
        span = lead + speech
    elapsed = local * span
    return _ease_progress(clamp01((elapsed - lead) / speech), easing)


def _shot_from_segment(segment: dict[str, Any], index: int, duration: float) -> dict[str, Any]:
    t0 = max(0.0, min(1.0, float(segment.get("t0", 0.0))))
    t1 = max(t0, min(1.0, float(segment.get("t1", 1.0))))
    lead = max(0.0, float(segment.get("speech_lead", 0.0)))
    speech = max(0.0, float(segment.get("speech_seconds", 0.0)))
    shot_duration = max(0.0, (t1 - t0) * duration)
    transition_fraction = max(0.04, min(0.18, _number(segment.get("transition_fraction"), 0.10)))
    transition_duration = min(
        shot_duration,
        max(0.0, _number(segment.get("transition_duration"), shot_duration * transition_fraction)),
    )
    caption = str(segment.get("voice_line") or segment.get("body") or segment.get("caption") or "")
    return {
        "id": str(segment.get("shot_id") or f"shot_{index + 1:02d}"),
        "index": index,
        "start": t0 * duration,
        "end": t1 * duration,
        "transition": str(segment.get("transition") or ("fade" if index == 0 else "dissolve")),
        "transition_duration": transition_duration,
        "transition_fraction": transition_fraction,
        "camera_intent": str(
            segment.get("camera_intent")
            or segment.get("shot_purpose")
            or ("establish" if index == 0 else "develop")
        ),
        "hierarchy": str(segment.get("hierarchy") or ("hero" if index == 0 else "support")),
        "audio_cue": str(segment.get("audio_cue") or ("narration" if speech > 0.0 else "none")),
        "beat_marker": str(segment.get("beat_marker") or ("hook" if index == 0 else f"beat_{index + 1:02d}")),
        "emphasis": float(segment.get("emphasis_weight", 1.0)),
        "caption_start": min(t1 * duration, t0 * duration + lead),
        "caption_end": min(t1 * duration, t0 * duration + lead + speech),
        "caption": caption,
    }


def _caption_timing_applies(plan: dict[str, Any], shot: dict[str, Any]) -> bool:
    caption_mode = str(plan.get("caption_mode") or "").strip().lower()
    if (
        not str(shot.get("caption") or "").strip()
        or plan.get("audio_enabled") is False
        or caption_mode in {"none", "off", "disabled"}
    ):
        return False
    cue = str(shot.get("audio_cue") or "").strip().lower()
    if cue in {"none", "off", "disabled", "silent"}:
        return False
    if cue:
        return True
    start = _number(shot.get("caption_start"), 0.0)
    end = _number(shot.get("caption_end"), 0.0)
    return end > start


def _ease_progress(value: float, easing: str) -> float:
    key = str(easing or "smooth").lower()
    if key == "linear":
        return clamp01(value)
    if key == "snappy":
        return ease_out_cubic(clamp01(value))
    return ease_in_out_cubic(clamp01(value))


def _number(value: Any, default: float) -> float:
    try:
        number = float(value)
    except (TypeError, ValueError):
        return float(default)
    return number if number == number and abs(number) != float("inf") else float(default)
