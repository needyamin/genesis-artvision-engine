"""Turn a user prompt into engine + creative direction (offline or OpenRouter)."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable

from app.ai.advisor import apply_creative_direction, format_direction_summary
from app.ai.client import AIClientError, chat_completion, has_api_key
from app.ai.prompts import SYSTEM_PROMPT_DIRECTOR, prompt_director_user_prompt
from app.ai.schemas import CreativeDirection, extract_json_object, parse_creative_direction
from app.core.randomizer import ENGINE_DEFAULT_STYLE
from app.utils.logger import get_logger

logger = get_logger("ai.prompt_brief")

ProgressFn = Callable[[dict[str, Any]], None]

ENGINES = ("kids_storybook", "how_it_works", "trend_brief")

_KIDS_WORDS = (
    "story", "bedtime", "kids", "child", "children", "picture book", "once upon",
    "puppy", "kitten", "luna", "teddy", "bedtime", "fairy", "adventure",
    "cat", "dog", "moon", "star", "rainbow", "friend",
)
_HOW_WORDS = (
    "how does", "how do", "how is", "explain", "science", "classroom", "step by step",
    "water cycle", "heartbeat", "electricity", "rainbow", "why does", "why do",
    "process", "diagram", "lesson", "learn how", "works",
)
_TREND_WORDS = (
    "trending", "viral", "this week", "tiktok", "internet", "news", "everyone is talking",
    "culture", "pulse", "brief", "headline", "social media", "ai agents",
)
_VERTICAL_WORDS = ("vertical", "tiktok", "shorts", "reels", "phone", "portrait")

_STOP = {
    "the", "a", "an", "and", "or", "but", "for", "with", "from", "that", "this",
    "into", "onto", "over", "under", "about", "after", "before", "then", "when",
    "what", "how", "why", "who", "make", "video", "please", "want", "need",
}

_DRAWABLE = {
    "APPLE", "BALL", "BIRD", "BOOK", "BUS", "CAKE", "CAR", "CAT", "CLOUD", "DOG",
    "DOOR", "DUCK", "EARTH", "EGG", "FISH", "FLOWER", "FOX", "HAT", "HOME", "HOUSE",
    "KEY", "KITE", "LAMP", "LEAF", "LIGHT", "LION", "MILK", "MOON", "MOUSE", "NEST",
    "NIGHT", "OCEAN", "OWL", "PLANE", "RAIN", "RAINBOW", "ROSE", "SHIP", "SHOE",
    "STAR", "SUN", "TRAIN", "TREE", "UMBRELLA", "VAN", "WAVE", "WATER",
}

_PHASES_HOW = ("HOOK", "STEP", "CAUSE", "EFFECT", "RESULT")
_PHASES_TREND = ("HOOK", "WHY", "CATCH", "PROOF", "NEXT")


def prompt_seed(text: str) -> int:
    blob = " ".join(str(text or "").strip().lower().split())
    digest = hashlib.sha256(blob.encode("utf-8")).hexdigest()
    return int(digest[:8], 16) % (2**31 - 1) or 1


def _norm(text: str) -> str:
    return " " + re.sub(r"[^a-z0-9]+", " ", (text or "").lower()).strip() + " "


def _hits(blob: str, phrases: tuple[str, ...]) -> int:
    score = 0
    for phrase in phrases:
        token = f" {phrase} "
        if token in blob:
            score += 2 if " " in phrase.strip() else 1
    return score


def classify_engine(prompt: str, hint: str | None = None) -> tuple[str, str]:
    """Pick engine + matching style from the prompt (or an explicit hint)."""
    hinted = str(hint or "").strip()
    if hinted in ENGINES:
        return hinted, ENGINE_DEFAULT_STYLE[hinted]
    blob = _norm(prompt)
    kids = _hits(blob, _KIDS_WORDS)
    how = _hits(blob, _HOW_WORDS)
    trend = _hits(blob, _TREND_WORDS)
    if "?" in (prompt or "") and (" how " in blob or " why " in blob):
        how += 3
    if " story " in blob or " bedtime " in blob:
        kids += 3
    ranked = sorted(
        (
            (how, "how_it_works"),
            (trend, "trend_brief"),
            (kids, "kids_storybook"),
        ),
        key=lambda row: row[0],
        reverse=True,
    )
    engine = ranked[0][1] if ranked[0][0] > 0 else "kids_storybook"
    return engine, ENGINE_DEFAULT_STYLE[engine]


def detect_resolution(prompt: str, quality: str = "1080") -> str:
    blob = _norm(prompt)
    vertical = any(f" {w} " in blob for w in _VERTICAL_WORDS)
    four_k = str(quality).lower() in {"4k", "uhd", "2160", "3840x2160"}
    if vertical and four_k:
        return "2160x3840"
    if vertical:
        return "1080x1920"
    if four_k:
        return "3840x2160"
    return "1920x1080"


def suggested_duration(prompt: str) -> float:
    sentences = split_sentences(prompt)
    n = max(4, min(8, len(sentences) or 4))
    return float(max(30, min(90, 8 * n)))


def split_sentences(text: str) -> list[str]:
    raw = re.split(r"[\n.!?]+", text or "")
    lines = [" ".join(part.split()) for part in raw if part and part.strip()]
    cleaned = [line.rstrip(" ,;:") for line in lines if len(line) >= 8]
    if cleaned:
        return cleaned[:8]
    words = (text or "").split()
    chunks: list[str] = []
    for i in range(0, len(words), 12):
        chunk = " ".join(words[i : i + 12]).strip()
        if chunk:
            chunks.append(chunk)
    return chunks[:8] or ["A short original story unfolds on screen."]


def extract_title(prompt: str) -> str:
    first = split_sentences(prompt)[0]
    words = [w for w in re.findall(r"[A-Za-z0-9']+", first) if w]
    title = " ".join(words[:8]).strip(" -:")
    return (title or "Prompt film")[:48]


def extract_nouns(prompt: str) -> list[str]:
    tokens = [t.upper() for t in re.findall(r"[A-Za-z]{3,}", prompt or "")]
    found: list[str] = []
    for tok in tokens:
        if tok in _DRAWABLE and tok not in found:
            found.append(tok)
    if found:
        return found[:8]
    leftovers = [t for t in tokens if t.lower() not in _STOP and t not in found]
    for tok in leftovers:
        if tok not in found:
            found.append(tok)
        if len(found) >= 6:
            break
    return found[:8] or ["STORY"]


def high_quality_look(engine: str) -> dict[str, Any]:
    """Look + audio knobs that read as a finished piece, not a random doodle."""
    if engine == "how_it_works":
        return {
            "param_overrides": {"board": "whiteboard", "diagram_speed": 0.85},
            "grade": "cinematic",
            "easing": "smooth",
            "camera_feel": "drift",
            "glow": 0.10,
            "blur": 0.04,
            "contrast": 1.14,
            "animation_speed": 0.78,
            "audio_profile": {
                "tempo_bpm": 88.0,
                "energy": 0.55,
                "scale": "soft_minor",
                "voice_rate": 0.96,
                "voice_pitch": 1.0,
            },
        }
    if engine == "trend_brief":
        return {
            "param_overrides": {"energy": 1.08, "ticker_speed": 1.05},
            "grade": "vivid",
            "easing": "snappy",
            "camera_feel": "pulse",
            "glow": 0.22,
            "blur": 0.03,
            "contrast": 1.18,
            "animation_speed": 1.12,
            "audio_profile": {
                "tempo_bpm": 118.0,
                "energy": 0.84,
                "scale": "pentatonic",
                "voice_rate": 1.0,
                "voice_pitch": 1.02,
            },
        }
    return {
        "param_overrides": {"show_word_images": True, "paper_warmth": 0.84, "page_turn": 0.72},
        "grade": "soft",
        "easing": "smooth",
        "camera_feel": "static",
        "glow": 0.12,
        "blur": 0.05,
        "contrast": 1.08,
        "animation_speed": 0.62,
        "audio_profile": {
            "tempo_bpm": 96.0,
            "energy": 0.46,
            "scale": "major",
            "pad_brightness": 0.5,
            "chime_density": 0.7,
            "voice_rate": 0.86,
            "voice_pitch": 1.10,
        },
    }


def _merge_look(data: dict[str, Any], engine: str) -> dict[str, Any]:
    look = high_quality_look(engine)
    merged = dict(look)
    for key, value in data.items():
        if value in (None, "", [], {}):
            continue
        if key == "param_overrides" and isinstance(value, dict):
            merged["param_overrides"] = {**look.get("param_overrides", {}), **value}
        elif key == "audio_profile" and isinstance(value, dict):
            merged["audio_profile"] = {**look.get("audio_profile", {}), **value}
        else:
            merged[key] = value
    return merged


def offline_direction_from_prompt(prompt: str, engine: str, style: str) -> CreativeDirection:
    """Build a full creative plan locally from the user's words."""
    lines = split_sentences(prompt)
    while len(lines) < 4:
        lines.append(lines[-1] if lines else "The story continues.")
    lines = lines[:6]
    title = extract_title(prompt)
    nouns = extract_nouns(prompt)
    beats: list[dict[str, Any]] = []
    voices: list[str] = []
    if engine == "kids_storybook":
        for i, line in enumerate(lines):
            word = nouns[i % len(nouns)]
            voice = line if line.endswith((".", "!", "?")) else f"{line}."
            beats.append(
                {
                    "overlay_text": line[:42],
                    "caption": line[:72],
                    "word": word,
                    "voice_line": voice[:160],
                    "image_brief": f"a friendly {word.lower()} in a warm picture book",
                }
            )
            voices.append(voice[:160])
        payload = _merge_look(
            {
                "title": title,
                "focus_words": nouns,
                "voice_lines": voices,
                "visual_beats": beats,
                "notes": "Offline prompt plan.",
            },
            engine,
        )
    elif engine == "how_it_works":
        for i, line in enumerate(lines):
            voice = line if line.endswith((".", "!", "?")) else f"{line}."
            beats.append(
                {
                    "phase": _PHASES_HOW[i % len(_PHASES_HOW)],
                    "overlay_text": line[:42],
                    "caption": line[:72],
                    "fact": nouns[i % len(nouns)].title() if nouns else f"Step {i + 1}",
                    "voice_line": voice[:160],
                }
            )
            voices.append(voice[:160])
        payload = _merge_look(
            {
                "title": title,
                "fun_facts": [lines[0], *lines[1:3]],
                "voice_lines": voices,
                "visual_beats": beats,
                "metrics": [{"label": "Topic", "val": title[:18], "unit": "classroom"}],
                "notes": "Offline prompt plan.",
            },
            engine,
        )
    else:
        for i, line in enumerate(lines):
            voice = line if line.endswith((".", "!", "?")) else f"{line}."
            beats.append(
                {
                    "phase": _PHASES_TREND[i % len(_PHASES_TREND)],
                    "overlay_text": line[:42],
                    "caption": line[:72],
                    "fact": "This week" if i == 0 else nouns[i % len(nouns)].title(),
                    "voice_line": voice[:160],
                }
            )
            voices.append(voice[:160])
        payload = _merge_look(
            {
                "title": title,
                "fun_facts": [lines[0], *lines[1:3]],
                "voice_lines": voices,
                "visual_beats": beats,
                "metrics": [{"label": "Signal", "val": "prompt", "unit": "now"}],
                "notes": "Offline prompt plan.",
            },
            engine,
        )
    return parse_creative_direction(payload, engine=engine, style=style)


