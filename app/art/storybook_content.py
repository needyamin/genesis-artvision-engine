"""Offline kids storybook catalog — short picture-book pages, not ABC drills."""

from __future__ import annotations

from typing import Any

import numpy as np

STORIES: list[dict[str, Any]] = [
    {
        "id": "luna_the_cat",
        "title": "Luna the Cat",
        "theme": "animals",
        "word": "CAT",
        "pages": [
            {"headline": "Meet Luna", "body": "Luna is a soft orange cat.", "voice_line": "This is Luna. Luna is a friendly orange cat.", "word": "CAT"},
            {"headline": "A sunny window", "body": "She loves the warm window light.", "voice_line": "Luna sits in the sunny window and purrs.", "word": "SUN"},
            {"headline": "A tiny mouse friend", "body": "A mouse says hello. They share a nap.", "voice_line": "A little mouse says hello. Luna is gentle and kind.", "word": "MOUSE"},
            {"headline": "Good night", "body": "The moon comes out. Luna curls up.", "voice_line": "Good night, Luna. Sleep well, little cat.", "word": "MOON"},
        ],
    },
    {
        "id": "rainy_day_duck",
        "title": "The Rainy Day Duck",
        "theme": "weather",
        "word": "DUCK",
        "pages": [
            {"headline": "Clouds arrive", "body": "Gray clouds fill the sky.", "voice_line": "Look at the gray clouds. Rain is coming soon.", "word": "CLOUD"},
            {"headline": "Pitter patter", "body": "Raindrops dance on the pond.", "voice_line": "Pitter patter. The rain taps the water.", "word": "RAIN"},
            {"headline": "Happy duck", "body": "A yellow duck loves the rain.", "voice_line": "The duck is happy. Ducks like rainy days.", "word": "DUCK"},
            {"headline": "A rainbow", "body": "The sun returns. A rainbow shines.", "voice_line": "The rain stops. A bright rainbow smiles in the sky.", "word": "RAINBOW"},
        ],
    },
    {
        "id": "sam_the_seed",
        "title": "Sam the Seed",
        "theme": "nature",
        "word": "SEED",
        "pages": [
            {"headline": "A tiny seed", "body": "Sam is a small brown seed.", "voice_line": "Sam is a tiny seed waiting in the soil.", "word": "SEED"},
            {"headline": "Water and sun", "body": "Rain and sun help Sam grow.", "voice_line": "Water and sunshine help the seed grow.", "word": "SUN"},
            {"headline": "A green sprout", "body": "A sprout peeks up. Hello, world!", "voice_line": "A green sprout peeks out. Hello, world!", "word": "LEAF"},
            {"headline": "A tall tree", "body": "Sam becomes a tree with shade.", "voice_line": "Sam grows into a tree. Birds can rest in the shade.", "word": "TREE"},
        ],
    },
    {
        "id": "red_balloon",
        "title": "The Red Balloon",
        "theme": "friendship",
        "word": "BALLOON",
        "pages": [
            {"headline": "A gift", "body": "Mia gets a red balloon.", "voice_line": "Mia gets a bright red balloon. It is light and round.", "word": "BALLOON"},
            {"headline": "It floats", "body": "The balloon lifts toward the sky.", "voice_line": "The balloon floats up, up, up toward the sky.", "word": "SKY"},
            {"headline": "A kind wind", "body": "The wind is gentle, not scary.", "voice_line": "A kind wind holds the string. Mia is not afraid.", "word": "WIND"},
            {"headline": "Together", "body": "Mia holds the string. They stay friends.", "voice_line": "Mia holds the string. The balloon stays with her.", "word": "FRIEND"},
        ],
    },
    {
        "id": "night_train",
        "title": "The Night Train",
        "theme": "adventure",
        "word": "TRAIN",
        "pages": [
            {"headline": "Clickety clack", "body": "A blue train rolls through town.", "voice_line": "Clickety clack. The night train rolls through town.", "word": "TRAIN"},
            {"headline": "Stars above", "body": "Stars sparkle over the tracks.", "voice_line": "Stars sparkle above the tracks. The night is quiet.", "word": "STAR"},
            {"headline": "A tunnel", "body": "Through a tunnel, then lights.", "voice_line": "Through a dark tunnel, then bright lights again.", "word": "LIGHT"},
            {"headline": "Home station", "body": "The train arrives. Sleepy town.", "voice_line": "The train arrives home. Good night, little town.", "word": "HOME"},
        ],
    },
    {
        "id": "busy_bee",
        "title": "Bella the Bee",
        "theme": "animals",
        "word": "BEE",
        "pages": [
            {"headline": "Buzz buzz", "body": "Bella is a busy yellow bee.", "voice_line": "Buzz buzz. Bella is a busy yellow bee.", "word": "BEE"},
            {"headline": "Flower visit", "body": "She lands on a pink flower.", "voice_line": "Bella lands on a pink flower and sips sweet nectar.", "word": "FLOWER"},
            {"headline": "Pollen dust", "body": "Gold dust sticks to her legs.", "voice_line": "Gold pollen dust sticks to her tiny legs.", "word": "GOLD"},
            {"headline": "Honey home", "body": "She flies home to make honey.", "voice_line": "Bella flies home to the hive to make honey.", "word": "HONEY"},
        ],
    },
    {
        "id": "ocean_wave",
        "title": "Little Wave",
        "theme": "nature",
        "word": "WAVE",
        "pages": [
            {"headline": "The shore", "body": "A small wave rolls to the sand.", "voice_line": "A little wave rolls toward the sandy shore.", "word": "WAVE"},
            {"headline": "Shells", "body": "It leaves a shiny shell behind.", "voice_line": "The wave leaves a shiny shell on the sand.", "word": "SHELL"},
            {"headline": "A crab", "body": "A crab waves hello with a claw.", "voice_line": "A tiny crab waves hello with one claw.", "word": "CRAB"},
            {"headline": "Back to sea", "body": "The wave returns to the ocean.", "voice_line": "The wave slides back to the big blue ocean.", "word": "OCEAN"},
        ],
    },
    {
        "id": "kind_kite",
        "title": "The Kind Kite",
        "theme": "play",
        "word": "KITE",
        "pages": [
            {"headline": "Windy hill", "body": "Leo flies a green kite.", "voice_line": "Leo stands on a windy hill with a green kite.", "word": "KITE"},
            {"headline": "It soars", "body": "The kite dances in the wind.", "voice_line": "The kite soars and dances in the wind.", "word": "WIND"},
            {"headline": "A snag", "body": "The string tangles in a tree.", "voice_line": "Oh no. The kite string tangles in a tree.", "word": "TREE"},
            {"headline": "Friends help", "body": "Friends lift Leo. The kite is free.", "voice_line": "Friends help Leo. The kite is free again.", "word": "FRIEND"},
        ],
    },
    {
        "id": "moon_soup",
        "title": "Moon Soup",
        "theme": "imagination",
        "word": "MOON",
        "pages": [
            {"headline": "A silver bowl", "body": "Grandma stirs moon soup.", "voice_line": "Grandma stirs a silver bowl of moon soup.", "word": "MOON"},
            {"headline": "Star sprinkles", "body": "She adds tiny star sprinkles.", "voice_line": "She adds tiny star sprinkles that sparkle.", "word": "STAR"},
            {"headline": "A sip", "body": "It tastes like warm night air.", "voice_line": "One sip tastes like warm, quiet night air.", "word": "NIGHT"},
            {"headline": "Sweet dreams", "body": "Time for bed under the moon.", "voice_line": "Time for bed. The moon watches over sweet dreams.", "word": "BED"},
        ],
    },
    {
        "id": "two_shoes",
        "title": "Two Little Shoes",
        "theme": "routine",
        "word": "SHOE",
        "pages": [
            {"headline": "Morning", "body": "Two shoes wait by the door.", "voice_line": "Two little shoes wait by the door in the morning.", "word": "SHOE"},
            {"headline": "Left and right", "body": "One left. One right. Ready!", "voice_line": "One for the left foot. One for the right foot. Ready!", "word": "FOOT"},
            {"headline": "A walk", "body": "They tap down the sunny path.", "voice_line": "Tap tap. They walk down the sunny path.", "word": "PATH"},
            {"headline": "Home again", "body": "Back by the door until tomorrow.", "voice_line": "Home again. The shoes rest until tomorrow.", "word": "HOME"},
        ],
    },
]


