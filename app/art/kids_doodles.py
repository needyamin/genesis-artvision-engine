"""Kids doodle board — crayons, shapes, and playful random art."""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont
from pathlib import Path

from app.art.base import ArtEngine, register_engine
from app.art.alphabet_cartoon import _load_font


@register_engine
class KidsDoodleEngine(ArtEngine):
    """Bright kids' classroom doodle board with shapes and stickers."""

    name = "kids_doodles"
    description = "Playful children's doodle board with shapes and stickers"

    def _on_setup(self) -> None:
        assert self.rng is not None
        self.shapes = []
        n = int(self.params.get("shape_count", 18))
        kinds = ["circle", "square", "triangle", "star", "heart", "blob"]
        for _ in range(n):
            self.shapes.append(
                {
                    "kind": str(self.rng.choice(kinds)),
                    "x": float(self.rng.random()),
                    "y": float(self.rng.random()),
                    "size": float(self.rng.uniform(0.04, 0.12)),
                    "hue": float(self.rng.random()),
                    "phase": float(self.rng.random() * np.pi * 2),
                    "spin": float(self.rng.uniform(-1.5, 1.5)),
                }
            )
        self.stickers = list(self.rng.choice(list("★♥✦✿☀☁☂♫"), size=8))
        self.font = _load_font(max(24, int(min(self.width, self.height) * 0.06)))

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))

        # Chalkboard or colorful wall
        board_mode = str(self.params.get("board_mode", "colorful"))
        if board_mode == "chalkboard":
            bg = np.full((self.height, self.width, 3), (34, 74, 48), dtype=np.uint8)
        else:
            c0 = np.array(self.palette.as_uint8(0.1), dtype=np.float32)
            c1 = np.array(self.palette.as_uint8(0.6), dtype=np.float32)
            yy = np.linspace(0, 1, self.height, dtype=np.float32)[:, None, None]
            bg = (c0 * (1.0 - yy) + c1 * yy)
            bg = np.broadcast_to(bg, (self.height, self.width, 3)).copy().astype(np.uint8)

        img = Image.fromarray(bg)
        draw = ImageDraw.Draw(img, "RGBA")

        for s in self.shapes:
            x = int((s["x"] + 0.03 * np.sin(t * anim * 3 + s["phase"])) * self.width)
            y = int((s["y"] + 0.03 * np.cos(t * anim * 2 + s["phase"])) * self.height)
            size = int(s["size"] * min(self.width, self.height) * (0.9 + 0.15 * np.sin(t * 5 + s["phase"])))
            color = self.palette.as_uint8((s["hue"] + t * 0.2) % 1.0)
            fill = (*color, 180)
            outline = (*tuple(max(0, c - 40) for c in color), 255)
            ang = t * anim * s["spin"] * 40

            if s["kind"] == "circle":
                draw.ellipse((x - size, y - size, x + size, y + size), fill=fill, outline=outline, width=3)
            elif s["kind"] == "square":
                draw.rectangle((x - size, y - size, x + size, y + size), fill=fill, outline=outline, width=3)
            elif s["kind"] == "triangle":
                pts = [
                    (x, y - size),
                    (x - size, y + size),
                    (x + size, y + size),
                ]
                draw.polygon(pts, fill=fill, outline=outline)
            elif s["kind"] == "star":
                pts = []
                for i in range(10):
                    a = np.radians(ang - 90 + i * 36)
                    r = size if i % 2 == 0 else size * 0.45
                    pts.append((x + np.cos(a) * r, y + np.sin(a) * r))
                draw.polygon(pts, fill=fill, outline=outline)
            elif s["kind"] == "heart":
                draw.ellipse((x - size, y - size // 2, x, y + size // 2), fill=fill)
                draw.ellipse((x, y - size // 2, x + size, y + size // 2), fill=fill)
                draw.polygon([(x - size, y), (x + size, y), (x, y + size)], fill=fill)
            else:  # blob
                pts = []
                for i in range(8):
                    a = np.radians(i * 45 + ang)
                    r = size * (0.7 + 0.3 * np.sin(i * 2 + t * 4))
                    pts.append((x + np.cos(a) * r, y + np.sin(a) * r))
                draw.polygon(pts, fill=fill, outline=outline)

        # Floating sticker characters
        for i, ch in enumerate(self.stickers):
            x = int(((i * 0.12 + t * anim * 0.15) % 1.0) * self.width)
            y = int(self.height * (0.15 + 0.1 * np.sin(i + t * 4)))
            draw.text((x, y), ch, font=self.font, fill=self.palette.as_uint8((i * 0.1 + t) % 1.0))

        # Crayon scribble lines
        arr = np.array(img.convert("RGB"), dtype=np.uint8, copy=True)
        for i in range(5):
            color = self.palette.as_uint8((0.2 * i + t) % 1.0)
            pts = []
            for k in range(12):
                pts.append(
                    [
                        int((0.1 + 0.8 * k / 11) * self.width),
                        int(self.height * (0.85 + 0.04 * i) + 12 * np.sin(k * 0.8 + t * 6 + i)),
                    ]
                )
            cv2.polylines(arr, [np.array(pts, dtype=np.int32)], False, color, 3, lineType=cv2.LINE_AA)
        return arr
