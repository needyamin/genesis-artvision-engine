"""Editorial timing — how a human editor/creator actually cuts a video.

Engines used to drive every pixel with linear t (0→1). Real videos do not:
they fade in, hold the hero, reveal the supporting shot, rest so the viewer
can read, then cut. This module is that brain. Audio stays synced to global t;
only motion *inside* a shot is remapped.
"""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


def clamp01(t: float) -> float:
    return float(np.clip(t, 0.0, 1.0))


def ease_in_out_cubic(t: float) -> float:
    t = clamp01(t)
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - ((-2.0 * t + 2.0) ** 3) / 2.0


def ease_out_cubic(t: float) -> float:
    t = clamp01(t)
    return 1.0 - (1.0 - t) ** 3


def director_time(t: float, feel: str = "cinematic") -> float:
    """Remap whole-video t so motion breathes instead of spinning at constant speed.

    Kids/documentary keep linear t so narration stays on the lesson timeline.
    """
    t = clamp01(t)
    key = str(feel or "cinematic").strip().lower()
    if key in {"linear", "kids_show", "broadcast"}:
        return t
    if key == "documentary":
        return 0.06 * t + 0.94 * ease_in_out_cubic(t)
    return ease_in_out_cubic(t)


def beat_pulse(t: float, bpm: float = 96.0, duration: float = 30.0) -> float:
    """0–1 pulse on a 4/4 downbeat. Editors hit cuts and light pops here."""
    beats = max(1.0, (duration * max(40.0, bpm)) / 60.0)
    phase = (t * beats) % 1.0
    return float(np.exp(-phase * 7.0))


def rule_of_thirds_focus(seed: int) -> tuple[float, float]:
    """Slight off-center subject — never dead-center like a screen saver."""
    rng = np.random.default_rng(int(seed) + 91)
    xs = (1.0 / 3.0, 0.5, 2.0 / 3.0)
    ys = (0.42, 0.50, 0.58)
    return float(rng.choice(xs)), float(rng.choice(ys))


@dataclass(frozen=True)
class StyleMotion:
    """How a style moves — every engine reads this so styles are not just palettes."""

    speed: float
    pulse: float
    noise: float
    glow: float
    ridge: float
    twist: float
    core: float
    turb: float
    plexus: float = 0.0
    warp: float = 1.0
    tilt: float = 0.0
    caustic: float = 0.5
    depth_layers: int = 3


STYLE_MOTION: dict[str, StyleMotion] = {
    "storybook": StyleMotion(0.50, 0.04, 0.42, 0.60, 0.12, 0.48, 0.70, 0.40, plexus=0.08, warp=0.35, tilt=0.08, caustic=0.30, depth_layers=2),
    "classroom": StyleMotion(0.62, 0.05, 0.40, 0.70, 0.12, 0.52, 0.75, 0.42, plexus=0.20, warp=0.30, tilt=0.12, caustic=0.22, depth_layers=2),
    "pulse": StyleMotion(1.28, 0.36, 0.80, 1.20, 0.50, 1.35, 0.72, 0.70, plexus=0.90, warp=0.55, tilt=0.42, caustic=0.85, depth_layers=3),
}


def style_motion(style: str) -> StyleMotion:
    key = str(style or "storybook").strip().lower()
    return STYLE_MOTION.get(key, STYLE_MOTION["storybook"])


def fade_alpha(t: float, duration: float, fade_in: float, fade_out: float) -> float:
    """Master fade envelope in seconds, returned 0–1 multiplier."""
    t = clamp01(t)
    dur = max(0.5, float(duration))
    fi = max(0.05, float(fade_in))
    fo = max(0.05, float(fade_out))
    sec = t * dur
    a_in = 1.0 if sec >= fi else ease_out_cubic(sec / fi)
    remain = dur - sec
    a_out = 1.0 if remain >= fo else ease_out_cubic(remain / fo)
    return float(min(a_in, a_out))
