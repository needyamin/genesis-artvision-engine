"""Strict JSON schema for AI creative direction."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass, field
from typing import Any

from app.core.randomizer import ENGINE_PARAM_SPECS, KIDS_ENGINES, TOPIC_BRIEF_ENGINES

SCHEMA_VERSION = 9

_JSON_FENCE = re.compile(r"```(?:json)?\s*([\s\S]*?)```", re.IGNORECASE)

VISUAL_PARAM_SPECS: dict[str, Any] = {
    "glow": (0.0, 1.0),
    "blur": (0.0, 1.5),
    "contrast": (0.5, 1.5),
    "animation_speed": (0.15, 2.0),
    "easing": ["smooth", "snappy", "floaty"],
    "camera_feel": ["static", "drift", "pulse"],
    "grade": ["soft", "vivid", "pastel", "cinematic"],
}

EASING_CHOICES = ("smooth", "snappy", "floaty")
CAMERA_CHOICES = ("static", "drift", "pulse")
GRADE_CHOICES = ("soft", "vivid", "pastel", "cinematic")
SCALE_CHOICES = ("major", "pentatonic", "soft_minor")


@dataclass
class CreativeDirection:
    """Validated creative direction used to enrich a ProjectSpec offline."""

    schema_version: int = SCHEMA_VERSION
    style: str | None = None
    param_overrides: dict[str, Any] = field(default_factory=dict)
    palette_colors: list[list[float]] | None = None
    palette_name: str | None = None
    lesson_theme: str | None = None
    focus_letters: list[str] = field(default_factory=list)
    focus_words: list[str] = field(default_factory=list)
    voice_lines: list[str] = field(default_factory=list)
    fun_facts: list[str] = field(default_factory=list)
    segment_plan: list[dict[str, Any]] = field(default_factory=list)
    segment_weights: list[float] = field(default_factory=list)
    glow: float | None = None
    blur: float | None = None
    contrast: float | None = None
    animation_speed: float | None = None
    easing: str | None = None
    camera_feel: str | None = None
    grade: str | None = None
    audio_profile: dict[str, Any] = field(default_factory=dict)
    visual_beats: list[dict[str, Any]] = field(default_factory=list)
    title: str | None = None
    metrics: list[dict[str, str]] = field(default_factory=list)
    notes: str = ""

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> CreativeDirection:
        if not data or not isinstance(data, dict):
            return cls()
        return cls(
            schema_version=int(data.get("schema_version", SCHEMA_VERSION)),
            style=_opt_str(data.get("style")),
            param_overrides=dict(data.get("param_overrides") or {}),
            palette_colors=_parse_palette(data.get("palette_colors") or data.get("palette_hint")),
            palette_name=_opt_str(data.get("palette_name")),
            lesson_theme=_opt_str(data.get("lesson_theme")),
            focus_letters=_str_list(data.get("focus_letters")),
            focus_words=_str_list(data.get("focus_words"), upper=True),
            voice_lines=_str_list(data.get("voice_lines")),
            fun_facts=_str_list(data.get("fun_facts")),
            segment_plan=_seg_list(data.get("segment_plan")),
            segment_weights=_float_list(data.get("segment_weights")),
            glow=_opt_float(data.get("glow")),
            blur=_opt_float(data.get("blur")),
            contrast=_opt_float(data.get("contrast")),
            animation_speed=_opt_float(data.get("animation_speed")),
            easing=_opt_str(data.get("easing")),
            camera_feel=_opt_str(data.get("camera_feel")),
            grade=_opt_str(data.get("grade")),
            audio_profile=dict(data.get("audio_profile") or {}),
            visual_beats=_seg_list(data.get("visual_beats") or data.get("beats")),
            title=_opt_str(data.get("title")),
            metrics=_metric_list(data.get("metrics")),
            notes=str(data.get("notes") or ""),
        )


def extract_json_object(text: str) -> dict[str, Any]:
    """Parse a JSON object from model output (raw or fenced)."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty model response")
    fence = _JSON_FENCE.search(text)
    if fence:
        text = fence.group(1).strip()
    start = text.find("{")
    end = text.rfind("}")
    if start < 0 or end <= start:
        raise ValueError("No JSON object in model response")
    return json.loads(text[start : end + 1])


