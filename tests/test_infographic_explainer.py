"""Unit tests for the new informative infographic documentary engine, knowledge content, and audio."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.art.base import ensure_engines_loaded, get_engine, list_engines
from app.art.knowledge_content import (
    KNOWLEDGE_TOPICS,
    build_knowledge_topic,
    get_topic_by_id,
    list_domains,
    list_topic_ids,
)
from app.art.palette import generate_palette
from app.art.styles import list_styles
from app.audio.documentary_soundtrack import generate_documentary_audio
from app.audio.offline_tts import documentary_narration_lines
from app.core.randomizer import ENGINE_PARAM_SPECS, Randomizer
from app.utils.validation import load_config


def test_knowledge_content_integrity():
    """Verify all knowledge topics contain required factual fields and narrative segments."""
    assert len(KNOWLEDGE_TOPICS) >= 8
    topic_ids = list_topic_ids()
    assert len(topic_ids) == len(set(topic_ids)), "Topic IDs must be unique"
    domains = list_domains()
    assert "astronomy" in domains
    assert "earth_science" in domains
    assert "technology" in domains
    assert "biology" in domains

    for topic in KNOWLEDGE_TOPICS:
        assert topic["id"]
        assert topic["domain"] in domains
        assert topic["title"]
        assert len(topic["segments"]) == 4, f"Topic {topic['id']} must have 4 timeline phases"
        assert len(topic["metrics"]) >= 3, f"Topic {topic['id']} should have at least 3 metrics"
        for seg in topic["segments"]:
            assert seg["phase"]
            assert seg["headline"]
            assert seg["body"]
            assert seg["voice_line"]


def test_build_knowledge_topic_timing():
    """Verify timed segment boundaries are monotonically increasing and span [0.0, 1.0]."""
    topic = build_knowledge_topic(12345, 20.0, domain="astronomy")
    assert topic["domain"] == "astronomy"
    assert len(topic["segments"]) == 4
    prev_t1 = 0.0
    for seg in topic["segments"]:
        assert seg["t0"] == prev_t1
        assert seg["t1"] > seg["t0"]
        prev_t1 = seg["t1"]
    assert np.isclose(prev_t1, 1.0)


def test_infographic_explainer_registered():
    """Verify infographic_explainer is loaded in registry and param specs."""
    ensure_engines_loaded()
    engines = list_engines()
    assert "infographic_explainer" in engines
    assert "infographic_explainer" in ENGINE_PARAM_SPECS


def test_infographic_explainer_renders_landscape_and_portrait():
    """Verify infographic_explainer renders both landscape and vertical HD aspect ratios."""
    cfg = load_config()
    rnd = Randomizer(cfg)
    ensure_engines_loaded()

    # Landscape
    spec_land = rnd.create_project(
        seed=42,
        engine="infographic_explainer",
        resolution="320x180",
        fps=10,
        duration=1,
    )
    eng_land = get_engine("infographic_explainer")
    eng_land.setup(320, 180, 10, spec_land.seed, spec_land.params, spec_land.palette())
    frame_land = eng_land.render_frame(3, 10)
    eng_land.cleanup()
    assert frame_land.shape == (180, 320, 3)
    assert frame_land.dtype == np.uint8

    # Portrait / vertical
    spec_port = rnd.create_project(
        seed=42,
        engine="infographic_explainer",
        resolution="180x320",
        fps=10,
        duration=1,
    )
    eng_port = get_engine("infographic_explainer")
    eng_port.setup(180, 320, 10, spec_port.seed, spec_port.params, spec_port.palette())
    frame_port = eng_port.render_frame(3, 10)
    eng_port.cleanup()
    assert frame_port.shape == (320, 180, 3)
    assert frame_port.dtype == np.uint8


def test_infographic_explainer_deterministic():
    """Verify identical seeds produce identical frames."""
    cfg = load_config()
    rnd = Randomizer(cfg)
    spec = rnd.create_project(seed=888, engine="infographic_explainer", resolution="240x135", fps=10, duration=1)
    frames = []
    for _ in range(2):
        eng = get_engine("infographic_explainer")
        eng.setup(240, 135, 10, spec.seed, spec.params, spec.palette())
        frames.append(eng.render_frame(5, 10))
        eng.cleanup()
    assert np.array_equal(frames[0], frames[1])


def test_documentary_audio_synthesis():
    """Verify documentary audio generates clean non-silent samples."""
    topic = build_knowledge_topic(999, 3.0, domain="technology")
    audio = generate_documentary_audio(3.0, 999, topic, sample_rate=22050, voice_enabled=False)
    assert isinstance(audio, np.ndarray)
    assert audio.dtype == np.float32
    assert len(audio) == int(3.0 * 22050)
    assert float(np.max(np.abs(audio))) > 0.05
    assert float(np.max(np.abs(audio))) <= 1.0


def test_documentary_narration_lines():
    """Verify documentary narration lines extract clean speech lines."""
    seg = {
        "voice_line": "The James Webb Space Telescope gazes into deep cosmic time.",
        "headline": "Orbiting L2",
        "body": "Located 1.5 million km away.",
    }
    lines = documentary_narration_lines(seg)
    assert len(lines) == 1
    assert "James Webb" in lines[0]


def test_documentary_styles_and_palette():
    """Verify documentary styles and palettes are registered and sample correctly."""
    styles = list_styles()
    for s in ("documentary", "playful", "cosmic"):
        assert s in styles

    rng = np.random.default_rng(101)
    pal = generate_palette(rng, style="documentary")
    assert pal.name
    assert len(pal.colors) >= 5
