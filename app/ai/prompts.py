"""Prompt templates for creative direction and catalog curation."""

from __future__ import annotations

import json
from typing import Any

from app.art.education_content import KIDS_EDUCATION_ENGINES
from app.core.randomizer import ENGINE_PARAM_SPECS

SYSTEM_ADVISOR = """You are a creative director for Genesis Artvision Engine, an OFFLINE procedural art video factory.
Return ONLY a JSON object (no markdown). Never invent image URLs or external assets.
Never change the engine. Direct THIS engine only. Do not suggest a different art mode.
Unknown keys will be dropped. Numeric params must stay inside the provided ranges.
The offline painter will DRAW image_briefs locally. Do not describe photoreal photos."""

_VISUAL_RULES = """This video is abstract procedural art — not a classroom lesson.
Do NOT use alphabet, letters, spelling, phonics, counting lessons, or teaching voice-overs.
Do NOT set lesson_theme, focus_letters, focus_words, voice_lines, or fun_facts.
visual_beats: cinematic image_brief plus a short artistic overlay_text (mood titles like "Deep Drift").
Never write overlays like "A is for Apple" or "Let's learn B"."""

_ABC_RULES = """This is an ABC kids lesson (age 3–7). Keep it slow, clear, and positive.
Kids videos teach something real: alphabet (letter + sound + word), dictionary (spell a word and say what it means), or real-world math (add/take-away stories kids can see).
Voice lines must be short sentences a child can repeat.

KIDS ALPHABET RULES:
1) Letter lessons: each beat is ONE letter and a word that STARTS with that letter.
   overlay_text like "S is for SUN". NEVER join first letters into a fake word like "SABP".
2) Spell / dictionary: pick ONE real kid word (SUN, CAT, FISH, APPLE). Spell it out loud.
3) Math: tiny add/take-away stories. overlay_text like "2 + 1 = 3". Never abstract algebra.
4) Spell-letter: pick ONE real kid word. Every beat is the next letter of THAT SAME word.
   focus_words must be a single-item list like ["SUN"].
If Current params mode is spell, you MUST pick one real spellable kid word and make every visual_beat a letter of that word in order."""

_KIDS_OTHER_RULES = """This is a kids drawing / shapes / colors lesson (age 3–7), NOT an A–Z alphabet video unless a letter is already in Current params.
Keep voice lines short and positive. Teach the shape, color, or drawing on screen.
Do not turn this into a full alphabet A–Z lesson."""

_INFOGRAPHIC_RULES = """This is a science / fact explainer with a documentary HUD.
Use short factual overlay_text and fun_facts. No alphabet drills, phonics, or "A is for" lines.
visual_beats: concrete image_brief of the science subject plus a title like "Solar Wind"."""

SYSTEM_CURATE = """You expand offline kids education catalogs for an alphabet learning video app.
Return ONLY a JSON object (no markdown). Content must be age 3–7 friendly.
Words should be simple nouns kids know. Facts and voice lines must be short (under 12 words when possible)."""


def _engine_rules(engine: str) -> str:
    if engine == "alphabet_cartoon":
        return _ABC_RULES
    if engine in KIDS_EDUCATION_ENGINES:
        return _KIDS_OTHER_RULES
    if engine == "infographic_explainer":
        return _INFOGRAPHIC_RULES
    return _VISUAL_RULES


def _schema_for_engine(engine: str) -> dict[str, Any]:
    schema: dict[str, Any] = {
        "style": "optional style name string or null — keep the given style unless a better look fits this engine",
        "param_overrides": "object with subset of engine params only",
        "glow": "0-1 post glow",
        "blur": "0-1.5 post blur",
        "contrast": "0.5-1.5",
        "animation_speed": "0.15-2.0",
        "easing": "smooth | snappy | floaty",
        "camera_feel": "static | drift | pulse",
        "grade": "soft | vivid | pastel | cinematic",
        "palette_colors": "optional list of [r,g,b] floats 0-1 (2-6 colors)",
        "palette_name": "optional short name",
        "title": "optional short video title for on-screen text",
        "visual_beats": [
            {
                "image_brief": "what to DRAW offline, matching this engine",
                "overlay_text": "short on-screen title",
                "caption": "one supporting line",
            }
        ],
        "audio_profile": {
            "tempo_bpm": "40-180",
            "energy": "0-1",
            "scale": "major | pentatonic | soft_minor",
            "pad_brightness": "0-1",
            "chime_density": "0-1",
        },
        "notes": "optional short note shown in the GUI",
    }
    if engine in KIDS_EDUCATION_ENGINES:
        schema["lesson_theme"] = "optional theme string for this kids engine"
        schema["focus_letters"] = "optional list of single letters (alphabet engine only)"
        schema["focus_words"] = "optional list of uppercase words"
        schema["voice_lines"] = "optional short narration lines"
        schema["fun_facts"] = "optional short kid facts"
        schema["segment_plan"] = "optional alias of visual_beats"
        schema["segment_weights"] = "optional list of positive floats for uneven lesson timing"
        schema["visual_beats"] = [
            {
                "image_brief": "what to DRAW offline, e.g. a red apple with a green leaf in sunshine",
                "overlay_text": "short on-screen title",
                "caption": "one supporting line",
                "word": "APPLE",
                "letter": "A",
                "voice_line": "A is for apple",
                "fact": "Apples can be red or green.",
            }
        ]
        schema["audio_profile"]["voice_rate"] = "0.78-0.94 for kids (clear, not sluggish)"
        schema["audio_profile"]["voice_pitch"] = "0.7-1.5"
    elif engine == "infographic_explainer":
        schema["fun_facts"] = "optional short science facts"
        schema["visual_beats"] = [
            {
                "image_brief": "what to DRAW offline for this science topic",
                "overlay_text": "short HUD title",
                "caption": "one supporting line",
                "fact": "One short fact.",
            }
        ]
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
    art_kind = (
        "kids lesson"
        if engine in KIDS_EDUCATION_ENGINES
        else "science explainer"
        if engine == "infographic_explainer"
        else "abstract visual art"
    )
    return (
        f"Seed: {seed}\n"
        f"Engine: {engine} ({art_kind}) — keep this engine.\n"
        f"Style: {style}\n"
        f"Resolution: {width}x{height}\n"
        f"Duration: {duration}s\n"
        f"Current params: {json.dumps(slim_params, default=str)}\n"
        f"Allowed param specs: {json.dumps(specs, default=str)}\n"
        f"{_engine_rules(engine)}\n"
        f"Return JSON matching this shape: {json.dumps(_schema_for_engine(engine))}\n"
        "Provide 4-8 visual_beats covering the video. Each beat MUST include image_brief "
        "and overlay_text so the offline illustrator can paint unique cards and titles. "
        "Bias toward modern, clean motion, cinematic grading, and vivid but soft palettes."
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