def parse_creative_direction(
    raw: str | dict[str, Any],
    *,
    engine: str,
    style: str | None = None,
) -> CreativeDirection:
    """Parse and validate/clamp creative direction for a given engine (+ optional locked style)."""
    if isinstance(raw, str):
        data = extract_json_object(raw)
    else:
        data = dict(raw)
    direction = CreativeDirection.from_dict(data)
    direction.param_overrides = clamp_param_overrides(engine, direction.param_overrides)
    direction.focus_letters = [
        c.upper() for c in direction.focus_letters if len(c) == 1 and c.isalnum()
    ][:12]
    direction.focus_words = [w for w in direction.focus_words if w][:24]
    direction.voice_lines = [v for v in direction.voice_lines if v][:24]
    direction.fun_facts = [f for f in direction.fun_facts if f][:24]
    direction.segment_weights = _clamp_weights(direction.segment_weights)
    direction.audio_profile = clamp_audio_profile(direction.audio_profile)
    plan = clamp_visual_beats(direction.segment_plan)
    beats = clamp_visual_beats(direction.visual_beats)
    merged = _merge_beats(plan, beats)
    direction.visual_beats = merged
    direction.segment_plan = [dict(b) for b in merged]
    if direction.title:
        direction.title = direction.title[:48]
    direction.metrics = _metric_list(direction.metrics)
    direction.glow = _clamp_opt(direction.glow, 0.0, 1.0)
    direction.blur = _clamp_opt(direction.blur, 0.0, 1.5)
    direction.contrast = _clamp_opt(direction.contrast, 0.5, 1.5)
    direction.animation_speed = _clamp_opt(direction.animation_speed, 0.15, 2.0)
    direction.easing = _choice(direction.easing, EASING_CHOICES)
    direction.camera_feel = _choice(direction.camera_feel, CAMERA_CHOICES)
    direction.grade = _choice(direction.grade, GRADE_CHOICES)
    if direction.palette_colors:
        cleaned: list[list[float]] = []
        for row in direction.palette_colors[:8]:
            if len(row) >= 3:
                cleaned.append(
                    [
                        float(max(0.0, min(1.0, row[0]))),
                        float(max(0.0, min(1.0, row[1]))),
                        float(max(0.0, min(1.0, row[2]))),
                    ]
                )
        direction.palette_colors = cleaned or None
    direction = sanitize_direction_for_engine(direction, engine)
    if style:
        direction.style = str(style)
    return direction


def sanitize_direction_for_engine(direction: CreativeDirection, engine: str) -> CreativeDirection:
    """Keep kids/education fields only for engines the user actually chose.

    Procedural art and the science explainer must not receive article cards,
    titles, or extra pictures — those engines paint the whole frame.
    """
    if engine in KIDS_ENGINES:
        direction.focus_letters = []
        return direction
    if engine in TOPIC_BRIEF_ENGINES:
        direction.lesson_theme = None
        direction.focus_letters = []
        direction.focus_words = []
        return direction
    direction.lesson_theme = None
    direction.focus_letters = []
    direction.focus_words = []
    direction.voice_lines = []
    direction.title = None
    direction.visual_beats = []
    direction.segment_plan = []
    direction.metrics = []
    direction.fun_facts = []
    direction.segment_weights = []
    direction.audio_profile = dict(direction.audio_profile or {})
    return direction


