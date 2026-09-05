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
        engine="particles",
        style="cosmic",
        width=320,
        height=180,
        fps=10,
        duration=3.0,
        params={"count": 400, "speed": 1.0},
        palette_name="test",
        palette_colors=[[1.0, 0.0, 0.0], [0.0, 0.0, 1.0]],
    )
    base.update(kwargs)
    return ProjectSpec(**base)


def test_clamp_param_overrides_drops_unknown_and_clamps():
    out = clamp_param_overrides(
        "particles",
        {"count": 99999, "speed": -5, "not_a_param": 1, "trail": 0.9},
    )
    assert "not_a_param" not in out
    assert out["count"] <= 1200
    assert out["speed"] >= 0.3
    assert 0.85 <= out["trail"] <= 0.98


def test_parse_creative_direction_from_fenced_json():
    raw = """```json
    {"style": "playful", "param_overrides": {"bounce": 0.8}, "focus_letters": ["a", "B", "!!"]}
    ```"""
    d = parse_creative_direction(raw, engine="alphabet_cartoon")
    assert d.style == "playful"
    assert d.focus_letters == ["A", "B"]
    assert "bounce" in d.param_overrides


def test_apply_creative_direction_mutates_spec():
    spec = _spec(engine="alphabet_cartoon", params={"mode": "lesson"})
    direction = parse_creative_direction(
        {
            "lesson_theme": "phonics",
            "focus_letters": ["M"],
            "focus_words": ["MOON"],
            "voice_lines": ["M is for moon"],
            "fun_facts": ["The moon lights the night."],
            "palette_colors": [[255, 200, 100], [40, 80, 200]],
        },
        engine="alphabet_cartoon",
    )
    apply_creative_direction(spec, direction)
    assert spec.params["lesson_theme"] == "phonics"
    assert spec.params["focus_letters"] == ["M"]
    assert spec.params["ai_voice_lines"] == ["M is for moon"]
    assert spec.params["ai_applied"] is True
    assert spec.palette_colors[0][0] == pytest.approx(1.0, abs=0.01)


def test_suggest_skips_without_key(tmp_path: Path):
    config = _cfg(tmp_path)
    with patch.dict("os.environ", {}, clear=True):
        # Ensure key absent even if user has one in real env for this process patch
        with patch("app.ai.advisor.has_api_key", return_value=False):
            assert suggest_for_spec(_spec(), config) is None


def test_suggest_uses_cache(tmp_path: Path):
    config = _cfg(tmp_path)
    cache = Path(config["ai"]["cache_dir"])
    cache.mkdir(parents=True)
    # Pre-seed cache with known key pattern by calling suggest once with mocked chat
    fake = json.dumps({"style": "minimal", "param_overrides": {"speed": 0.5}})
    with patch("app.ai.advisor.has_api_key", return_value=True):
        with patch("app.ai.advisor.chat_completion", return_value=fake) as mock_chat:
            first = suggest_for_spec(_spec(), config)
            assert first is not None
            assert first.style == "cosmic"
            assert first.param_overrides.get("speed") == 0.5
            assert mock_chat.call_count == 1
            second = suggest_for_spec(_spec(), config)
            assert second is not None
            assert second.style == "cosmic"
            assert mock_chat.call_count == 1  # cache hit


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


def test_education_lesson_honors_focus_letters():
    from app.art.education_content import build_education_lesson

    lesson = build_education_lesson(
        42,
        20.0,
        params={
            "lesson_theme": "letter_of_day",
            "focus_letters": ["Q", "X"],
            "focus_words": ["QUEEN", "X-RAY"],
            "ai_voice_lines": ["Q is for queen", "X is for x-ray"],
        },
    )
    assert lesson["letters"][:2] == ["Q", "X"]
    assert lesson["segments"][0]["word"] == "QUEEN"


def test_offline_generate_with_ai_disabled(tmp_path: Path):
    config = load_config()
    config["ai"] = {"enabled": False, "per_video": False}
    config["output"] = {"directory": str(tmp_path / "out"), "thumbnail": False, "bitrate": "1M"}
    config["temp"] = {"directory": str(tmp_path / "temp"), "keep_on_failure": False}
    factory_config = config
    # Smoke: create_project still works; advisor path not required
    spec = Randomizer(factory_config).create_project(seed=7, engine="particles", duration=1.0)
    out = maybe_enrich_spec(spec, factory_config)
    assert out.params.get("ai_applied") is not True


