"""Creative advisor: optional OpenRouter call + disk cache + ProjectSpec apply."""

from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Any, Callable

import numpy as np

from app.ai.client import AIClientError, chat_completion, has_api_key
from app.ai.prompts import SYSTEM_ADVISOR, advisor_user_prompt
from app.ai.schemas import SCHEMA_VERSION, CreativeDirection, parse_creative_direction
from app.art.styles import sample_style_multiplier
from app.utils.logger import get_logger
from app.utils.paths import resolve_path

logger = get_logger("ai.advisor")

ProgressFn = Callable[[dict[str, Any]], None]


def _cache_dir(config: dict[str, Any]) -> Path:
    ai = config.get("ai") or {}
    return resolve_path(ai.get("cache_dir") or "./data/ai_cache")


def _cache_key(spec: Any, model: str) -> str:
    raw = f"{SCHEMA_VERSION}|{spec.seed}|{spec.engine}|{spec.style}|{model}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:32]


def _cache_path(config: dict[str, Any], key: str) -> Path:
    return _cache_dir(config) / f"{key}.json"


def load_cached_direction(config: dict[str, Any], key: str) -> CreativeDirection | None:
    path = _cache_path(config, key)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return CreativeDirection.from_dict(data.get("direction") or data)
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        logger.warning("Corrupt AI cache %s: %s", path, exc)
        return None


def save_cached_direction(
    config: dict[str, Any],
    key: str,
    direction: CreativeDirection,
    *,
    meta: dict[str, Any] | None = None,
) -> None:
    path = _cache_path(config, key)
    path.parent.mkdir(parents=True, exist_ok=True)
    payload = {
        "schema_version": SCHEMA_VERSION,
        "meta": meta or {},
        "direction": direction.to_dict(),
    }
    path.write_text(json.dumps(payload, indent=2), encoding="utf-8")


def format_direction_summary(direction: CreativeDirection) -> str:
    """Plain-text summary for the GUI AI log."""
    lines: list[str] = ["AI applied — creative direction is driving this video."]
    if direction.style:
        lines.append(f"Style: {direction.style}")
    look: list[str] = []
    if direction.grade:
        look.append(f"grade {direction.grade}")
    if direction.easing:
        look.append(f"easing {direction.easing}")
    if direction.camera_feel:
        look.append(f"camera {direction.camera_feel}")
    if direction.glow is not None:
        look.append(f"glow {direction.glow:.2f}")
    if direction.animation_speed is not None:
        look.append(f"speed {direction.animation_speed:.2f}")
    if look:
        lines.append("Look: " + ", ".join(look))
    if direction.lesson_theme:
        lines.append(f"Lesson: {direction.lesson_theme}")
    if direction.focus_letters:
        lines.append("Letters: " + " ".join(direction.focus_letters[:12]))
    if direction.focus_words:
        lines.append("Words: " + ", ".join(direction.focus_words[:8]))
    if direction.voice_lines:
        preview = "; ".join(direction.voice_lines[:4])
        lines.append(f"Voice: {preview}")
    if direction.fun_facts:
        lines.append(f"Fact: {direction.fun_facts[0]}")
    profile = direction.audio_profile or {}
    if profile:
        bits = []
        if "tempo_bpm" in profile:
            bits.append(f"{profile['tempo_bpm']:.0f} bpm")
        if "scale" in profile:
            bits.append(str(profile["scale"]))
        if "energy" in profile:
            bits.append(f"energy {profile['energy']:.2f}")
        if bits:
            lines.append("Audio: " + ", ".join(bits))
    if direction.visual_beats:
        lines.append(f"Beats: {len(direction.visual_beats)} image+text suggestions")
        first = direction.visual_beats[0]
        if first.get("image_brief"):
            lines.append(f"Image 1: {first['image_brief']}")
        if first.get("overlay_text"):
            lines.append(f"Text 1: {first['overlay_text']}")
    if direction.title:
        lines.append(f"Title: {direction.title}")
    if direction.notes:
        lines.append(f"Note: {direction.notes}")
    return "\n".join(lines)


def _emit(on_progress: ProgressFn | None, payload: dict[str, Any]) -> None:
    if on_progress:
        on_progress(payload)


