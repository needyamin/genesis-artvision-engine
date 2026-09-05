"""Advanced children's educational alphabet videos — random lessons + cartoon art."""

from __future__ import annotations

import cv2
import numpy as np
from PIL import Image, ImageDraw

from app.art.base import ArtEngine, register_engine
from app.art.education_anim import (
    draw_glow_ring,
    kids_breathe,
    kids_pop,
    segment_local,
)
from app.art.edit_brain import kids_shot
from app.art.education_content import build_education_lesson
from app.art.education_ui import draw_kids_chrome, draw_picture_card, draw_stage_card, paste_picture
from app.art.fonts import load_font, paint_text
from app.art.kids_layout import chart_cell_center, kids_layout
from app.art.word_images import ensure_word_image


def _blend(
    c: tuple[int, int, int],
    factor: float,
    toward: tuple[int, int, int] = (255, 255, 255),
) -> tuple[int, int, int]:
    return tuple(int(np.clip(a * (1 - factor) + b * factor, 0, 255)) for a, b in zip(c, toward))


def _draw_bubble_letter(
    draw: ImageDraw.ImageDraw,
    text: str,
    xy: tuple[int, int],
    font,
    fill: tuple[int, int, int],
    *,
    outline: tuple[int, int, int] = (35, 45, 70),
    outline_w: int = 6,
) -> None:
    x, y = xy
    ow = max(2, int(outline_w))
    for dx, dy in (
        (-ow, 0),
        (ow, 0),
        (0, -ow),
        (0, ow),
        (-ow, -ow),
        (-ow, ow),
        (ow, -ow),
        (ow, ow),
    ):
        paint_text(draw, (x + dx, y + dy), text, font, outline, anchor="mm")
    paint_text(draw, (x, y), text, font, fill, anchor="mm")


