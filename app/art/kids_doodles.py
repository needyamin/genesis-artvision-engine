"""Kids doodle board — smooth educational shapes, colors, counting, and playful art."""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw

from app.art.base import ArtEngine, register_engine
from app.art.education_anim import (
    draw_confetti,
    draw_glow_ring,
    draw_prompt_bubble,
    ease_in_out_cubic,
    segment_local,
    smooth_pop,
)
from app.art.education_content import build_kids_doodle_lesson
from app.art.education_ui import (
    draw_closing_banner,
    draw_engagement_overlay,
    draw_learning_strip,
    draw_progress_dots,
    draw_title_banner,
    load_font,
    segment_at,
)
from app.art.word_images import ensure_word_image, paste_word_image


@register_engine
class KidsDoodleEngine(ArtEngine):
    """Smooth educational kids doodle board — shapes, colors, counting, and stickers."""

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
        for seg in self.segments:
            seg["_total"] = len(self.segments)
        self.lesson_title = str(self.lesson.get("title") or "Doodle & Learn")
        self.closing = str(self.lesson.get("closing") or "Great job!")
        self.show_word_images = bool(self.params.get("show_word_images", True))
        self.show_captions = bool(self.params.get("show_captions", True))

        base = min(self.width, self.height)
        self.font_lg = load_font(max(48, int(base * 0.22)))
        self.font_md = load_font(max(28, int(base * 0.075)))
        self.font_sm = load_font(max(18, int(base * 0.042)))
        self.font_xs = load_font(max(14, int(base * 0.032)))

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
                    "spin": float(self.rng.uniform(-1.0, 1.0)),
                }
            )
        self.stickers = list(self.rng.choice(list("★♥✦✿☀☁☂♫"), size=8))
        self.confetti_seeds = self.rng.random(40).astype(np.float32)
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
            base = np.full((self.height, self.width, 3), (34, 74, 48), dtype=np.float32)
            dust = self.rng.random((self.height, self.width)).astype(np.float32) * 6 * np.sin(t * 3)
            base = np.clip(base + dust[:, :, None], 0, 255)
            return Image.fromarray(base.astype(np.uint8))
        c0 = np.array(self.palette.as_uint8(0.08), dtype=np.float32)
        c1 = np.array(self.palette.as_uint8(0.55), dtype=np.float32)
        yy = np.linspace(0, 1, self.height, dtype=np.float32)[:, None, None]
        wave = 0.04 * np.sin(yy * np.pi * 3 + t * 2)
        bg = (c0 * (1.0 - yy - wave) + c1 * (yy + wave))
        bg = np.broadcast_to(bg, (self.height, self.width, 3)).copy()
        return Image.fromarray(np.clip(bg, 0, 255).astype(np.uint8))

    def _shape_points(self, kind: str, x: float, y: float, size: float, ang: float = 0.0) -> list[tuple[float, float]]:
        kind = kind.lower()
        if kind == "circle":
            a = np.linspace(0, 2 * np.pi, 48, endpoint=False)
            return [(x + np.cos(v) * size, y + np.sin(v) * size) for v in a]
        if kind == "square":
            s = size
            return [(x - s, y - s), (x + s, y - s), (x + s, y + s), (x - s, y + s), (x - s, y - s)]
        if kind == "triangle":
            return [(x, y - size), (x - size, y + size), (x + size, y + size), (x, y - size)]
        if kind == "star":
            pts = []
            for i in range(10):
                a = np.radians(ang - 90 + i * 36)
                r = size if i % 2 == 0 else size * 0.45
                pts.append((x + np.cos(a) * r, y + np.sin(a) * r))
            pts.append(pts[0])
            return pts
        if kind == "heart":
            a = np.linspace(0, 2 * np.pi, 40, endpoint=False)
            return [
                (x + size * 0.5 * (16 * np.sin(v) ** 3) / 16,
                 y - size * 0.5 * (13 * np.cos(v) - 5 * np.cos(2 * v) - 2 * np.cos(3 * v) - np.cos(4 * v)) / 16)
                for v in a
            ]
        pts = []
        for i in range(9):
            a = np.radians(i * 45 + ang)
            r = size * (0.7 + 0.3 * np.sin(i * 2))
            pts.append((x + np.cos(a) * r, y + np.sin(a) * r))
        pts.append(pts[0])
        return pts

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
        *,
        trace: float = 1.0,
        glow: bool = False,
        t: float = 0.0,
    ) -> None:
        if glow:
            draw_glow_ring(draw, x, y, size, fill, t)
        pts = self._shape_points(kind, float(x), float(y), float(size), ang)
        n_show = max(2, int(len(pts) * ease_in_out_cubic(trace)))
        trace_pts = pts[:n_show]
        if trace < 0.95:
            draw.line(trace_pts, fill=outline, width=5, joint="curve")
        else:
            fill_rgba = (*fill, 210)
            outline_rgba = (*outline, 255)
            kind_l = kind.lower()
            if kind_l == "circle":
                draw.ellipse((x - size, y - size, x + size, y + size), fill=fill_rgba, outline=outline_rgba, width=4)
            elif kind_l == "square":
                draw.rectangle((x - size, y - size, x + size, y + size), fill=fill_rgba, outline=outline_rgba, width=4)
            elif kind_l == "heart":
                draw.ellipse((x - size, y - size // 2, x, y + size // 2), fill=fill_rgba)
                draw.ellipse((x, y - size // 2, x + size, y + size // 2), fill=fill_rgba)
                draw.polygon([(x - size, y), (x + size, y), (x, y + size)], fill=fill_rgba)
            else:
                draw.polygon(trace_pts, fill=fill_rgba, outline=outline_rgba)

    def _draw_decor(self, draw: ImageDraw.ImageDraw, t: float, anim: float) -> None:
        assert self.palette is not None
        for s in self.shapes:
            drift = ease_in_out_cubic((np.sin(t * anim * 2 + s["phase"]) + 1) * 0.5)
            x = int((s["x"] + 0.015 * drift) * self.width)
            y = int((s["y"] + 0.012 * np.cos(t * anim * 1.5 + s["phase"])) * self.height)
            size = int(s["size"] * min(self.width, self.height) * (0.55 + 0.1 * np.sin(t * 3 + s["phase"])))
            color = self.palette.as_uint8((s["hue"] + t * 0.08) % 1.0)
            outline = tuple(max(0, c - 50) for c in color)
            self._draw_shape(draw, s["kind"], x, y, size, color, outline, t * s["spin"] * 20, trace=0.6 + 0.4 * drift)

        for i, ch in enumerate(self.stickers):
            x = int(((i * 0.12 + t * anim * 0.08) % 1.0) * self.width)
            y = int(self.height * (0.11 + 0.05 * np.sin(i + t * 3)))
            draw.text((x, y), ch, font=self.font_sm, fill=self.palette.as_uint8((i * 0.1 + t) % 1.0))

    def _draw_focus_segment(
        self, draw: ImageDraw.ImageDraw, img: Image.Image, seg: dict, t: float, anim: float,
    ) -> None:
        assert self.palette is not None
        local = segment_local(t, seg)
        scale = smooth_pop(min(1.0, local * 2.5))
        trace = ease_in_out_cubic(min(1.0, local * 1.8))
        shape = str(seg.get("shape", "circle"))
        cx, cy = self.width // 2, int(self.height * 0.36)
        bounce = int(np.sin(t * anim * np.pi * 3) * 10 * scale)
        size = int(min(self.width, self.height) * 0.17 * scale)

        if seg.get("color_rgb"):
            color = tuple(int(c) for c in seg["color_rgb"])
        else:
            color = self.palette.as_uint8((hash(shape) % 100) / 100.0 + t * 0.12)
        outline = tuple(max(0, c - 45) for c in color)
        self._draw_shape(draw, shape, cx, cy + bounce, size, color, outline, t * anim * 30, trace=trace, glow=True, t=t)

        label = str(seg.get("color_name") or shape.title())
        label_scale = smooth_pop(min(1.0, local * 1.5), elastic=False)
        if label_scale > 0.1:
            draw.text((cx, int(self.height * 0.56)), label, font=self.font_lg, fill=(40, 50, 70), anchor="mm")

        word = str(seg.get("word") or "")
        if self.show_word_images and word and scale > 0.3:
            paste_word_image(
                img, word,
                (int(self.width * 0.72), int(self.height * 0.40)),
                max(90, int(min(self.width, self.height) * 0.17 * scale)),
                bounce=int(4 * np.sin(t * 4)),
            )

        if local > 0.75 and seg.get("engage"):
            draw_prompt_bubble(draw, str(seg["engage"]), cx, int(self.height * 0.26), self.font_xs, (local - 0.75) * 4)

    def _draw_count_segment(
        self, draw: ImageDraw.ImageDraw, img: Image.Image, seg: dict, t: float, anim: float,
    ) -> None:
        assert self.palette is not None
        count = int(seg.get("count", 3))
        shape = str(seg.get("shape", "circle"))
        local = segment_local(t, seg)
        reveal = int(min(count, np.floor(ease_in_out_cubic(local) * count * 1.15) + 1))
        cols = min(count, 5)
        rows = int(np.ceil(count / cols))
        cell_w = self.width * 0.7 / cols
        cell_h = self.height * 0.32 / max(1, rows)
        start_x = self.width * 0.15
        start_y = self.height * 0.20

        for i in range(reveal):
            row, col = divmod(i, cols)
            cx = int(start_x + (col + 0.5) * cell_w)
            cy = int(start_y + (row + 0.5) * cell_h)
            item_local = ease_in_out_cubic(float(np.clip(local * count * 1.15 - i, 0, 1)))
            pop = smooth_pop(item_local)
            size = int(min(cell_w, cell_h) * 0.30 * pop)
            color = self.palette.as_uint8((i * 0.12 + t * 0.08) % 1.0)
            outline = tuple(max(0, c - 40) for c in color)
            self._draw_shape(draw, shape, cx, cy, size, color, outline, t * 25 + i * 15, trace=item_local, glow=(i == reveal - 1), t=t)

        num_scale = smooth_pop(min(1.0, local * 2))
        if num_scale > 0.1:
            draw.text((self.width // 2, int(self.height * 0.60)), str(count), font=self.font_lg, fill=(50, 70, 100), anchor="mm")

        word = str(seg.get("word") or "")
        if self.show_word_images and word and local > 0.4:
            paste_word_image(img, word, (int(self.width * 0.78), int(self.height * 0.34)), max(80, int(min(self.width, self.height) * 0.14)))

    def _draw_stickers(self, draw: ImageDraw.ImageDraw, img: Image.Image, seg: dict, t: float, anim: float) -> None:
        assert self.palette is not None
        letter = str(seg.get("letter", "A"))
        local = segment_local(t, seg)
        scale = smooth_pop(min(1.0, local * 2.5))
        cx, cy = self.width // 2, int(self.height * 0.35)
        color = self.palette.as_uint8((hash(letter) % 100) / 100.0)
        size = int(min(self.width, self.height) * 0.13 * scale)
        draw_glow_ring(draw, cx, cy, size, color, t)
        draw.ellipse((cx - size, cy - size, cx + size, cy + size), fill=(*color, 200), outline=(50, 60, 80), width=4)
        draw.text((cx, cy), letter, font=self.font_lg, fill=(255, 255, 255), anchor="mm")

        shape = str(seg.get("shape", "star"))
        sx, sy = int(self.width * 0.24), int(self.height * 0.40)
        self._draw_shape(draw, shape, sx, sy, int(size * 0.8), color, (40, 50, 70), t * 40, trace=ease_in_out_cubic(local), t=t)

        word = str(seg.get("word") or "")
        if self.show_word_images and word and scale > 0.25:
            paste_word_image(img, word, (int(self.width * 0.72), int(self.height * 0.37)), max(100, int(min(self.width, self.height) * 0.18 * scale)))

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        seg = self._segment_at(t)

        img = self._make_background(t)
        draw = ImageDraw.Draw(img, "RGBA")
        self._draw_decor(draw, t, anim * 0.5)

        if self.mode == "count":
            self._draw_count_segment(draw, img, seg, t, anim)
        elif self.mode == "stickers":
            self._draw_stickers(draw, img, seg, t, anim)
        else:
            self._draw_focus_segment(draw, img, seg, t, anim)

        draw = ImageDraw.Draw(img.convert("RGB"))
        if self.show_captions:
            draw_title_banner(draw, self.width, self.height, self.lesson_title, self.font_sm)
            draw_learning_strip(
                draw, img, seg, self.width, self.height,
                {"md": self.font_md, "sm": self.font_sm},
                show_word_image=self.show_word_images, t=t,
            )
            draw_engagement_overlay(draw, seg, self.width, self.height, self.font_xs, t, self.confetti_seeds)
            draw_progress_dots(draw, seg, self.segments, self.width, self.height, self.palette.as_uint8(0.5), t=t)
            if t > 0.92:
                draw_closing_banner(draw, self.width, self.height, self.closing, self.font_sm)
                draw_confetti(draw, self.width, self.height, t, self.confetti_seeds, intensity=1.0)

        arr = np.array(img.convert("RGB"), dtype=np.uint8, copy=True)
        for i in range(3):
            color = self.palette.as_uint8((0.15 * i + t) % 1.0)
            pts = []
            for k in range(16):
                pts.append([
                    int((0.08 + 0.84 * k / 15) * self.width),
                    int(self.height * (0.71 + 0.025 * i) + 8 * np.sin(k * 0.7 + t * 5 + i * 0.5)),
                ])
            cv2.polylines(arr, [np.array(pts, dtype=np.int32)], False, color, 2, lineType=cv2.LINE_AA)
        blur = cv2.GaussianBlur(arr, (0, 0), sigmaX=0.8)
        return cv2.addWeighted(arr, 0.92, blur, 0.08, 0)