def suggest_for_spec(
    spec: Any,
    config: dict[str, Any],
    *,
    on_progress: ProgressFn | None = None,
) -> CreativeDirection | None:
    """
    Return creative direction for a project.

    Uses disk cache when available. On any failure, returns None (offline fallback).
    Network I/O stays on the caller thread (GUI uses a worker QThread).
    """
    ai = config.get("ai") or {}
    if not ai.get("enabled"):
        return None

    model = str(ai.get("model") or "openai/gpt-4o-mini")
    key = _cache_key(spec, model)
    cached = load_cached_direction(config, key)
    if cached is not None:
        logger.info("AI cache hit seed=%s engine=%s", spec.seed, spec.engine)
        direction = parse_creative_direction(cached.to_dict(), engine=spec.engine)
        _emit(
            on_progress,
            {
                "phase": "ai",
                "ai_status": "cache",
                "seed": spec.seed,
                "engine": spec.engine,
                "style": spec.style,
                "message": "Using cached AI creative direction (same seed = same look).",
                "detail": format_direction_summary(direction),
            },
        )
        return direction

    if not has_api_key(config):
        logger.warning("AI enabled but %s missing — skipping advisor", "OPENROUTER_API_KEY")
        _emit(
            on_progress,
            {
                "phase": "ai",
                "ai_status": "skipped",
                "seed": spec.seed,
                "engine": spec.engine,
                "style": spec.style,
                "message": "AI skipped — OPENROUTER_API_KEY missing. Using offline randomizer.",
            },
        )
        return None

    _emit(
        on_progress,
        {
            "phase": "ai",
            "ai_status": "asking",
            "seed": spec.seed,
            "engine": spec.engine,
            "style": spec.style,
            "message": f"Asking OpenRouter ({model}) for creative direction… GUI stays responsive.",
        },
    )

    messages = [
        {"role": "system", "content": SYSTEM_ADVISOR},
        {
            "role": "user",
            "content": advisor_user_prompt(
                seed=spec.seed,
                engine=spec.engine,
                style=spec.style,
                duration=spec.duration,
                width=spec.width,
                height=spec.height,
                params=dict(spec.params or {}),
            ),
        },
    ]
    try:
        content = chat_completion(messages=messages, config=config)
        direction = parse_creative_direction(content, engine=spec.engine)
        save_cached_direction(
            config,
            key,
            direction,
            meta={"seed": spec.seed, "engine": spec.engine, "style": spec.style, "model": model},
        )
        logger.info("AI advisor ok seed=%s engine=%s", spec.seed, spec.engine)
        return direction
    except (AIClientError, ValueError, json.JSONDecodeError) as exc:
        logger.warning("AI advisor failed seed=%s: %s", spec.seed, exc)
        _emit(
            on_progress,
            {
                "phase": "ai",
                "ai_status": "failed",
                "seed": spec.seed,
                "engine": spec.engine,
                "style": spec.style,
                "message": f"AI advisor failed — using offline randomizer.\n{exc}",
            },
        )
        return None


