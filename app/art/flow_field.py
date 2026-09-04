"""Flow field particle art engine."""

from __future__ import annotations

import numpy as np

from app.art.base import ArtEngine, register_engine


def _value_noise2d(x: np.ndarray, y: np.ndarray, rng_seed: int) -> np.ndarray:
    """Simple hash-based value noise."""
    xi = np.floor(x).astype(np.int64)
    yi = np.floor(y).astype(np.int64)
    xf = x - xi.astype(np.float32)
    yf = y - yi.astype(np.float32)
    xf = xf * xf * (3 - 2 * xf)
    yf = yf * yf * (3 - 2 * yf)

    def hash_xy(a: np.ndarray, b: np.ndarray) -> np.ndarray:
        n = (
            a.astype(np.int64) * np.int64(374761393)
            + b.astype(np.int64) * np.int64(668265263)
            + np.int64(rng_seed) * np.int64(1274126177)
        )
        n = n & np.int64(0x7FFFFFFF)
        n = (n ^ (n >> np.int64(13))) * np.int64(1274126177)
        n = (n ^ (n >> np.int64(16))) & np.int64(0xFFFF)
        return n.astype(np.float32) / 65535.0

    n00 = hash_xy(xi, yi)
    n10 = hash_xy(xi + 1, yi)
    n01 = hash_xy(xi, yi + 1)
    n11 = hash_xy(xi + 1, yi + 1)
    nx0 = n00 * (1 - xf) + n10 * xf
    nx1 = n01 * (1 - xf) + n11 * xf
    return nx0 * (1 - yf) + nx1 * yf


@register_engine
class FlowFieldEngine(ArtEngine):
    name = "flow_field"
    description = "Particles following a Perlin-like flow field"

    def _on_setup(self) -> None:
        assert self.rng is not None
        n = int(self.params.get("particle_count", 800))
        self.pos = np.column_stack(
            [
                self.rng.random(n) * self.width,
                self.rng.random(n) * self.height,
            ]
        ).astype(np.float32)
        self.hue = self.rng.random(n).astype(np.float32)
        self.canvas = self._blank()
        self.z = 0.0
        self.noise_seed = int(self.rng.integers(1, 1_000_000))

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        trail = float(self.params.get("trail", 0.94))
        scale = float(self.params.get("noise_scale", 0.004))
        strength = float(self.params.get("strength", 1.5))
        z_speed = float(self.params.get("z_speed", 0.01)) * float(
            self.params.get("animation_speed", 1.0)
        )
        self.canvas *= trail
        self.z += z_speed
        t = frame_number / max(1, total_frames)

        nx = _value_noise2d(self.pos[:, 0] * scale, self.pos[:, 1] * scale + self.z, self.noise_seed)
        ny = _value_noise2d(
            self.pos[:, 0] * scale + 100,
            self.pos[:, 1] * scale + self.z,
            self.noise_seed + 17,
        )
        angle = nx * np.pi * 2
        self.pos[:, 0] += np.cos(angle) * strength * (0.5 + ny)
        self.pos[:, 1] += np.sin(angle) * strength * (0.5 + ny)

        out = (self.pos[:, 0] < 0) | (self.pos[:, 0] >= self.width) | (self.pos[:, 1] < 0) | (
            self.pos[:, 1] >= self.height
        )
        if np.any(out):
            self.pos[out, 0] = np.random.default_rng(self.seed + frame_number).random(out.sum()) * self.width
            self.pos[out, 1] = np.random.default_rng(self.seed + frame_number + 1).random(out.sum()) * self.height

        xs = np.clip(self.pos[:, 0].astype(np.int32), 0, self.width - 1)
        ys = np.clip(self.pos[:, 1].astype(np.int32), 0, self.height - 1)
        for i in range(0, len(xs), max(1, len(xs) // 1500)):
            c = np.asarray(self.palette.sample(float(self.hue[i] + t)), dtype=np.float32)
            self.canvas[ys[i], xs[i]] = np.maximum(self.canvas[ys[i], xs[i]], c)
        return self._to_uint8(self.canvas)
