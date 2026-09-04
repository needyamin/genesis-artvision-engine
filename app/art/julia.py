"""Julia set animation engine."""

from __future__ import annotations

import numpy as np

from app.art.base import ArtEngine, register_engine


@register_engine
class JuliaEngine(ArtEngine):
    name = "julia"
    description = "Animated Julia set"

    def _on_setup(self) -> None:
        self.render_w = min(self.width, 640)
        self.render_h = max(1, int(self.render_w * self.height / self.width))
        self.max_iter = int(self.params.get("max_iter", 80))
        ys = np.linspace(-1.5, 1.5, self.render_h, dtype=np.float64)
        xs = np.linspace(-1.5, 1.5, self.render_w, dtype=np.float64)
        self.xv, self.yv = np.meshgrid(xs, ys)

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        cx_amp = float(self.params.get("cx_amp", 0.6))
        cy_amp = float(self.params.get("cy_amp", 0.6))
        zoom = float(self.params.get("zoom", 1.2))
        c = complex(
            cx_amp * np.sin(t * np.pi * 2 * anim),
            cy_amp * np.cos(t * np.pi * 2 * anim * 0.85),
        )
        z = (self.xv + 1j * self.yv) / zoom
        escape = np.zeros(z.shape, dtype=np.float64)
        for i in range(self.max_iter):
            mask = np.abs(z) <= 2
            z[mask] = z[mask] ** 2 + c
            escape[mask] = i
        with np.errstate(invalid="ignore", divide="ignore"):
            smooth = escape + 1 - np.log2(np.log2(np.abs(z) + 1e-9))
        smooth = np.nan_to_num(smooth, nan=0.0, posinf=0.0, neginf=0.0)
        norm = smooth / max(1.0, self.max_iter)
        cycle = float(self.params.get("color_cycle", 1.0))
        lut = self.palette.array(256)
        idx = np.clip(((norm * cycle + t) % 1.0) * 255, 0, 255).astype(np.int32)
        small = lut[idx]
        y_idx = (np.linspace(0, self.render_h - 1, self.height)).astype(np.int32)
        x_idx = (np.linspace(0, self.render_w - 1, self.width)).astype(np.int32)
        frame = small[y_idx][:, x_idx]
        return self._to_uint8(frame * float(self.params.get("contrast", 0.85)))
