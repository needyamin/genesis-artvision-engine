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


def smoothstep(edge0: float, edge1: float, x: float) -> float:
    t = clamp01((x - edge0) / max(1e-6, edge1 - edge0))
    return t * t * (3.0 - 2.0 * t)


def ease_in_out_cubic(t: float) -> float:
    t = clamp01(t)
    if t < 0.5:
        return 4.0 * t * t * t
    return 1.0 - ((-2.0 * t + 2.0) ** 3) / 2.0


def ease_out_cubic(t: float) -> float:
    t = clamp01(t)
    return 1.0 - (1.0 - t) ** 3


def ease_out_back(t: float, overshoot: float = 0.45) -> float:
    t = clamp01(t)
    c1 = overshoot
    c3 = c1 + 1.0
    return 1.0 + c3 * (t - 1.0) ** 3 + c1 * (t - 1.0) ** 2


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
class KidsShot:
    """One lesson beat, staged the way kids-TV editors cut it."""

    local: float
    letter_scale: float
    picture_scale: float
    caption_alpha: float
    celebrate: bool
    hold_still: bool
    bounce: float
    zoom: float


def kids_shot(local: float) -> KidsShot:
    """Anticipate → pop letter → HOLD → picture → HOLD both → celebrate.

    The holds are the whole point. Constant bouncing reads as a screensaver,
    not a teacher.
    """
    t = clamp01(local)
    letter = 0.0
    picture = 0.0
    caption = 0.0
    bounce = 0.0
    zoom = 1.0
    celebrate = False

    if t < 0.07:
        letter = 0.0
    elif t < 0.22:
        u = (t - 0.07) / 0.15
        letter = ease_out_back(u, overshoot=0.38)
        bounce = (1.0 - letter) * 10.0
    elif t < 0.48:
        letter = 1.0
        caption = smoothstep(0.24, 0.38, t)
        zoom = 1.0 + 0.012 * smoothstep(0.22, 0.48, t)
    elif t < 0.62:
        letter = 1.0
        picture = ease_out_back((t - 0.48) / 0.14, overshoot=0.32)
        caption = 1.0
        zoom = 1.012
    elif t < 0.86:
        letter = 1.0
        picture = 1.0
        caption = 1.0
        zoom = 1.012 + 0.008 * smoothstep(0.62, 0.86, t)
    else:
        letter = 1.0
        picture = 1.0
        caption = 1.0
        celebrate = True
        zoom = 1.02

    hold_still = (0.22 <= t < 0.48) or (0.62 <= t < 0.86)
    return KidsShot(
        local=t,
        letter_scale=float(letter),
        picture_scale=float(picture),
        caption_alpha=float(caption),
        celebrate=celebrate,
        hold_still=hold_still,
        bounce=float(bounce),
        zoom=float(zoom),
    )


@dataclass(frozen=True)
class DocShot:
    """Documentary card: fade in, hold for reading, fade toward the next cut."""

    local: float
    entry: float
    body: float
    hold: bool
    exit: float


def documentary_shot(local: float) -> DocShot:
    t = clamp01(local)
    entry = smoothstep(0.0, 0.16, t)
    body = smoothstep(0.14, 0.42, t)
    exit_fade = 1.0 - smoothstep(0.88, 1.0, t)
    return DocShot(
        local=t,
        entry=float(entry * exit_fade),
        body=float(body * exit_fade),
        hold=0.42 <= t < 0.88,
        exit=float(exit_fade),
    )


def draw_progress(local: float, count: int, index: int) -> float:
    """How far through a step-by-step draw: finish early, then rest on the result."""
    if count <= 0:
        return 1.0
    if index < count - 1:
        return 1.0
    return ease_out_cubic(min(1.0, local / 0.72))


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
    "abstract": StyleMotion(1.00, 0.12, 1.00, 1.00, 0.28, 1.00, 1.00, 1.00, plexus=0.35, warp=1.20, tilt=0.25, caustic=0.70, depth_layers=3),
    "cosmic": StyleMotion(0.58, 0.05, 0.70, 1.40, 0.16, 0.65, 1.50, 0.50, plexus=0.18, warp=0.85, tilt=0.55, caustic=0.45, depth_layers=3),
    "minimal": StyleMotion(0.45, 0.03, 0.32, 0.50, 0.10, 0.40, 0.65, 0.35, plexus=0.06, warp=0.40, tilt=0.15, caustic=0.20, depth_layers=2),
    "organic": StyleMotion(0.70, 0.07, 1.40, 0.85, 0.40, 0.78, 0.88, 0.90, plexus=0.22, warp=1.65, tilt=0.30, caustic=0.90, depth_layers=3),
    "digital": StyleMotion(1.22, 0.32, 0.75, 1.15, 0.46, 1.30, 0.80, 0.62, plexus=0.85, warp=0.60, tilt=0.40, caustic=0.80, depth_layers=3),
    "playful": StyleMotion(0.88, 0.10, 0.55, 0.72, 0.22, 0.70, 0.78, 0.48, plexus=0.10, warp=0.50, tilt=0.10, caustic=0.50, depth_layers=2),
    "documentary": StyleMotion(0.52, 0.04, 0.48, 0.82, 0.14, 0.50, 1.12, 0.40, plexus=0.42, warp=0.50, tilt=0.35, caustic=0.30, depth_layers=3),
}


def style_motion(style: str) -> StyleMotion:
    key = str(style or "abstract").strip().lower()
    return STYLE_MOTION.get(key, STYLE_MOTION["abstract"])


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
