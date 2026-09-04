"""Geometric shapes art engine."""

from __future__ import annotations

import cv2
import numpy as np

from app.art.base import ArtEngine, register_engine


@register_engine
class GeometricEngine(ArtEngine):
    name = "geometric"
    description = "Animated geometric polygons and lines"

    def _on_setup(self) -> None:
        assert self.rng is not None
        n = int(self.params.get("shape_count", 16))
        self.shapes = []
        for _ in range(n):
            sides = int(self.rng.integers(3, 8))
            self.shapes.append(
                {
                    "sides": sides,
                    "cx": float(self.rng.uniform(0.1, 0.9)),
                    "cy": float(self.rng.uniform(0.1, 0.9)),
                    "radius": float(self.rng.uniform(0.04, 0.22)),
                    "phase": float(self.rng.random() * np.pi * 2),
                    "spin": float(self.rng.uniform(-1, 1)),
                    "hue": float(self.rng.random()),
                    "filled": bool(self.rng.random() < float(self.params.get("filled_ratio", 0.5))),
                    "orbit": float(self.rng.uniform(0.0, 0.15)),
                }
            )

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        speed = float(self.params.get("rotation_speed", 0.8)) * float(
            self.params.get("animation_speed", 1.0)
        )
        line_w = max(1, int(self.params.get("line_width", 2)))
        frame = self._blank()
        img = self._to_uint8(frame)

        for s in self.shapes:
            angle = s["phase"] + t * speed * s["spin"] * np.pi * 4
            ox = s["orbit"] * np.sin(t * speed * np.pi * 2 + s["phase"])
            oy = s["orbit"] * np.cos(t * speed * np.pi * 2 + s["phase"])
            cx = (s["cx"] + ox) * self.width
            cy = (s["cy"] + oy) * self.height
            radius = s["radius"] * min(self.width, self.height) * (
                0.85 + 0.15 * np.sin(t * np.pi * 2 + s["phase"])
            )
            pts = []
            for i in range(s["sides"]):
                a = angle + i * (2 * np.pi / s["sides"])
                pts.append([cx + np.cos(a) * radius, cy + np.sin(a) * radius])
            pts_arr = np.array(pts, dtype=np.int32)
            color = self.palette.as_uint8((s["hue"] + t) % 1.0)
            if s["filled"]:
                overlay = img.copy()
                cv2.fillPoly(overlay, [pts_arr], color)
                cv2.addWeighted(overlay, 0.45, img, 0.55, 0, img)
            cv2.polylines(img, [pts_arr], True, color, line_w, lineType=cv2.LINE_AA)
        return img
