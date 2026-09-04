"""Tunnel / hyperspace art engine."""

from __future__ import annotations

import numpy as np

from app.art.base import ArtEngine, register_engine


@register_engine
class TunnelEngine(ArtEngine):
    name = "tunnel"
    description = "Perspective tunnel animation"

    def _on_setup(self) -> None:
        ys = np.linspace(-1, 1, self.height, dtype=np.float32)
        xs = np.linspace(-1, 1, self.width, dtype=np.float32)
        self.xx, self.yy = np.meshgrid(xs, ys)
        # Correct aspect
        self.xx = self.xx * (self.width / max(1, self.height))
        self.r = np.sqrt(self.xx ** 2 + self.yy ** 2) + 1e-4
        self.a = np.arctan2(self.yy, self.xx)

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        speed = float(self.params.get("speed", 1.2)) * anim
        twist = float(self.params.get("twist", 0.8))
        rings = int(self.params.get("rings", 24))
        spokes = int(self.params.get("spokes", 16))
        pulse = float(self.params.get("pulse", 0.6))

        depth = 1.0 / self.r
        u = depth + t * speed * 8
        v = self.a / np.pi + twist * depth * 0.2 + t * speed * 0.3
        pattern = (
            0.5
            + 0.5 * np.sin(u * rings * 0.5)
            * np.sin(v * spokes * np.pi)
            * (0.7 + 0.3 * np.sin(t * pulse * 10))
        )
        fog = np.clip(1.0 - self.r * 0.65, 0, 1)
        value = pattern * fog
        lut = self.palette.array(256)
        idx = np.clip(((value + t * 0.2) % 1.0) * 255, 0, 255).astype(np.int32)
        rgb = lut[idx] * fog[..., None]
        # Center glow
        glow = np.exp(-self.r * 4) * float(self.params.get("glow", 0.5))
        accent = np.asarray(self.palette.sample((t + 0.5) % 1.0), dtype=np.float32)
        rgb = rgb + glow[..., None] * accent
        return self._to_uint8(rgb)
