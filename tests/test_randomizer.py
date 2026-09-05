"""Tests for the randomizer and deterministic seeding."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.randomizer import Randomizer
from app.gui.branding import app_icon_path, app_logo_path
from app.utils.validation import load_config


def test_app_icon_files_exist():
    assert app_logo_path().is_file()
    assert app_icon_path().is_file()


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
        style="cosmic",
        resolution="1080x1080",
        fps=24,
        duration=15,
    )
    assert spec.engine == "particles"
    assert spec.style == "cosmic"
    assert (spec.width, spec.height) == (1080, 1080)
    assert spec.fps == 24
    assert spec.duration == 15


def test_random_engine_stays_on_visual_art():
    cfg = load_config()
    rnd = Randomizer(cfg)
    engines = {
        rnd.create_project(seed=s, resolution="1280x720", fps=30, duration=10).engine
        for s in range(1, 80)
    }
    kids = {"alphabet_cartoon", "hand_art", "kids_doodles", "infographic_explainer"}
    assert engines.isdisjoint(kids)
    assert engines <= {"particles", "galaxy", "waves", "tunnel"}


def test_explicit_education_engine_is_kept():
    cfg = load_config()
    rnd = Randomizer(cfg)
    spec = rnd.create_project(
        seed=7,
        engine="alphabet_cartoon",
        style="cosmic",
        resolution="1280x720",
        fps=30,
        duration=10,
    )
    assert spec.engine == "alphabet_cartoon"


def test_playful_style_can_pick_kids_engines():
    cfg = load_config()
    rnd = Randomizer(cfg)
    engines = {
        rnd.create_project(
            seed=s, style="playful", resolution="1280x720", fps=30, duration=10
        ).engine
        for s in range(1, 40)
    }
    assert engines <= {"alphabet_cartoon", "kids_doodles", "hand_art"}
