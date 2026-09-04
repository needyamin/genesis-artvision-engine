"""Kaleidoscope art engine."""

from __future__ import annotations

import cv2
import numpy as np

from app.art.base import ArtEngine, register_engine


@register_engine
class KaleidoscopeEngine(ArtEngine):
    name = "kaleidoscope"
    description = "Symmetric kaleidoscope patterns"

    def _on_setup(self) -> None:
        assert self.rng is not None
        self.segments = int(self.params.get("segments", 8))
        self.layers = int(self.params.get("layers", 4))
        self.seeds = self.rng.random((self.layers, 6)).astype(np.float32)

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        spin = float(self.params.get("spin", 0.8)) * anim
        pulse = float(self.params.get("pulse", 0.6))
        size = min(self.width, self.height)
        # Draw wedge pattern then mirror
        canvas = np.zeros((size, size, 3), dtype=np.uint8)
        cx = cy = size // 2
        for li in range(self.layers):
            s = self.seeds[li]
            radius = int(size * (0.15 + 0.7 * ((li + 1) / self.layers)) * (0.85 + 0.15 * np.sin(t * pulse * 8 + s[0] * 6)))
            angle = t * spin * np.pi * 2 + s[1] * np.pi * 2
            for k in range(3):
                a = angle + k * 0.4 + s[2 + k]
                x = int(cx + np.cos(a) * radius * s[5])
                y = int(cy + np.sin(a) * radius * (0.5 + s[4] * 0.5))
                color = self.palette.as_uint8((s[0] + t + li * 0.1) % 1.0)
                cv2.circle(canvas, (x, y), max(3, int(8 + 20 * s[3])), color, -1, lineType=cv2.LINE_AA)
                cv2.line(canvas, (cx, cy), (x, y), color, 2, lineType=cv2.LINE_AA)

        # Polar kaleidoscope via angular wrap
        yy, xx = np.mgrid[:size, :size]
        dx = xx - cx
        dy = yy - cy
        ang = (np.arctan2(dy, dx) + np.pi) / (2 * np.pi)
        rad = np.sqrt(dx * dx + dy * dy)
        seg = 1.0 / self.segments
        ang_mod = ang % seg
        ang_fold = np.where(ang_mod > seg / 2, seg - ang_mod, ang_mod)
        src_ang = ang_fold * self.segments * 2 * np.pi - np.pi
        sx = np.clip((cx + rad * np.cos(src_ang)).astype(np.int32), 0, size - 1)
        sy = np.clip((cy + rad * np.sin(src_ang)).astype(np.int32), 0, size - 1)
        kaleido = canvas[sy, sx]

        out = np.zeros((self.height, self.width, 3), dtype=np.uint8)
        bg = self.palette.as_uint8(0.0)
        out[:, :] = bg
        y0 = (self.height - size) // 2
        x0 = (self.width - size) // 2
        y1, x1 = y0 + size, x0 + size
        # Clip if canvas larger than frame
        src = kaleido
        if y0 < 0 or x0 < 0:
            src = cv2.resize(kaleido, (self.width, self.height))
            out = src
        else:
            out[y0:y1, x0:x1] = src
        return out
