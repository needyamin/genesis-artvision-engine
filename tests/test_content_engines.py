"""Tests for kids storybook, how-it-works, and trending-brief engines."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.art.base import ensure_engines_loaded, get_engine, list_engines
from app.art.how_it_works_content import PROCESSES, build_how_it_works_topic
from app.art.storybook_content import STORIES, build_storybook_lesson
from app.art.trend_content import TRENDS, build_trend_topic
from app.audio.offline_tts import kids_narration_lines
from app.core.randomizer import ENGINE_DEFAULT_STYLE, ENGINE_PARAM_SPECS, Randomizer
from app.utils.validation import load_config

NEW_ENGINES = ("kids_storybook", "how_it_works", "trend_brief")


def test_new_engines_registered_with_param_specs():
    ensure_engines_loaded()
    engines = set(list_engines())
    for name in NEW_ENGINES:
        assert name in engines
        assert name in ENGINE_PARAM_SPECS


def test_offline_catalogs_have_enough_entries():
    assert len(STORIES) >= 8
    assert len(PROCESSES) >= 8
    assert len(TRENDS) >= 8
    for story in STORIES:
        assert story["title"]
        assert 4 <= len(story["pages"]) <= 8
    for process in PROCESSES:
        assert process["title"]
        assert len(process["segments"]) >= 4
    for trend in TRENDS:
        assert trend["title"]
        assert len(trend["segments"]) >= 4


def test_builders_are_seed_stable():
    a = build_storybook_lesson(42, 12.0)
    b = build_storybook_lesson(42, 12.0)
    assert a["title"] == b["title"]
    assert a["segments"][0]["word"] == b["segments"][0]["word"]

    t1 = build_how_it_works_topic(7, 16.0)
    t2 = build_how_it_works_topic(7, 16.0)
    assert t1["id"] == t2["id"]
    assert t1["segments"][0]["headline"] == t2["segments"][0]["headline"]

    r1 = build_trend_topic(9, 16.0)
    r2 = build_trend_topic(9, 16.0)
    assert r1["id"] == r2["id"]


def test_ai_fields_fill_builders():
    lesson = build_storybook_lesson(
        1,
        10.0,
        params={
            "ai_title": "Pip the Pup",
            "ai_voice_lines": ["Meet Pip.", "Pip finds a ball."],
            "focus_words": ["PUP", "BALL"],
            "ai_visual_beats": [
                {"overlay_text": "Meet Pip", "caption": "A small brown pup.", "word": "PUP", "voice_line": "Meet Pip."},
                {"overlay_text": "A red ball", "caption": "Pip finds a ball.", "word": "BALL", "voice_line": "Pip finds a ball."},
            ],
        },
    )
    assert lesson["title"] == "Pip the Pup"
    assert lesson["segments"][0]["word"] == "PUP"

    topic = build_how_it_works_topic(
        1,
        12.0,
        params={
            "ai_title": "How Bread Toasts",
            "ai_fun_facts": ["Heat dries the slice."],
            "ai_voice_lines": ["Heat dries the slice.", "Then it browns."],
            "ai_visual_beats": [
                {"phase": "HEAT", "overlay_text": "Heat first", "caption": "The coil glows.", "fact": "Infrared"},
                {"phase": "BROWN", "overlay_text": "Then brown", "caption": "Sugars caramelize.", "fact": "Maillard"},
            ],
            "ai_metrics": [{"label": "Temp", "val": "150", "unit": "C"}],
        },
    )
    assert topic["title"] == "How Bread Toasts"
    assert topic["metrics"][0]["label"] == "Temp"
    assert topic["segments"][0]["phase"] == "HEAT"

    trend = build_trend_topic(
        1,
        12.0,
        params={
            "ai_title": "A Viral Meme Format",
            "ai_fun_facts": ["A new template is everywhere this week."],
            "ai_visual_beats": [
                {"phase": "HOOK", "overlay_text": "It spread overnight", "caption": "One clip, then a thousand copies."},
            ],
        },
    )
    assert trend["title"] == "A Viral Meme Format"
    assert trend["hook"].startswith("A new template")


def test_each_new_engine_renders_seed_stable_frame():
    cfg = load_config()
    rnd = Randomizer(cfg)
    ensure_engines_loaded()
    for name in NEW_ENGINES:
        spec = rnd.create_project(
            seed=4242,
            engine=name,
            resolution="160x90",
            fps=10,
            duration=1,
        )
        assert spec.engine == name
        frames = []
        for _ in range(2):
            eng = get_engine(name)
            eng.setup(160, 90, 10, spec.seed, spec.params, spec.palette())
            frames.append(eng.render_frame(3, 10))
            eng.cleanup()
        assert frames[0].shape == (90, 160, 3)
        assert frames[0].dtype == np.uint8
        assert np.array_equal(frames[0], frames[1])


def test_catalogs_keep_distinct_concepts():
    story_titles = {s["title"] for s in STORIES}
    process_titles = {p["title"] for p in PROCESSES}
    trend_titles = {t["title"] for t in TRENDS}
    assert not story_titles & process_titles
    assert not story_titles & trend_titles
    assert not process_titles & trend_titles
    for story in STORIES:
        for page in story["pages"]:
            voice = str(page["voice_line"])
            assert page["word"]
            assert "A is for" not in voice
            assert "Say " not in voice
    for process in PROCESSES:
        assert process["schematic_type"]
        assert all(seg.get("headline") and seg.get("voice_line") for seg in process["segments"])


def test_how_it_works_diagram_matches_the_process():
    assert "schematic_type" not in ENGINE_PARAM_SPECS["how_it_works"]
    heart = build_how_it_works_topic(1, 16.0, topic_id="heartbeat", params={"schematic_type": "cycle"})
    assert heart["id"] == "heartbeat"
    assert heart["schematic_type"] == "heart"
    assert heart["title"] == "How Your Heart Beats"
    fridge = build_how_it_works_topic(1, 16.0, topic_id="fridge_cold")
    assert fridge["diagram_labels"][:4] == ["Evap", "Pump", "Coils", "Loop"]
    toast = build_how_it_works_topic(
        1,
        12.0,
        params={
            "ai_title": "How Bread Toasts",
            "ai_fun_facts": ["Heat dries the slice."],
            "ai_visual_beats": [
                {"phase": "HEAT", "overlay_text": "Heat first", "caption": "The coil glows."},
                {"phase": "BROWN", "overlay_text": "Then brown", "caption": "Sugars caramelize."},
            ],
        },
    )
    assert toast["schematic_type"] == "heat"


def test_storybook_pages_speak_the_story():
    lesson = build_storybook_lesson(1, 12.0, params={"story_id": "luna_the_cat"})
    assert lesson["title"] == "Luna the Cat"
    seg = lesson["segments"][0]
    assert seg["kind"] == "story"
    assert seg["word"] == "CAT"
    lines = kids_narration_lines(seg)
    assert lines == [seg["voice_line"]]
    blob = " ".join(lines).lower()
    assert "great job" not in blob
    assert "say cat with me" not in blob


def test_engine_without_style_uses_matching_look():
    cfg = load_config()
    rnd = Randomizer(cfg)
    for engine, style in ENGINE_DEFAULT_STYLE.items():
        spec = rnd.create_project(seed=9, engine=engine, resolution="160x90", fps=10, duration=1)
        assert spec.style == style
    for seed in range(1, 40):
        spec = rnd.create_project(seed=seed, resolution="160x90", fps=10, duration=1)
        assert spec.style == ENGINE_DEFAULT_STYLE[spec.engine]


def test_story_pages_hold_until_speech_finishes(monkeypatch):
    import numpy as np

    from app.audio.kids_education import fit_lesson_to_narration
    from app.audio import kids_education as kids_mod

    sr = 8000
    monkeypatch.setattr(
        kids_mod,
        "speak_narration",
        lambda lines, **kwargs: np.ones(int(5.0 * sr), dtype=np.float32),
    )
    lesson = build_storybook_lesson(1, 8.0, params={"story_id": "luna_the_cat"})
    new_dur = fit_lesson_to_narration(lesson, seed=1, sample_rate=sr, min_duration=8.0)
    assert lesson["segments"][-1]["t1"] == 1.0
    for seg in lesson["segments"]:
        span = (float(seg["t1"]) - float(seg["t0"])) * new_dur
        assert span + 1e-6 >= float(seg["speech_lead"]) + float(seg["speech_seconds"])


def test_explainer_beats_hold_until_speech_finishes(monkeypatch):
    import numpy as np

    from app.audio.documentary_soundtrack import fit_topic_to_narration
    from app.audio import documentary_soundtrack as doc_mod

    sr = 8000
    monkeypatch.setattr(
        doc_mod,
        "speak_documentary",
        lambda lines, **kwargs: np.ones(int(6.0 * sr), dtype=np.float32),
    )
    topic = build_how_it_works_topic(1, 10.0, topic_id="heartbeat")
    new_dur = fit_topic_to_narration(topic, seed=1, sample_rate=sr, min_duration=10.0)
    assert topic["speech_synced"] is True
    assert topic["segments"][-1]["t1"] == 1.0
    for seg in topic["segments"]:
        span = (float(seg["t1"]) - float(seg["t0"])) * new_dur
        assert span + 1e-6 >= float(seg["speech_lead"]) + float(seg["speech_seconds"])
    assert new_dur >= 10.0

