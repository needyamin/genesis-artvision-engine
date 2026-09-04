"""Voronoi animation art engine."""

from __future__ import annotations

import numpy as np

from app.art.base import ArtEngine, register_engine


@register_engine
class VoronoiEngine(ArtEngine):
    name = "voronoi"
    description = "Animated Voronoi tessellation"

    def _on_setup(self) -> None:
        assert self.rng is not None
        n = int(self.params.get("sites", 30))
        # Render at reduced resolution for performance
        self.rw = min(self.width, 480)
        self.rh = max(1, int(self.rw * self.height / self.width))
        self.sites = self.rng.random((n, 2), dtype=np.float32)
        self.vel = (self.rng.random((n, 2), dtype=np.float32) - 0.5) * 0.01
        self.hue = self.rng.random(n, dtype=np.float32)
        ys = np.linspace(0, 1, self.rh, dtype=np.float32)
        xs = np.linspace(0, 1, self.rw, dtype=np.float32)
        self.gx, self.gy = np.meshgrid(xs, ys)

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        speed = float(self.params.get("speed", 0.6)) * float(self.params.get("animation_speed", 1.0))
        morph = float(self.params.get("morph", 0.5))
        edge_w = float(self.params.get("edge_width", 0.03))
        mode = str(self.params.get("fill_mode", "distance"))

        self.sites += self.vel * speed * morph * 8
        # Bounce
        for d in (0, 1):
            over = self.sites[:, d] > 1
            under = self.sites[:, d] < 0
            self.vel[over | under, d] *= -1
            self.sites[:, d] = np.clip(self.sites[:, d], 0, 1)

        # Distance to nearest / second nearest
        # Use chunked computation to limit memory
        min_d = np.full((self.rh, self.rw), np.inf, dtype=np.float32)
        second = np.full_like(min_d, np.inf)
        nearest = np.zeros((self.rh, self.rw), dtype=np.int32)
        for i, (sx, sy) in enumerate(self.sites):
            d = (self.gx - sx) ** 2 + (self.gy - sy) ** 2
            closer = d < min_d
            second = np.where(closer, min_d, np.minimum(second, d))
            nearest = np.where(closer, i, nearest)
            min_d = np.where(closer, d, min_d)

        min_d = np.sqrt(min_d)
        second = np.sqrt(second)
        edge = np.clip((second - min_d) / max(edge_w, 1e-4), 0, 1)

        lut = self.palette.array(256)
        if mode == "solid":
            hues = (self.hue[nearest] + t) % 1.0
            idx = (hues * 255).astype(np.int32)
            rgb = lut[idx] * edge[..., None]
        elif mode == "gradient":
            idx = np.clip(((min_d * 3 + t) % 1.0) * 255, 0, 255).astype(np.int32)
            rgb = lut[idx] * edge[..., None]
        else:
            idx = np.clip((min_d / (min_d.max() + 1e-6) * 255), 0, 255).astype(np.int32)
            cell = lut[((self.hue[nearest] + t) * 255 % 255).astype(np.int32)]
            rgb = cell * (0.35 + 0.65 * (1 - min_d / (min_d.max() + 1e-6)))[..., None]
            rgb *= 0.4 + 0.6 * edge[..., None]

        y_idx = (np.linspace(0, self.rh - 1, self.height)).astype(np.int32)
        x_idx = (np.linspace(0, self.rw - 1, self.width)).astype(np.int32)
        frame = rgb[y_idx][:, x_idx]
        return self._to_uint8(frame)
