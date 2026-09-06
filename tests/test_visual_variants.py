"""Seeded visual-variant selection, replay, and render coverage."""

from __future__ import annotations

import hashlib
import sys
from pathlib import Path

import numpy as np
import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.art.base import ensure_engines_loaded, get_engine
from app.art.brief_layout import brief_layout, brief_layout_variants
from app.art.kids_layout import kids_layout, kids_layout_variants
from app.art.procedural_backgrounds import VARIANTS as PAINT_VARIANTS, paint_background
from app.art.visual_variants import (
    BACKGROUND_VARIANTS,
    CLASSIC_BACKGROUND_VARIANTS,
    CLASSIC_LAYOUT_VARIANTS,
    LAYOUT_VARIANTS,
    VISUAL_VARIANT_VERSION,
    resolve_visual_variants,
    select_visual_variants,
    validate_variant_name,
)
from app.core.randomizer import ProjectSpec, Randomizer
from app.utils.validation import load_config
from app.video.captions import export_manifest

RATIO_CASES = (("320x180", 320, 180), ("180x320", 180, 320), ("240x240", 240, 240))


def _digest(frame: np.ndarray) -> str:
    return hashlib.sha256(np.ascontiguousarray(frame).tobytes()).hexdigest()


def _render(engine_name: str, spec, width: int, height: int, frame_idx: int = 1) -> np.ndarray:
    engine = get_engine(engine_name)
    engine.setup(width, height, spec.fps, spec.seed, spec.params, spec.palette())
    try:
        return engine.render_frame(frame_idx, 8)
    finally:
        engine.cleanup()


def test_registries_match_painters_and_layouts():
    assert set(BACKGROUND_VARIANTS) == set(LAYOUT_VARIANTS) == set(PAINT_VARIANTS)
    for engine, names in BACKGROUND_VARIANTS.items():
        assert names == PAINT_VARIANTS[engine]
        assert CLASSIC_BACKGROUND_VARIANTS[engine] in names
        assert CLASSIC_LAYOUT_VARIANTS[engine] in LAYOUT_VARIANTS[engine]
        for name in names:
            assert validate_variant_name(engine, "background", name) == name
        for name in LAYOUT_VARIANTS[engine]:
            assert validate_variant_name(engine, "layout", name) == name


def test_select_is_deterministic_and_diverse():
    cfg = load_config().get("visual_variation") or {}
    first = select_visual_variants("trend_brief", 4242, cfg)
    again = select_visual_variants("trend_brief", 4242, cfg)
    assert first == again
    backgrounds = {
        select_visual_variants("kids_storybook", seed, cfg).background_variant
        for seed in range(1, 90)
    }
    layouts = {
        select_visual_variants("how_it_works", seed, cfg).layout_variant
        for seed in range(1, 90)
    }
    assert len(backgrounds) >= 3
    assert len(layouts) >= 2


def test_explicit_override_and_disabled_mode():
    cfg = load_config().get("visual_variation") or {}
    chosen = select_visual_variants(
        "how_it_works",
        9,
        cfg,
        background_variant="lab_bench",
        layout_variant="diagram_focus",
    )
    assert chosen.background_variant == "lab_bench"
    assert chosen.layout_variant == "diagram_focus"
    classic = select_visual_variants("how_it_works", 9, {**cfg, "enabled": False})
    assert classic.background_variant == "whiteboard"
    assert classic.layout_variant == "split_right"
    with pytest.raises(ValueError):
        select_visual_variants("trend_brief", 1, cfg, background_variant="desk_stack")


def test_legacy_params_resolve_to_classic_and_board_alias():
    kids = resolve_visual_variants("kids_storybook", {})
    assert kids.background_variant == "desk_stack"
    assert kids.layout_variant == "classic_split"
    chalk = resolve_visual_variants("how_it_works", {"board": "chalkboard"})
    assert chalk.background_variant == "chalkboard"
    explicit = resolve_visual_variants(
        "how_it_works",
        {"board": "chalkboard", "background_variant": "poster_wall"},
    )
    assert explicit.background_variant == "poster_wall"


