"""Prompt templates for creative direction and catalog curation."""

from __future__ import annotations

import json
from typing import Any

from app.art.styles import STYLE_EDIT, STYLE_PROFILES
from app.core.randomizer import ENGINE_PARAM_SPECS, KIDS_ENGINES, TOPIC_BRIEF_ENGINES

SYSTEM_ADVISOR = """You are a creative director for Genesis Artvision Engine, an OFFLINE procedural art video factory.
Return ONLY a JSON object (no markdown). Never invent image URLs or external assets.
Direct the given Engine + Style pair. Never change the engine. Never change the style.
Engine paints the entire frame. Style only changes look: palette, glow, speed, grade, audio mood.
Unknown keys will be dropped. Numeric params must stay inside the provided ranges."""

ENGINE_GUIDES: dict[str, str] = {
    "kids_storybook": (
        "Kids Storybook: a short picture-book story for ages 3–7 (animals, weather, friendship). "
        "Return a story title, 4–6 page beats, voice lines, and simple picture words. "
        "Do not turn this into an A–Z alphabet lesson."
    ),
    "how_it_works": (
        "How It Works: everyday education (water cycle, heartbeat, electricity, rainbow). "
        "Return an informative process: title, hook, 4–6 step beats, voice lines, metrics. "
        "The engine draws its own classroom diagrams."
    ),
    "trend_brief": (
        "Trending Brief: a short kinetic-type video about a CURRENTLY TRENDING internet topic "
        "(this week's viral tech, culture, science, or news-of-the-week). "
        "Name a real-feeling current-web topic. Return title, hook, 4–6 fact beats, voice lines. "
        "This engine paints the brief itself."
    ),
}

STYLE_GUIDES: dict[str, str] = {
    "storybook": "Storybook: warm paper, soft grade, slow page pacing.",
    "classroom": "Classroom: clean board, medium contrast, calm diagrams.",
    "pulse": "Pulse: fast, punchy, high energy, neon accents.",
}

_KIDS_STORY_RULES = """Kids story must be age 3–7, slow, kind, and concrete.
Return a short picture-book: title, 4–6 page beats, voice lines, and one simple noun per page.
Each visual_beat is one page: overlay_text (headline), caption (body), voice_line, word (picture noun), image_brief.
Do not turn this into a full alphabet A–Z lesson."""

_HOW_IT_WORKS_RULES = """Return an everyday how-it-works process (water cycle, heart, electricity, rainbow, plants).
JSON: title, fun_facts (hook first), voice_lines, metrics [{label, val, unit}], visual_beats as STEPS.
Each visual_beat: phase, overlay_text (headline), caption (body), fact (data_point), voice_line.
The engine draws classroom diagrams."""

_TREND_RULES = """Pick a CURRENTLY TRENDING internet topic from this week (viral tech, culture, science, or news).
JSON: title, fun_facts (hook first), voice_lines, metrics [{label, val, unit}], visual_beats as 4–6 fact beats.
Each visual_beat: phase (HOOK/WHY/CATCH/NEXT), overlay_text, caption, fact, voice_line.
This engine draws the brief."""

SYSTEM_PROMPT_DIRECTOR = """You are a creative director for Genesis Artvision Engine, an OFFLINE procedural art video factory.
The user wrote a prompt. Turn THAT prompt into a high-quality video plan the local engines can paint.
Return ONLY a JSON object (no markdown). Never invent image URLs or external assets.
Pick exactly one engine:
- kids_storybook: ages 3–7 picture book (animals, weather, friendship). Style must be storybook.
- how_it_works: everyday classroom explainer (rain, heart, electricity). Style must be classroom.
- trend_brief: kinetic brief about a current-web topic. Style must be pulse.
Follow the user's topic closely. Write 5–6 concrete visual_beats with spoken voice_lines.
High production: strong titles, readable captions, one picture noun per kids page, no filler."""

SYSTEM_CURATE = """You expand offline kids story catalogs for a picture-book video app.
Return ONLY a JSON object (no markdown). Content must be age 3–7 friendly.
Words should be simple nouns kids know. Facts and voice lines must be short (under 12 words when possible)."""


def _engine_rules(engine: str) -> str:
    if engine == "kids_storybook":
        return _KIDS_STORY_RULES
    if engine == "how_it_works":
        return _HOW_IT_WORKS_RULES
    if engine == "trend_brief":
        return _TREND_RULES
    return _KIDS_STORY_RULES


