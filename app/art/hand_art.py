"""Hand-drawn educational art engine — step-by-step draw-along lessons."""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw

from app.art.base import ArtEngine, register_engine
from app.art.education_content import build_hand_art_lesson
from app.art.education_ui import (
    draw_closing_banner,
    draw_learning_strip,
    draw_progress_dots,
    draw_title_banner,
    load_font,
    segment_at,
)
from app.art.word_images import ensure_word_image


def _wobble_polyline(
    pts: np.ndarray,
    rng: np.random.Generator,
    amount: float = 2.0,
) -> np.ndarray:
    noise = (rng.random(pts.shape) - 0.5) * amount
    return pts + noise


def _hand_circle(cx: float, cy: float, r: float, n: int = 36) -> np.ndarray:
    a = np.linspace(0, 2 * np.pi, n, endpoint=True)
    return np.column_stack([cx + np.cos(a) * r, cy + np.sin(a) * r])


def _hand_star(cx: float, cy: float, r: float) -> np.ndarray:
    pts = []
    for i in range(10):
        ang = -np.pi / 2 + i * np.pi / 5
        rad = r if i % 2 == 0 else r * 0.45
        pts.append([cx + np.cos(ang) * rad, cy + np.sin(ang) * rad])
    pts.append(pts[0])
    return np.asarray(pts, dtype=np.float32)


