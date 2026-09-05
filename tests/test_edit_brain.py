"""Editorial timing and finish — hold, reveal, fade."""

from __future__ import annotations

import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.art.edit_brain import (
    beat_pulse,
    director_time,
    documentary_shot,
    fade_alpha,
    kids_shot,
)
from app.video.effects import apply_editorial_finish, apply_grade


def test_kids_shot_holds_the_letter_before_the_picture():
    early = kids_shot(0.12)
    hold = kids_shot(0.35)
    pic = kids_shot(0.58)
    rest = kids_shot(0.75)
    assert early.letter_scale > 0.3
    assert early.picture_scale < 0.05
    assert hold.letter_scale == 1.0
    assert hold.hold_still
    assert hold.picture_scale < 0.05
    assert hold.bounce == 0.0
    assert pic.picture_scale > 0.4
    assert rest.letter_scale == 1.0
    assert rest.picture_scale == 1.0
    assert rest.hold_still


def test_kids_shot_caption_waits_for_the_letter():
    assert kids_shot(0.10).caption_alpha < 0.2
    assert kids_shot(0.40).caption_alpha > 0.9


def test_director_time_is_linear_for_kids_audio_sync():
    for t in (0.0, 0.25, 0.5, 0.75, 1.0):
        assert director_time(t, "kids_show") == t
        assert director_time(t, "linear") == t
    mid = director_time(0.5, "cinematic")
    assert 0.45 <= mid <= 0.55


def test_documentary_shot_holds_then_exits():
    shot = documentary_shot(0.6)
    assert shot.hold
    assert shot.entry > 0.9
    assert documentary_shot(0.97).exit < 0.5


def test_fade_alpha_opens_and_closes():
    assert fade_alpha(0.0, 30.0, 0.5, 1.0) < 0.05
    assert fade_alpha(0.5, 30.0, 0.5, 1.0) == 1.0
    assert fade_alpha(1.0, 30.0, 0.5, 1.0) < 0.05


def test_beat_pulse_peaks_on_the_downbeat():
    assert beat_pulse(0.0, bpm=60.0, duration=4.0) > 0.9
    assert beat_pulse(0.2, bpm=60.0, duration=4.0) < 0.5


def test_broadcast_grade_and_editorial_finish_are_deterministic():
    frame = np.full((40, 60, 3), 120, dtype=np.uint8)
    graded = apply_grade(frame, "broadcast")
    assert graded.shape == frame.shape
    params = {
        "_kids_text": True,
        "edit_feel": "kids_show",
        "fade_in": 0.3,
        "fade_out": 0.3,
        "vignette": 0.08,
        "grain": 0.0,
        "camera_push": 0.0,
    }
    a = apply_editorial_finish(frame, params, 5, 30, duration=3.0, fps=10, seed=7)
    b = apply_editorial_finish(frame, params, 5, 30, duration=3.0, fps=10, seed=7)
    assert np.array_equal(a, b)
    assert a.dtype == np.uint8