def _style_look_hint(style: str) -> str:
    profile = STYLE_PROFILES.get(style) or {}
    edit = STYLE_EDIT.get(style) or {}
    bits = [STYLE_GUIDES.get(style, f"Style {style}: keep this look.")]
    grade = edit.get("grade")
    feel = edit.get("edit_feel")
    if grade:
        bits.append(f"Prefer grade={grade}.")
    if feel:
        bits.append(f"Editorial feel={feel}.")
    bpm = edit.get("bpm")
    if isinstance(bpm, tuple) and len(bpm) == 2:
        bits.append(f"Audio tempo around {bpm[0]:.0f}-{bpm[1]:.0f} bpm.")
    glow = profile.get("glow")
    if isinstance(glow, tuple):
        bits.append(f"Glow roughly {glow[0]:.2f}-{glow[1]:.2f}.")
    return " ".join(bits)


def _schema_for_engine(engine: str, style: str) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "style": f"must be \"{style}\" or null — do not switch styles",
        "param_overrides": "object with subset of THIS engine's params only",
        "glow": "0-1 post glow",
        "blur": "0-1.5 post blur",
        "contrast": "0.5-1.5",
        "animation_speed": "0.15-2.0",
        "easing": "smooth | snappy | floaty",
        "camera_feel": "static | drift | pulse",
        "grade": "soft | vivid | pastel | cinematic",
        "palette_colors": "optional list of [r,g,b] floats 0-1 (2-6 colors) matching this style",
        "palette_name": "optional short name",
        "audio_profile": {
            "tempo_bpm": "40-180",
            "energy": "0-1",
            "scale": "major | pentatonic | soft_minor",
            "pad_brightness": "0-1",
            "chime_density": "0-1",
        },
        "notes": "optional short note shown in the GUI",
    }
    if engine == "kids_storybook":
        schema["title"] = "short picture-book title"
        schema["focus_words"] = "optional picture nouns, e.g. CAT, RAIN"
        schema["voice_lines"] = "one short line per page"
        schema["visual_beats"] = [
            {
                "overlay_text": "Meet Luna",
                "caption": "Luna is a soft orange cat.",
                "word": "CAT",
                "voice_line": "This is Luna. Luna is a friendly orange cat.",
                "image_brief": "a friendly orange cat in a picture book",
            }
        ]
        schema["audio_profile"]["voice_rate"] = "0.78-0.94"
        schema["audio_profile"]["voice_pitch"] = "0.7-1.5"
    elif engine == "how_it_works":
        schema["title"] = "process title, e.g. The Water Cycle"
        schema["fun_facts"] = "hook first, then short facts"
        schema["voice_lines"] = "one calm line per step"
        schema["metrics"] = [{"label": "Ocean water", "val": "97%", "unit": "of Earth's water"}]
        schema["visual_beats"] = [
            {
                "phase": "EVAPORATE",
                "overlay_text": "Sun lifts the water",
                "caption": "Heat turns ocean water into vapor.",
                "fact": "Liquid → vapor",
                "voice_line": "The sun warms lakes and oceans, and water rises as vapor.",
            }
        ]
        schema["audio_profile"]["voice_rate"] = "0.82-1.0"
        schema["audio_profile"]["voice_pitch"] = "0.85-1.1"
    elif engine == "trend_brief":
        schema["title"] = "currently trending internet topic title"
        schema["fun_facts"] = "hook first: why this is trending now"
        schema["voice_lines"] = "one punchy line per beat"
        schema["metrics"] = [{"label": "Signal", "val": "viral", "unit": "this week"}]
        schema["visual_beats"] = [
            {
                "phase": "HOOK",
                "overlay_text": "Why it is everywhere",
                "caption": "One-sentence current context.",
                "fact": "This week",
                "voice_line": "Here is the trend people are talking about this week.",
            }
        ]
        schema["audio_profile"]["voice_rate"] = "0.88-1.08"
        schema["audio_profile"]["voice_pitch"] = "0.9-1.15"
    return schema


