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
        "preferred_engines": ["galaxy", "particles", "noise", "tunnel"],
    },
    "neon": {
        "glow": (0.7, 1.0),
        "speed": (0.8, 1.5),
        "contrast": (0.8, 1.0),
        "density": (0.3, 0.7),
        "preferred_engines": ["neon_lines", "particle_trails", "geometric", "kaleidoscope"],
    },
    "minimal": {
        "glow": (0.0, 0.3),
        "speed": (0.2, 0.6),
        "contrast": (0.3, 0.6),
        "density": (0.1, 0.4),
        "preferred_engines": ["geometric", "waves", "l_system", "noise"],
    },
    "psychedelic": {
        "glow": (0.5, 1.0),
        "speed": (1.0, 1.8),
        "contrast": (0.7, 1.0),
        "density": (0.6, 1.0),
        "preferred_engines": ["kaleidoscope", "fractal", "julia", "waves"],
    },
    "geometric": {
        "glow": (0.2, 0.6),
        "speed": (0.4, 1.0),
        "contrast": (0.5, 0.9),
        "density": (0.3, 0.7),
        "preferred_engines": ["geometric", "voronoi", "tunnel", "neon_lines"],
    },
    "organic": {
        "glow": (0.2, 0.5),
        "speed": (0.3, 0.9),
        "contrast": (0.4, 0.8),
        "density": (0.4, 0.9),
        "preferred_engines": ["reaction_diffusion", "l_system", "waves", "noise"],
    },
    "dreamlike": {
        "glow": (0.4, 0.8),
        "speed": (0.2, 0.7),
        "contrast": (0.3, 0.7),
        "density": (0.3, 0.7),
        "preferred_engines": ["noise", "waves", "galaxy", "flow_field"],
    },
    "digital": {
        "glow": (0.3, 0.7),
        "speed": (0.8, 1.4),
        "contrast": (0.6, 1.0),
        "density": (0.4, 0.8),
        "preferred_engines": ["flow_field", "neon_lines", "voronoi", "particles"],
    },
    "mathematical": {
        "glow": (0.2, 0.6),
        "speed": (0.4, 1.0),
        "contrast": (0.5, 0.9),
        "density": (0.4, 0.8),
        "preferred_engines": ["mandelbrot", "julia", "fractal", "l_system"],
    },
    "futuristic": {
        "glow": (0.5, 0.9),
        "speed": (0.6, 1.3),
        "contrast": (0.7, 1.0),
        "density": (0.4, 0.8),
        "preferred_engines": ["tunnel", "neon_lines", "geometric", "flow_field"],
    },
    "calm": {
        "glow": (0.1, 0.4),
        "speed": (0.15, 0.5),
        "contrast": (0.3, 0.6),
        "density": (0.2, 0.5),
        "preferred_engines": ["waves", "noise", "galaxy", "l_system"],
    },
    "chaotic": {
        "glow": (0.4, 1.0),
        "speed": (1.2, 2.0),
        "contrast": (0.7, 1.0),
        "density": (0.7, 1.0),
        "preferred_engines": ["particles", "particle_trails", "flow_field", "reaction_diffusion"],
    },
    "playful": {
        "glow": (0.3, 0.7),
        "speed": (0.6, 1.3),
        "contrast": (0.5, 0.9),
        "density": (0.5, 0.9),
        "preferred_engines": ["alphabet_cartoon", "kids_doodles", "hand_art", "geometric"],
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