def clamp_param_overrides(engine: str, overrides: dict[str, Any]) -> dict[str, Any]:
    """Keep known engine + visual-quality keys and clamp numeric ranges."""
    specs = {**VISUAL_PARAM_SPECS, **ENGINE_PARAM_SPECS.get(engine, {})}
    out: dict[str, Any] = {}
    for key, value in (overrides or {}).items():
        if key not in specs:
            continue
        spec = specs[key]
        if isinstance(spec, list):
            choices = list(spec)
            if value in choices:
                out[key] = value
            elif choices and isinstance(choices[0], str) and str(value) in choices:
                out[key] = str(value)
            elif choices and isinstance(choices[0], bool) and bool(value) in choices:
                out[key] = bool(value)
            continue
        lo, hi = spec
        try:
            num = float(value)
        except (TypeError, ValueError):
            continue
        num = max(float(lo), min(float(hi), num))
        if isinstance(lo, int) and isinstance(hi, int):
            out[key] = int(round(num))
        else:
            out[key] = num
    return out


_BEAT_STR_KEYS = (
    "letter",
    "word",
    "voice_line",
    "fact",
    "line",
    "phonics",
    "image_brief",
    "image",
    "overlay_text",
    "caption",
    "title",
    "headline",
    "body",
    "phase",
    "data_point",
    "shape",
    "motif",
    "image_path",
    "shot_purpose",
    "hierarchy",
    "transition_intent",
    "audio_cue",
)
_BEAT_STR_LIMITS = {
    "image_brief": 120,
    "image": 120,
    "overlay_text": 48,
    "caption": 72,
    "title": 48,
    "headline": 48,
    "body": 140,
    "phase": 24,
    "data_point": 48,
    "voice_line": 160,
    "fact": 120,
    "line": 64,
    "phonics": 64,
    "word": 24,
    "letter": 2,
    "shape": 24,
    "motif": 24,
    "image_path": 260,
    "shot_purpose": 48,
    "hierarchy": 24,
    "transition_intent": 32,
    "audio_cue": 32,
}


def clamp_visual_beats(raw: Any) -> list[dict[str, Any]]:
    """Keep only drawable/speakable fields the offline illustrator can use."""
    if not isinstance(raw, list):
        return []
    out: list[dict[str, Any]] = []
    for item in raw[:16]:
        if not isinstance(item, dict):
            continue
        beat: dict[str, Any] = {}
        for key in _BEAT_STR_KEYS:
            if key not in item or item[key] is None:
                continue
            text = str(item[key]).strip()
            if not text:
                continue
            limit = _BEAT_STR_LIMITS.get(key, 80)
            beat[key] = text[:limit]
        if beat.get("image") and not beat.get("image_brief"):
            beat["image_brief"] = beat["image"]
        beat.pop("image", None)
        if beat.get("word"):
            beat["word"] = beat["word"].upper()
        if beat.get("letter"):
            beat["letter"] = beat["letter"].upper()[:1]
        for num_key in ("t0", "t1"):
            if num_key in item:
                try:
                    beat[num_key] = float(max(0.0, min(1.0, float(item[num_key]))))
                except (TypeError, ValueError):
                    pass
        if "emphasis" in item or "emphasis_weight" in item:
            try:
                emphasis = item.get("emphasis", item.get("emphasis_weight", 1.0))
                beat["emphasis_weight"] = float(max(0.5, min(2.0, float(emphasis))))
            except (TypeError, ValueError):
                pass
        if beat:
            out.append(beat)
    return out