def test_randomizer_persists_and_replays_variants(tmp_path):
    cfg = load_config()
    rnd = Randomizer(cfg)
    spec = rnd.create_project(seed=777, engine="trend_brief", resolution="320x180", fps=10, duration=2)
    assert spec.params["background_variant"] in BACKGROUND_VARIANTS["trend_brief"]
    assert spec.params["layout_variant"] in LAYOUT_VARIANTS["trend_brief"]
    assert spec.params["visual_variant_version"] == VISUAL_VARIANT_VERSION
    restored = ProjectSpec.from_dict(spec.to_dict())
    assert restored.params["background_variant"] == spec.params["background_variant"]
    assert restored.params["layout_variant"] == spec.params["layout_variant"]
    video = tmp_path / "art.mp4"
    video.write_bytes(b"not-a-real-video")
    manifest = export_manifest(video, restored, caption_path=None, qc={"passed": True})
    payload = manifest.read_text(encoding="utf-8")
    assert spec.params["background_variant"] in payload
    assert spec.params["layout_variant"] in payload


def test_painters_are_deterministic_and_distinct():
    palette = ((0.1, 0.2, 0.3), (0.2, 0.8, 0.6), (0.9, 0.3, 0.4))
    for engine, names in BACKGROUND_VARIANTS.items():
        digests = []
        for name in names:
            first = np.asarray(paint_background(engine, 96, 64, 21, palette, variant=name, t=0.2, beat=0.4))
            second = np.asarray(paint_background(engine, 96, 64, 21, palette, variant=name, t=0.2, beat=0.4))
            assert first.shape == (64, 96, 3)
            assert np.array_equal(first, second)
            digests.append(_digest(first))
        assert len(set(digests)) == len(names)


def test_layouts_stay_safe_for_every_variant():
    for width, height in ((320, 180), (180, 320), (240, 240)):
        for variant in kids_layout_variants():
            layout = kids_layout(width, height, variant=variant)
            assert not layout.stage.overlaps(layout.picture, gap=0)
            assert layout.stage.y1 <= layout.caption.y0
            assert layout.picture.y1 <= layout.caption.y0
        for engine, names in (
            ("how_it_works", brief_layout_variants("how_it_works")),
            ("trend_brief", brief_layout_variants("trend_brief")),
        ):
            for variant in names:
                layout = brief_layout(
                    width,
                    height,
                    ticker=engine == "trend_brief",
                    engine=engine,
                    variant=variant,
                )
                assert layout.header.y1 <= layout.visual.y0 or layout.header.y1 <= layout.card.y0
                assert not (
                    layout.visual.x0 < layout.card.x1
                    and layout.card.x0 < layout.visual.x1
                    and layout.visual.y0 < layout.card.y1
                    and layout.card.y0 < layout.visual.y1
                )


def test_engines_render_every_background_and_layout():
    cfg = load_config()
    rnd = Randomizer(cfg)
    ensure_engines_loaded()
    for engine_name, backgrounds in BACKGROUND_VARIANTS.items():
        layouts = LAYOUT_VARIANTS[engine_name]
        spec = rnd.create_project(
            seed=33,
            engine=engine_name,
            resolution="160x90",
            fps=10,
            duration=1,
        )
        bg_digests = []
        for background in backgrounds:
            spec.params["background_variant"] = background
            spec.params["layout_variant"] = CLASSIC_LAYOUT_VARIANTS[engine_name]
            frame = _render(engine_name, spec, 160, 90)
            assert frame.shape == (90, 160, 3)
            bg_digests.append(_digest(frame))
        assert len(set(bg_digests)) == len(backgrounds)
        layout_digests = []
        for layout_name in layouts:
            spec.params["background_variant"] = CLASSIC_BACKGROUND_VARIANTS[engine_name]
            spec.params["layout_variant"] = layout_name
            frame = _render(engine_name, spec, 160, 90)
            assert frame.shape == (90, 160, 3)
            layout_digests.append(_digest(frame))
        assert len(set(layout_digests)) == len(layouts)


@pytest.mark.parametrize("resolution,width,height", RATIO_CASES)
def test_variant_combo_renders_across_ratios(resolution, width, height):
    cfg = load_config()
    rnd = Randomizer(cfg)
    ensure_engines_loaded()
    for engine_name in BACKGROUND_VARIANTS:
        spec = rnd.create_project(
            seed=51,
            engine=engine_name,
            resolution=resolution,
            fps=10,
            duration=1,
            background_variant=BACKGROUND_VARIANTS[engine_name][2],
            layout_variant=LAYOUT_VARIANTS[engine_name][-1],
        )
        first = _render(engine_name, spec, width, height, 2)
        second = _render(engine_name, spec, width, height, 2)
        assert first.shape == (height, width, 3)
        assert np.array_equal(first, second)
