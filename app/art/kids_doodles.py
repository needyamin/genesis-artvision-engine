"""Kids doodle board — smooth educational shapes, colors, counting, and playful art."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from app.art.base import ArtEngine, register_engine
from app.art.education_anim import (
    draw_glow_ring,
    ease_in_out_cubic,
    kids_breathe,
    kids_pop,
    segment_local,
)
from app.art.edit_brain import kids_shot
from app.art.education_content import build_kids_doodle_lesson
from app.art.education_ui import (
    draw_kids_chrome,
    draw_picture_card,
    draw_shape_properties_badge,
    draw_stage_card,
    draw_ten_frame,
    load_font,
    paint_text,
    paste_picture,
    segment_at,
)
from app.art.kids_layout import kids_layout
from app.art.word_images import ensure_word_image


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
        self.easing = "smooth"
        self.camera_feel = "static"

        self.layout = kids_layout(self.width, self.height)
        self.font_lg = load_font(self.layout.hero_font)
        self.font_md = load_font(self.layout.md_font)
        self.font_sm = load_font(self.layout.sm_font)
        self.font_xs = load_font(max(14, self.layout.sm_font - 2))

        self.shapes = []
        n = min(6, max(3, int(self.params.get("shape_count", 6))))
        kinds = ["circle", "square", "triangle", "star", "heart"]
        for _ in range(n):
            self.shapes.append(
                {
                    "kind": str(self.rng.choice(kinds)),
                    "x": float(self.rng.uniform(0.10, 0.90)),
                    "y": float(self.rng.uniform(0.18, 0.55)),
                    "size": float(self.rng.uniform(0.018, 0.035)),
                    "hue": float(self.rng.random()),
                    "phase": float(self.rng.random() * np.pi * 2),
                    "spin": 0.0,
                }
            )
        self.stickers: list[str] = []
        self.confetti_seeds = self.rng.random(18).astype(np.float32)
        self._dust = self.rng.random((self.height, self.width)).astype(np.float32) * 3
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
            base = np.clip(base + self._dust[:, :, None], 0, 255)
            return Image.fromarray(base.astype(np.uint8))
        c0 = np.array(self.palette.as_uint8(0.08), dtype=np.float32)
        c1 = np.array(self.palette.as_uint8(0.55), dtype=np.float32)
        yy = np.linspace(0, 1, self.height, dtype=np.float32)[:, None, None]
        wave = 0.015 * np.sin(yy * np.pi * 2)
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
        del anim
        assert self.palette is not None
        stage = self.layout.stage
        for s in self.shapes:
            x = int(stage.x0 + s["x"] * stage.w)
            y = int(stage.y0 + s["y"] * stage.h)
            size = int(s["size"] * min(stage.w, stage.h))
            color = self.palette.as_uint8(s["hue"])
            faded = tuple(int(c * 0.55 + 255 * 0.45) for c in color)
            outline = tuple(max(0, c - 40) for c in faded)
            self._draw_shape(draw, s["kind"], x, y, size, faded, outline, 0.0, trace=1.0, t=t)

    def _draw_focus_segment(
        self, draw: ImageDraw.ImageDraw, img: Image.Image, seg: dict, t: float, anim: float,
    ) -> None:
        del anim
        assert self.palette is not None
        local = segment_local(t, seg)
        shot = kids_shot(local)
        scale = shot.letter_scale
        trace = ease_in_out_cubic(min(1.0, local / 0.35))
        shape = str(seg.get("shape", "circle"))
        cx, cy = self.layout.letter_xy
        bounce = int(shot.bounce)
        size = int(min(self.layout.stage.w, self.layout.stage.h) * 0.36 * max(0.35, scale))

        draw_stage_card(draw, self.layout)
        if scale < 0.08:
            return
        if seg.get("color_rgb"):
            color = tuple(int(c) for c in seg["color_rgb"])
        else:
            color = self.palette.as_uint8((hash(shape) % 100) / 100.0)
        outline = tuple(max(0, c - 45) for c in color)
        self._draw_shape(draw, shape, cx, cy + bounce, size, color, outline, 0.0, trace=trace, glow=True, t=t)

        # Geometry Teacher Properties Badge (Sides & Vertices callout)
        if seg.get("shape_sides") is not None and shot.caption_alpha > 0.35:
            bw = min(220, int(self.layout.stage.w * 0.44))
            bh = max(38, int(self.layout.stage.h * 0.16))
            bx = cx - bw // 2
            by = self.layout.stage.y1 - bh - max(8, int(self.layout.stage.h * 0.04))
            sides = int(seg.get("shape_sides", 0))
            vertices = int(seg.get("shape_vertices", 0))
            fact = str(seg.get("shape_fact") or "")
            draw_shape_properties_badge(draw, sides, vertices, (bx, by), bw, bh, self.font_xs, fact=fact)

        if self.show_word_images and (seg.get("image_path") or seg.get("word")) and shot.picture_scale > 0.12:
            paste_picture(img, seg, self.layout, bounce=0 if shot.hold_still else int(kids_breathe(t, 3.0) * scale))
        else:
            draw_picture_card(draw, self.layout)
            pcx, pcy = self.layout.picture_xy
            ps = max(16, int(min(self.layout.picture.w, self.layout.picture.h) * 0.22))
            draw.ellipse((pcx - ps, pcy - ps, pcx + ps, pcy + ps), fill=color, outline=outline, width=4)
            paint_text(
                draw, (pcx, pcy + ps + 18),
                str(seg.get("color_name") or shape).upper(),
                self.font_sm, (40, 50, 70), anchor="mm",
                max_width=self.layout.picture.w - 16,
            )

    def _draw_count_segment(
        self, draw: ImageDraw.ImageDraw, img: Image.Image, seg: dict, t: float, anim: float,
    ) -> None:
        del anim
        assert self.palette is not None
        count = max(1, int(seg.get("count", 3)))
        shape = str(seg.get("shape", "circle"))
        local = segment_local(t, seg)
        reveal = int(min(count, np.floor(ease_in_out_cubic(min(1.0, local / 0.75)) * count) + 1))
        cols = min(count, 5)
        rows = int(np.ceil(count / cols))
        stage = self.layout.stage
        draw_stage_card(draw, self.layout)
        if seg.get("math_op"):
            eq = f"{int(seg.get('math_left', 0))} {seg.get('math_op')} {int(seg.get('math_right', 0))} = {count}"
            paint_text(
                draw,
                (stage.cx, stage.y0 + max(16, int(stage.h * 0.12))),
                eq,
                self.font_md,
                (40, 55, 90),
                anchor="mm",
                max_width=stage.w - 24,
            )
            cell_h = (stage.h * 0.78) / max(1, rows)
            y_off = int(stage.h * 0.18)
        else:
            cell_h = stage.h / max(1, rows)
            y_off = 0
        cell_w = stage.w / cols

        for i in range(reveal):
            row, col = divmod(i, cols)
            cx = int(stage.x0 + (col + 0.5) * cell_w)
            cy = int(stage.y0 + y_off + (row + 0.5) * cell_h)
            item_local = kids_pop(float(np.clip((local * count * 0.85) - i, 0, 1)))
            pop = item_local
            size = int(min(cell_w, cell_h) * 0.32 * max(0.05, pop))
            color = self.palette.as_uint8((i * 0.12) % 1.0)
            outline = tuple(max(0, c - 40) for c in color)
            self._draw_shape(draw, shape, cx, cy, size, color, outline, 0.0, trace=max(0.15, pop), glow=(i == reveal - 1), t=t)

        if self.show_word_images and (seg.get("image_path") or seg.get("word")) and kids_shot(local).picture_scale > 0.12:
            paste_picture(img, seg, self.layout)
        else:
            draw_picture_card(draw, self.layout)
            if count <= 10:
                tf_w = min(170, int(self.layout.picture.w * 0.85))
                tf_h = max(36, int(tf_w * 0.42))
                tf_x = self.layout.picture.cx - tf_w // 2
                tf_y = self.layout.picture.cy - tf_h // 2 + 10
                paint_text(
                    draw, (self.layout.picture.cx, tf_y - 18), str(count),
                    self.font_md, (50, 70, 100), anchor="mm",
                )
                dot_c = self.palette.as_uint8(0.2)
                draw_ten_frame(draw, count, (tf_x, tf_y), tf_w, tf_h, dot_color=dot_c, alpha=1.0)
            else:
                paint_text(
                    draw, self.layout.picture_xy, str(count),
                    self.font_lg, (50, 70, 100), anchor="mm",
                )

    def _draw_stickers(self, draw: ImageDraw.ImageDraw, img: Image.Image, seg: dict, t: float, anim: float) -> None:
        del anim
        assert self.palette is not None
        letter = str(seg.get("letter", "A"))
        word = str(seg.get("word") or letter).upper()
        local = segment_local(t, seg)
        shot = kids_shot(local)
        scale = shot.letter_scale
        cx, cy = self.layout.letter_xy
        color = self.palette.as_uint8((hash(letter) % 100) / 100.0)
        size = int(min(self.layout.stage.w, self.layout.stage.h) * 0.22 * max(0.2, scale))
        draw_stage_card(draw, self.layout)
        draw_glow_ring(draw, cx, cy, size, color, t, layers=2)
        if len(word) > 1:
            paint_text(
                draw, (cx, cy), word, self.font_lg, color, anchor="mm",
                max_width=self.layout.stage.w - 36,
            )
            spelled = "  ".join(word)
            paint_text(
                draw, (cx, cy + int(size * 0.85)), spelled, self.font_sm, (40, 55, 80),
                anchor="mm", max_width=self.layout.stage.w - 28,
            )
        else:
            draw.ellipse((cx - size, cy - size, cx + size, cy + size), fill=(*color, 200), outline=(50, 60, 80), width=4)
            paint_text(draw, (cx, cy), letter, self.font_lg, (255, 255, 255), anchor="mm")

        if self.show_word_images and (seg.get("image_path") or seg.get("word")) and shot.picture_scale > 0.12:
            paste_picture(img, seg, self.layout)
        else:
            draw_picture_card(draw, self.layout)
            paint_text(draw, self.layout.picture_xy, letter, self.font_lg, color, anchor="mm")

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

        if img.mode != "RGB":
            img = img.convert("RGB")
        draw = ImageDraw.Draw(img)
        if self.show_captions:
            shot = kids_shot(segment_local(t, seg))
            draw_kids_chrome(
                draw, img, self.layout,
                title=self.lesson_title,
                seg=seg,
                segments=self.segments,
                fonts={"md": self.font_md, "sm": self.font_sm},
                t=t,
                closing=self.closing,
                accent=self.palette.as_uint8(0.5),
                confetti_seeds=self.confetti_seeds,
                caption_alpha=shot.caption_alpha,
                celebrate=shot.celebrate,
            )

        arr = np.array(img, dtype=np.uint8, copy=True)
        return arr
