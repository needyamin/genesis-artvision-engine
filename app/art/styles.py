"""Visual style definitions that bias randomization."""

from __future__ import annotations

from typing import Any

import numpy as np


STYLE_PROFILES: dict[str, dict[str, Any]] = {
    "storybook": {
        "glow": (0.15, 0.40),
        "speed": (0.25, 0.55),
        "contrast": (0.40, 0.70),
        "density": (0.30, 0.60),
        "preferred_engines": ["kids_storybook"],
    },
    "classroom": {
        "glow": (0.10, 0.35),
        "speed": (0.35, 0.70),
        "contrast": (0.50, 0.80),
        "density": (0.35, 0.65),
        "preferred_engines": ["how_it_works"],
    },
    "pulse": {
        "glow": (0.45, 0.85),
        "speed": (0.95, 1.45),
        "contrast": (0.70, 1.05),
        "density": (0.50, 0.90),
        "preferred_engines": ["trend_brief"],
    },
}


def list_styles() -> list[str]:
    return sorted(STYLE_PROFILES.keys())


def sample_style_multiplier(rng: np.random.Generator, style: str) -> dict[str, float]:
    """Sample continuous multipliers for glow/speed/contrast/density."""
    profile = STYLE_PROFILES.get(style, STYLE_PROFILES["storybook"])
    return {
        "glow": float(rng.uniform(*profile["glow"])),
        "speed": float(rng.uniform(*profile["speed"])),
        "contrast": float(rng.uniform(*profile["contrast"])),
        "density": float(rng.uniform(*profile["density"])),
    }


def preferred_engines(style: str) -> list[str] | None:
    return STYLE_PROFILES.get(style, {}).get("preferred_engines")


# Editorial finish unique to each style (grade, fade, camera, grain).
STYLE_EDIT: dict[str, dict[str, Any]] = {
    "storybook": {
        "edit_feel": "kids_show",
        "grade": "pastel",
        "vignette": (0.08, 0.16),
        "grain": (0.012, 0.028),
        "fade_in": (0.40, 0.60),
        "fade_out": (0.70, 1.00),
        "camera_push": (0.0, 0.0),
        "micro_contrast": 0.08,
        "bpm": (76.0, 88.0),
        "chroma": (0.0, 0.2),
        "bloom": (0.04, 0.12),
    },
    "classroom": {
        "edit_feel": "documentary",
        "grade": "soft",
        "vignette": (0.10, 0.20),
        "grain": (0.008, 0.020),
        "fade_in": (0.40, 0.65),
        "fade_out": (0.70, 1.05),
        "camera_push": (0.008, 0.018),
        "micro_contrast": 0.10,
        "bpm": (80.0, 96.0),
        "chroma": (0.0, 0.25),
        "bloom": (0.0, 0.10),
    },
    "pulse": {
        "edit_feel": "cinematic",
        "grade": "vivid",
        "vignette": (0.22, 0.36),
        "grain": (0.010, 0.024),
        "fade_in": (0.18, 0.32),
        "fade_out": (0.40, 0.70),
        "camera_push": (0.050, 0.085),
        "micro_contrast": 0.18,
        "bpm": (118.0, 138.0),
        "chroma": (1.6, 3.0),
        "bloom": (0.22, 0.48),
    },
}


def style_chrome(
    style: str,
    *,
    dark: bool,
    text: tuple[int, int, int],
    muted: tuple[int, int, int],
    accent: tuple[int, int, int],
    card: tuple[int, int, int, int],
    border: tuple[int, int, int, int],
    short_side: int = 720,
) -> dict[str, Any]:
    """Turn a style name into card, type, and motion treatment for any engine."""
    key = str(style or "storybook").strip().lower()
    radius_frac = {"pulse": 0.016, "classroom": 0.018, "storybook": 0.026}.get(key, 0.022)
    radius = max(6, int(short_side * radius_frac))
    if key == "pulse":
        card_fill = (12, 16, 28, 220) if dark else (18, 22, 34, 228)
        ink = (250, 252, 255) if dark else (22, 24, 32)
        soft = (196, 206, 220) if dark else (70, 76, 90)
        stroke = 2
        density = 1.15
    elif key == "classroom":
        card_fill = (20, 32, 28, 220) if dark else (255, 255, 255, 236)
        ink = (236, 244, 238) if dark else (36, 48, 58)
        soft = (186, 204, 194) if dark else (70, 80, 90)
        stroke = 2
        density = 0.85
    else:
        card_fill = card if dark else (255, 248, 236, 240)
        ink = text if dark else (60, 42, 30)
        soft = muted if dark else (90, 70, 55)
        stroke = 2
        density = 0.75
    return {
        "card_radius": radius,
        "card_fill": card_fill,
        "text": ink,
        "muted": soft,
        "accent": accent,
        "border": border,
        "stroke": stroke,
        "density": density,
        "type_scale": 1.08 if key == "pulse" else 0.96 if key == "classroom" else 1.0,
    }


def sample_edit_look(rng: np.random.Generator, style: str) -> dict[str, Any]:
    """Sample a full editorial look for this style."""
    profile = STYLE_EDIT.get(style, STYLE_EDIT["storybook"])
    out: dict[str, Any] = {}
    for key, value in profile.items():
        if isinstance(value, tuple) and len(value) == 2:
            lo, hi = value
            out[key] = float(rng.uniform(float(lo), float(hi)))
        else:
            out[key] = value
    return out