def _emit(on_progress: ProgressFn | None, payload: dict[str, Any]) -> None:
    if on_progress:
        on_progress(payload)


def ai_direction_from_prompt(
    prompt: str,
    *,
    engine: str | None,
    style: str | None,
    config: dict[str, Any],
    on_progress: ProgressFn | None = None,
) -> tuple[str, str, CreativeDirection] | None:
    """Ask OpenRouter to plan the video. Returns None on any failure."""
    if not has_api_key(config):
        return None
    ai_cfg = dict(config.get("ai") or {})
    ai_cfg["timeout_sec"] = max(float(ai_cfg.get("timeout_sec") or 20), 45.0)
    call_config = dict(config)
    call_config["ai"] = ai_cfg
    model = str(ai_cfg.get("model") or "openai/gpt-4o-mini")
    _emit(
        on_progress,
        {
            "phase": "ai",
            "ai_status": "asking",
            "engine": engine or "auto",
            "style": style or "auto",
            "message": f"Turning your prompt into a video plan ({model})…",
        },
    )
    messages = [
        {"role": "system", "content": SYSTEM_PROMPT_DIRECTOR},
        {
            "role": "user",
            "content": prompt_director_user_prompt(
                user_prompt=prompt,
                engine=engine,
                style=style,
            ),
        },
    ]
    try:
        content = chat_completion(messages=messages, config=call_config, temperature=0.35)
        data = extract_json_object(content)
        picked = str(data.get("engine") or engine or "").strip()
        if picked not in ENGINES:
            picked, _ = classify_engine(prompt, engine)
        sty = style or ENGINE_DEFAULT_STYLE[picked]
        direction = parse_creative_direction(data, engine=picked, style=sty)
        look = high_quality_look(picked)
        if not direction.param_overrides:
            direction.param_overrides = dict(look.get("param_overrides") or {})
        if not direction.audio_profile:
            direction.audio_profile = dict(look.get("audio_profile") or {})
        if direction.grade is None:
            direction.grade = look.get("grade")
        if direction.easing is None:
            direction.easing = look.get("easing")
        if direction.camera_feel is None:
            direction.camera_feel = look.get("camera_feel")
        logger.info("Prompt AI plan engine=%s title=%s", picked, direction.title)
        return picked, sty, direction
    except (AIClientError, ValueError, json.JSONDecodeError, TypeError) as exc:
        logger.warning("Prompt AI plan failed: %s", exc)
        _emit(
            on_progress,
            {
                "phase": "ai",
                "ai_status": "failed",
                "engine": engine or "auto",
                "style": style or "auto",
                "message": f"AI prompt plan failed — using offline prompt plan.\n{exc}",
            },
        )
        return None