def _draw_motif(
    draw: ImageDraw.ImageDraw,
    kind: str,
    cx: int,
    cy: int,
    s: int,
    color: tuple[int, int, int],
    t: float = 0.0,
) -> None:
    s = max(10, int(s * (1.0 + 0.08 * np.sin(t * np.pi * 4))))
    dark = _blend(color, 0.0, (20, 20, 30))
    light = _blend(color, 0.45)
    w = max(2, s // 10)
    kind = kind.upper()

    if kind in {"APPLE", "ORANGE", "BALL", "EGG", "GRAPE", "ICE", "JAR", "YARN", "LEMON"}:
        draw.ellipse((cx - s, cy - s, cx + s, cy + s), fill=color, outline=dark, width=w)
        draw.ellipse((cx - s // 2, cy - s // 2, cx - s // 8, cy - s // 8), fill=light)
        if kind == "APPLE":
            draw.line((cx, cy - s, cx, cy - int(s * 1.35)), fill=(80, 50, 20), width=w)
            draw.ellipse((cx, cy - int(s * 1.4), cx + s // 2, cy - s), fill=(60, 160, 70), outline=dark)
    elif kind in {"SUN", "MOON", "STAR", "YELLOW"}:
        draw.ellipse((cx - s, cy - s, cx + s, cy + s), fill=color, outline=dark, width=w)
        for a in range(0, 360, 30):
            rad = np.radians(a + t * 40)
            draw.line(
                (
                    cx + int(np.cos(rad) * s * 1.15),
                    cy + int(np.sin(rad) * s * 1.15),
                    cx + int(np.cos(rad) * s * 1.55),
                    cy + int(np.sin(rad) * s * 1.55),
                ),
                fill=color,
                width=w,
            )
    elif kind in {"HOUSE", "VAN", "BOX", "BUS"}:
        draw.rectangle((cx - s, cy - s // 3, cx + s, cy + s), fill=color, outline=dark, width=w)
        draw.polygon([(cx - s, cy - s // 3), (cx, cy - s), (cx + s, cy - s // 3)], fill=light, outline=dark)
    elif kind in {"TREE", "LEAF", "NEST", "FLOWER"}:
        draw.rectangle((cx - s // 8, cy, cx + s // 8, cy + s), fill=(120, 80, 40), outline=dark)
        draw.ellipse((cx - s, cy - s, cx + s, cy + s // 4), fill=color, outline=dark, width=w)
    elif kind in {"FISH", "SNAKE"}:
        draw.ellipse((cx - s, cy - s // 2, cx + s // 2, cy + s // 2), fill=color, outline=dark, width=w)
        draw.polygon([(cx + s // 2, cy), (cx + s, cy - s // 2), (cx + s, cy + s // 2)], fill=light, outline=dark)
    elif kind in {"KITE", "QUEEN", "CROWN"}:
        pts = []
        for i in range(10):
            ang = -np.pi / 2 + i * np.pi / 5 + t
            r = s if i % 2 == 0 else s * 0.45
            pts.append((cx + np.cos(ang) * r, cy + np.sin(ang) * r))
        draw.polygon(pts, fill=color, outline=dark)
    elif kind == "RAINBOW":
        bands = [(255, 80, 80), (255, 160, 60), (255, 220, 80), (80, 200, 100), (80, 140, 255)]
        for i, band in enumerate(bands):
            r = s - i * max(2, s // 8)
            draw.arc((cx - r, cy - r, cx + r, cy + r), 200, 340, fill=band, width=max(2, s // 10))
    elif kind in {"CAT", "DOG", "LION", "TIGER", "WOLF", "FOX", "YAK", "GOAT", "HORSE", "PIG", "MOUSE", "MONKEY", "RABBIT", "BIRD", "OWL", "DUCK", "FROG", "ALLIGATOR", "ELEPHANT", "KANGAROO", "ZEBRA"}:
        draw.ellipse((cx - s, cy - s // 2, cx + s, cy + s // 2), fill=color, outline=dark, width=w)
        draw.ellipse((cx - s // 3, cy - s // 8, cx - s // 8, cy + s // 8), fill=dark)
        draw.ellipse((cx + s // 8, cy - s // 8, cx + s // 3, cy + s // 8), fill=dark)
        if kind in {"CAT", "TIGER", "LION"}:
            draw.polygon([(cx - s // 2, cy - s // 2), (cx - s // 4, cy - s), (cx, cy - s // 3)], fill=color, outline=dark)
            draw.polygon([(cx + s // 2, cy - s // 2), (cx + s // 4, cy - s), (cx, cy - s // 3)], fill=color, outline=dark)
    elif kind == "UMBRELLA":
        draw.pieslice((cx - s, cy - s, cx + s, cy + s // 3), 180, 360, fill=color, outline=dark)
        draw.line((cx, cy, cx, cy + s), fill=dark, width=w)
    elif kind == "PENCIL":
        draw.rectangle((cx - s // 4, cy - s, cx + s // 4, cy + s // 2), fill=color, outline=dark, width=w)
        draw.polygon(
            [(cx - s // 4, cy + s // 2), (cx, cy + s), (cx + s // 4, cy + s // 2)],
            fill=(240, 210, 160),
            outline=dark,
        )
    elif kind in {"WAVE", "WATER", "OCEAN"}:
        pts = []
        for i in range(12):
            xx = cx - s + i * (2 * s / 11)
            yy = cy + np.sin(i * 0.8 + t * 6) * (s // 3)
            pts.append((xx, yy))
        draw.line(pts, fill=color, width=max(3, w + 1))
    else:
        draw.ellipse((cx - s // 2, cy - s // 2, cx + s // 2, cy + s // 2), fill=color, outline=dark, width=w)


@register_engine
class AlphabetCartoonEngine(ArtEngine):
    """Educational kids alphabet engine with random lessons, words, and facts."""

    name = "alphabet_cartoon"
    description = "Educational ABC videos — random letters, words, facts, and phonics"

    def _on_setup(self) -> None:
        assert self.rng is not None
        duration = float(self.params.get("_duration", 30.0))
        if isinstance(self.params.get("education_lesson"), dict):
            self.lesson = self.params["education_lesson"]
        else:
            self.lesson = build_education_lesson(self.seed, duration, params=self.params)
        # Lesson plan owns the on-screen mode. Randomizer "spell" must not
        # draw spelling blanks over a math or letter lesson.
        vis = str(self.lesson.get("visual_mode") or "lesson")
        self.mode = vis if vis in {"chart", "focus", "parade", "lesson", "spell"} else "lesson"

        self.letters = list(self.lesson["letters"])
        self.spell_word = str(self.lesson.get("spell_word") or "")
        self.segments = list(self.lesson["segments"])
        for seg in self.segments:
            seg["_total"] = len(self.segments)
        self.lesson_title = str(self.lesson.get("title") or "Let's Learn!")
        self.closing = str(self.lesson.get("closing") or "Great job!")

        self.layout = kids_layout(self.width, self.height)
        self.cols = max(4, min(int(self.params.get("columns", 7)), 9))
        self.rows = max(1, int(np.ceil(len(self.letters) / self.cols)))
        n = max(1, len(self.letters))
        self.phases = self.rng.random(n).astype(np.float32)
        self.hues = self.rng.random(n).astype(np.float32)
        self.bounce = float(min(0.4, max(0.15, self.params.get("bounce", 0.28))))
        self.wobble = float(min(0.18, max(0.0, self.params.get("wobble", 0.08))))
        self.easing = "smooth"
        self.camera_feel = "static"
        self.show_motifs = bool(self.params.get("show_motifs", True))
        self.show_lowercase = bool(self.params.get("show_lowercase", True))
        bg = str(self.params.get("background") or "pastel")
        self.bg_style = bg if bg in {"notebook", "sky", "classroom", "pastel"} else "pastel"
        self.sparkle = float(min(0.2, max(0.0, self.params.get("sparkle", 0.12))))
        self.pop_in = True

        cell = min(self.layout.stage.w / self.cols, self.layout.stage.h / max(1, self.rows))
        self.font_size = max(28, int(cell * 0.52))
        self.font = load_font(self.font_size)
        self.font_lg = load_font(self.layout.hero_font)
        self.font_md = load_font(self.layout.md_font)
        self.font_sm = load_font(self.layout.sm_font)
        self.outline_w = max(4, self.layout.hero_font // 14)

        sp = int(6 + 14 * self.sparkle)
        self.sparks_x = self.rng.random(sp).astype(np.float32)
        self.sparks_y = self.rng.random(sp).astype(np.float32)
        self.sparks_r = self.rng.uniform(1.5, 4.5, sp).astype(np.float32)
        self.sparks_ph = self.rng.random(sp).astype(np.float32)
        self.confetti_seeds = self.rng.random(40).astype(np.float32)

        # Expose lesson for audio pipeline (copied into params by renderer caller if needed)
        self.params["education_lesson"] = self.lesson
        self.show_word_images = bool(self.params.get("show_word_images", True))
        # Ensure offline illustrations exist for this lesson's words (no internet)
        if self.show_word_images:
            for seg in self.segments:
                ensure_word_image(str(seg.get("word", "FUN")))
                ensure_word_image(str(seg.get("motif", seg.get("word", "STAR"))))

    def _segment_at(self, t: float) -> dict:
        for seg in self.segments:
            if float(seg["t0"]) <= t < float(seg["t1"]):
                return seg
        return self.segments[-1] if self.segments else {
            "letter": "A",
            "word": "APPLE",
            "motif": "APPLE",
            "fact": "Learning is fun!",
            "phonics": "A says /a/",
            "tip": "Say it out loud!",
            "line": "A is for APPLE",
            "index": 0,
            "t0": 0.0,
            "t1": 1.0,
        }

    def _pop_scale(self, local_t: float) -> float:
        if not self.pop_in:
            return 1.0
        return kids_pop(local_t)

    def _make_background(self, t: float) -> Image.Image:
        assert self.palette is not None
        if self.bg_style == "notebook":
            img = Image.new("RGB", (self.width, self.height), (250, 247, 235))
            draw = ImageDraw.Draw(img)
            step = max(28, self.height // 24)
            for y in range(int(self.height * 0.12), self.height, step):
                draw.line((40, y, self.width - 40, y), fill=(180, 210, 230), width=2)
            draw.line((int(self.width * 0.08), 0, int(self.width * 0.08), self.height), fill=(240, 140, 140), width=3)
        elif self.bg_style == "sky":
            top = np.array(self.palette.as_uint8(0.55), dtype=np.float32)
            bot = np.array((255, 230, 180), dtype=np.float32)
            arr = np.zeros((self.height, self.width, 3), dtype=np.float32)
            for y in range(self.height):
                f = y / max(1, self.height - 1)
                arr[y] = top * (1 - f) + bot * f
            img = Image.fromarray(arr.astype(np.uint8))
            draw = ImageDraw.Draw(img)
            for i in range(3):
                cx = int(((i * 0.28 + t * 0.02) % 1.15) * self.width)
                cy = int(self.height * (0.14 + 0.07 * (i % 2)))
                for ox, oy, r in ((-30, 0, 36), (0, -12, 42), (34, 0, 34)):
                    draw.ellipse((cx + ox - r, cy + oy - r, cx + ox + r, cy + oy + r), fill=(255, 255, 255))
        elif self.bg_style == "classroom":
            img = Image.new("RGB", (self.width, self.height), (62, 110, 78))
            draw = ImageDraw.Draw(img)
            m = int(min(self.width, self.height) * 0.04)
            draw.rectangle((m, m, self.width - m, self.height - m), outline=(230, 230, 210), width=4)
            draw.rectangle((0, int(self.height * 0.88), self.width, self.height), fill=(140, 90, 50))
        else:
            arr = np.full((self.height, self.width, 3), 240, dtype=np.float32)
            yy, xx = np.ogrid[: self.height, : self.width]
            for i in range(3):
                c = np.array(self.palette.as_uint8((i * 0.22) % 1.0), dtype=np.float32)
                cx = (0.28 + 0.22 * i) * self.width
                cy = (0.28 + 0.18 * (i % 2)) * self.height
                dist = ((xx - cx) ** 2 + (yy - cy) ** 2) / (min(self.width, self.height) ** 2)
                mask = np.exp(-dist * 5)[..., None]
                arr = arr * (1 - 0.22 * mask) + c * (0.22 * mask)
            img = Image.fromarray(np.clip(arr, 0, 255).astype(np.uint8))
            draw = ImageDraw.Draw(img)

        if self.sparkle > 0.1:
            for i in range(len(self.sparks_x)):
                tw = 0.45 + 0.55 * abs(np.sin((t + self.sparks_ph[i]) * np.pi * 1.4))
                if tw < 0.4:
                    continue
                x = int(self.sparks_x[i] * self.width)
                y = int(self.sparks_y[i] * self.height * 0.9)
                r = int(self.sparks_r[i] * tw)
                col = self.palette.as_uint8(float((self.sparks_ph[i] + t) % 1.0))
                draw.ellipse((x - r, y - r, x + r, y + r), fill=col)
        return img

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t = frame_number / max(1, total_frames)
        anim = float(self.params.get("animation_speed", 1.0))
        img = self._make_background(t)
        draw = ImageDraw.Draw(img)
        seg = self._segment_at(t)

        if self.mode == "parade":
            self._draw_parade(draw, img, t, anim)
        elif self.mode in {"focus", "lesson"}:
            self._draw_lesson(draw, img, t, anim, seg)
            draw = ImageDraw.Draw(img)
        elif self.mode == "spell":
            self._draw_spell(draw, img, t, anim, seg)
            draw = ImageDraw.Draw(img)
        else:
            self._draw_chart(draw, img, t, anim, seg)
            draw = ImageDraw.Draw(img)

        self._draw_hud(draw, img, t, seg)

        arr = np.array(img, dtype=np.uint8, copy=True)
        blur = cv2.GaussianBlur(arr, (0, 0), sigmaX=0.4)
        return cv2.addWeighted(arr, 0.97, blur, 0.03, 0)

    def _draw_hud(self, draw: ImageDraw.ImageDraw, img: Image.Image, t: float, seg: dict) -> None:
        hud = dict(seg)
        shot = kids_shot(segment_local(t, seg))
        if 0.6 < shot.local < 0.85 and seg.get("quiz"):
            hud["caption"] = str(seg["quiz"])
        draw_kids_chrome(
            draw,
            img,
            self.layout,
            title=self.lesson_title,
            seg=hud,
            segments=self.segments,
            fonts={"md": self.font_md, "sm": self.font_sm},
            t=t,
            closing=self.closing,
            accent=self.palette.as_uint8(0.4) if self.palette is not None else (80, 120, 180),
            confetti_seeds=self.confetti_seeds,
            caption_alpha=shot.caption_alpha,
            celebrate=shot.celebrate,
        )

    def _paste_picture(self, draw: ImageDraw.ImageDraw, img: Image.Image, seg: dict, t: float, scale: float = 1.0) -> None:
        shot = kids_shot(segment_local(t, seg))
        pic = shot.picture_scale
        if pic < 0.08:
            return
        bounce = 0 if shot.hold_still else int(kids_breathe(t, 3.0) * pic)
        if self.show_word_images:
            paste_picture(img, seg, self.layout, bounce=bounce)
            return
        if self.show_motifs:
            draw_picture_card(draw, self.layout)
            color = self.palette.as_uint8(0.4) if self.palette is not None else (80, 140, 200)
            _draw_motif(
                draw,
                str(seg.get("motif") or seg.get("word") or "STAR"),
                self.layout.picture.cx,
                self.layout.picture.cy + bounce,
                max(18, int(min(self.layout.picture.w, self.layout.picture.h) * 0.28 * pic)),
                color,
                t,
            )

    def _cell_center(self, i: int) -> tuple[int, int]:
        return chart_cell_center(self.layout, i, len(self.letters), self.cols)

    def _draw_chart(self, draw: ImageDraw.ImageDraw, img: Image.Image, t: float, anim: float, seg: dict) -> None:
        assert self.palette is not None
        draw_stage_card(draw, self.layout)
        shot = kids_shot(segment_local(t, seg))
        n = len(self.letters)
        active = int(seg.get("index", 0))
        for i, letter in enumerate(self.letters):
            reveal = (t * 1.2) - (i / max(1, n)) * 0.85
            scale = self._pop_scale(float(np.clip(reveal, 0, 1)))
            if scale < 0.08:
                continue
            cx, cy = self._cell_center(i)
            amp = self.bounce * self.font_size * 0.04
            bounce = 0.0
            if i == active and not shot.hold_still:
                bounce = kids_breathe(t, amp)
            x, y = int(cx), int(cy + bounce)
            color = self.palette.as_uint8(float(self.hues[i % len(self.hues)]))
            if i == active:
                draw.ellipse((x - self.font_size, y - self.font_size, x + self.font_size, y + self.font_size), outline=color, width=4)
            ow = max(3, int(self.outline_w * scale))
            _draw_bubble_letter(draw, letter, (x, y), self.font, color, outline_w=ow)
            if self.show_lowercase and letter.isalpha():
                paint_text(
                    draw,
                    (x + self.font_size // 2, y + self.font_size // 3),
                    letter.lower(),
                    self.font_sm,
                    _blend(color, 0.2, (30, 40, 60)),
                    anchor="mm",
                )

        self._paste_picture(draw, img, seg, t)

    def _draw_lesson(self, draw: ImageDraw.ImageDraw, img: Image.Image, t: float, anim: float, seg: dict) -> None:
        del anim
        assert self.palette is not None
        letter = str(seg.get("letter", "A"))
        shot = kids_shot(segment_local(t, seg))
        color = self.palette.as_uint8((hash(letter) % 100) / 100.0)
        x, y = self.layout.letter_xy
        bounce = int(shot.bounce)

        draw_stage_card(draw, self.layout)
        if shot.letter_scale < 0.08:
            return
        if seg.get("math_op"):
            eq = str(seg.get("overlay_text") or seg.get("line") or "")
            if eq:
                paint_text(
                    draw,
                    (self.layout.stage.cx, self.layout.stage.y0 + max(16, int(self.layout.stage.h * 0.14))),
                    eq,
                    self.font_md,
                    (40, 55, 90),
                    anchor="mm",
                    max_width=self.layout.stage.w - 28,
                )
            y = y + int(self.layout.stage.h * 0.05)
        glow_r = int(min(self.layout.stage.w, self.layout.stage.h) * 0.22 * shot.letter_scale)
        draw_glow_ring(draw, x, y + bounce, glow_r, color, t, layers=1)
        _draw_bubble_letter(draw, letter, (x, y + bounce), self.font_lg, color, outline_w=max(6, self.outline_w))
        self._paste_picture(draw, img, seg, t, shot.picture_scale)

    def _draw_parade(self, draw: ImageDraw.ImageDraw, img: Image.Image, t: float, anim: float) -> None:
        del anim
        assert self.palette is not None
        n = len(self.letters)
        stage = self.layout.stage
        draw_stage_card(draw, self.layout)
        gy = stage.y1 - max(10, stage.h // 12)
        draw.line((stage.x0 + 16, gy, stage.x1 - 16, gy), fill=(120, 160, 100), width=6)
        for i, letter in enumerate(self.letters):
            progress = (t * 0.09 + i / max(1, n)) % 1.0
            x = int(stage.x0 + progress * stage.w)
            bounce = abs(np.sin(progress * np.pi)) * 5 * self.bounce
            y = int(stage.cy - bounce)
            color = self.palette.as_uint8(float(self.hues[i % len(self.hues)]))
            _draw_bubble_letter(draw, letter, (x, y), self.font, color, outline_w=max(3, self.outline_w // 2))
        self._paste_picture(draw, img, self._segment_at(t), t)

    def _draw_spell(self, draw: ImageDraw.ImageDraw, img: Image.Image, t: float, anim: float, seg: dict) -> None:
        del anim
        assert self.palette is not None
        word = str(self.spell_word or seg.get("spell_word") or "").upper()
        if not word.isalpha():
            word = "".join(ch for ch in word if ch.isalpha()) or "SUN"
        letters = list(word)
        n = max(1, len(letters))
        active = min(n - 1, max(0, int(seg.get("index", 0))))
        local = segment_local(t, seg)
        shot = kids_shot(local)
        pop = shot.letter_scale

        stage = self.layout.stage
        draw_stage_card(draw, self.layout)
        slot_w = int(stage.w * 0.82 / n)
        start_x = stage.cx - (slot_w * n) / 2
        cy = stage.cy
        slot_font = load_font(max(32, int(min(slot_w * 0.55, stage.h * 0.40))))
        active_font = load_font(max(36, int(min(slot_w * 0.62, stage.h * 0.48))))
        baseline = cy + int(min(slot_w, stage.h) * 0.28)

        for i, letter in enumerate(letters):
            x = int(start_x + (i + 0.5) * slot_w)
            y = cy
            color = self.palette.as_uint8(float(self.hues[i % len(self.hues)]))
            draw.line(
                (x - int(slot_w * 0.28), baseline, x + int(slot_w * 0.28), baseline),
                fill=(170, 185, 205),
                width=4,
            )
            if i > active:
                paint_text(draw, (x, y), "•", self.font_md, (200, 208, 218), anchor="mm")
                continue
            if i == active:
                draw_glow_ring(draw, x, y, int(slot_w * 0.34), color, t, layers=1)
                font = active_font
                outline = max(4, int(self.outline_w * 0.9))
            else:
                font = slot_font
                outline = max(3, int(self.outline_w * 0.7))
            _draw_bubble_letter(draw, letter, (x, y), font, color, outline_w=outline)

        pic_seg = dict(seg)
        pic_seg["word"] = word
        pic_seg["motif"] = word
        self._paste_picture(draw, img, pic_seg, t, pop)