@register_engine
class HandArtEngine(ArtEngine):
    """Educational hand-art draw-along: step-by-step sketch lessons with narration."""

    name = "hand_art"
    description = "Hand-drawn draw-along lessons with sketchy step-by-step art"

    def _on_setup(self) -> None:
        assert self.rng is not None
        duration = float(self.params.get("_duration", 30.0))
        if isinstance(self.params.get("education_lesson"), dict):
            self.lesson = self.params["education_lesson"]
        else:
            self.lesson = build_hand_art_lesson(self.seed, duration, params=self.params)

        self.mode = str(self.lesson.get("visual_mode", "draw_along"))
        self.segments = list(self.lesson.get("segments") or [])
        self.lesson_title = str(self.lesson.get("title") or "Draw Along")
        self.closing = str(self.lesson.get("closing") or "Great drawing!")
        self.show_captions = bool(self.params.get("show_captions", True))
        self.show_word_images = bool(self.params.get("show_word_images", True))

        base = min(self.width, self.height)
        self.font_md = load_font(max(28, int(base * 0.075)))
        self.font_sm = load_font(max(18, int(base * 0.042)))

        self.stroke = max(1, int(self.params.get("stroke_width", 2)))
        self.sketchiness = float(self.params.get("sketchiness", 0.7))
        self.paper_grain = float(self.params.get("paper_grain", 0.35))
        self.params["education_lesson"] = self.lesson

        if self.show_word_images:
            for seg in self.segments:
                w = str(seg.get("word") or seg.get("motif") or "")
                if w:
                    ensure_word_image(w)

    def _segment_at(self, t: float) -> dict:
        return segment_at(self.segments, t)

    def _paper(self) -> np.ndarray:
        assert self.palette is not None and self.rng is not None
        base = np.array(self.palette.as_uint8(0.05), dtype=np.float32)
        paper = np.full((self.height, self.width, 3), [236, 228, 210], dtype=np.float32)
        paper = paper * 0.75 + base * 0.25
        if self.paper_grain > 0.05:
            grain = self.rng.normal(0, 6 * self.paper_grain, (self.height, self.width, 1)).astype(np.float32)
            paper = paper + grain
        return np.clip(paper, 0, 255).astype(np.uint8)

    def _stroke(self, img: np.ndarray, pts: np.ndarray, color: tuple[int, int, int], rng: np.random.Generator) -> None:
        if len(pts) < 2:
            return
        wob = _wobble_polyline(pts.astype(np.float32), rng, amount=1.2 + self.sketchiness * 2.5)
        arr = wob.astype(np.int32)
        cv2.polylines(img, [arr], False, color, self.stroke + 1, lineType=cv2.LINE_AA)
        faint = tuple(min(255, c + 40) for c in color)
        cv2.polylines(img, [arr], False, faint, max(1, self.stroke), lineType=cv2.LINE_AA)

    def _draw_doodle(
        self,
        img: np.ndarray,
        kind: str,
        cx: float,
        cy: float,
        s: float,
        color: tuple[int, int, int],
        rng: np.random.Generator,
        t: float,
        anim: float,
        progress: float = 1.0,
    ) -> None:
        progress = float(np.clip(progress, 0.05, 1.0))
        kind = kind.lower()

        if kind == "scribble":
            n = max(4, int(20 * progress))
            ang = np.linspace(0, 4 * np.pi, n) + t * anim
            rad = np.linspace(s * 0.2, s, n)
            pts = np.column_stack([cx + np.cos(ang) * rad, cy + np.sin(ang) * rad])
            self._stroke(img, pts, color, rng)
        elif kind == "spiral":
            n = max(4, int(60 * progress))
            ang = np.linspace(0, 5 * np.pi, n) + t * anim * 2
            rad = np.linspace(2, s, n)
            pts = np.column_stack([cx + np.cos(ang) * rad, cy + np.sin(ang) * rad])
            self._stroke(img, pts, color, rng)
        elif kind == "star":
            pts = _hand_star(cx, cy, s * progress)
            self._stroke(img, pts, color, rng)
        elif kind == "sun":
            pts = _hand_circle(cx, cy, s * 0.45 * progress)
            self._stroke(img, pts, color, rng)
            rays = int(12 * progress)
            for a in range(0, rays * 30, 30):
                rad = np.radians(a + t * 40)
                p0 = np.array([[cx + np.cos(rad) * s * 0.55, cy + np.sin(rad) * s * 0.55]])
                p1 = np.array([[cx + np.cos(rad) * s, cy + np.sin(rad) * s]])
                self._stroke(img, np.vstack([p0, p1]), color, rng)
        elif kind == "flower":
            petals = max(1, int(6 * progress))
            for k in range(petals):
                ang = k * np.pi / 3 + t * anim
                px = cx + np.cos(ang) * s * 0.55
                py = cy + np.sin(ang) * s * 0.55
                self._stroke(img, _hand_circle(px, py, s * 0.28), color, rng)
            if progress > 0.5:
                self._stroke(img, _hand_circle(cx, cy, s * 0.2), color, rng)
        elif kind == "house":
            if progress > 0.2:
                base = np.array(
                    [
                        [cx - s, cy + s * 0.6],
                        [cx + s, cy + s * 0.6],
                        [cx + s, cy - s * 0.1],
                        [cx - s, cy - s * 0.1],
                        [cx - s, cy + s * 0.6],
                    ],
                    dtype=np.float32,
                )
                self._stroke(img, base[: max(2, int(len(base) * progress))], color, rng)
            if progress > 0.55:
                roof = np.array([[cx - s, cy - s * 0.1], [cx, cy - s], [cx + s, cy - s * 0.1]], dtype=np.float32)
                self._stroke(img, roof, color, rng)
        elif kind == "stick":
            if progress > 0.15:
                head = _hand_circle(cx, cy - s * 0.55, s * 0.22)
                self._stroke(img, head, color, rng)
            if progress > 0.35:
                body = np.array([[cx, cy - s * 0.3], [cx, cy + s * 0.35]], dtype=np.float32)
                self._stroke(img, body, color, rng)
            if progress > 0.55:
                arms = np.array([[cx - s * 0.45, cy], [cx + s * 0.45, cy]], dtype=np.float32)
                self._stroke(img, arms, color, rng)
            if progress > 0.75:
                leg1 = np.array([[cx, cy + s * 0.35], [cx - s * 0.35, cy + s * 0.85]], dtype=np.float32)
                leg2 = np.array([[cx, cy + s * 0.35], [cx + s * 0.35, cy + s * 0.85]], dtype=np.float32)
                self._stroke(img, leg1, color, rng)
                self._stroke(img, leg2, color, rng)
        elif kind == "heart":
            a = np.linspace(0, 2 * np.pi * progress, max(8, int(50 * progress)))
            x = cx + s * 0.08 * (16 * np.sin(a) ** 3)
            y = cy - s * 0.08 * (13 * np.cos(a) - 5 * np.cos(2 * a) - 2 * np.cos(3 * a) - np.cos(4 * a))
            self._stroke(img, np.column_stack([x, y]), color, rng)
        elif kind == "cloud":
            blobs = [(-0.4, 0.0, 0.35), (0.0, -0.15, 0.42), (0.4, 0.0, 0.35), (0.0, 0.15, 0.3)]
            for j, (ox, oy, rr) in enumerate(blobs[: max(1, int(len(blobs) * progress))]):
                self._stroke(img, _hand_circle(cx + ox * s, cy + oy * s, rr * s), color, rng)
        elif kind == "tree":
            if progress > 0.3:
                trunk = np.array([[cx, cy], [cx, cy + s]], dtype=np.float32)
                self._stroke(img, trunk, color, rng)
            if progress > 0.5:
                self._stroke(img, _hand_circle(cx, cy - s * 0.2, s * 0.55), color, rng)
        elif kind == "fish":
            if progress > 0.2:
                self._stroke(img, _hand_circle(cx - s * 0.2, cy, s * 0.5), color, rng)
            if progress > 0.6:
                tail = np.array([[cx + s * 0.3, cy], [cx + s, cy - s * 0.4], [cx + s, cy + s * 0.4], [cx + s * 0.3, cy]], dtype=np.float32)
                self._stroke(img, tail, color, rng)
        else:
            xs = np.linspace(cx - s, cx + s, max(3, int(9 * progress)))
            ys = cy + np.resize([-s * 0.35, s * 0.35], len(xs))
            self._stroke(img, np.column_stack([xs, ys]), color, rng)

    def _draw_step_hint(self, draw: ImageDraw.ImageDraw, seg: dict, local: float) -> None:
        steps = list(seg.get("steps") or [])
        if not steps:
            return
        idx = min(len(steps) - 1, int(local * len(steps)))
        hint = steps[idx]
        draw.rounded_rectangle(
            (int(self.width * 0.08), int(self.height * 0.14), int(self.width * 0.92), int(self.height * 0.20)),
            radius=10,
            fill=(255, 252, 240),
            outline=(100, 90, 70),
            width=2,
        )
        draw.text((self.width // 2, int(self.height * 0.17)), hint, font=self.font_sm, fill=(70, 60, 50), anchor="mm")

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        seg = self._segment_at(t)
        local = (t - float(seg["t0"])) / max(1e-6, float(seg["t1"]) - float(seg["t0"]))
        progress = float(np.clip(local * 1.15, 0.05, 1.0))

        img = self._paper()
        cx = self.width * 0.42
        cy = self.height * 0.42
        s = min(self.width, self.height) * 0.14
        kind = str(seg.get("doodle_kind", "star"))
        color = tuple(max(0, int(c * 0.75)) for c in self.palette.as_uint8((hash(kind) % 100) / 100.0 + t * 0.1))
        rng = np.random.default_rng(self.seed + int(seg.get("index", 0)) * 97 + 3)

        # Guide pencil circle (fades as drawing progresses)
        if progress < 0.85:
            guide = _hand_circle(cx, cy, s * 1.05)
            cv2.polylines(
                img,
                [guide.astype(np.int32)],
                True,
                (180, 175, 165),
                1,
                lineType=cv2.LINE_AA,
            )

        self._draw_doodle(img, kind, cx, cy, s, color, rng, t, anim, progress=progress)

        # Story mode: faint previous drawings
        if self.mode == "story" and int(seg.get("index", 0)) > 0:
            for prev in self.segments[: int(seg.get("index", 0))]:
                pk = str(prev.get("doodle_kind", "star"))
                pc = tuple(max(0, int(c * 0.55)) for c in self.palette.as_uint8(0.3))
                prng = np.random.default_rng(self.seed + int(prev.get("index", 0)) * 53)
                ox = self.width * (0.12 + 0.08 * int(prev.get("index", 0)))
                oy = self.height * (0.72 + 0.04 * int(prev.get("index", 0)))
                self._draw_doodle(img, pk, ox, oy, s * 0.35, pc, prng, t, anim * 0.5, progress=1.0)

        pil = Image.fromarray(img)
        draw = ImageDraw.Draw(pil)
        self._draw_step_hint(draw, seg, local)

        if self.show_captions:
            draw_title_banner(draw, self.width, self.height, self.lesson_title, self.font_sm)
            draw_learning_strip(
                draw,
                pil,
                seg,
                self.width,
                self.height,
                {"md": self.font_md, "sm": self.font_sm},
                show_word_image=self.show_word_images,
            )
            draw_progress_dots(draw, seg, self.segments, self.width, self.height, self.palette.as_uint8(0.45))
            if t > 0.92:
                draw_closing_banner(draw, self.width, self.height, self.closing, self.font_sm)

        return np.array(pil, dtype=np.uint8)
