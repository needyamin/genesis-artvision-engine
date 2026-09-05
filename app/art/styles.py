"""Visual style definitions that bias randomization."""

from __future__ import annotations

from typing import Any

import numpy as np


STYLE_PROFILES: dict[str, dict[str, Any]] = {
    "abstract": {
        "glow": (0.3, 0.7),
        "speed": (0.7, 1.3),
        "contrast": (0.5, 0.9),
        "density": (0.4, 0.8),
        "preferred_engines": None,
    },
    "cosmic": {
        "glow": (0.4, 0.9),
        "speed": (0.3, 0.8),
        "contrast": (0.6, 1.0),
        "density": (0.5, 1.0),
        "preferred_engines": ["galaxy", "particles", "tunnel"],
    },
    "minimal": {
        "glow": (0.0, 0.3),
        "speed": (0.2, 0.6),
        "contrast": (0.3, 0.6),
        "density": (0.1, 0.4),
        "preferred_engines": ["waves", "tunnel", "particles"],
    },
    "organic": {
        "glow": (0.2, 0.5),
        "speed": (0.3, 0.9),
        "contrast": (0.4, 0.8),
        "density": (0.4, 0.9),
        "preferred_engines": ["waves", "galaxy", "particles"],
    },
    "digital": {
        "glow": (0.3, 0.7),
        "speed": (0.8, 1.4),
        "contrast": (0.6, 1.0),
        "density": (0.4, 0.8),
        "preferred_engines": ["particles", "tunnel", "waves"],
    },
    "playful": {
        "glow": (0.3, 0.7),
        "speed": (0.6, 1.3),
        "contrast": (0.5, 0.9),
        "density": (0.5, 0.9),
        "preferred_engines": ["alphabet_cartoon", "kids_doodles", "hand_art"],
    },
    "documentary": {
        "glow": (0.3, 0.7),
        "speed": (0.4, 0.9),
        "contrast": (0.6, 0.95),
        "density": (0.4, 0.8),
        "preferred_engines": ["infographic_explainer", "galaxy", "tunnel", "particles"],
    },
}


def list_styles() -> list[str]:
    return sorted(STYLE_PROFILES.keys())


def sample_style_multiplier(rng: np.random.Generator, style: str) -> dict[str, float]:
    """Sample continuous multipliers for glow/speed/contrast/density."""
    profile = STYLE_PROFILES.get(style, STYLE_PROFILES["abstract"])
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
    "abstract": {
        "edit_feel": "cinematic",
        "grade": "vivid",
        "vignette": (0.24, 0.36),
        "grain": (0.032, 0.055),
        "fade_in": (0.55, 0.85),
        "fade_out": (0.90, 1.30),
        "camera_push": (0.040, 0.070),
        "micro_contrast": 0.16,
        "bpm": (88.0, 108.0),
        "chroma": (0.8, 1.8),
        "bloom": (0.15, 0.35),
    },
    "cosmic": {
        "edit_feel": "cinematic",
        "grade": "cinematic",
        "vignette": (0.36, 0.50),
        "grain": (0.040, 0.070),
        "fade_in": (0.85, 1.15),
        "fade_out": (1.20, 1.60),
        "camera_push": (0.028, 0.050),
        "micro_contrast": 0.13,
        "bpm": (68.0, 84.0),
        "chroma": (0.5, 1.5),
        "bloom": (0.25, 0.55),
    },
    "minimal": {
        "edit_feel": "cinematic",
        "grade": "soft",
        "vignette": (0.16, 0.26),
        "grain": (0.018, 0.035),
        "fade_in": (0.90, 1.20),
        "fade_out": (1.30, 1.70),
        "camera_push": (0.015, 0.035),
        "micro_contrast": 0.09,
        "bpm": (64.0, 80.0),
        "chroma": (0.0, 0.3),
        "bloom": (0.0, 0.12),
    },
    "organic": {
        "edit_feel": "cinematic",
        "grade": "cinematic",
        "vignette": (0.20, 0.32),
        "grain": (0.028, 0.050),
        "fade_in": (0.70, 1.00),
        "fade_out": (1.10, 1.50),
        "camera_push": (0.022, 0.045),
        "micro_contrast": 0.12,
        "bpm": (76.0, 92.0),
        "chroma": (0.2, 0.8),
        "bloom": (0.10, 0.30),
    },
    "digital": {
        "edit_feel": "cinematic",
        "grade": "vivid",
        "vignette": (0.18, 0.30),
        "grain": (0.012, 0.028),
        "fade_in": (0.30, 0.50),
        "fade_out": (0.65, 0.95),
        "camera_push": (0.048, 0.080),
        "micro_contrast": 0.20,
        "bpm": (108.0, 128.0),
        "chroma": (1.5, 3.2),
        "bloom": (0.20, 0.50),
    },
    "playful": {
        "edit_feel": "kids_show",
        "grade": "broadcast",
        "vignette": (0.04, 0.10),
        "grain": (0.0, 0.0),
        "fade_in": (0.30, 0.40),
        "fade_out": (0.60, 0.80),
        "camera_push": (0.0, 0.0),
        "micro_contrast": 0.07,
        "bpm": (90.0, 96.0),
        "chroma": (0.0, 0.0),
        "bloom": (0.0, 0.08),
    },
    "documentary": {
        "edit_feel": "documentary",
        "grade": "cinematic",
        "vignette": (0.28, 0.42),
        "grain": (0.030, 0.055),
        "fade_in": (0.80, 1.10),
        "fade_out": (1.20, 1.55),
        "camera_push": (0.020, 0.042),
        "micro_contrast": 0.14,
        "bpm": (72.0, 84.0),
        "chroma": (0.2, 0.6),
        "bloom": (0.05, 0.20),
    },
}


def sample_edit_look(rng: np.random.Generator, style: str) -> dict[str, Any]:
    """Sample a full editorial look for this style."""
    profile = STYLE_EDIT.get(style, STYLE_EDIT["abstract"])
    out: dict[str, Any] = {}
    for key, value in profile.items():
        if isinstance(value, tuple) and len(value) == 2:
            lo, hi = value
            out[key] = float(rng.uniform(float(lo), float(hi)))
        else:
            out[key] = value
    return out
