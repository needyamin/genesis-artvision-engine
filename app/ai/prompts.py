"""Prompt templates for creative direction and catalog curation."""

from __future__ import annotations

import json
from typing import Any

from app.art.education_content import KIDS_EDUCATION_ENGINES
from app.art.styles import STYLE_EDIT, STYLE_PROFILES
from app.core.randomizer import ENGINE_PARAM_SPECS, VISUAL_ART_ENGINES

SYSTEM_ADVISOR = """You are a creative director for Genesis Artvision Engine, an OFFLINE procedural art video factory.
Return ONLY a JSON object (no markdown). Never invent image URLs or external assets.
Direct the given Engine + Style pair. Never change the engine. Never change the style.
Engine paints the entire frame. Style only changes look: palette, glow, speed, grade, audio mood.
For procedural art engines, NEVER add titles, captions, article cards, headlines, or extra pictures.
Unknown keys will be dropped. Numeric params must stay inside the provided ranges."""

ENGINE_GUIDES: dict[str, str] = {
    "particles": (
        "Particle Universe: the video IS moving particles (trails, gravity, turbulence). "
        "Only tune count, size, speed, trail, attraction, glow. Do not add titles or pictures."
    ),
    "galaxy": (
        "Galaxy / Starfield: the video IS a procedural spiral galaxy. "
        "Only tune star_count, arm_count, spin, core_glow, drift. Do not add titles or pictures."
    ),
    "waves": (
        "Waves / Liquid: the video IS layered liquid interference. "
        "Only tune layers, frequency, amplitude, speed, distortion. Do not add titles or pictures."
    ),
    "tunnel": (
        "Tunnel: the video IS rings and spokes rushing toward the camera. "
        "Only tune rings, spokes, speed, twist, pulse. Do not add titles or pictures."
    ),
    "alphabet_cartoon": (
        "ABC Educational: kids letter/word/math lesson (age 3–7). "
        "Each beat is a letter, a real word, or a tiny add/take-away story."
    ),
    "hand_art": (
        "Draw Along: kids follow a simple drawing (house, sun, tree, cat). "
        "Teach the doodle on screen. Do not turn this into a full A–Z alphabet video."
    ),
    "kids_doodles": (
        "Shapes & Colors: kids learn shapes, colors, counting, or a simple word sticker. "
        "Teach what is drawn. Do not turn this into a full A–Z alphabet video."
    ),
    "infographic_explainer": (
        "Science Explainer: the engine already draws a documentary HUD and diagrams. "
        "Tune domain, hud_density, schematic_glow. Suggest fun_facts only. "
        "Do not add extra title cards or pictures on top."
    ),
}

STYLE_GUIDES: dict[str, str] = {
    "abstract": "Abstract: mixed geometry, medium glow, neither cute nor documentary.",
    "cosmic": "Cosmic: deep space palette, slow drift, high glow, cinematic grade.",
    "minimal": "Minimal: sparse, soft, slow, low grain, lots of quiet space.",
    "organic": "Organic: nature, fluid, earth and plant tones, gentle motion.",
    "digital": "Digital: neon, fast, crisp, extra contrast and chroma.",
    "playful": (
        "Playful: bright friendly colors and bouncy motion. "
        "If the engine is not a kids engine, apply only this LOOK — no alphabet or classroom content."
    ),
    "documentary": (
        "Documentary: restrained HUD energy, factual titles, cinematic grade. "
        "If the engine is not the science explainer, apply only this LOOK — do not invent a lecture."
    ),
}

_ABC_RULES = """Kids content must be age 3–7, slow, clear, and positive.
1) Letter lessons: each beat is ONE letter and a word that STARTS with that letter.
   overlay_text like "S is for SUN". NEVER join first letters into a fake word like "SABP".
2) Spell / dictionary: pick ONE real kid word (SUN, CAT, FISH, APPLE). Spell it out loud.
3) Math: tiny add/take-away stories. overlay_text like "2 + 1 = 3". Never abstract algebra.
4) Spell-letter: pick ONE real kid word. Every beat is the next letter of THAT SAME word.
   focus_words must be a single-item list like ["SUN"].
If Current params mode is spell, you MUST pick one real spellable kid word and make every visual_beat a letter of that word in order."""

