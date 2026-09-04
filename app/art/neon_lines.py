"""Neon line animation art engine."""

from __future__ import annotations

import cv2
import numpy as np

from app.art.base import ArtEngine, register_engine


@register_engine
class NeonLinesEngine(ArtEngine):
    name = "neon_lines"
    description = "Glowing neon polyline animation"

    def _on_setup(self) -> None:
        assert self.rng is not None
        n = int(self.params.get("line_count", 16))
        self.lines = []
        for _ in range(n):
            pts = int(self.rng.integers(4, 10))
            self.lines.append(
                {
                    "pts": self.rng.random((pts, 2)).astype(np.float32),
                    "phase": float(self.rng.random() * np.pi * 2),
                    "speed": float(self.rng.uniform(0.5, 1.5)),
                    "hue": float(self.rng.random()),
                    "amp": float(self.rng.uniform(0.02, 0.12)),
                }
            )

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        speed = float(self.params.get("speed", 1.0)) * anim
        thickness = max(1, int(self.params.get("thickness", 3)))
        glow = float(self.params.get("glow", 0.8))
        chaos = float(self.params.get("chaos", 0.4))

        base = self._to_uint8(self._blank())
        glow_layer = np.zeros_like(base)

        for line in self.lines:
            pts = []
            for i, p in enumerate(line["pts"]):
                wobble = line["amp"] * np.sin(t * speed * line["speed"] * np.pi * 4 + line["phase"] + i)
                cx = (p[0] + wobble * np.cos(line["phase"] + i) * chaos) % 1.0
                cy = (p[1] + wobble * np.sin(line["phase"] + i * 0.7) + t * 0.05 * line["speed"]) % 1.0
                pts.append([cx * self.width, cy * self.height])
            arr = np.array(pts, dtype=np.int32)
            color = self.palette.as_uint8((line["hue"] + t) % 1.0)
            cv2.polylines(glow_layer, [arr], False, color, thickness + 4, lineType=cv2.LINE_AA)
            cv2.polylines(base, [arr], False, color, thickness, lineType=cv2.LINE_AA)

        # Soft bloom
        blurred = cv2.GaussianBlur(glow_layer, (0, 0), sigmaX=6 + glow * 8)
        out = cv2.addWeighted(base, 1.0, blurred, 0.55 * glow, 0)
        return out
