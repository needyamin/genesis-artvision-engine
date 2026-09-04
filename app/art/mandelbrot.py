"""Mandelbrot zoom animation engine."""

from __future__ import annotations

import numpy as np

from app.art.base import ArtEngine, register_engine


@register_engine
class MandelbrotEngine(ArtEngine):
    name = "mandelbrot"
    description = "Mandelbrot set zoom animation"

    def _on_setup(self) -> None:
        # Use half resolution grid then upscale-ish via repeat for speed on large frames
        self.render_w = min(self.width, 640)
        self.render_h = max(1, int(self.render_w * self.height / self.width))
        self.max_iter = int(self.params.get("max_iter", 80))
        self.pan_x = float(self.params.get("pan_x", -0.5))
        self.pan_y = float(self.params.get("pan_y", 0.0))

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        zoom = 1.5 * (0.35 ** (t * float(self.params.get("zoom_speed", 0.5)) * anim))
        # Interesting Mandelbrot target region
        cx = self.pan_x + 0.05 * np.sin(t * 2)
        cy = self.pan_y + 0.05 * np.cos(t * 3)

        xs = np.linspace(cx - zoom, cx + zoom, self.render_w, dtype=np.float64)
        ys = np.linspace(cy - zoom * self.render_h / self.render_w,
                         cy + zoom * self.render_h / self.render_w,
                         self.render_h, dtype=np.float64)
        xv, yv = np.meshgrid(xs, ys)
        c = xv + 1j * yv
        z = np.zeros_like(c)
        escape = np.zeros(c.shape, dtype=np.float64)
        for i in range(self.max_iter):
            mask = np.abs(z) <= 2
            z[mask] = z[mask] * z[mask] + c[mask]
            escape[mask] = i
        # Smooth coloring
        with np.errstate(invalid="ignore", divide="ignore"):
            smooth = escape + 1 - np.log2(np.log2(np.abs(z) + 1e-9))
        smooth = np.nan_to_num(smooth, nan=0.0, posinf=0.0, neginf=0.0)
        norm = smooth / max(1.0, self.max_iter)
        cycle = float(self.params.get("color_cycle", 1.0))
        lut = self.palette.array(256)
        idx = np.clip(((norm * cycle + t) % 1.0) * 255, 0, 255).astype(np.int32)
        small = lut[idx]
        # Nearest-neighbor upscale
        y_idx = (np.linspace(0, self.render_h - 1, self.height)).astype(np.int32)
        x_idx = (np.linspace(0, self.render_w - 1, self.width)).astype(np.int32)
        frame = small[y_idx][:, x_idx]
        return self._to_uint8(frame * float(self.params.get("contrast", 0.85)))
