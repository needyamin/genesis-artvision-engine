"""Kids storybook engine — picture-book pages the engine paints itself."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from app.art.base import ArtEngine, register_engine
from app.art.education_ui import draw_title_banner, load_font, paint_text, paste_picture, segment_at
from app.art.kids_layout import kids_layout
from app.art.storybook_content import build_storybook_lesson
from app.art.word_images import ensure_word_image


@register_engine
class KidsStorybookEngine(ArtEngine):
    name = "kids_storybook"
    description = "Kids picture-book story pages"
    parallel_frames = True

    def _on_setup(self) -> None:
        assert self.rng is not None
        duration = float(self.params.get("_duration", 30.0))
        if isinstance(self.params.get("education_lesson"), dict):
            self.lesson = self.params["education_lesson"]
        else:
            self.lesson = build_storybook_lesson(self.seed, duration, params=self.params)
        self.segments = list(self.lesson.get("segments") or [])
        self.params["education_lesson"] = self.lesson
        self.layout = kids_layout(self.width, self.height)
        self.font_lg = load_font(max(22, int(self.layout.hero_font * 0.42)))
        self.font_md = load_font(self.layout.md_font)
        self.font_sm = load_font(self.layout.sm_font)
        if bool(self.params.get("show_word_images", True)):
            for seg in self.segments:
                w = str(seg.get("word") or "")
                if w:
                    ensure_word_image(w)

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        t = frame_number / max(1, total_frames)
        seg = segment_at(self.segments, t)
        img = self._paper_page()
        draw = ImageDraw.Draw(img)
        title = str(self.lesson.get("title") or "Storybook")
        page = int(seg.get("index") or 0) + 1
        total = max(1, len(self.segments))
        draw_title_banner(
            draw,
            self.width,
            self.height,
            title,
            self.font_sm,
            layout=self.layout,
            count_label=f"{page}/{total}",
        )
        headline = str(seg.get("headline") or seg.get("overlay_text") or "")
        body = str(seg.get("caption") or seg.get("body") or "")
        ly = self.layout
        paint_text(
            draw,
            (ly.stage.cx, ly.stage.y0 + int(ly.stage.h * 0.18)),
            headline[:42],
            self.font_lg,
            (70, 45, 30),
            anchor="mm",
            max_width=ly.stage.w - 24,
        )
        if str(seg.get("word") or ""):
            paste_picture(img, seg, ly)
        if body:
            cap = ly.caption
            draw.rounded_rectangle(cap.xy, radius=14, fill=(255, 248, 236), outline=(180, 140, 100), width=2)
            paint_text(
                draw,
                (cap.cx, cap.cy),
                body[:72],
                self.font_md,
                (60, 50, 40),
                anchor="mm",
                max_width=cap.w - 20,
            )
        return np.array(img.convert("RGB"), dtype=np.uint8)

    def _paper_page(self) -> Image.Image:
        w, h = self.width, self.height
        cream = np.array((242, 228, 204), dtype=np.float32)
        if self.palette is not None and self.palette.colors:
            p0 = np.array(self.palette.as_uint8(0.15), dtype=np.float32)
            warmth = float(self.params.get("paper_warmth", 0.55))
            cream = cream * (1.0 - 0.5 * warmth) + p0 * (0.5 * warmth)
        yy = np.linspace(0, 1, h, dtype=np.float32)[:, None, None]
        page = cream * (1.0 - 0.06 * yy)
        page = np.broadcast_to(page, (h, w, 3)).copy()
        rng = np.random.default_rng(self.seed + 3)
        grain = rng.random((h, w, 1)).astype(np.float32) * 8.0 - 4.0
        page = np.clip(page + grain, 0, 255)
        img = Image.fromarray(page.astype(np.uint8))
        draw = ImageDraw.Draw(img)
        margin = int(min(w, h) * 0.04)
        draw.rectangle((margin, margin, w - margin, h - margin), outline=(180, 140, 100), width=3)
        for i in range(8):
            x = margin + 6 + i
            draw.line((x, margin + 4, x, h - margin - 4), fill=(160, 120, 90))
        return img
