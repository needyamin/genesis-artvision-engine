"""Galaxy / starfield art engine."""

from __future__ import annotations

import cv2
import numpy as np

from app.art.base import ArtEngine, register_engine


@register_engine
class GalaxyEngine(ArtEngine):
    name = "galaxy"
    description = "Spiral galaxy / starfield"

    def _on_setup(self) -> None:
        assert self.rng is not None
        n = int(self.params.get("star_count", 1500))
        arms = int(self.params.get("arm_count", 4))
        self.r = np.sqrt(self.rng.random(n)).astype(np.float32)
        self.theta = (
            self.rng.random(n) * 2 * np.pi / arms
            + (np.arange(n) % arms) * (2 * np.pi / arms)
            + self.r * 3.5
        ).astype(np.float32)
        self.sizes = self.rng.uniform(0.5, 2.5, n).astype(np.float32)
        self.hue = self.rng.random(n).astype(np.float32)
        self.bright = self.rng.uniform(0.4, 1.0, n).astype(np.float32)
        bg_n = max(50, n // 3)
        self.bg_x = self.rng.random(bg_n).astype(np.float32)
        self.bg_y = self.rng.random(bg_n).astype(np.float32)
        self.bg_b = self.rng.uniform(0.15, 0.6, bg_n).astype(np.float32)

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        spin = float(self.params.get("spin", 0.6)) * float(self.params.get("animation_speed", 1.0))
        drift = float(self.params.get("drift", 0.2))
        img = self._to_uint8(self._blank())

        bx = (self.bg_x * self.width).astype(np.int32) % self.width
        by = (self.bg_y * self.height).astype(np.int32) % self.height
        tw = 0.5 + 0.5 * np.sin(t * 20 + self.bg_b * 10)
        for i in range(0, len(bx), max(1, len(bx) // 800)):
            v = int(255 * tw[i] * self.bg_b[i])
            img[by[i], bx[i]] = (v, v, min(255, v + 20))

        theta = self.theta + t * spin * np.pi * 2
        noise = float(self.params.get("noise_strength", 0.4))
        rr = self.r * (0.35 + 0.1 * np.sin(t * drift * 10))
        x = 0.5 + rr * np.cos(theta) * 0.45 + noise * 0.02 * np.sin(theta * 3 + t)
        y = 0.5 + rr * np.sin(theta) * 0.45 * (self.width / max(1, self.height)) + noise * 0.02 * np.cos(
            theta * 2
        )
        xs = np.clip((x * self.width).astype(np.int32), 0, self.width - 1)
        ys = np.clip((y * self.height).astype(np.int32), 0, self.height - 1)

        core = float(self.params.get("core_glow", 0.6))
        glow_c = self.palette.as_uint8(0.3 + t * 0.2)
        overlay = img.copy()
        cv2.circle(
            overlay,
            (self.width // 2, self.height // 2),
            max(8, int(min(self.width, self.height) * 0.08 * core)),
            glow_c,
            -1,
            lineType=cv2.LINE_AA,
        )
        img = cv2.addWeighted(img, 1.0, overlay, 0.35 * core, 0)

        for i in range(len(xs)):
            color = self.palette.as_uint8(float((self.hue[i] + t) % 1.0))
            scale = self.bright[i]
            c = tuple(int(ch * scale) for ch in color)
            r = 1 if self.sizes[i] < 1.5 else 2
            cv2.circle(img, (int(xs[i]), int(ys[i])), r, c, -1, lineType=cv2.LINE_AA)
        return img
