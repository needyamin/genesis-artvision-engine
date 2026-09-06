"""Tests for prompt-to-video planning (offline)."""

from __future__ import annotations

from unittest.mock import patch

from app.ai.prompt_brief import (
    classify_engine,
    detect_resolution,
    enrich_from_user_prompt,
    extract_title,
    offline_direction_from_prompt,
    prompt_seed,
    suggested_duration,
)
from app.core.randomizer import ProjectSpec


def test_classify_kids_story():
    engine, style = classify_engine("a bedtime story about a cat named Luna")
    assert engine == "kids_storybook"
    assert style == "storybook"


def test_classify_how_it_works():
    engine, style = classify_engine("Explain how rain is made, step by step")
    assert engine == "how_it_works"
    assert style == "classroom"


def test_classify_trend():
    engine, style = classify_engine("Why everyone is talking about viral AI agents this week")
    assert engine == "trend_brief"
    assert style == "pulse"


def test_classify_hint_wins():
    engine, style = classify_engine("a bedtime story", hint="how_it_works")
    assert engine == "how_it_works"
    assert style == "classroom"


def test_prompt_seed_is_stable():
    assert prompt_seed("Luna the cat") == prompt_seed("luna  the   cat")
    assert prompt_seed("Luna the cat") != prompt_seed("Luna the dog")


def test_detect_resolution_quality_and_vertical():
    assert detect_resolution("a calm story", "1080") == "1920x1080"
    assert detect_resolution("a calm story", "4k") == "3840x2160"
    assert detect_resolution("make a tiktok vertical short", "1080") == "1080x1920"


def test_offline_kids_direction_has_beats_and_words():
    d = offline_direction_from_prompt(
        "A bedtime story about a brave orange cat who finds the moon.",
        "kids_storybook",
        "storybook",
    )
    assert d.title
    assert d.visual_beats
    assert d.voice_lines
    assert d.focus_words
    assert d.grade == "soft"
    assert any(b.get("word") for b in d.visual_beats)


def test_offline_explainer_direction():
    d = offline_direction_from_prompt(
        "Explain how rain is made. The sun lifts water. Clouds form. Rain falls back.",
        "how_it_works",
        "classroom",
    )
    assert len(d.visual_beats) >= 4
    assert d.voice_lines
    assert d.grade == "cinematic"


def test_suggested_duration_covers_speech():
    assert suggested_duration("Short.") >= 30
    long_prompt = ". ".join(f"Sentence number {i} is spoken clearly" for i in range(8))
    assert suggested_duration(long_prompt) >= 48


def test_enrich_offline_sets_prompt_source():
    spec = ProjectSpec(
        project_id="art_1",
        seed=1,
        engine="kids_storybook",
        style="storybook",
        width=320,
        height=180,
        fps=10,
        duration=8.0,
        params={"user_prompt": "A story about a cat and the moon.", "prompt_mode": "offline"},
    )
    enrich_from_user_prompt(spec, {"ai": {"enabled": False}})
    assert spec.params["prompt_source"] == "offline"
    assert spec.params["ai_title"]
    assert spec.params["ai_visual_beats"]


def test_ai_mode_falls_back_without_key():
    spec = ProjectSpec(
        project_id="art_1",
        seed=1,
        engine="how_it_works",
        style="classroom",
        width=320,
        height=180,
        fps=10,
        duration=10.0,
        params={
            "user_prompt": "How does a rainbow appear in the sky after rain?",
            "prompt_mode": "ai",
        },
    )
    with patch("app.ai.prompt_brief.has_api_key", return_value=False):
        enrich_from_user_prompt(spec, {"ai": {"enabled": True, "per_video": True}})
    assert spec.params["prompt_source"] == "offline"
    assert spec.params["ai_voice_lines"]


def test_extract_title_is_short():
    title = extract_title("The brave orange cat finds the moon behind the rain.")
    assert title
    assert len(title) <= 48
