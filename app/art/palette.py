"""Color palette generation for procedural art."""

from __future__ import annotations

from dataclasses import dataclass

import numpy as np


@dataclass(frozen=True)
class Palette:
    """A reusable color palette with interpolation helpers."""

    name: str
    colors: tuple[tuple[float, float, float], ...]  # RGB 0-1

    def sample(self, t: float) -> tuple[float, float, float]:
        """Interpolate palette color at normalized position t."""
        if not self.colors:
            return (1.0, 1.0, 1.0)
        if len(self.colors) == 1:
            return self.colors[0]
        t = float(np.clip(t % 1.0, 0.0, 1.0))
        scaled = t * (len(self.colors) - 1)
        i = int(scaled)
        frac = scaled - i
        if i >= len(self.colors) - 1:
            return self.colors[-1]
        c0 = np.asarray(self.colors[i], dtype=np.float64)
        c1 = np.asarray(self.colors[i + 1], dtype=np.float64)
        out = c0 * (1.0 - frac) + c1 * frac
        return (float(out[0]), float(out[1]), float(out[2]))

    def as_uint8(self, t: float) -> tuple[int, int, int]:
        r, g, b = self.sample(t)
        return (int(r * 255), int(g * 255), int(b * 255))

    def array(self, n: int = 256) -> np.ndarray:
        """Return an (n, 3) float palette lookup table."""
        ts = np.linspace(0.0, 1.0, n, dtype=np.float64)
        return np.array([self.sample(float(t)) for t in ts], dtype=np.float64)


def _hsl_to_rgb(h: float, s: float, l: float) -> tuple[float, float, float]:
    h = h % 1.0
    s = float(np.clip(s, 0.0, 1.0))
    l = float(np.clip(l, 0.0, 1.0))
    if s == 0:
        return (l, l, l)

    def hue2rgb(p: float, q: float, t: float) -> float:
        if t < 0:
            t += 1
        if t > 1:
            t -= 1
        if t < 1 / 6:
            return p + (q - p) * 6 * t
        if t < 1 / 2:
            return q
        if t < 2 / 3:
            return p + (q - p) * (2 / 3 - t) * 6
        return p

    q = l * (1 + s) if l < 0.5 else l + s - l * s
    p = 2 * l - q
    r = hue2rgb(p, q, h + 1 / 3)
    g = hue2rgb(p, q, h)
    b = hue2rgb(p, q, h - 1 / 3)
    return (r, g, b)


def generate_palette(rng: np.random.Generator, style: str = "abstract") -> Palette:
    """Create an aesthetically pleasing palette based on style and RNG."""
    mode = rng.choice(
        ["monochromatic", "analogous", "complementary", "triadic", "artistic"],
        p=[0.18, 0.28, 0.18, 0.18, 0.18],
    )
    base_h = float(rng.random())

    # Style-biased lightness / saturation
    style_bias = {
        "neon": (0.85, 0.55, 0.12),
        "cosmic": (0.7, 0.45, 0.06),
        "minimal": (0.25, 0.55, 0.82),
        "psychedelic": (0.95, 0.55, 0.15),
        "calm": (0.4, 0.55, 0.2),
        "chaotic": (0.9, 0.5, 0.08),
        "organic": (0.55, 0.45, 0.15),
        "dreamlike": (0.5, 0.65, 0.18),
        "futuristic": (0.75, 0.5, 0.08),
        "mathematical": (0.45, 0.5, 0.1),
        "digital": (0.8, 0.45, 0.05),
        "geometric": (0.6, 0.5, 0.1),
        "abstract": (0.65, 0.5, 0.1),
        "playful": (0.85, 0.62, 0.88),
    }
    sat, light, bg_l = style_bias.get(style, (0.65, 0.5, 0.1))
    sat = float(np.clip(sat + rng.uniform(-0.1, 0.1), 0.2, 0.98))
    light = float(np.clip(light + rng.uniform(-0.1, 0.1), 0.25, 0.8))

    hues: list[float]
    if mode == "monochromatic":
        hues = [base_h + rng.uniform(-0.04, 0.04) for _ in range(5)]
    elif mode == "analogous":
        hues = [base_h + d for d in (-0.08, -0.04, 0.0, 0.04, 0.08)]
    elif mode == "complementary":
        hues = [base_h, base_h, base_h + 0.5, base_h + 0.5, base_h + 0.25]
    elif mode == "triadic":
        hues = [base_h, base_h + 1 / 3, base_h + 2 / 3, base_h + 0.1, base_h + 0.45]
    else:
        hues = [base_h + rng.uniform(-0.2, 0.2) + i * 0.12 for i in range(5)]

    colors: list[tuple[float, float, float]] = []
    # Dark background-friendly first color
    colors.append(_hsl_to_rgb(hues[0], sat * 0.4, bg_l))
    for i, h in enumerate(hues):
        l = light + (i - 2) * 0.06 + rng.uniform(-0.05, 0.05)
        s = sat + rng.uniform(-0.08, 0.08)
        colors.append(_hsl_to_rgb(h, s, l))

    # Accent highlight
    colors.append(_hsl_to_rgb(hues[-1] + 0.05, min(1.0, sat + 0.15), min(0.9, light + 0.2)))
    return Palette(name=f"{mode}_{style}", colors=tuple(colors))
