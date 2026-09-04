"""Generic fractal / IFS-like animated fractal engine."""

from __future__ import annotations

import numpy as np

from app.art.base import ArtEngine, register_engine


@register_engine
class FractalEngine(ArtEngine):
    name = "fractal"
    description = "Animated escape-time fractal field"

    def _on_setup(self) -> None:
        assert self.rng is not None
        # Precompute coordinate grid at render resolution (may be heavy for 4K — OK)
        ys = np.linspace(-1.5, 1.5, self.height, dtype=np.float32)
        xs = np.linspace(-1.5, 1.5, self.width, dtype=np.float32)
        self.xx, self.yy = np.meshgrid(xs, ys)
        self.iters = int(self.params.get("iterations", 6))

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        zoom = 1.0 + t * float(self.params.get("zoom_speed", 0.8)) * anim
        rot = t * float(self.params.get("rotation_speed", 0.5)) * anim * np.pi * 2
        cos_r, sin_r = np.cos(rot), np.sin(rot)
        x = (self.xx * cos_r - self.yy * sin_r) / zoom
        y = (self.xx * sin_r + self.yy * cos_r) / zoom

        # Burning-ship / julia hybrid
        cx = 0.35 * np.sin(t * np.pi * 2 * anim)
        cy = 0.35 * np.cos(t * np.pi * 2 * anim * 0.7)
        zx, zy = x.copy(), y.copy()
        bailout = float(self.params.get("bailout", 4.0))
        escape = np.zeros_like(zx)
        for i in range(self.iters * 8):
            # z = |z|^2 + c style variation
            zx2 = zx * zx
            zy2 = zy * zy
            mask = (zx2 + zy2) < bailout
            if not np.any(mask):
                break
            zy_new = 2.0 * np.abs(zx) * np.abs(zy) + cy
            zx_new = zx2 - zy2 + cx
            zx = np.where(mask, zx_new, zx)
            zy = np.where(mask, zy_new, zy)
            escape = np.where(mask, i, escape)

        norm = escape / max(1.0, escape.max())
        color_speed = float(self.params.get("color_speed", 1.0))
        lut = self.palette.array(256)
        idx = np.clip(((norm * color_speed + t) % 1.0) * 255, 0, 255).astype(np.int32)
        rgb = lut[idx]
        contrast = float(self.params.get("contrast", 0.8))
        return self._to_uint8(rgb * contrast)
