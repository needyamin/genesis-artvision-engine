"""Tests for the randomizer and deterministic seeding."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.randomizer import Randomizer
from app.utils.validation import load_config


def test_same_seed_same_spec():
    cfg = load_config()
    rnd = Randomizer(cfg)
    a = rnd.create_project(seed=847293847, resolution="1280x720", fps=30, duration=10)
    b = rnd.create_project(seed=847293847, resolution="1280x720", fps=30, duration=10)
    assert a.seed == b.seed == 847293847
    assert a.engine == b.engine
    assert a.style == b.style
    assert a.params == b.params
    assert a.palette_colors == b.palette_colors


def test_different_seeds_differ():
    cfg = load_config()
    rnd = Randomizer(cfg)
    a = rnd.create_project(seed=1, resolution="1280x720", fps=30, duration=10)
    b = rnd.create_project(seed=2, resolution="1280x720", fps=30, duration=10)
    assert a.seed != b.seed
    # Extremely unlikely all match
    assert not (a.engine == b.engine and a.style == b.style and a.params == b.params)


def test_forced_engine_style():
    cfg = load_config()
    rnd = Randomizer(cfg)
    spec = rnd.create_project(
        seed=42,
        engine="particles",
        style="neon",
        resolution="1080x1080",
        fps=24,
        duration=15,
    )
    assert spec.engine == "particles"
    assert spec.style == "neon"
    assert (spec.width, spec.height) == (1080, 1080)
    assert spec.fps == 24
    assert spec.duration == 15