def apply_creative_direction(spec: Any, direction: CreativeDirection | None) -> Any:
    """Mutate ProjectSpec in place with validated creative direction."""
    if direction is None:
        return spec

    if direction.style:
        spec.style = str(direction.style)
        rng = np.random.default_rng(int(spec.seed) + 101)
        multipliers = sample_style_multiplier(rng, spec.style)
        spec.params["style_multipliers"] = multipliers
        spec.params["glow"] = multipliers["glow"]
        prev_blur = float(spec.params.get("blur", 0.2))
        spec.params["blur"] = float(max(0.0, min(1.5, prev_blur * multipliers["glow"])))
        spec.params["animation_speed"] = multipliers["speed"]
        spec.params["contrast"] = multipliers["contrast"]

    if direction.param_overrides:
        spec.params.update(direction.param_overrides)

    for key, value in (
        ("glow", direction.glow),
        ("blur", direction.blur),
        ("contrast", direction.contrast),
        ("animation_speed", direction.animation_speed),
        ("easing", direction.easing),
        ("camera_feel", direction.camera_feel),
        ("grade", direction.grade),
    ):
        if value is not None:
            spec.params[key] = value

    if direction.lesson_theme:
        spec.params["lesson_theme"] = direction.lesson_theme

    if direction.focus_letters:
        spec.params["focus_letters"] = list(direction.focus_letters)

    if direction.focus_words:
        spec.params["focus_words"] = list(direction.focus_words)

    if direction.voice_lines:
        spec.params["ai_voice_lines"] = list(direction.voice_lines)

    if direction.fun_facts:
        spec.params["ai_fun_facts"] = list(direction.fun_facts)

    if direction.segment_plan:
        spec.params["ai_segment_plan"] = list(direction.segment_plan)

    if direction.visual_beats:
        spec.params["ai_visual_beats"] = list(direction.visual_beats)
        if not direction.segment_plan:
            spec.params["ai_segment_plan"] = list(direction.visual_beats)

    if direction.title:
        spec.params["ai_title"] = direction.title

    if direction.segment_weights:
        spec.params["segment_weights"] = list(direction.segment_weights)

    if direction.audio_profile:
        spec.params["audio_profile"] = dict(direction.audio_profile)

    if direction.palette_colors:
        spec.palette_colors = [list(c) for c in direction.palette_colors]
        if direction.palette_name:
            spec.palette_name = direction.palette_name
        else:
            spec.palette_name = spec.palette_name or "ai_suggested"

    if direction.notes:
        spec.params["ai_notes"] = direction.notes

    spec.params["ai_applied"] = True
    spec.params["ai_summary"] = format_direction_summary(direction)
    _sanitize_alphabet_direction(spec)
    return spec


def _sanitize_alphabet_direction(spec: Any) -> None:
    """Keep ABC A–Z complete and stop SPELL videos from using first-letter salad like SABP."""
    if spec.params.get("complete_alphabet"):
        spec.engine = "alphabet_cartoon"
        spec.params["lesson_theme"] = "abc_complete"
        spec.params["mode"] = "lesson"
        spec.params["include_numbers"] = False
        spec.params.pop("focus_letters", None)
        spec.params.pop("ai_segment_plan", None)
        spec.params.pop("ai_visual_beats", None)
        spec.params.pop("segment_weights", None)
        return
    if getattr(spec, "engine", "") != "alphabet_cartoon":
        return
    from app.art.education_content import _is_letter_salad, choose_spell_word

    mode = str(spec.params.get("mode") or "").lower()
    theme = str(spec.params.get("lesson_theme") or "")
    if mode != "spell" and theme != "word_builder":
        return
    words = [str(w) for w in (spec.params.get("focus_words") or []) if str(w).strip()]
    letters = [str(c) for c in (spec.params.get("focus_letters") or []) if str(c).strip()]
    joined = "".join(letters)
    salad = _is_letter_salad(joined, words)
    if not salad and len(words) >= 2:
        salad = True
    if not salad:
        return
    spec.params.pop("focus_letters", None)
    beats = spec.params.get("ai_visual_beats") or spec.params.get("ai_segment_plan") or []
    rng = np.random.default_rng(int(getattr(spec, "seed", 1)) + 19)
    real = choose_spell_word(
        rng,
        focus_words=words,
        segment_plan=list(beats) if isinstance(beats, list) else [],
    )
    spec.params["focus_words"] = [real]


def maybe_enrich_spec(
    spec: Any,
    config: dict[str, Any],
    *,
    on_progress: ProgressFn | None = None,
) -> Any:
    """If AI per-video advisor is on, suggest and apply; otherwise no-op."""
    ai = config.get("ai") or {}
    if not ai.get("enabled") or not ai.get("per_video"):
        _emit(
            on_progress,
            {
                "phase": "ai",
                "ai_status": "off",
                "seed": getattr(spec, "seed", None),
                "engine": getattr(spec, "engine", None),
                "style": getattr(spec, "style", None),
                "message": "AI advisor off — fully offline randomizer.",
            },
        )
        return spec
    direction = suggest_for_spec(spec, config, on_progress=on_progress)
    if direction is None:
        return spec
    apply_creative_direction(spec, direction)
    if spec.params.get("ai_applied") and spec.params.get("ai_summary"):
        _emit(
            on_progress,
            {
                "phase": "ai",
                "ai_status": "applied",
                "seed": spec.seed,
                "engine": spec.engine,
                "style": spec.style,
                "message": "AI applied.",
                "detail": spec.params["ai_summary"],
            },
        )
    return spec
