"""Noise-based abstract art engine."""

from __future__ import annotations

import numpy as np

from app.art.base import ArtEngine, register_engine
from app.art.flow_field import _value_noise2d


@register_engine
class NoiseEngine(ArtEngine):
    name = "noise"
    description = "Multi-octave noise fields with domain warping"

    def _on_setup(self) -> None:
        self.rw = min(self.width, 480)
        self.rh = max(1, int(self.rw * self.height / self.width))
        ys = np.linspace(0, 4, self.rh, dtype=np.float32)
        xs = np.linspace(0, 4 * self.rw / self.rh, self.rw, dtype=np.float32)
        self.xx, self.yy = np.meshgrid(xs, ys)
        self.noise_seed = int(self.seed % 1_000_000) + 1

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        speed = float(self.params.get("speed", 0.8)) * anim
        octaves = int(self.params.get("octaves", 4))
        lac = float(self.params.get("lacunarity", 2.0))
        gain = float(self.params.get("gain", 0.5))
        warp = float(self.params.get("warp", 0.5))
        contrast = float(self.params.get("contrast", 1.0)) * float(
            self.params.get("contrast", 1.0)
        )

        z = t * speed * 3
        x = self.xx
        y = self.yy
        if warp > 0:
            wx = _value_noise2d(x, y + z, self.noise_seed)
            wy = _value_noise2d(x + 50, y + z, self.noise_seed + 3)
            x = x + wx * warp
            y = y + wy * warp

        amp = 1.0
        freq = 1.0
        total = np.zeros((self.rh, self.rw), dtype=np.float32)
        norm = 0.0
        for o in range(octaves):
            n = _value_noise2d(x * freq, y * freq + z, self.noise_seed + o * 19)
            total += n * amp
            norm += amp
            amp *= gain
            freq *= lac
        total /= max(norm, 1e-6)
        total = np.clip((total - 0.5) * contrast * float(self.params.get("contrast", 1.0)) + 0.5, 0, 1)

        lut = self.palette.array(256)
        idx = np.clip(((total + t * 0.15) % 1.0) * 255, 0, 255).astype(np.int32)
        small = lut[idx]
        y_idx = (np.linspace(0, self.rh - 1, self.height)).astype(np.int32)
        x_idx = (np.linspace(0, self.rw - 1, self.width)).astype(np.int32)
        return self._to_uint8(small[y_idx][:, x_idx])
