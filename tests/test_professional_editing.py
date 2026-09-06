"""Regression coverage for the professional automatic-editing pipeline."""

from __future__ import annotations

import json
import sys
import wave
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.art.base import ensure_engines_loaded, get_engine
from app.art.brief_layout import brief_layout, composite_segment_layers
from app.art.editorial import (
    build_editorial_plan,
    finalize_editorial_plan,
    reveal_progress,
    segment_state,
    validate_editorial_plan,
)
from app.art.fonts import load_font, paint_multiline_text
from app.audio.mastering import master_audio
from app.audio.voice_sync import apply_speech_holds
from app.core.randomizer import ProjectSpec, Randomizer
from app.utils.validation import load_config
from app.video.captions import export_manifest, export_srt, inspect_caption_file, overlay_caption_frame
from app.video.ffmpeg import quality_encode_profile
from app.video.qc import inspect_render


def test_editorial_plan_uses_emphasis_and_final_timing():
    segments = [{"voice_line": "Hook"}, {"voice_line": "Explanation"}]
    params = {"segment_weights": [1.5, 0.8]}
    plan = build_editorial_plan(segments, engine="trend_brief", duration=10, params=params)
    duration = apply_speech_holds(segments, [2.0, 2.0], min_duration=5.0)
    finalize_editorial_plan(plan, segments, duration)
    assert segments[0]["hold_seconds"] > 2.0
    assert segments[0]["emphasis_weight"] == 1.5
    assert plan["shots"][0]["caption"] == "Hook"
    assert plan["shots"][-1]["end"] == duration
    assert segment_state(segments[0], segments[0]["t0"])["enter"] == 0.0
    assert validate_editorial_plan(plan) == []


def test_srt_manifest_and_project_replay(tmp_path: Path):
    cfg = load_config()
    spec = Randomizer(cfg).create_project(
        seed=77,
        engine="how_it_works",
        resolution="320x180",
        duration=4,
        edit_preset="master",
    )
    spec.params["user_prompt"] = "private creative brief"
    plan = {
        "shots": [
            {"caption_start": 0.25, "caption_end": 2.5, "caption": "A verified caption."}
        ]
    }
    video = tmp_path / "sample.mp4"
    srt = export_srt(video, plan)
    manifest = export_manifest(video, spec, caption_path=srt, qc={"passed": True})
    assert srt and "00:00:00,250 --> 00:00:02,500" in srt.read_text(encoding="utf-8")
    manifest_data = json.loads(manifest.read_text(encoding="utf-8"))
    assert manifest_data["qc"]["passed"] is True
    assert "user_prompt" not in manifest_data["spec"]["params"]
    assert manifest_data["ai"]["prompt_sha256"]
    restored = ProjectSpec.from_dict(spec.to_dict())
    assert restored.to_dict() == spec.to_dict()
    assert restored.params["edit_preset"] == "master"


def test_audio_mastering_respects_peak_ceiling():
    signal = np.sin(np.linspace(0, 100, 44100, dtype=np.float32)) * 0.03
    mastered = master_audio(signal, target_lufs=-14.0, ceiling_dbfs=-1.0)
    assert mastered.dtype == np.float32
    assert float(np.max(np.abs(mastered))) <= 10 ** (-1.0 / 20.0) + 1e-5
    assert float(np.sqrt(np.mean(mastered * mastered))) > float(np.sqrt(np.mean(signal * signal)))


def test_audio_qc_detects_silence(tmp_path: Path):
    wav_path = tmp_path / "silent.wav"
    with wave.open(str(wav_path), "wb") as wav:
        wav.setnchannels(1)
        wav.setsampwidth(2)
        wav.setframerate(8000)
        wav.writeframes(np.zeros(8000, dtype=np.int16).tobytes())
    missing_video = tmp_path / "missing.mp4"
    report = inspect_render(missing_video, expected_duration=1.0, audio_path=wav_path)
    assert report["passed"] is False
    assert report["errors"]


