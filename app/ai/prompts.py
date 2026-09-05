"""Prompt templates for creative direction and catalog curation."""

from __future__ import annotations

import json
from typing import Any

from app.core.randomizer import ENGINE_PARAM_SPECS

SYSTEM_ADVISOR = """You are a creative director for Genesis Artvision Engine, an OFFLINE procedural art video factory.
Return ONLY a JSON object (no markdown). Never invent image URLs or external assets.
For EVERY visual beat, suggest:
- image_brief: what the offline illustrator should draw (6-14 words, kid-friendly, concrete nouns + color + setting)
- overlay_text: short on-screen title (under 6 words)
- caption: one short supporting line
- word / letter / voice_line / fact when this is a kids lesson
The offline painter will DRAW those image_briefs locally. Do not describe photoreal photos.
Kids content must be age 3–7 friendly, slow, clear, and positive.
Kids videos teach something real: alphabet (letter + sound + word), dictionary (spell a word and say what it means), or real-world math (add/take-away stories kids can see: apples, birds, cars).
Voice lines must be slow enough for a child to repeat: short sentences, spell C. A. T., count 1. 2. 3., and end with "Say the word" or the answer.

KIDS ALPHABET RULES (critical):
1) Letter lessons: each beat is ONE letter and a word that STARTS with that letter.
   overlay_text like "S is for SUN". Different beats may use different words (SUN, APPLE, BALL).
   NEVER join those first letters into a fake word. "SABP" is wrong and must not appear.
2) Spell / dictionary lessons: pick ONE real kid word (SUN, CAT, FISH, APPLE). Spell it out loud.
   overlay_text is the word. caption is a one-sentence meaning a child understands.
3) Math lessons: use tiny add/take-away stories from real life. overlay_text like "2 + 1 = 3".
   voice_line counts slowly. Never use abstract algebra.
4) Spell-letter lessons: pick ONE real kid word. Every beat is the next letter of THAT SAME word.
   focus_words must be a single-item list like ["SUN"]. overlay_text like "S in SUN".
Unknown keys will be dropped. Numeric params must stay inside the provided ranges."""

SYSTEM_CURATE = """You expand offline kids education catalogs for an alphabet learning video app.
Return ONLY a JSON object (no markdown). Content must be age 3–7 friendly.
Words should be simple nouns kids know. Facts and voice lines must be short (under 12 words when possible)."""


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
    # Drop bulky nested values from the prompt
    slim_params = {
        k: v
        for k, v in params.items()
        if k not in {"education_lesson", "style_multipliers"} and not str(k).startswith("_")
    }
    schema = {
        "style": "optional style name string or null",
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
        "lesson_theme": "optional theme string for kids engines",
        "focus_letters": "optional list of single letters",
        "focus_words": "optional list of uppercase words",
        "voice_lines": "optional short narration lines",
        "fun_facts": "optional short kid facts",
        "title": "optional short video title for on-screen text",
        "visual_beats": [
            {
                "image_brief": "what to DRAW offline, e.g. a red apple with a green leaf in sunshine",
                "overlay_text": "short on-screen title",
                "caption": "one supporting line",
                "word": "APPLE",
                "letter": "A",
                "voice_line": "A is for apple",
                "fact": "Apples can be red or green.",
            }
        ],
        "segment_plan": "optional alias of visual_beats for kids lessons",
        "segment_weights": "optional list of positive floats for uneven lesson timing",
        "audio_profile": {
            "tempo_bpm": "40-180",
            "energy": "0-1",
            "scale": "major | pentatonic | soft_minor",
            "pad_brightness": "0-1",
            "chime_density": "0-1",
            "voice_rate": "0.78-0.94 for kids (clear, not sluggish)",
            "voice_pitch": "0.7-1.5",
        },
        "notes": "optional short note shown in the GUI",
    }
    return (
        f"Seed: {seed}\n"
        f"Engine: {engine}\n"
        f"Style: {style}\n"
        f"Resolution: {width}x{height}\n"
        f"Duration: {duration}s\n"
        f"Current params: {json.dumps(slim_params, default=str)}\n"
        f"Allowed param specs: {json.dumps(specs, default=str)}\n"
        f"Return JSON matching this shape: {json.dumps(schema)}\n"
        "Provide 4-8 visual_beats covering the video. Each beat MUST include image_brief "
        "and overlay_text so the offline illustrator can paint unique cards and titles. "
        "Bias toward modern, clean motion, cinematic grading, and vivid but soft palettes. "
        "If Engine is alphabet_cartoon and Current params mode is spell, you MUST pick one real "
        "spellable kid word and make every visual_beat a letter of that word in order."
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