def enrich_from_user_prompt(
    spec: Any,
    config: dict[str, Any],
    *,
    on_progress: ProgressFn | None = None,
) -> Any:
    """Apply a user prompt as the concept bag. AI first when requested, else offline."""
    prompt = str(spec.params.get("user_prompt") or "").strip()
    if not prompt:
        return spec
    mode = str(spec.params.get("prompt_mode") or "offline").strip().lower()
    engine = str(spec.engine)
    style = str(spec.style)
    source = "offline"
    direction: CreativeDirection | None = None
    if mode == "ai":
        planned = ai_direction_from_prompt(
            prompt,
            engine=engine if engine in ENGINES else None,
            style=style,
            config=config,
            on_progress=on_progress,
        )
        if planned is not None:
            _, _, direction = planned
            source = "ai"
    if direction is None:
        locked = engine if engine in ENGINES else None
        engine, style = classify_engine(prompt, locked)
        spec.engine = engine
        spec.style = style
        direction = offline_direction_from_prompt(prompt, engine, style)
        source = "offline"
    apply_creative_direction(spec, direction)
    spec.params["user_prompt"] = prompt
    spec.params["prompt_mode"] = mode
    spec.params["prompt_source"] = source
    spec.params["ai_applied"] = True
    spec.params["ai_summary"] = (
        f"Prompt ({source}): {prompt[:180]}\n" + format_direction_summary(direction)
    )
    _emit(
        on_progress,
        {
            "phase": "ai",
            "ai_status": "applied",
            "seed": spec.seed,
            "engine": spec.engine,
            "style": spec.style,
            "message": f"Prompt plan ready ({source}).",
            "detail": spec.params["ai_summary"],
        },
    )
    return spec
