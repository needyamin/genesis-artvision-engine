"""Tests for optional OpenRouter AI advisor (offline / mocked)."""

from __future__ import annotations

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest

from app.ai.advisor import apply_creative_direction, maybe_enrich_spec, suggest_for_spec
from app.ai.client import AIClientError
from app.ai.curate import merge_catalogs, parse_curate_payload
from app.ai.schemas import clamp_param_overrides, parse_creative_direction
from app.core.randomizer import ProjectSpec, Randomizer
from app.utils.validation import load_config


def _cfg(tmp_path: Path, **ai_overrides) -> dict:
    config = load_config()
    ai = dict(config.get("ai") or {})
    ai.update(
        {
            "enabled": True,
            "per_video": True,
            "cache_dir": str(tmp_path / "cache"),
            "catalog_dir": str(tmp_path / "catalogs"),
        }
    )
    ai.update(ai_overrides)
    config["ai"] = ai
    return config


def _spec(**kwargs) -> ProjectSpec:
    base = dict(
        project_id="art_00000001",
        seed=1,
        engine="trend_brief",
        style="pulse",
        width=320,
        height=180,
        fps=10,
        duration=3.0,
        params={"energy": 0.9},
        palette_name="test",
        palette_colors=[[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
    )
    base.update(kwargs)
    return ProjectSpec(**base)


def test_clamp_param_overrides_drops_unknown_and_clamps():
    out = clamp_param_overrides(
        "trend_brief",
        {"energy": 99, "not_a_param": 1, "ticker_speed": 0.8},
    )
    assert "not_a_param" not in out
    assert out["energy"] <= 1.20
    assert 0.45 <= out["ticker_speed"] <= 1.40


def test_parse_creative_direction_from_fenced_json():
    raw = """```json
    {"style": "storybook", "param_overrides": {"paper_warmth": 0.8}, "focus_words": ["cat"]}
    ```"""
    d = parse_creative_direction(raw, engine="kids_storybook")
    assert d.style == "storybook"
    assert d.focus_words == ["CAT"]
    assert "paper_warmth" in d.param_overrides


def test_apply_creative_direction_mutates_spec():
    spec = _spec(engine="kids_storybook", style="storybook", params={})
    direction = parse_creative_direction(
        {
            "title": "Luna the Cat",
            "focus_words": ["CAT"],
            "voice_lines": ["This is Luna."],
            "palette_colors": [[255, 200, 100], [40, 80, 200]],
        },
        engine="kids_storybook",
    )
    apply_creative_direction(spec, direction)
    assert spec.params["ai_title"] == "Luna the Cat"
    assert spec.params["ai_voice_lines"] == ["This is Luna."]
    assert spec.params["ai_applied"] is True
    assert spec.palette_colors[0][0] == pytest.approx(1.0, abs=0.01)


def test_suggest_skips_without_key(tmp_path: Path):
    config = _cfg(tmp_path)
    with patch.dict("os.environ", {}, clear=True):
        with patch("app.ai.advisor.has_api_key", return_value=False):
            assert suggest_for_spec(_spec(), config) is None


def test_suggest_uses_cache(tmp_path: Path):
    config = _cfg(tmp_path)
    cache = Path(config["ai"]["cache_dir"])
    cache.mkdir(parents=True)
    fake = json.dumps({"style": "classroom", "param_overrides": {"energy": 0.7}})
    with patch("app.ai.advisor.has_api_key", return_value=True):
        with patch("app.ai.advisor.chat_completion", return_value=fake) as mock_chat:
            first = suggest_for_spec(_spec(), config)
            assert first is not None
            assert first.style == "pulse"
            assert first.param_overrides.get("energy") == 0.7
            assert mock_chat.call_count == 1
            second = suggest_for_spec(_spec(), config)
            assert second is not None
            assert second.style == "pulse"
            assert mock_chat.call_count == 1


def test_suggest_failure_falls_back(tmp_path: Path):
    config = _cfg(tmp_path)
    with patch("app.ai.advisor.has_api_key", return_value=True):
        with patch("app.ai.advisor.chat_completion", side_effect=AIClientError("boom")):
            assert suggest_for_spec(_spec(), config) is None


def test_maybe_enrich_respects_per_video_flag(tmp_path: Path):
    config = _cfg(tmp_path, enabled=True, per_video=False)
    spec = _spec()
    with patch("app.ai.advisor.suggest_for_spec") as mock_s:
        out = maybe_enrich_spec(spec, config)
        mock_s.assert_not_called()
        assert out is spec


def test_parse_and_merge_curate_payload():
    raw = {
        "words": {"A": ["APPLE", "ANT"], "b": ["BALL"]},
        "fun_facts": {"A": ["Ants work hard."]},
        "voice_lines": {"A": ["A is for apple"]},
    }
    parsed = parse_curate_payload(raw)
    assert parsed["words"]["A"] == ["APPLE", "ANT"]
    assert "B" in parsed["words"]
    merged = merge_catalogs(parsed, {"words": {"A": ["AIRPLANE"]}, "fun_facts": {}, "voice_lines": {}})
    assert "AIRPLANE" in merged["words"]["A"]
    assert "APPLE" in merged["words"]["A"]


def test_offline_generate_with_ai_disabled(tmp_path: Path):
    config = load_config()
    config["ai"] = {"enabled": False, "per_video": False}
    config["output"] = {"directory": str(tmp_path / "out"), "thumbnail": False, "bitrate": "1M"}
    config["temp"] = {"directory": str(tmp_path / "temp"), "keep_on_failure": False}
    spec = Randomizer(config).create_project(seed=7, engine="trend_brief", duration=1.0)
    out = maybe_enrich_spec(spec, config)
    assert out.params.get("ai_applied") is not True


def test_schema_clamps_visual_audio_and_easing():
    raw = {
        "glow": 9.0,
        "blur": -1,
        "contrast": 0.1,
        "animation_speed": 99,
        "easing": "snappy",
        "camera_feel": "drift",
        "grade": "cinematic",
        "audio_profile": {
            "tempo_bpm": 999,
            "energy": 1.5,
            "scale": "soft_minor",
            "unknown": "drop-me",
        },
        "param_overrides": {"glow": 0.2, "not_a_param": 1},
    }
    d = parse_creative_direction(raw, engine="how_it_works")
    assert d.glow == 1.0
    assert d.blur == 0.0
    assert d.contrast == 0.5
    assert d.animation_speed == 2.0
    assert d.easing == "snappy"
    assert d.camera_feel == "drift"
    assert d.grade == "cinematic"
    assert d.audio_profile["tempo_bpm"] == 180.0
    assert d.audio_profile["energy"] == 1.0
    assert "unknown" not in d.audio_profile
    assert d.param_overrides["glow"] == 0.2
    bogus = parse_creative_direction({"easing": "robotic", "grade": "hdr"}, engine="how_it_works")
    assert bogus.easing is None
    assert bogus.grade is None


def test_chosen_style_and_engine_stay_locked():
    spec = _spec(engine="trend_brief", style="pulse", params={"glow": 0.95})
    direction = parse_creative_direction(
        {"style": "storybook", "glow": 0.25},
        engine="trend_brief",
        style="pulse",
    )
    apply_creative_direction(spec, direction)
    assert spec.engine == "trend_brief"
    assert spec.style == "pulse"
    assert spec.params["glow"] == 0.25
    assert spec.params["ai_applied"] is True


def test_audio_profile_passthrough_and_visual_params():
    spec = _spec(engine="kids_storybook", style="storybook", params={})
    direction = parse_creative_direction(
        {
            "glow": 0.4,
            "easing": "floaty",
            "camera_feel": "pulse",
            "grade": "pastel",
            "audio_profile": {"tempo_bpm": 96, "scale": "pentatonic", "energy": 0.4},
        },
        engine="kids_storybook",
    )
    apply_creative_direction(spec, direction)
    assert spec.params["glow"] == 0.4
    assert spec.params["easing"] == "floaty"
    assert spec.params["camera_feel"] == "pulse"
    assert spec.params["grade"] == "pastel"
    assert spec.params["audio_profile"]["tempo_bpm"] == 96


def test_offline_illustrator_and_realize(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from app.ai.realize import realize_visual_assets
    from app.art import offline_illustrator

    monkeypatch.setattr(offline_illustrator, "scene_dir", lambda: tmp_path)
    spec = _spec(
        engine="trend_brief",
        params={
            "ai_applied": True,
            "ai_visual_beats": [
                {
                    "image_brief": "a blue star at night",
                    "overlay_text": "Night Star",
                    "word": "STAR",
                }
            ],
        },
    )
    realize_visual_assets(spec)
    beat = spec.params["ai_visual_beats"][0]
    assert "image_path" not in beat
    parsed = offline_illustrator.parse_image_brief("a red apple in the garden", fallback_word="FUN")
    assert parsed["subject"] == "APPLE"
    assert parsed["color"] == "red"
    assert parsed["setting"] == "garden"


def test_load_dotenv_from_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from app.utils.dotenv import load_dotenv

    env_file = tmp_path / ".env"
    env_file.write_text('OPENROUTER_API_KEY="sk-or-v1-test-key"\n', encoding="utf-8")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    loaded = load_dotenv(env_file, override=True)
    assert loaded == env_file
    assert os.environ.get("OPENROUTER_API_KEY") == "sk-or-v1-test-key"


def test_unknown_engine_strips_topic_fields():
    d = parse_creative_direction(
        {
            "title": "Chip Shortage Talk",
            "fun_facts": ["Fabs are the new oil."],
            "voice_lines": ["Chip supply is the story this week."],
            "visual_beats": [{"overlay_text": "Why chips are news"}],
        },
        engine="unknown_engine",
    )
    assert d.title is None
    assert d.visual_beats == []
    assert d.fun_facts == []
    assert d.voice_lines == []


def test_ai_does_not_switch_engine():
    spec = _spec(engine="how_it_works", style="classroom", params={})
    direction = parse_creative_direction(
        {
            "style": "pulse",
            "title": "A Viral Meme",
        },
        engine="how_it_works",
        style="classroom",
    )
    apply_creative_direction(spec, direction)
    assert spec.engine == "how_it_works"
    assert spec.style == "classroom"
    assert spec.params["ai_title"] == "A Viral Meme"
    assert spec.params.get("ai_applied") is True


def test_advisor_prompt_matches_engine():
    from app.ai.prompts import ENGINE_GUIDES, STYLE_GUIDES, advisor_user_prompt

    for engine in ENGINE_GUIDES:
        for style in STYLE_GUIDES:
            text = advisor_user_prompt(
                seed=3, engine=engine, style=style, duration=8, width=640, height=360, params={}
            )
            assert f"Engine={engine} + Style={style}" in text
            assert ENGINE_GUIDES[engine].split(":")[0] in text or engine in text


def test_trend_brief_keeps_topic_fields():
    trend = parse_creative_direction(
        {
            "title": "Chip Shortage Talk",
            "fun_facts": ["Fabs are the new oil."],
            "voice_lines": ["Chip supply is the story this week."],
            "metrics": [{"label": "Lead time", "val": "26", "unit": "weeks"}],
            "visual_beats": [
                {
                    "phase": "HOOK",
                    "overlay_text": "Why chips are news",
                    "caption": "A shortage headline is everywhere.",
                    "fact": "This week",
                    "voice_line": "Chip supply is the story this week.",
                }
            ],
        },
        engine="trend_brief",
        style="pulse",
    )
    assert trend.title == "Chip Shortage Talk"
    spec = _spec(engine="trend_brief", style="pulse", params={"energy": 0.9})
    apply_creative_direction(spec, trend)
    assert spec.params["ai_title"] == "Chip Shortage Talk"
    assert spec.params["ai_visual_beats"]
    assert spec.params["ai_metrics"]


def test_how_it_works_and_storybook_prompts():
    from app.ai.prompts import advisor_user_prompt

    trend = advisor_user_prompt(
        seed=1, engine="trend_brief", style="pulse", duration=10, width=1920, height=1080, params={}
    )
    assert "currently trending internet topic" in trend.lower() or "TRENDING" in trend
    assert "visual_beats" in trend.split("Return JSON", 1)[-1]

    story = advisor_user_prompt(
        seed=1, engine="kids_storybook", style="storybook", duration=10, width=1920, height=1080, params={}
    )
    assert "Kids Storybook" in story

    how = advisor_user_prompt(
        seed=1, engine="how_it_works", style="classroom", duration=10, width=1920, height=1080, params={}
    )
    assert "How It Works" in how
    assert "visual_beats" in how.split("Return JSON", 1)[-1]