def test_schema_v2_clamps_visual_audio_and_easing():
    raw = {
        "glow": 9.0,
        "blur": -1,
        "contrast": 0.1,
        "animation_speed": 99,
        "easing": "snappy",
        "camera_feel": "drift",
        "grade": "cinematic",
        "segment_weights": [3, 1, 2],
        "audio_profile": {
            "tempo_bpm": 999,
            "energy": 1.5,
            "scale": "soft_minor",
            "pad_brightness": 0.4,
            "chime_density": 0.8,
            "voice_rate": 0.95,
            "voice_pitch": 1.2,
            "unknown": "drop-me",
        },
        "param_overrides": {"glow": 0.2, "not_a_param": 1},
    }
    d = parse_creative_direction(raw, engine="particles")
    assert d.glow == 1.0
    assert d.blur == 0.0
    assert d.contrast == 0.5
    assert d.animation_speed == 2.0
    assert d.easing == "snappy"
    assert d.camera_feel == "drift"
    assert d.grade == "cinematic"
    assert d.audio_profile["tempo_bpm"] == 180.0
    assert d.audio_profile["energy"] == 1.0
    assert d.audio_profile["scale"] == "soft_minor"
    assert "unknown" not in d.audio_profile
    assert "voice_rate" not in d.audio_profile
    assert d.segment_weights == []
    assert d.param_overrides["glow"] == 0.2
    assert "not_a_param" not in d.param_overrides
    bogus = parse_creative_direction({"easing": "robotic", "grade": "hdr"}, engine="particles")
    assert bogus.easing is None
    assert bogus.grade is None


def test_chosen_style_and_engine_stay_locked():
    spec = _spec(
        engine="particles",
        style="digital",
        params={
            "glow": 0.95,
            "animation_speed": 1.4,
            "contrast": 0.95,
            "blur": 0.4,
            "style_multipliers": {"glow": 0.95, "speed": 1.4, "contrast": 0.95, "density": 0.5},
        },
    )
    direction = parse_creative_direction(
        {"style": "minimal", "glow": 0.25},
        engine="particles",
        style="digital",
    )
    apply_creative_direction(spec, direction)
    assert spec.engine == "particles"
    assert spec.style == "digital"
    assert spec.params["glow"] == 0.25
    assert spec.params["ai_applied"] is True


def test_audio_profile_passthrough_and_visual_params():
    spec = _spec(engine="alphabet_cartoon", params={"mode": "lesson", "bounce": 0.5})
    direction = parse_creative_direction(
        {
            "glow": 0.4,
            "blur": 0.2,
            "contrast": 0.9,
            "animation_speed": 0.8,
            "easing": "floaty",
            "camera_feel": "pulse",
            "grade": "pastel",
            "audio_profile": {"tempo_bpm": 96, "scale": "pentatonic", "energy": 0.4},
            "segment_weights": [2, 1, 1, 1.5],
        },
        engine="alphabet_cartoon",
    )
    apply_creative_direction(spec, direction)
    assert spec.params["glow"] == 0.4
    assert spec.params["easing"] == "floaty"
    assert spec.params["camera_feel"] == "pulse"
    assert spec.params["grade"] == "pastel"
    assert spec.params["audio_profile"]["tempo_bpm"] == 96
    assert spec.params["audio_profile"]["scale"] == "pentatonic"
    assert spec.params["segment_weights"] == [2.0, 1.0, 1.0, 1.5]


