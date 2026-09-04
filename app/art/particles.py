"""Particle universe art engine."""

from __future__ import annotations

import cv2
import numpy as np

from app.art.base import ArtEngine, register_engine


@register_engine
class ParticleUniverseEngine(ArtEngine):
    name = "particles"
    description = "Particle universe with gravity and turbulence"

    def _on_setup(self) -> None:
        assert self.rng is not None
        n = int(self.params.get("count", 800))
        self.pos = self.rng.random((n, 2), dtype=np.float32)
        self.pos[:, 0] *= self.width
        self.pos[:, 1] *= self.height
        speed = float(self.params.get("speed", 1.0))
        self.vel = (self.rng.random((n, 2), dtype=np.float32) - 0.5) * speed * 4
        self.sizes = self.rng.uniform(
            0.5, float(self.params.get("size", 2.5)), size=n
        ).astype(np.float32)
        self.hue = self.rng.random(n, dtype=np.float32)
        self.canvas = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        bg = self.palette.as_uint8(0.0) if self.palette else (5, 5, 12)
        self.canvas[:] = bg
        self.cx = self.width * 0.5
        self.cy = self.height * 0.5

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.rng is not None and self.palette is not None
        trail = float(self.params.get("trail", 0.92))
        gravity = float(self.params.get("gravity", 0.01))
        turb = float(self.params.get("turbulence", 0.5))
        attract = float(self.params.get("attraction", 0.3))
        anim = float(self.params.get("animation_speed", 1.0))

        # Fade trails toward background
        bg = np.array(self.palette.as_uint8(0.0), dtype=np.float32)
        faded = self.canvas.astype(np.float32) * trail + bg * (1.0 - trail)
        self.canvas = np.clip(faded, 0, 255).astype(np.uint8)

        t = frame_number / max(1, total_frames)
        tx = self.cx + np.sin(t * np.pi * 2 * anim) * self.width * 0.15
        ty = self.cy + np.cos(t * np.pi * 2 * anim * 0.7) * self.height * 0.15
        dx = tx - self.pos[:, 0]
        dy = ty - self.pos[:, 1]
        dist = np.sqrt(dx * dx + dy * dy) + 1e-3
        self.vel[:, 0] += (dx / dist) * attract * anim
        self.vel[:, 1] += (dy / dist) * attract * anim + gravity
        self.vel += (self.rng.random(self.vel.shape, dtype=np.float32) - 0.5) * turb * 0.4
        self.vel *= 0.99
        self.pos += self.vel * anim
        self.pos[:, 0] %= self.width
        self.pos[:, 1] %= self.height

        xs = np.clip(self.pos[:, 0].astype(np.int32), 0, self.width - 1)
        ys = np.clip(self.pos[:, 1].astype(np.int32), 0, self.height - 1)
        for i in range(len(xs)):
            color = self.palette.as_uint8(float((self.hue[i] + t) % 1.0))
            r = max(1, int(self.sizes[i]))
            cv2.circle(self.canvas, (int(xs[i]), int(ys[i])), r, color, -1, lineType=cv2.LINE_AA)

        glow = float(self.params.get("glow", 0.4))
        if glow > 0.2:
            blur = cv2.GaussianBlur(self.canvas, (0, 0), sigmaX=2 + glow * 3)
            return cv2.addWeighted(self.canvas, 0.75, blur, 0.4, 0)
        return self.canvas.copy()
