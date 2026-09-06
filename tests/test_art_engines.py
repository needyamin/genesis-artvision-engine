"""Tests for art engines."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.art.base import ensure_engines_loaded, get_engine, list_engines
from app.art.edit_brain import STYLE_MOTION, style_motion
from app.art.styles import STYLE_EDIT, list_styles
from app.core.randomizer import ENGINE_PARAM_SPECS, Randomizer
from app.utils.validation import load_config

REQUIRED_ENGINES = [
    "kids_storybook",
    "how_it_works",
    "trend_brief",
]
REQUIRED_STYLES = [
    "storybook",
    "classroom",
    "pulse",
]


def test_all_engines_registered():
    ensure_engines_loaded()
    engines = list_engines()
    for name in ENGINE_PARAM_SPECS:
        assert name in engines, f"missing engine {name}"
    assert set(engines) == set(REQUIRED_ENGINES)


def test_new_engines_are_parallel():
    ensure_engines_loaded()
    assert get_engine("kids_storybook").parallel_frames is True
    assert get_engine("how_it_works").parallel_frames is True
    assert get_engine("trend_brief").parallel_frames is True


def test_each_engine_renders_frame():
    cfg = load_config()
    rnd = Randomizer(cfg)
    ensure_engines_loaded()
    for name in list_engines():
        spec = rnd.create_project(
            seed=12345,
            engine=name,
            resolution="320x180",
            fps=10,
            duration=1,
        )
        engine = get_engine(name)
        engine.setup(320, 180, 10, spec.seed, spec.params, spec.palette())
        frame = engine.render_frame(0, 10)
        engine.cleanup()
        assert frame.shape == (180, 320, 3)
        assert frame.dtype == np.uint8


def test_deterministic_frames():
    cfg = load_config()
    rnd = Randomizer(cfg)
    spec = rnd.create_project(seed=999, engine="trend_brief", resolution="160x90", fps=10, duration=1)
    frames = []
    for _ in range(2):
        eng = get_engine("trend_brief")
        eng.setup(160, 90, 10, spec.seed, spec.params, spec.palette())
        frames.append(eng.render_frame(3, 10))
        eng.cleanup()
    assert np.array_equal(frames[0], frames[1])


def test_required_engines_and_styles_are_complete():
    ensure_engines_loaded()
    engines = set(list_engines())
    styles = set(list_styles())
    for name in REQUIRED_ENGINES:
        assert name in engines
        assert name in ENGINE_PARAM_SPECS
    for name in REQUIRED_STYLES:
        assert name in styles
        assert name in STYLE_EDIT
        assert name in STYLE_MOTION
    assert styles == set(REQUIRED_STYLES)


def test_each_style_has_its_own_edit_and_motion():
    signatures = []
    for name in REQUIRED_STYLES:
        edit = STYLE_EDIT[name]
        motion = style_motion(name)
        signatures.append(
            (
                edit["edit_feel"],
                edit["grade"],
                round(float(edit["micro_contrast"]), 3),
                round(motion.speed, 3),
                round(motion.pulse, 3),
                round(motion.noise, 3),
            )
        )
    assert len(set(signatures)) == len(REQUIRED_STYLES)
    assert style_motion("pulse").speed > style_motion("storybook").speed


def test_every_engine_every_style_renders_a_frame():
    cfg = load_config()
    rnd = Randomizer(cfg)
    ensure_engines_loaded()
    for engine_name in REQUIRED_ENGINES:
        for style_name in REQUIRED_STYLES:
            spec = rnd.create_project(
                seed=42,
                engine=engine_name,
                style=style_name,
                resolution="160x90",
                fps=10,
                duration=1,
            )
            assert spec.engine == engine_name
            assert spec.style == style_name
            assert spec.params.get("style") == style_name
            eng = get_engine(engine_name)
            eng.setup(160, 90, 10, spec.seed, spec.params, spec.palette())
            frame = eng.render_frame(2, 10)
            eng.cleanup()
            assert frame.shape == (90, 160, 3)
            assert frame.dtype == np.uint8


def test_kids_storybook_uses_storybook_edit():
    cfg = load_config()
    rnd = Randomizer(cfg)
    spec = rnd.create_project(
        seed=7,
        engine="kids_storybook",
        style="pulse",
        resolution="320x180",
        fps=10,
        duration=5,
    )
    assert spec.params["edit_feel"] == "kids_show"
    assert spec.params["grade"] == "pastel"
    assert spec.params["style"] == "pulse"


def test_remaining_styles_keep_distinct_grades():
    cfg = load_config()
    rnd = Randomizer(cfg)
    story = rnd.create_project(seed=11, engine="kids_storybook", style="storybook", resolution="160x90", fps=10, duration=1)
    classroom = rnd.create_project(seed=11, engine="how_it_works", style="classroom", resolution="160x90", fps=10, duration=1)
    pulse = rnd.create_project(seed=11, engine="trend_brief", style="pulse", resolution="160x90", fps=10, duration=1)
    assert story.params["grade"] == "pastel"
    assert classroom.params["grade"] == "soft"
    assert pulse.params["grade"] == "vivid"
