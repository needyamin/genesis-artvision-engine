"""Tests for the randomizer and deterministic seeding."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.core.randomizer import ENGINE_DEFAULT_STYLE, Randomizer
from app.gui.branding import app_icon_path, app_logo_path
from app.utils.validation import load_config

KEEP_ENGINES = {"kids_storybook", "how_it_works", "trend_brief"}
KEEP_STYLES = {"storybook", "classroom", "pulse"}


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
    assert not (a.engine == b.engine and a.style == b.style and a.params == b.params)


def test_forced_engine_style():
    cfg = load_config()
    rnd = Randomizer(cfg)
    spec = rnd.create_project(
        seed=42,
        engine="trend_brief",
        style="pulse",
        resolution="1080x1080",
        fps=24,
        duration=15,
    )
    assert spec.engine == "trend_brief"
    assert spec.style == "pulse"
    assert (spec.width, spec.height) == (1080, 1080)
    assert spec.fps == 24
    assert spec.duration == 15


def test_random_engine_stays_on_kept_engines():
    cfg = load_config()
    rnd = Randomizer(cfg)
    engines = {
        rnd.create_project(seed=s, resolution="1280x720", fps=30, duration=10).engine
        for s in range(1, 80)
    }
    styles = {
        rnd.create_project(seed=s, resolution="1280x720", fps=30, duration=10).style
        for s in range(1, 80)
    }
    assert engines <= KEEP_ENGINES
    assert styles <= KEEP_STYLES


def test_forced_trend_brief_stays_trend_brief():
    cfg = load_config()
    rnd = Randomizer(cfg)
    spec = rnd.create_project(
        seed=7,
        engine="trend_brief",
        style="classroom",
        resolution="1280x720",
        fps=30,
        duration=10,
    )
    assert spec.engine == "trend_brief"


def test_styles_prefer_matching_engines():
    cfg = load_config()
    rnd = Randomizer(cfg)
    story = {
        rnd.create_project(seed=s, style="storybook", resolution="1280x720", fps=30, duration=10).engine
        for s in range(1, 20)
    }
    class_room = {
        rnd.create_project(seed=s, style="classroom", resolution="1280x720", fps=30, duration=10).engine
        for s in range(1, 20)
    }
    pulse = {
        rnd.create_project(seed=s, style="pulse", resolution="1280x720", fps=30, duration=10).engine
        for s in range(1, 20)
    }
    assert story == {"kids_storybook"}
    assert class_room == {"how_it_works"}
    assert pulse == {"trend_brief"}


def test_random_pairs_engine_with_its_default_style():
    cfg = load_config()
    rnd = Randomizer(cfg)
    for seed in range(1, 40):
        spec = rnd.create_project(seed=seed, resolution="1280x720", fps=30, duration=10)
        assert spec.style == ENGINE_DEFAULT_STYLE[spec.engine]
    for engine, style in ENGINE_DEFAULT_STYLE.items():
        spec = rnd.create_project(seed=3, engine=engine, resolution="1280x720", fps=30, duration=10)
        assert spec.engine == engine
        assert spec.style == style