_KIDS_OTHER_RULES = """Kids content must be age 3–7, slow, clear, and positive.
Keep voice lines short. Teach the shape, color, or drawing on screen.
Do not turn this into a full alphabet A–Z lesson unless a letter is already in Current params."""

_INFOGRAPHIC_RULES = """The explainer engine already paints HUD cards.
Suggest fun_facts and engine params only.
Do NOT set visual_beats, title, overlay_text, image_brief, or captions.
No alphabet drills or 'A is for' lines."""

_VISUAL_RULES = """This is abstract procedural art. The engine paints every pixel.
Do NOT set lesson_theme, focus_letters, focus_words, voice_lines, fun_facts,
visual_beats, title, overlay_text, captions, or image_brief.
Do not invent articles, headlines, or sticker pictures.
Only return param_overrides, glow, blur, contrast, animation_speed, easing,
camera_feel, grade, palette_colors, audio_profile, and notes."""

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
    if engine == "alphabet_cartoon":
        schema["lesson_theme"] = "optional theme for this ABC lesson"
        schema["focus_letters"] = "optional list of single letters"
        schema["focus_words"] = "optional list of uppercase words"
        schema["voice_lines"] = "optional short narration lines"
        schema["fun_facts"] = "optional short kid facts"
        schema["segment_weights"] = "optional list of positive floats for uneven lesson timing"
        schema["visual_beats"] = [
            {
                "image_brief": "matching picture for the letter-word already in the lesson",
                "word": "APPLE",
                "letter": "A",
                "voice_line": "A is for apple",
            }
        ]
        schema["audio_profile"]["voice_rate"] = "0.78-0.94 for kids (clear, not sluggish)"
        schema["audio_profile"]["voice_pitch"] = "0.7-1.5"
    elif engine == "kids_doodles":
        schema["lesson_theme"] = "shape_fun | color_rainbow | count_along | real_world_math | dictionary"
        schema["voice_lines"] = "optional short narration lines about the shape or color"
        schema["visual_beats"] = [
            {
                "image_brief": "a big yellow circle like a sun on paper",
                "shape": "circle",
                "voice_line": "This is a circle. It is round.",
            }
        ]
        schema["audio_profile"]["voice_rate"] = "0.78-0.94"
        schema["audio_profile"]["voice_pitch"] = "0.7-1.5"
    elif engine == "hand_art":
        schema["lesson_theme"] = "draw_along | sketch_practice | doodle_story"
        schema["focus_words"] = "optional simple things to draw, e.g. HOUSE"
        schema["voice_lines"] = "optional short draw-along lines"
        schema["visual_beats"] = [
            {
                "image_brief": "a simple house doodle with a triangle roof",
                "word": "HOUSE",
                "voice_line": "Let's draw a house together.",
            }
        ]
        schema["audio_profile"]["voice_rate"] = "0.78-0.94"
        schema["audio_profile"]["voice_pitch"] = "0.7-1.5"
    elif engine == "infographic_explainer":
        schema["fun_facts"] = "optional short science facts"
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
    if engine in VISUAL_ART_ENGINES:
        combo += (
            " Suggest look, motion, palette, and audio only. "
            "No titles, captions, article cards, or extra pictures."
        )
    elif engine == "infographic_explainer":
        combo += " Suggest facts and HUD params. No extra pictures or title stickers."
    else:
        combo += " Suggest lesson theme, voice, and matching picture briefs. The engine already draws the lesson cards."
    if engine in VISUAL_ART_ENGINES and style == "playful":
        combo += " Playful look only — still no letters or lessons."
    if engine in KIDS_EDUCATION_ENGINES and style != "playful":
        combo += f" Keep the kids lesson of {engine}; dress it in {style} color and motion."
    if engine == "infographic_explainer" and style != "documentary":
        combo += f" Keep the science explainer; dress it in {style} color and motion."
    closing = (
        "Tune param_overrides and look knobs only. Do not return visual_beats or title."
        if engine not in KIDS_EDUCATION_ENGINES
        else "Optional visual_beats may include image_brief matching the lesson word. Do not invent a separate article overlay."
    )
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