def test_kids_voice_line_not_overwritten_by_intro():
    from app.art.education_content import (
        build_education_lesson,
        build_hand_art_lesson,
        build_kids_doodle_lesson,
    )

    ai_line = "M is for moon and magic"
    lesson = build_education_lesson(
        42,
        20.0,
        params={
            "lesson_theme": "letter_of_day",
            "focus_letters": ["M"],
            "focus_words": ["MOON"],
            "ai_voice_lines": [ai_line],
        },
    )
    assert lesson["segments"][0]["voice_line"] == ai_line
    doodle = build_kids_doodle_lesson(
        7,
        18.0,
        params={"lesson_theme": "shape_fun", "ai_voice_lines": ["This is a circle we love"]},
    )
    shape = str(doodle["segments"][0].get("shape") or "")
    voice = doodle["segments"][0]["voice_line"].lower()
    assert shape.lower() in voice
    hand = build_hand_art_lesson(
        9,
        18.0,
        params={"ai_voice_lines": ["Let's draw a house together"]},
    )
    hv = hand["segments"][0]["voice_line"].lower()
    assert str(hand["segments"][0].get("doodle_kind") or "").lower() in hv or str(
        hand["segments"][0].get("word") or ""
    ).lower() in hv


def test_segment_weights_change_timing():
    from app.art.education_content import build_education_lesson

    even = build_education_lesson(3, 20.0, params={"focus_letters": ["A", "B", "C", "D"]})
    uneven = build_education_lesson(
        3,
        20.0,
        params={
            "focus_letters": ["A", "B", "C", "D"],
            "segment_weights": [4, 1, 1, 1],
        },
    )
    even_span = even["segments"][0]["t1"] - even["segments"][0]["t0"]
    uneven_span = uneven["segments"][0]["t1"] - uneven["segments"][0]["t0"]
    assert uneven_span > even_span


def test_visual_beats_parse_and_apply():
    d = parse_creative_direction(
        {
            "title": "Letter Party",
            "visual_beats": [
                {
                    "image": "a red apple in sunshine",
                    "overlay_text": "A is for Apple",
                    "word": "apple",
                    "letter": "a",
                }
            ],
        },
        engine="alphabet_cartoon",
    )
    assert d.title == "Letter Party"
    assert d.visual_beats[0]["word"] == "APPLE"
    assert d.visual_beats[0]["letter"] == "A"
    assert "apple" in d.visual_beats[0]["image_brief"]
    spec = _spec(engine="alphabet_cartoon", params={"mode": "lesson"})
    apply_creative_direction(spec, d)
    assert spec.params["ai_title"] == "Letter Party"
    assert spec.params["ai_visual_beats"][0]["overlay_text"] == "A is for Apple"


