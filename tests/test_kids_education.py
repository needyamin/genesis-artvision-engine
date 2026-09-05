"""Tests for kids education content and offline voice."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.art.education_content import (
    EASY_SPELL_WORDS,
    build_education_lesson,
    build_hand_art_lesson,
    build_kids_doodle_lesson,
    build_lesson_for_engine,
    choose_spell_word,
)
from app.art.fonts import load_font, paint_text, usable_caption
from app.audio.kids_education import generate_kids_education_audio
from app.audio.offline_tts import kids_narration_lines, speak_text
from app.audio.procedural_voice import synthesize_speech, text_to_phonemes
from PIL import Image, ImageDraw


def test_kids_doodle_lesson_has_segments():
    lesson = build_kids_doodle_lesson(42, 30.0)
    assert lesson["engine"] == "kids_doodles"
    assert len(lesson["segments"]) >= 3
    seg = lesson["segments"][0]
    assert "voice_line" in seg
    assert "shape" in seg or "color_name" in seg or "count" in seg or "word" in seg


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


def test_usable_caption_drops_lone_dot():
    assert usable_caption(".") == ""
    assert usable_caption(".", "A is for APPLE") == "A is for APPLE"
    assert usable_caption("A is for APPLE") == "A is for APPLE"


def test_paint_text_is_visible():
    img = Image.new("RGB", (320, 80), (255, 255, 255))
    draw = ImageDraw.Draw(img)
    paint_text(draw, (160, 40), "HELLO KIDS", load_font(28), (40, 55, 80), anchor="mm")
    arr = np.array(img)
    dark = np.all(arr < 90, axis=2).sum()
    assert dark > 80


def test_alphabet_lesson_paints_headline_not_only_dots():
    from app.art.base import ensure_engines_loaded, get_engine
    from app.art.kids_layout import kids_layout
    from app.art.palette import generate_palette

    ensure_engines_loaded()
    lesson = {
        "theme": "abc",
        "title": "Letter Fun",
        "visual_mode": "lesson",
        "engine": "alphabet_cartoon",
        "letters": ["A"],
        "segments": [
            {
                "index": 0,
                "t0": 0.0,
                "t1": 1.0,
                "letter": "A",
                "word": "APPLE",
                "motif": "APPLE",
                "overlay_text": "A is for APPLE",
                "line": "A is for APPLE",
                "phonics": "A says /a/",
                "fact": "Apples grow on trees",
                "tip": "Say it out loud!",
            }
        ],
        "closing": "Great job!",
    }
    pal = generate_palette(np.random.default_rng(3), "pastel")
    eng = get_engine("alphabet_cartoon")
    eng.setup(
        640,
        360,
        10,
        3,
        {
            "mode": "lesson",
            "education_lesson": lesson,
            "show_word_images": False,
            "show_motifs": False,
            "sparkle": 0.0,
        },
        pal,
    )
    frame = eng.render_frame(8, 20)
    eng.cleanup()
    L = kids_layout(640, 360)
    band = frame[L.caption.y0 + 6 : L.caption.y0 + 42, L.caption.x0 + 16 : L.caption.x1 - 16]
    target = np.array([40, 55, 80], dtype=np.int16)
    close = int(np.all(np.abs(band.astype(np.int16) - target) < 40, axis=2).sum())
    assert close > 40, f"expected headline pixels, found {close}"


def test_kids_doodles_paints_title_banner():
    from app.art.base import ensure_engines_loaded, get_engine
    from app.art.palette import generate_palette

    ensure_engines_loaded()
    pal = generate_palette(np.random.default_rng(5), "pastel")
    eng = get_engine("kids_doodles")
    eng.setup(
        640,
        360,
        10,
        5,
        {"show_word_images": False, "show_captions": True},
        pal,
    )
    frame = eng.render_frame(4, 16)
    title = str(getattr(eng, "lesson_title", "Doodle"))
    eng.cleanup()
    from app.art.kids_layout import kids_layout

    L = kids_layout(640, 360)
    band = frame[L.title.y0 : L.title.y1, L.title.x0 + 20 : L.title.x1 - 80]
    target = np.array([40, 60, 90], dtype=np.int16)
    close = int(np.all(np.abs(band.astype(np.int16) - target) < 45, axis=2).sum())
    assert close > 30, f"expected title {title!r} pixels, found {close}"


def test_kids_narration_includes_playful_lines():
    lines = kids_narration_lines(
        {
            "voice_line": "A is for APPLE",
            "word": "APPLE",
            "fact": "Apples grow on trees",
            "celebrate": "You got it!",
        }
    )
    blob = " ".join(lines).lower()
    assert "apple" in blob
    assert len(lines) >= 2
    assert any("got it" in line.lower() or "trees" in line.lower() for line in lines)


def test_speak_text_offline_fallback(monkeypatch):
    monkeypatch.setattr("app.audio.offline_tts._sapi_cached", lambda *a, **k: None)
    audio = speak_text("Hello kids", sample_rate=22050, seed=3)
    assert audio.dtype == np.float32
    assert len(audio) > 800
    assert float(np.max(np.abs(audio))) <= 1.0


def test_kids_education_audio_mixes_voice(monkeypatch):
    monkeypatch.setattr("app.audio.offline_tts._sapi_cached", lambda *a, **k: None)
    lesson = build_kids_doodle_lesson(1, 6.0)
    audio = generate_kids_education_audio(6.0, 1, lesson, sample_rate=22050)
    assert audio.dtype == np.float32
    assert len(audio) == int(6.0 * 22050)
    assert float(np.max(np.abs(audio))) > 0.05


def test_spell_rejects_first_letter_salad():
    lesson = build_education_lesson(
        11,
        20.0,
        params={
            "mode": "spell",
            "lesson_theme": "word_builder",
            "focus_letters": ["S", "A", "B", "P"],
            "focus_words": ["SUN", "APPLE", "BALL", "PIG"],
            "ai_visual_beats": [
                {"letter": "S", "word": "SUN", "overlay_text": "S is for SUN"},
                {"letter": "A", "word": "APPLE", "overlay_text": "A is for APPLE"},
                {"letter": "B", "word": "BALL", "overlay_text": "B is for BALL"},
                {"letter": "P", "word": "PIG", "overlay_text": "P is for PIG"},
            ],
        },
    )
    assert lesson["visual_mode"] == "spell"
    assert lesson["spell_word"] != "SABP"
    assert lesson["spell_word"] in {"SUN", "APPLE", "BALL", "PIG"}
    assert "".join(lesson["letters"]) == lesson["spell_word"]
    assert all(seg["word"] == lesson["spell_word"] for seg in lesson["segments"])
    assert all(seg["letter"] == lesson["spell_word"][i] for i, seg in enumerate(lesson["segments"]))
    assert "SABP" not in (lesson["segments"][0].get("overlay_text") or "")


def test_letter_lesson_keeps_different_words():
    lesson = build_education_lesson(
        11,
        20.0,
        params={
            "mode": "lesson",
            "lesson_theme": "letter_of_day",
            "focus_letters": ["S", "A"],
            "focus_words": ["SUN", "APPLE"],
        },
    )
    assert lesson["visual_mode"] != "spell"
    assert lesson["letters"][:2] == ["S", "A"]
    assert lesson["segments"][0]["word"] == "SUN"
    assert lesson["segments"][1]["word"] == "APPLE"


def test_kids_pop_grows_smoothly():
    from app.art.education_anim import kids_pop

    assert kids_pop(0.0) == 0.0
    assert kids_pop(1.0) >= 0.95
    assert kids_pop(0.5) > kids_pop(0.2)


def test_real_world_math_lesson_teaches_counting():
    lesson = build_education_lesson(21, 30.0, params={"lesson_theme": "real_world_math"})
    assert lesson["theme"] == "real_world_math"
    assert lesson["segments"]
    for seg in lesson["segments"]:
        assert seg.get("kind") == "math"
        assert seg.get("math_op") in {"+", "-"}
        voice = str(seg["voice_line"]).lower()
        assert "plus" in voice or "take away" in voice
        assert any(ch.isdigit() for ch in voice)
        assert "=" in str(seg.get("overlay_text") or "")
        lines = kids_narration_lines(seg)
        blob = " ".join(lines).lower()
        assert "plus" in blob or "take away" in blob


def test_dictionary_lesson_spells_and_defines():
    lesson = build_education_lesson(
        8,
        24.0,
        params={"lesson_theme": "dictionary", "focus_words": ["CAT"]},
    )
    assert lesson["theme"] == "dictionary"
    seg = lesson["segments"][0]
    assert seg.get("kind") == "dictionary"
    assert seg["word"] == "CAT"
    voice = str(seg["voice_line"]).upper()
    assert "C." in voice and "A." in voice and "T." in voice
    meaning = str(seg.get("fact") or "").lower()
    assert "cat" in meaning and ("pet" in meaning or "meow" in meaning)
    lines = kids_narration_lines(seg)
    blob = " ".join(lines).lower()
    assert "cat" in blob
    assert "pet" in blob or "meow" in blob


def test_doodle_math_and_dictionary_themes():
    math_lesson = build_kids_doodle_lesson(5, 30.0, params={"lesson_theme": "real_world_math"})
    assert math_lesson["visual_mode"] == "count"
    assert math_lesson["segments"][0].get("math_op") in {"+", "-"}
    dict_lesson = build_kids_doodle_lesson(5, 30.0, params={"lesson_theme": "dictionary"})
    assert dict_lesson["visual_mode"] == "stickers"
    assert dict_lesson["segments"][0].get("kind") == "dictionary"
    assert dict_lesson["segments"][0].get("spell_word")
    assert "say" in str(dict_lesson["segments"][0]["voice_line"]).lower()


def test_kids_ssml_is_slow_and_pauses_letters():
    from app.audio.offline_tts import _ssml_for

    ssml = _ssml_for(["Cat. C. A. T. A cat is a pet.", "1. 2. 3."], 10, kids=True)
    assert 'rate="slow"' in ssml
    assert "<break time=" in ssml
    assert "C<break" in ssml.replace(" ", "")
    assert "1<break" in ssml.replace(" ", "")
    adult = _ssml_for(["Hello there."], 0, kids=False)
    assert 'rate="medium"' in adult


def test_choose_spell_word_skips_initials():
    rng = np.random.default_rng(0)
    word = choose_spell_word(
        rng,
        focus_words=["SUN", "APPLE", "BALL", "PIG"],
        focus_letters=["S", "A", "B", "P"],
    )
    assert word != "SABP"
    assert word in {"SUN", "APPLE", "BALL", "PIG"} or word in EASY_SPELL_WORDS


def test_kids_layout_regions_do_not_overlap():
    from itertools import combinations

    from app.art.kids_layout import kids_layout

    for w, h in ((1920, 1080), (1080, 1920), (1080, 1080), (640, 360), (3840, 2160)):
        layout = kids_layout(w, h)
        for a, b in combinations((layout.title, layout.stage, layout.picture, layout.caption), 2):
            assert not a.overlaps(b), f"{w}x{h}: {a} overlaps {b}"
        assert layout.stage.contains(*layout.letter_xy)
        assert layout.picture.contains(*layout.picture_xy)
        assert layout.caption.contains(*layout.bubble_xy)
        assert layout.title.contains(layout.counter.cx, layout.counter.cy)


def test_alphabet_letter_stays_in_stage_card():
    from app.art.base import ensure_engines_loaded, get_engine
    from app.art.kids_layout import kids_layout
    from app.art.palette import generate_palette

    ensure_engines_loaded()
    lesson = {
        "theme": "abc",
        "title": "Letter Fun",
        "visual_mode": "lesson",
        "engine": "alphabet_cartoon",
        "letters": ["A"],
        "segments": [
            {
                "index": 0,
                "t0": 0.0,
                "t1": 1.0,
                "letter": "A",
                "word": "APPLE",
                "overlay_text": "A is for APPLE",
                "line": "A is for APPLE",
                "phonics": "A says /a/",
                "fact": "Apples grow on trees",
                "tip": "Say it!",
            }
        ],
        "closing": "Great job!",
    }
    pal = generate_palette(np.random.default_rng(3), "pastel")
    eng = get_engine("alphabet_cartoon")
    eng.setup(
        1920,
        1080,
        10,
        3,
        {
            "mode": "lesson",
            "education_lesson": lesson,
            "show_word_images": False,
            "show_motifs": False,
            "sparkle": 0.0,
            "show_lowercase": False,
        },
        pal,
    )
    frame = eng.render_frame(12, 24)
    layout = kids_layout(1920, 1080)
    eng.cleanup()
    sx0, sy0, sx1, sy1 = layout.stage.xy
    stage = frame[sy0:sy1, sx0:sx1]
    # Big letter ink lives in the stage card, not the caption or title.
    strong = int(np.any(stage < 80, axis=2).sum())
    assert strong > 400, f"expected letter ink in stage, found {strong}"
    cap = frame[layout.caption.y0 : layout.caption.y1, layout.caption.x0 : layout.caption.x1]
    caption_ink = int(np.all(np.abs(cap.astype(np.int16) - np.array([40, 55, 80])) < 40, axis=2).sum())
    assert caption_ink > 80, f"expected caption text, found {caption_ink}"
    title_band = frame[layout.title.y0 : layout.title.y1, layout.title.x0 : layout.title.x1]
    white = int(np.all(title_band > 230, axis=2).sum())
    assert white > 200, f"expected title bar, found {white}"


def test_math_theme_ignores_spell_mode():
    lesson = build_education_lesson(
        4,
        24.0,
        params={"lesson_theme": "real_world_math", "mode": "spell"},
    )
    assert lesson["visual_mode"] == "lesson"
    assert lesson["spell_word"] == ""
    assert lesson["segments"][0]["kind"] == "math"
    voice = lesson["segments"][0]["voice_line"].lower()
    word = str(lesson["segments"][0]["word"]).lower()
    assert word in voice or word.rstrip("s") in voice
    assert "plus" in voice or "take away" in voice


def test_letter_word_voice_and_image_stay_together():
    lesson = build_education_lesson(
        3,
        20.0,
        params={
            "lesson_theme": "letter_of_day",
            "mode": "spell",
            "focus_letters": ["B"],
            "focus_words": ["MOON"],
            "ai_voice_lines": ["M is for moon"],
            "ai_visual_beats": [
                {
                    "letter": "M",
                    "word": "MOON",
                    "voice_line": "M is for moon",
                    "overlay_text": "M is for MOON",
                    "image_brief": "a yellow sun in the sky",
                }
            ],
        },
    )
    assert lesson["visual_mode"] != "spell"
    seg = lesson["segments"][0]
    assert seg["letter"] == "B"
    assert str(seg["word"]).startswith("B")
    blob = f"{seg['voice_line']} {seg['overlay_text']} {seg.get('image_brief') or ''}".lower()
    assert str(seg["word"]).lower() in blob
    assert "m is for moon" not in str(seg["voice_line"]).lower()


def test_kids_engine_mode_follows_lesson():
    from app.art.base import ensure_engines_loaded, get_engine
    from app.art.palette import generate_palette

    ensure_engines_loaded()
    lesson = build_education_lesson(8, 12.0, params={"lesson_theme": "real_world_math", "mode": "spell"})
    pal = generate_palette(np.random.default_rng(1), "playful")
    eng = get_engine("alphabet_cartoon")
    eng.setup(
        320,
        180,
        10,
        8,
        {"mode": "spell", "education_lesson": lesson, "show_word_images": False, "sparkle": 0.0},
        pal,
    )
    assert eng.mode == "lesson"
    frame = eng.render_frame(4, 12)
    eng.cleanup()
    assert frame.shape == (180, 320, 3)

