"""Random particle trails art engine."""

from __future__ import annotations

import cv2
import numpy as np

from app.art.base import ArtEngine, register_engine


@register_engine
class ParticleTrailsEngine(ArtEngine):
    name = "particle_trails"
    description = "Curling particles with persistent trails"

    def _on_setup(self) -> None:
        assert self.rng is not None
        n = int(self.params.get("count", 80))
        trail = int(self.params.get("trail_length", 40))
        self.trail_len = trail
        self.pos = self.rng.random((n, 2), dtype=np.float32)
        self.pos[:, 0] *= self.width
        self.pos[:, 1] *= self.height
        self.angle = self.rng.random(n).astype(np.float32) * np.pi * 2
        self.hue = self.rng.random(n).astype(np.float32)
        self.hist = np.zeros((n, trail, 2), dtype=np.float32)
        for i in range(n):
            self.hist[i, :, :] = self.pos[i]
        self.cursor = 0

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None and self.rng is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        speed = float(self.params.get("speed", 1.2)) * anim
        curl = float(self.params.get("curl", 1.0))
        size = max(1, int(self.params.get("size", 2)))

        # Curl noise steering
        self.angle += (self.rng.random(len(self.angle)) - 0.5) * curl * 0.4
        self.angle += np.sin(self.pos[:, 0] * 0.01 + t * 4) * curl * 0.05
        self.pos[:, 0] += np.cos(self.angle) * speed * 3
        self.pos[:, 1] += np.sin(self.angle) * speed * 3
        self.pos[:, 0] %= self.width
        self.pos[:, 1] %= self.height

        self.hist[:, self.cursor % self.trail_len, :] = self.pos
        self.cursor += 1

        img = self._to_uint8(self._blank())
        for i in range(len(self.pos)):
            color = self.palette.as_uint8((float(self.hue[i]) + t) % 1.0)
            pts = self.hist[i].astype(np.int32)
            # Order points by ring buffer
            ordered = np.vstack([pts[self.cursor % self.trail_len :], pts[: self.cursor % self.trail_len]])
            cv2.polylines(img, [ordered], False, color, size, lineType=cv2.LINE_AA)
            cv2.circle(img, (int(self.pos[i, 0]), int(self.pos[i, 1])), size + 1, color, -1)
        glow = float(self.params.get("glow", 0.5))
        if glow > 0.2:
            blur = cv2.GaussianBlur(img, (0, 0), sigmaX=3 + glow * 4)
            img = cv2.addWeighted(img, 0.75, blur, 0.45, 0)
        return img