def test_offline_illustrator_and_realize(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from app.ai.realize import realize_visual_assets
    from app.art import offline_illustrator

    monkeypatch.setattr(offline_illustrator, "scene_dir", lambda: tmp_path)
    spec = _spec(
        engine="particles",
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


def test_kids_lesson_uses_ai_overlay_text():
    from app.art.education_content import build_education_lesson

    lesson = build_education_lesson(
        1,
        12.0,
        params={
            "lesson_theme": "letter_of_day",
            "focus_letters": ["A"],
            "ai_visual_beats": [
                {
                    "word": "APPLE",
                    "overlay_text": "Look, an apple!",
                    "image_brief": "a red apple",
                    "voice_line": "A is for apple",
                }
            ],
        },
    )
    assert lesson["segments"][0]["overlay_text"] == "Look, an apple!"
    assert lesson["segments"][0]["line"] == "Look, an apple!"
    assert lesson["segments"][0]["voice_line"] == "A is for apple"


def test_ai_overlay_on_abstract_frame(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    import numpy as np

    from app.ai.realize import realize_visual_assets
    from app.art import offline_illustrator
    from app.video.overlays import apply_ai_overlays

    monkeypatch.setattr(offline_illustrator, "scene_dir", lambda: tmp_path)
    spec = _spec(
        engine="particles",
        width=160,
        height=90,
        params={
            "ai_applied": True,
            "ai_visual_beats": [
                {"image_brief": "a yellow sun", "overlay_text": "Sunshine", "word": "SUN"}
            ],
        },
    )
    realize_visual_assets(spec)
    frame = np.zeros((90, 160, 3), dtype=np.uint8)
    out = apply_ai_overlays(frame, spec, 0, 10)
    assert out.shape == frame.shape
    assert out.dtype == np.uint8
    assert np.array_equal(out, frame)


def test_load_dotenv_from_file(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    from app.utils.dotenv import load_dotenv

    env_file = tmp_path / ".env"
    env_file.write_text('OPENROUTER_API_KEY="sk-or-v1-test-key"\n', encoding="utf-8")
    monkeypatch.delenv("OPENROUTER_API_KEY", raising=False)
    loaded = load_dotenv(env_file, override=True)
    assert loaded == env_file
    assert os.environ.get("OPENROUTER_API_KEY") == "sk-or-v1-test-key"


def test_visual_engine_strips_kids_direction():
    d = parse_creative_direction(
        {
            "lesson_theme": "phonics",
            "focus_letters": ["A", "B"],
            "focus_words": ["APPLE"],
            "voice_lines": ["A is for apple"],
            "fun_facts": ["Apples are fruit."],
            "visual_beats": [
                {
                    "image_brief": "a red apple in sunshine",
                    "overlay_text": "A is for Apple",
                    "letter": "A",
                    "word": "APPLE",
                    "voice_line": "A is for apple",
                },
                {
                    "image_brief": "deep blue nebula clouds",
                    "overlay_text": "Deep Drift",
                },
            ],
        },
        engine="galaxy",
    )
    assert d.lesson_theme is None
    assert d.focus_letters == []
    assert d.focus_words == []
    assert d.voice_lines == []
    assert d.fun_facts == []
    assert d.visual_beats == []
    assert d.title is None


def test_ai_does_not_switch_engine_or_inject_abc():
    spec = _spec(engine="particles", params={"count": 400})
    direction = parse_creative_direction(
        {
            "style": "playful",
            "lesson_theme": "abc_complete",
            "focus_letters": ["A", "Z"],
            "voice_lines": ["Let's learn A to Z"],
            "visual_beats": [{"overlay_text": "A is for Ant", "letter": "A", "image_brief": "an ant"}],
        },
        engine="particles",
    )
    apply_creative_direction(spec, direction)
    assert spec.engine == "particles"
    assert spec.style == "cosmic"
    assert "focus_letters" not in spec.params
    assert "lesson_theme" not in spec.params
    assert "ai_voice_lines" not in spec.params
    assert "ai_visual_beats" not in spec.params
    assert "ai_title" not in spec.params
    assert spec.params.get("ai_applied") is True


def test_advisor_prompt_matches_engine():
    from app.ai.prompts import ENGINE_GUIDES, STYLE_GUIDES, advisor_user_prompt

    visual = advisor_user_prompt(
        seed=1, engine="galaxy", style="cosmic", duration=10, width=1920, height=1080, params={}
    )
    assert "Engine=galaxy + Style=cosmic" in visual
    assert "Galaxy / Starfield" in visual
    assert "Cosmic:" in visual
    assert "No titles" in visual or "no titles" in visual.lower()
    assert '"visual_beats"' not in visual.split("Return JSON", 1)[-1]
    assert '"focus_letters"' not in visual.split("Return JSON", 1)[-1]

    abc = advisor_user_prompt(
        seed=1,
        engine="alphabet_cartoon",
        style="playful",
        duration=10,
        width=1920,
        height=1080,
        params={"mode": "lesson"},
    )
    assert "Engine=alphabet_cartoon + Style=playful" in abc
    assert "letter" in abc.lower()
    assert "alphabet_cartoon" in abc

    doodle = advisor_user_prompt(
        seed=1, engine="kids_doodles", style="organic", duration=10, width=1920, height=1080, params={}
    )
    assert "Engine=kids_doodles + Style=organic" in doodle
    assert "Shapes & Colors" in doodle
    assert "full alphabet A–Z" in doodle or "full alphabet" in doodle.lower()
    assert '"focus_letters"' not in doodle.split("Return JSON", 1)[-1]

    playful_galaxy = advisor_user_prompt(
        seed=1, engine="galaxy", style="playful", duration=10, width=1920, height=1080, params={}
    )
    assert "Playful look only" in playful_galaxy
    assert "KIDS ALPHABET RULES" not in playful_galaxy

    for engine in ENGINE_GUIDES:
        for style in STYLE_GUIDES:
            text = advisor_user_prompt(
                seed=3, engine=engine, style=style, duration=8, width=640, height=360, params={}
            )
            assert f"Engine={engine} + Style={style}" in text
            assert ENGINE_GUIDES[engine].split(":")[0] in text or engine in text