def _merge_beats(plan: list[dict[str, Any]], beats: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Index-merge segment_plan lesson fields with visual_beats image/text."""
    if not beats:
        return list(plan)
    if not plan:
        return list(beats)
    n = max(len(plan), len(beats))
    merged: list[dict[str, Any]] = []
    for i in range(n):
        row: dict[str, Any] = {}
        if i < len(plan):
            row.update(plan[i])
        if i < len(beats):
            row.update(beats[i])
        merged.append(row)
    return merged


def clamp_audio_profile(raw: Any) -> dict[str, Any]:
    """Validate soundtrack knobs used by offline procedural audio."""
    if not isinstance(raw, dict):
        return {}
    out: dict[str, Any] = {}
    tempo = _clamp_opt(raw.get("tempo_bpm"), 40.0, 180.0)
    if tempo is not None:
        out["tempo_bpm"] = tempo
    energy = _clamp_opt(raw.get("energy"), 0.0, 1.0)
    if energy is not None:
        out["energy"] = energy
    scale = _choice(_opt_str(raw.get("scale")), SCALE_CHOICES)
    if scale:
        out["scale"] = scale
    brightness = _clamp_opt(raw.get("pad_brightness"), 0.0, 1.0)
    if brightness is not None:
        out["pad_brightness"] = brightness
    density = _clamp_opt(raw.get("chime_density"), 0.0, 1.0)
    if density is not None:
        out["chime_density"] = density
    rate = _clamp_opt(raw.get("voice_rate"), 0.6, 1.4)
    if rate is not None:
        out["voice_rate"] = rate
    pitch = _clamp_opt(raw.get("voice_pitch"), 0.7, 1.5)
    if pitch is not None:
        out["voice_pitch"] = pitch
    return out


def _metric_list(value: Any) -> list[dict[str, str]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, str]] = []
    for item in value[:6]:
        if isinstance(item, dict):
            label = str(item.get("label") or "").strip()[:32]
            val = str(item.get("val") or item.get("value") or "").strip()[:24]
            unit = str(item.get("unit") or "").strip()[:32]
            if label or val:
                out.append({"label": label, "val": val, "unit": unit})
        elif isinstance(item, str) and item.strip():
            out.append({"label": item.strip()[:32], "val": "", "unit": ""})
    return out


def _opt_str(value: Any) -> str | None:
    if value is None:
        return None
    s = str(value).strip()
    return s or None


def _opt_float(value: Any) -> float | None:
    if value is None or value == "":
        return None
    try:
        return float(value)
    except (TypeError, ValueError):
        return None


def _clamp_opt(value: float | None, lo: float, hi: float) -> float | None:
    if value is None:
        return None
    return max(lo, min(hi, float(value)))


def _choice(value: str | None, allowed: tuple[str, ...]) -> str | None:
    if not value:
        return None
    key = str(value).strip().lower()
    return key if key in allowed else None


def _str_list(value: Any, *, upper: bool = False) -> list[str]:
    if not isinstance(value, list):
        return []
    out: list[str] = []
    for item in value:
        s = str(item).strip()
        if not s:
            continue
        out.append(s.upper() if upper else s)
    return out


def _float_list(value: Any) -> list[float]:
    if not isinstance(value, list):
        return []
    out: list[float] = []
    for item in value[:16]:
        try:
            out.append(float(item))
        except (TypeError, ValueError):
            continue
    return out


def _clamp_weights(weights: list[float]) -> list[float]:
    if not weights:
        return []
    return [max(0.05, min(20.0, w)) for w in weights[:16]]


def _seg_list(value: Any) -> list[dict[str, Any]]:
    if not isinstance(value, list):
        return []
    out: list[dict[str, Any]] = []
    for item in value[:16]:
        if isinstance(item, dict):
            out.append(dict(item))
    return out


def _parse_palette(value: Any) -> list[list[float]] | None:
    if value is None:
        return None
    if isinstance(value, str):
        return None  # name-only hints ignored at color level
    if not isinstance(value, list) or not value:
        return None
    # Single RGB as 0-255 or 0-1
    if value and not isinstance(value[0], (list, tuple)):
        if len(value) >= 3 and all(isinstance(x, (int, float)) for x in value[:3]):
            return [_normalize_rgb(list(value[:3]))]
        return None
    rows: list[list[float]] = []
    for row in value:
        if isinstance(row, (list, tuple)) and len(row) >= 3:
            rows.append(_normalize_rgb(list(row[:3])))
    return rows or None


def _normalize_rgb(row: list[Any]) -> list[float]:
    vals = [float(x) for x in row[:3]]
    if any(v > 1.0 for v in vals):
        vals = [max(0.0, min(255.0, v)) / 255.0 for v in vals]
    else:
        vals = [max(0.0, min(1.0, v)) for v in vals]
    return vals