def advisor_user_prompt(
    *,
    seed: int,
    engine: str,
    style: str,
    duration: float,
    width: int,
    height: int,
    params: dict[str, Any],
) -> str:
    specs = ENGINE_PARAM_SPECS.get(engine, {})
    slim_params = {
        k: v
        for k, v in params.items()
        if k not in {"education_lesson", "style_multipliers"} and not str(k).startswith("_")
    }
    engine_guide = ENGINE_GUIDES.get(engine, f"Engine {engine}: keep this art mode.")
    style_guide = _style_look_hint(style)
    combo = (
        f"LOCKED combination: Engine={engine} + Style={style}.\n"
        "Do not switch to another engine or style. Direct THIS pair only."
    )
    if engine == "trend_brief":
        combo += (
            " Pick a currently trending internet topic (this week's viral tech/culture/science/news). "
            "Return structured topic JSON this engine will draw."
        )
    elif engine == "how_it_works":
        combo += " Return an informative how-it-works process JSON this engine will draw as classroom diagrams."
    else:
        combo += " Suggest story title, voice, and matching picture briefs. The engine already draws the story pages."
    if engine in KIDS_ENGINES and style != "storybook":
        combo += f" Keep the kids story of {engine}; dress it in {style} color and motion."
    if engine == "how_it_works" and style != "classroom":
        combo += f" Keep the how-it-works lesson; dress it in {style} color and motion."
    if engine == "trend_brief" and style != "pulse":
        combo += f" Keep the trending brief; dress it in {style} color and motion."
    if engine in KIDS_ENGINES:
        closing = "Optional visual_beats may include image_brief matching the story word."
    elif engine in TOPIC_BRIEF_ENGINES:
        closing = "Return title, fun_facts, voice_lines, metrics, and visual_beats. This engine paints those fields."
    else:
        closing = "Return title, voice_lines, and visual_beats this engine will paint."
    return (
        f"Seed: {seed}\n"
        f"{combo}\n"
        f"Engine guide: {engine_guide}\n"
        f"Style guide: {style_guide}\n"
        f"Resolution: {width}x{height}\n"
        f"Duration: {duration}s\n"
        f"Current params: {json.dumps(slim_params, default=str)}\n"
        f"Allowed param specs for {engine}: {json.dumps(specs, default=str)}\n"
        f"{_engine_rules(engine)}\n"
        f"Return JSON matching this shape: {json.dumps(_schema_for_engine(engine, style))}\n"
        f"{closing}"
    )


def prompt_director_user_prompt(
    *,
    user_prompt: str,
    engine: str | None,
    style: str | None,
) -> str:
    locked = ""
    if engine:
        sty = style or {"kids_storybook": "storybook", "how_it_works": "classroom", "trend_brief": "pulse"}.get(
            engine, "storybook"
        )
        locked = (
            f"LOCKED engine={engine} style={sty}. Do not switch engines.\n"
            f"{ENGINE_GUIDES.get(engine, '')}\n"
            f"{_engine_rules(engine)}\n"
            f"Return JSON matching this shape plus an \"engine\" field equal to \"{engine}\": "
            f"{json.dumps(_schema_for_engine(engine, sty))}\n"
        )
    else:
        locked = (
            "Choose the best engine for the user's prompt. Put it in JSON as \"engine\".\n"
            "kids_storybook → storybook. how_it_works → classroom. trend_brief → pulse.\n"
            "Also return title, voice_lines, visual_beats (5–6), and engine-specific fields.\n"
        )
    return (
        f"USER PROMPT:\n{user_prompt.strip()}\n\n"
        f"{locked}"
        "Make the video feel high quality: specific nouns, short spoken lines, clear headlines.\n"
        "Kids pages need word (uppercase noun) and image_brief. Explainers need phase + voice_line."
    )


def curate_user_prompt(letters: list[str]) -> str:
    letters = [c.upper() for c in letters]
    schema = {
        "words": {letter: ["WORD1", "WORD2"] for letter in letters[:2]},
        "fun_facts": {letter: ["Short fact."] for letter in letters[:2]},
        "voice_lines": {letter: ["L is for WORD"] for letter in letters[:2]},
    }
    return (
        f"Expand offline catalogs for letters: {', '.join(letters)}.\n"
        "For EACH letter provide:\n"
        "- words: 3-5 uppercase easy nouns starting with that letter\n"
        "- fun_facts: 2-3 short facts\n"
        "- voice_lines: 2 short narration lines\n"
        f"Example shape (extend to all requested letters): {json.dumps(schema)}\n"
        "Avoid brands, violence, politics, or hard words."
    )
