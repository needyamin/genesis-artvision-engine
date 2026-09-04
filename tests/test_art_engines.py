"""Tests for art engines."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.art.base import ensure_engines_loaded, get_engine, list_engines
from app.art.palette import generate_palette
from app.core.randomizer import ENGINE_PARAM_SPECS, Randomizer
from app.utils.validation import load_config


def test_all_engines_registered():
    ensure_engines_loaded()
    engines = list_engines()
    for name in ENGINE_PARAM_SPECS:
        assert name in engines, f"missing engine {name}"


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
    spec = rnd.create_project(seed=999, engine="geometric", resolution="160x90", fps=10, duration=1)
    frames = []
    for _ in range(2):
        eng = get_engine("geometric")
        eng.setup(160, 90, 10, spec.seed, spec.params, spec.palette())
        frames.append(eng.render_frame(3, 10))
        eng.cleanup()
    assert np.array_equal(frames[0], frames[1])
