"""Kids doodle board — educational shapes, colors, counting, and playful art."""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw

from app.art.base import ArtEngine, register_engine
from app.art.education_content import build_kids_doodle_lesson
from app.art.education_ui import (
    draw_closing_banner,
    draw_learning_strip,
    draw_progress_dots,
    draw_title_banner,
    load_font,
    pop_scale,
    segment_at,
)
from app.art.word_images import ensure_word_image, paste_word_image


@register_engine
class KidsDoodleEngine(ArtEngine):
    """Educational kids doodle board with shapes, colors, counting, and word stickers."""

    name = "kids_doodles"
    description = "Educational kids doodle board — shapes, colors, counting, and stickers"

    def _on_setup(self) -> None:
        assert self.rng is not None
        duration = float(self.params.get("_duration", 30.0))
        if isinstance(self.params.get("education_lesson"), dict):
            self.lesson = self.params["education_lesson"]
        else:
            self.lesson = build_kids_doodle_lesson(self.seed, duration, params=self.params)

        self.mode = str(self.lesson.get("visual_mode", "focus"))
        self.segments = list(self.lesson.get("segments") or [])
        self.lesson_title = str(self.lesson.get("title") or "Doodle & Learn")
        self.closing = str(self.lesson.get("closing") or "Great job!")
        self.show_word_images = bool(self.params.get("show_word_images", True))
        self.show_captions = bool(self.params.get("show_captions", True))

        base = min(self.width, self.height)
        self.font_lg = load_font(max(48, int(base * 0.22)))
        self.font_md = load_font(max(28, int(base * 0.075)))
        self.font_sm = load_font(max(18, int(base * 0.042)))

        # Decorative floating shapes for background energy
        self.shapes = []
        n = int(self.params.get("shape_count", 14))
        kinds = ["circle", "square", "triangle", "star", "heart", "blob"]
        for _ in range(n):
            self.shapes.append(
                {
                    "kind": str(self.rng.choice(kinds)),
                    "x": float(self.rng.random()),
                    "y": float(self.rng.random()),
                    "size": float(self.rng.uniform(0.03, 0.08)),
                    "hue": float(self.rng.random()),
                    "phase": float(self.rng.random() * np.pi * 2),
                    "spin": float(self.rng.uniform(-1.5, 1.5)),
                }
            )
        self.stickers = list(self.rng.choice(list("★♥✦✿☀☁☂♫"), size=8))
        self.params["education_lesson"] = self.lesson

        if self.show_word_images:
            for seg in self.segments:
                w = str(seg.get("word") or seg.get("motif") or "")
                if w:
                    ensure_word_image(w)

    def _segment_at(self, t: float) -> dict:
        return segment_at(self.segments, t)

    def _make_background(self, t: float) -> Image.Image:
        assert self.palette is not None
        board_mode = str(self.params.get("board_mode", "colorful"))
        if board_mode == "chalkboard":
            return Image.fromarray(np.full((self.height, self.width, 3), (34, 74, 48), dtype=np.uint8))
        c0 = np.array(self.palette.as_uint8(0.1), dtype=np.float32)
        c1 = np.array(self.palette.as_uint8(0.6), dtype=np.float32)
        yy = np.linspace(0, 1, self.height, dtype=np.float32)[:, None, None]
        bg = (c0 * (1.0 - yy) + c1 * yy)
        bg = np.broadcast_to(bg, (self.height, self.width, 3)).copy().astype(np.uint8)
        return Image.fromarray(bg)

    def _draw_shape(
        self,
        draw: ImageDraw.ImageDraw,
        kind: str,
        x: int,
        y: int,
        size: int,
        fill: tuple[int, int, int],
        outline: tuple[int, int, int],
        ang: float = 0.0,
    ) -> None:
        fill_rgba = (*fill, 200)
        outline_rgba = (*outline, 255)
        kind = kind.lower()
        if kind == "circle":
            draw.ellipse((x - size, y - size, x + size, y + size), fill=fill_rgba, outline=outline_rgba, width=4)
        elif kind == "square":
            draw.rectangle((x - size, y - size, x + size, y + size), fill=fill_rgba, outline=outline_rgba, width=4)
        elif kind == "triangle":
            pts = [(x, y - size), (x - size, y + size), (x + size, y + size)]
            draw.polygon(pts, fill=fill_rgba, outline=outline_rgba)
        elif kind == "star":
            pts = []
            for i in range(10):
                a = np.radians(ang - 90 + i * 36)
                r = size if i % 2 == 0 else size * 0.45
                pts.append((x + np.cos(a) * r, y + np.sin(a) * r))
            draw.polygon(pts, fill=fill_rgba, outline=outline_rgba)
        elif kind == "heart":
            draw.ellipse((x - size, y - size // 2, x, y + size // 2), fill=fill_rgba)
            draw.ellipse((x, y - size // 2, x + size, y + size // 2), fill=fill_rgba)
            draw.polygon([(x - size, y), (x + size, y), (x, y + size)], fill=fill_rgba)
        else:
            pts = []
            for i in range(8):
                a = np.radians(i * 45 + ang)
                r = size * (0.7 + 0.3 * np.sin(i * 2))
                pts.append((x + np.cos(a) * r, y + np.sin(a) * r))
            draw.polygon(pts, fill=fill_rgba, outline=outline_rgba)

    def _draw_decor(self, draw: ImageDraw.ImageDraw, t: float, anim: float) -> None:
        assert self.palette is not None
        for s in self.shapes:
            x = int((s["x"] + 0.02 * np.sin(t * anim * 3 + s["phase"])) * self.width)
            y = int((s["y"] + 0.02 * np.cos(t * anim * 2 + s["phase"])) * self.height)
            size = int(s["size"] * min(self.width, self.height) * 0.6)
            color = self.palette.as_uint8((s["hue"] + t * 0.1) % 1.0)
            outline = tuple(max(0, c - 50) for c in color)
            self._draw_shape(draw, s["kind"], x, y, size, color, outline, t * s["spin"] * 30)

        for i, ch in enumerate(self.stickers):
            x = int(((i * 0.12 + t * anim * 0.1) % 1.0) * self.width)
            y = int(self.height * (0.12 + 0.06 * np.sin(i + t * 4)))
            draw.text((x, y), ch, font=self.font_sm, fill=self.palette.as_uint8((i * 0.1 + t) % 1.0))

    def _draw_focus_segment(self, draw: ImageDraw.ImageDraw, img: Image.Image, seg: dict, t: float, anim: float) -> None:
        assert self.palette is not None
        local = (t - float(seg["t0"])) / max(1e-6, float(seg["t1"]) - float(seg["t0"]))
        scale = pop_scale(float(np.clip(local * 2.0, 0, 1)))
        shape = str(seg.get("shape", "circle"))
        cx, cy = self.width // 2, int(self.height * 0.38)
        bounce = int(np.sin(t * anim * np.pi * 4) * 14 * scale)
        size = int(min(self.width, self.height) * 0.16 * scale)

        if seg.get("color_rgb"):
            color = tuple(int(c) for c in seg["color_rgb"])
        else:
            color = self.palette.as_uint8((hash(shape) % 100) / 100.0 + t * 0.15)
        outline = tuple(max(0, c - 45) for c in color)
        ang = t * anim * 40
        self._draw_shape(draw, shape, cx, cy + bounce, size, color, outline, ang)

        # Label
        label = str(seg.get("color_name") or shape.title())
        draw.text((cx, int(self.height * 0.58)), label, font=self.font_lg, fill=(40, 50, 70), anchor="mm")

        word = str(seg.get("word") or "")
        if self.show_word_images and word:
            paste_word_image(
                img,
                word,
                (int(self.width * 0.72), int(self.height * 0.42)),
                max(90, int(min(self.width, self.height) * 0.16 * scale)),
                bounce=int(5 * np.sin(t * 5)),
            )

    def _draw_count_segment(self, draw: ImageDraw.ImageDraw, img: Image.Image, seg: dict, t: float, anim: float) -> None:
        assert self.palette is not None
        count = int(seg.get("count", 3))
        shape = str(seg.get("shape", "circle"))
        local = (t - float(seg["t0"])) / max(1e-6, float(seg["t1"]) - float(seg["t0"]))
        reveal = int(min(count, np.floor(local * count * 1.2) + 1))
        cols = min(count, 5)
        rows = int(np.ceil(count / cols))
        cell_w = self.width * 0.7 / cols
        cell_h = self.height * 0.35 / max(1, rows)
        start_x = self.width * 0.15
        start_y = self.height * 0.22

        for i in range(reveal):
            row, col = divmod(i, cols)
            cx = int(start_x + (col + 0.5) * cell_w)
            cy = int(start_y + (row + 0.5) * cell_h)
            pop = pop_scale(float(np.clip(local * count - i, 0, 1)))
            size = int(min(cell_w, cell_h) * 0.28 * pop)
            color = self.palette.as_uint8((i * 0.12 + t * 0.1) % 1.0)
            outline = tuple(max(0, c - 40) for c in color)
            self._draw_shape(draw, shape, cx, cy, size, color, outline, t * 30 + i * 20)

        draw.text((self.width // 2, int(self.height * 0.62)), str(count), font=self.font_lg, fill=(50, 70, 100), anchor="mm")

        word = str(seg.get("word") or "")
        if self.show_word_images and word:
            paste_word_image(img, word, (int(self.width * 0.78), int(self.height * 0.35)), max(80, int(min(self.width, self.height) * 0.14)))

    def _draw_stickers(self, draw: ImageDraw.ImageDraw, img: Image.Image, seg: dict, t: float, anim: float) -> None:
        assert self.palette is not None
        letter = str(seg.get("letter", "A"))
        local = (t - float(seg["t0"])) / max(1e-6, float(seg["t1"]) - float(seg["t0"]))
        scale = pop_scale(float(np.clip(local * 2.0, 0, 1)))
        cx, cy = self.width // 2, int(self.height * 0.36)
        color = self.palette.as_uint8((hash(letter) % 100) / 100.0)
        size = int(min(self.width, self.height) * 0.12 * scale)
        draw.ellipse((cx - size, cy - size, cx + size, cy + size), fill=(*color, 180), outline=(50, 60, 80), width=4)
        draw.text((cx, cy), letter, font=self.font_lg, fill=(255, 255, 255), anchor="mm")

        shape = str(seg.get("shape", "star"))
        sx = int(self.width * 0.25)
        sy = int(self.height * 0.42)
        self._draw_shape(draw, shape, sx, sy, int(size * 0.85), color, (40, 50, 70), t * 50)

        word = str(seg.get("word") or "")
        if self.show_word_images and word:
            paste_word_image(img, word, (int(self.width * 0.72), int(self.height * 0.38)), max(100, int(min(self.width, self.height) * 0.18 * scale)))

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        seg = self._segment_at(t)

        img = self._make_background(t)
        draw = ImageDraw.Draw(img, "RGBA")
        self._draw_decor(draw, t, anim * 0.6)

        if self.mode == "count":
            self._draw_count_segment(draw, img, seg, t, anim)
        elif self.mode == "stickers":
            self._draw_stickers(draw, img, seg, t, anim)
        elif self.mode in {"focus", "color", "playground"}:
            self._draw_focus_segment(draw, img, seg, t, anim)
        else:
            self._draw_focus_segment(draw, img, seg, t, anim)

        draw = ImageDraw.Draw(img.convert("RGB"))
        if self.show_captions:
            draw_title_banner(draw, self.width, self.height, self.lesson_title, self.font_sm)
            draw_learning_strip(
                draw,
                img,
                seg,
                self.width,
                self.height,
                {"md": self.font_md, "sm": self.font_sm},
                show_word_image=self.show_word_images,
                accent_color=self.palette.as_uint8(0.4),
            )
            draw_progress_dots(draw, seg, self.segments, self.width, self.height, self.palette.as_uint8(0.5))
            if t > 0.92:
                draw_closing_banner(draw, self.width, self.height, self.closing, self.font_sm)

        # Crayon scribble at bottom
        arr = np.array(img.convert("RGB"), dtype=np.uint8, copy=True)
        for i in range(4):
            color = self.palette.as_uint8((0.2 * i + t) % 1.0)
            pts = []
            for k in range(12):
                pts.append(
                    [
                        int((0.1 + 0.8 * k / 11) * self.width),
                        int(self.height * (0.72 + 0.03 * i) + 10 * np.sin(k * 0.8 + t * 6 + i)),
                    ]
                )
            cv2.polylines(arr, [np.array(pts, dtype=np.int32)], False, color, 2, lineType=cv2.LINE_AA)
        return arr
