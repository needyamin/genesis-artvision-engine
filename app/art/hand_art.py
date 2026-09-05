"""Hand-drawn educational art engine — smooth step-by-step draw-along lessons."""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw

from app.art.base import ArtEngine, register_engine
from app.art.education_anim import (
    ease_in_out_cubic,
    kids_breathe,
    partial_polyline,
    segment_local,
)
from app.art.edit_brain import kids_shot
from app.art.education_content import build_hand_art_lesson
from app.art.education_ui import (
    draw_kids_chrome,
    draw_stage_card,
    load_font,
    paste_picture,
    segment_at,
)
from app.art.kids_layout import kids_layout
from app.art.word_images import ensure_word_image


def _wobble_polyline(pts: np.ndarray, rng: np.random.Generator, amount: float = 2.0) -> np.ndarray:
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
    """Smooth hand-art draw-along with pencil animation and step-by-step lessons."""

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
        for seg in self.segments:
            seg["_total"] = len(self.segments)
        self.lesson_title = str(self.lesson.get("title") or "Draw Along")
        self.closing = str(self.lesson.get("closing") or "Great drawing!")
        self.show_captions = bool(self.params.get("show_captions", True))
        self.show_word_images = bool(self.params.get("show_word_images", True))
        self.easing = "smooth"
        self.camera_feel = "static"

        self.layout = kids_layout(self.width, self.height)
        self.font_md = load_font(self.layout.md_font)
        self.font_sm = load_font(self.layout.sm_font)
        self.font_xs = load_font(max(14, self.layout.sm_font - 2))

        self.stroke = max(1, int(self.params.get("stroke_width", 2)))
        self.sketchiness = float(self.params.get("sketchiness", 0.7))
        self.paper_grain = float(self.params.get("paper_grain", 0.35))
        self.confetti_seeds = self.rng.random(40).astype(np.float32)
        self.params["education_lesson"] = self.lesson
        self._paper_cache = self._make_paper()

        if self.show_word_images:
            for seg in self.segments:
                w = str(seg.get("word") or seg.get("motif") or "")
                if w:
                    ensure_word_image(w)

    def _segment_at(self, t: float) -> dict:
        return segment_at(self.segments, t)

    def _make_paper(self) -> np.ndarray:
        assert self.palette is not None and self.rng is not None
        base = np.array(self.palette.as_uint8(0.05), dtype=np.float32)
        paper = np.full((self.height, self.width, 3), [236, 228, 210], dtype=np.float32)
        paper = paper * 0.75 + base * 0.25
        if self.paper_grain > 0.05:
            grain = self.rng.normal(0, 6 * self.paper_grain, (self.height, self.width, 1)).astype(np.float32)
            paper = paper + grain
        return np.clip(paper, 0, 255).astype(np.uint8)

    def _paper(self) -> np.ndarray:
        return self._paper_cache.copy()

    def _stroke(
        self, img: np.ndarray, pts: np.ndarray, color: tuple[int, int, int],
        rng: np.random.Generator, progress: float = 1.0,
    ) -> None:
        if len(pts) < 2:
            return
        pts = partial_polyline(pts.astype(np.float32), progress)
        if len(pts) < 2:
            return
        wob = _wobble_polyline(pts, rng, amount=1.0 + self.sketchiness * 2.0)
        arr = wob.astype(np.int32)
        cv2.polylines(img, [arr], False, color, self.stroke + 1, lineType=cv2.LINE_AA)
        faint = tuple(min(255, c + 40) for c in color)
        cv2.polylines(img, [arr], False, faint, max(1, self.stroke), lineType=cv2.LINE_AA)

    def _pencil_tip(self, img: np.ndarray, x: float, y: float, color: tuple[int, int, int]) -> None:
        """Animated pencil cursor at drawing tip."""
        px, py = int(x), int(y)
        cv2.circle(img, (px, py), 5, (60, 50, 40), -1, lineType=cv2.LINE_AA)
        cv2.circle(img, (px, py), 3, color, -1, lineType=cv2.LINE_AA)
        cv2.line(img, (px, py), (px + 12, py + 18), (180, 160, 120), 2, lineType=cv2.LINE_AA)

    def _collect_strokes(self, kind: str, cx: float, cy: float, s: float, t: float, anim: float) -> list[np.ndarray]:
        """Return list of stroke polylines for a doodle kind."""
        kind = kind.lower()
        strokes: list[np.ndarray] = []
        if kind == "scribble":
            ang = np.linspace(0, 4 * np.pi, 24) + t * anim
            rad = np.linspace(s * 0.2, s, 24)
            strokes.append(np.column_stack([cx + np.cos(ang) * rad, cy + np.sin(ang) * rad]))
        elif kind == "spiral":
            ang = np.linspace(0, 5 * np.pi, 60) + t * anim * 2
            rad = np.linspace(2, s, 60)
            strokes.append(np.column_stack([cx + np.cos(ang) * rad, cy + np.sin(ang) * rad]))
        elif kind == "star":
            strokes.append(_hand_star(cx, cy, s))
        elif kind == "sun":
            strokes.append(_hand_circle(cx, cy, s * 0.45))
            for a in range(0, 360, 30):
                rad = np.radians(a + t * 40)
                strokes.append(np.array([
                    [cx + np.cos(rad) * s * 0.55, cy + np.sin(rad) * s * 0.55],
                    [cx + np.cos(rad) * s, cy + np.sin(rad) * s],
                ]))
        elif kind == "flower":
            for k in range(6):
                ang = k * np.pi / 3 + t * anim
                px = cx + np.cos(ang) * s * 0.55
                py = cy + np.sin(ang) * s * 0.55
                strokes.append(_hand_circle(px, py, s * 0.28))
            strokes.append(_hand_circle(cx, cy, s * 0.2))
        elif kind == "house":
            strokes.append(np.array([
                [cx - s, cy + s * 0.6], [cx + s, cy + s * 0.6],
                [cx + s, cy - s * 0.1], [cx - s, cy - s * 0.1], [cx - s, cy + s * 0.6],
            ], dtype=np.float32))
            strokes.append(np.array([[cx - s, cy - s * 0.1], [cx, cy - s], [cx + s, cy - s * 0.1]], dtype=np.float32))
        elif kind == "stick":
            strokes.append(_hand_circle(cx, cy - s * 0.55, s * 0.22))
            strokes.append(np.array([[cx, cy - s * 0.3], [cx, cy + s * 0.35]], dtype=np.float32))
            strokes.append(np.array([[cx - s * 0.45, cy], [cx + s * 0.45, cy]], dtype=np.float32))
            strokes.append(np.array([[cx, cy + s * 0.35], [cx - s * 0.35, cy + s * 0.85]], dtype=np.float32))
            strokes.append(np.array([[cx, cy + s * 0.35], [cx + s * 0.35, cy + s * 0.85]], dtype=np.float32))
        elif kind == "heart":
            a = np.linspace(0, 2 * np.pi, 50)
            x = cx + s * 0.08 * (16 * np.sin(a) ** 3)
            y = cy - s * 0.08 * (13 * np.cos(a) - 5 * np.cos(2 * a) - 2 * np.cos(3 * a) - np.cos(4 * a))
            strokes.append(np.column_stack([x, y]))
        elif kind == "cloud":
            for ox, oy, rr in ((-0.4, 0.0, 0.35), (0.0, -0.15, 0.42), (0.4, 0.0, 0.35), (0.0, 0.15, 0.3)):
                strokes.append(_hand_circle(cx + ox * s, cy + oy * s, rr * s))
        elif kind == "tree":
            strokes.append(np.array([[cx, cy], [cx, cy + s]], dtype=np.float32))
            strokes.append(_hand_circle(cx, cy - s * 0.2, s * 0.55))
        elif kind == "fish":
            strokes.append(_hand_circle(cx - s * 0.2, cy, s * 0.5))
            strokes.append(np.array([
                [cx + s * 0.3, cy], [cx + s, cy - s * 0.4], [cx + s, cy + s * 0.4], [cx + s * 0.3, cy],
            ], dtype=np.float32))
        else:
            xs = np.linspace(cx - s, cx + s, 9)
            ys = cy + np.resize([-s * 0.35, s * 0.35], 9)
            strokes.append(np.column_stack([xs, ys]))
        return strokes

    def _draw_doodle_smooth(
        self, img: np.ndarray, kind: str, cx: float, cy: float, s: float,
        color: tuple[int, int, int], rng: np.random.Generator,
        t: float, anim: float, progress: float,
    ) -> tuple[float, float] | None:
        """Draw doodle with smooth stroke-by-stroke progress. Returns pencil tip position."""
        strokes = self._collect_strokes(kind, cx, cy, s, t, anim)
        n = len(strokes)
        if n == 0:
            return None
        overall = progress * n
        tip: tuple[float, float] | None = None
        for i, pts in enumerate(strokes):
            stroke_prog = float(np.clip(overall - i, 0.0, 1.0))
            if stroke_prog <= 0:
                break
            self._stroke(img, pts, color, rng, progress=stroke_prog)
            partial = partial_polyline(pts.astype(np.float32), stroke_prog)
            if len(partial) >= 1:
                tip = (float(partial[-1][0]), float(partial[-1][1]))
        return tip

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        seg = self._segment_at(t)
        local = segment_local(t, seg)
        shot = kids_shot(local)
        progress = ease_in_out_cubic(min(1.0, local / 0.72))

        img = self._paper()
        stage = self.layout.stage
        cx = float(stage.cx)
        cy = float(stage.cy + (0 if shot.hold_still else kids_breathe(t, 2.0)))
        s = min(stage.w, stage.h) * 0.28
        kind = str(seg.get("doodle_kind", "star"))
        color = tuple(max(0, int(c * 0.75)) for c in self.palette.as_uint8((hash(kind) % 100) / 100.0 + t * 0.08))
        rng = np.random.default_rng(self.seed + int(seg.get("index", 0)) * 97 + 3)

        if progress < 0.9:
            guide = _hand_circle(cx, cy, s * 1.08)
            fade = int(180 * (1.0 - progress))
            cv2.polylines(img, [guide.astype(np.int32)], True, (fade, fade - 10, fade - 15), 1, lineType=cv2.LINE_AA)

        tip = self._draw_doodle_smooth(img, kind, cx, cy, s, color, rng, t, anim, progress)
        if tip and progress < 0.98:
            self._pencil_tip(img, tip[0], tip[1], color)

        if self.mode == "story" and int(seg.get("index", 0)) > 0:
            pic = self.layout.picture
            for prev in self.segments[: int(seg.get("index", 0))]:
                pk = str(prev.get("doodle_kind", "star"))
                pc = tuple(max(0, int(c * 0.5)) for c in self.palette.as_uint8(0.3))
                prng = np.random.default_rng(self.seed + int(prev.get("index", 0)) * 53)
                idx = int(prev.get("index", 0))
                ox = pic.x0 + pic.w * (0.22 + 0.18 * (idx % 3))
                oy = pic.y0 + pic.h * (0.28 + 0.22 * (idx // 3))
                self._draw_doodle_smooth(img, pk, ox, oy, s * 0.28, pc, prng, t, anim * 0.4, 1.0)

        pil = Image.fromarray(img)
        draw = ImageDraw.Draw(pil)
        draw_stage_card(draw, self.layout, fill=None)
        hud = dict(seg)
        steps = list(seg.get("steps") or [])
        if steps:
            idx = min(len(steps) - 1, int(ease_in_out_cubic(local) * len(steps)))
            hud["overlay_text"] = str(steps[idx])
            hud["line"] = str(steps[idx])

        if self.show_captions:
            if (
                self.show_word_images
                and self.mode != "story"
                and (seg.get("image_path") or seg.get("word"))
                and shot.picture_scale > 0.12
            ):
                paste_picture(pil, seg, self.layout)
            draw_kids_chrome(
                draw, pil, self.layout,
                title=self.lesson_title,
                seg=hud,
                segments=self.segments,
                fonts={"md": self.font_md, "sm": self.font_sm},
                t=t,
                closing=self.closing,
                accent=self.palette.as_uint8(0.45),
                confetti_seeds=self.confetti_seeds,
                caption_alpha=shot.caption_alpha,
                celebrate=shot.celebrate,
            )

        arr = np.array(pil, dtype=np.uint8)
        blur = cv2.GaussianBlur(arr, (0, 0), sigmaX=0.6)
        return cv2.addWeighted(arr, 0.94, blur, 0.06, 0)
