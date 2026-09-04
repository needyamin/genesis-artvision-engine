"""Tests for kids education content and offline voice."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.art.education_content import (
    build_hand_art_lesson,
    build_kids_doodle_lesson,
    build_lesson_for_engine,
)
from app.audio.procedural_voice import synthesize_speech, text_to_phonemes


def test_kids_doodle_lesson_has_segments():
    lesson = build_kids_doodle_lesson(42, 30.0)
    assert lesson["engine"] == "kids_doodles"
    assert len(lesson["segments"]) >= 3
    seg = lesson["segments"][0]
    assert "voice_line" in seg
    assert "shape" in seg or "color_name" in seg or "count" in seg


def test_hand_art_lesson_has_draw_steps():
    lesson = build_hand_art_lesson(99, 20.0)
    assert lesson["engine"] == "hand_art"
    assert lesson["segments"][0].get("doodle_kind")
    assert lesson["segments"][0].get("steps")


def test_lesson_factory_routes_engines():
    for engine in ("alphabet_cartoon", "kids_doodles", "hand_art"):
        lesson = build_lesson_for_engine(engine, 7, 15.0)
        assert lesson is not None
        assert lesson["engine"] == engine


def test_voice_synthesis_offline():
    phonemes = text_to_phonemes("A is for apple")
    assert len(phonemes) > 3
    audio = synthesize_speech("Hello kids", sample_rate=22050, seed=1)
    assert audio.dtype == np.float32
    assert len(audio) > 1000
    assert float(np.max(np.abs(audio))) <= 1.0