def _time_pages(pages: list[dict[str, Any]], duration: float) -> list[dict[str, Any]]:
    n = max(1, len(pages))
    step = 1.0 / n
    out: list[dict[str, Any]] = []
    for i, page in enumerate(pages):
        t0 = i * step
        t1 = min(1.0, (i + 1) * step)
        word = str(page.get("word") or "STORY").upper()
        headline = str(page.get("headline") or f"Page {i + 1}")
        voice = str(page.get("voice_line") or headline)
        out.append(
            {
                "index": i,
                "t0": float(t0),
                "t1": float(t1),
                "headline": headline,
                "overlay_text": headline,
                "line": headline,
                "caption": str(page.get("body") or ""),
                "body": str(page.get("body") or ""),
                "voice_line": voice,
                "word": word,
                "motif": word,
                "kind": "story",
                "image_brief": str(page.get("image_brief") or f"a friendly {word.lower()} in a picture book"),
            }
        )
    return out


def _lesson_from_story(story: dict[str, Any], seed: int, duration: float) -> dict[str, Any]:
    pages = list(story.get("pages") or [])
    segments = _time_pages(pages, duration)
    return {
        "id": story.get("id", "story"),
        "title": str(story.get("title") or "Storybook"),
        "theme": str(story.get("theme") or "story"),
        "word": str(story.get("word") or segments[0]["word"] if segments else "STORY"),
        "visual_mode": "storybook",
        "engine": "kids_storybook",
        "duration": float(duration),
        "seed": int(seed),
        "closing": "The end. Sweet dreams!",
        "engage_intro": f"Let's read {story.get('title') or 'a story'} together!",
        "segments": segments,
    }