def test_all_engines_render_portrait_with_editorial_plan():
    cfg = load_config()
    rnd = Randomizer(cfg)
    ensure_engines_loaded()
    for name in ("kids_storybook", "how_it_works", "trend_brief"):
        spec = rnd.create_project(seed=91, engine=name, resolution="180x320", fps=10, duration=3)
        container_key = "education_lesson" if name == "kids_storybook" else "topic_data"
        engine = get_engine(name)
        engine.setup(spec.width, spec.height, spec.fps, spec.seed, spec.params, spec.palette())
        container = engine.params.get(container_key)
        segments = list(container.get("segments") or [])
        build_editorial_plan(segments, engine=name, duration=spec.duration, params=engine.params)
        frame = engine.render_frame(12, 30)
        engine.cleanup()
        assert frame.shape == (320, 180, 3)
        assert frame.dtype == np.uint8


def test_responsive_brief_layouts_are_valid_and_non_overlapping():
    expected = [((320, 180), "landscape"), ((180, 320), "portrait"), ((240, 240), "square")]
    for (width, height), orientation in expected:
        layout = brief_layout(width, height, ticker=True)
        assert layout.orientation == orientation
        for box in (layout.header, layout.visual, layout.card, layout.footer):
            assert 0 <= box.x0 < box.x1 <= width
            assert 0 <= box.y0 < box.y1 <= height
        if orientation == "landscape":
            assert layout.visual.x1 <= layout.card.x0
        else:
            assert layout.visual.y1 <= layout.card.y0
        for variant in ("split_left", "diagram_focus", "card_emphasis", "full_bleed"):
            alt = brief_layout(width, height, ticker=True, variant=variant)
            assert alt.visual.w >= 1 and alt.card.w >= 1


def test_multiline_type_and_stateless_transitions():
    image = Image.new("RGBA", (320, 180), (15, 20, 30, 255))
    draw = ImageDraw.Draw(image, "RGBA")
    result = paint_multiline_text(
        draw,
        (20, 20),
        "A professional headline wraps cleanly without crude character slicing.",
        load_font(28),
        (255, 255, 255),
        max_width=180,
        max_height=90,
        max_lines=3,
        fit_font_size=True,
        shadow_offset=(1, 2),
    )
    assert 1 <= result["line_count"] <= 3
    old = Image.new("RGBA", (64, 36), (255, 0, 0, 255))
    new = Image.new("RGBA", (64, 36), (0, 0, 255, 255))
    mid = composite_segment_layers(old, new, enter=0.5, leave=0.5, kind="dissolve")
    assert np.asarray(mid)[10, 10, 0] > 0
    assert np.asarray(mid)[10, 10, 2] > 0


def test_caption_fallback_burn_and_timing_validation(tmp_path: Path):
    plan = {
        "shots": [
            {"start": 0.0, "end": 1.0, "caption_start": 0.0, "caption_end": 0.0, "caption": "First"},
            {"start": 1.0, "end": 2.0, "caption_start": 1.0, "caption_end": 1.0, "caption": "Second"},
        ]
    }
    srt = export_srt(tmp_path / "clip.mp4", plan)
    assert srt is not None
    assert inspect_caption_file(srt, expected_duration=2.0)["passed"] is True
    frame = np.zeros((180, 320, 3), dtype=np.uint8)
    burned = overlay_caption_frame(frame, plan, 0.5)
    assert not np.array_equal(frame, burned)


def test_reveal_and_delivery_presets_are_deterministic():
    segment = {"t0": 0.0, "t1": 0.5, "hold_seconds": 5.0, "speech_lead": 1.0, "speech_seconds": 2.0}
    assert reveal_progress(segment, 0.05, duration=10.0) == 0.0
    assert reveal_progress(segment, 0.30, duration=10.0) > 0.0
    _, master = quality_encode_profile("libx264", "master", fps=30)
    assert master["gop_frames"] == 60
    cfg = load_config()
    spec = Randomizer(cfg).create_project(
        seed=12,
        engine="trend_brief",
        resolution="320x180",
        edit_preset="master",
        caption_mode="both",
        edit_intensity=1.25,
    )
    assert spec.params["caption_mode"] == "both"
    assert spec.params["motion_scale"] == 1.25