def _story_from_ai(params: dict[str, Any], seed: int, duration: float) -> dict[str, Any] | None:
    title = str(params.get("ai_title") or params.get("title") or "").strip()
    beats = params.get("ai_segment_plan") or params.get("ai_visual_beats") or []
    voices = [str(v) for v in (params.get("ai_voice_lines") or []) if str(v).strip()]
    words = [str(w).upper() for w in (params.get("focus_words") or []) if str(w).strip()]
    if not title and not beats and not voices:
        return None
    pages: list[dict[str, Any]] = []
    if isinstance(beats, list) and beats:
        for i, beat in enumerate(beats[:8]):
            if not isinstance(beat, dict):
                continue
            word = str(beat.get("word") or (words[i % len(words)] if words else "STORY")).upper()
            headline = str(beat.get("overlay_text") or beat.get("title") or beat.get("headline") or f"Page {i + 1}")
            voice = str(beat.get("voice_line") or (voices[i] if i < len(voices) else headline))
            pages.append(
                {
                    "headline": headline[:48],
                    "body": str(beat.get("caption") or beat.get("fact") or beat.get("body") or "")[:120],
                    "voice_line": voice[:160],
                    "word": word[:24],
                    "image_brief": str(beat.get("image_brief") or f"a friendly {word.lower()} in a picture book"),
                }
            )
    elif voices:
        for i, voice in enumerate(voices[:6]):
            word = words[i % len(words)] if words else "STORY"
            pages.append(
                {
                    "headline": voice[:36],
                    "body": voice[:80],
                    "voice_line": voice[:160],
                    "word": word,
                }
            )
    if not pages:
        pages = [{"headline": title or "Story time", "body": "", "voice_line": title or "Let's read a story.", "word": words[0] if words else "STORY"}]
    return _lesson_from_story(
        {"id": "ai_story", "title": title or "Story time", "theme": "story", "word": pages[0]["word"], "pages": pages},
        seed,
        duration,
    )


def build_storybook_lesson(
    seed: int,
    duration: float,
    *,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a timed kids story lesson. AI fields win when present."""
    params = params or {}
    existing = params.get("education_lesson")
    if isinstance(existing, dict) and existing.get("segments"):
        lesson = dict(existing)
        lesson["duration"] = float(duration)
        lesson["seed"] = int(seed)
        return lesson
    ai_lesson = _story_from_ai(params, seed, duration)
    if ai_lesson:
        return ai_lesson
    rng = np.random.default_rng(seed)
    story_id = str(params.get("story_id") or "").strip()
    if story_id:
        match = next((s for s in STORIES if s["id"] == story_id), None)
        story = match or STORIES[int(rng.integers(0, len(STORIES)))]
    else:
        story = STORIES[int(rng.integers(0, len(STORIES)))]
    return _lesson_from_story(story, seed, duration)
