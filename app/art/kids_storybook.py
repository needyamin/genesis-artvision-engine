"""Kids storybook engine — picture-book pages the engine paints itself."""

from __future__ import annotations

import numpy as np
from PIL import Image, ImageDraw

from app.art.base import ArtEngine, register_engine
from app.art.brief_layout import composite_segment_layers, paint_text_block
from app.art.editorial import segment_state
from app.art.education_ui import draw_title_banner, load_font, paint_text, paste_picture, segment_at
from app.art.kids_layout import kids_layout
from app.art.procedural_backgrounds import get_chrome_theme, paint_background
from app.art.storybook_content import build_storybook_lesson
from app.art.styles import style_chrome
from app.art.visual_variants import resolve_visual_variants
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
        self.variant = resolve_visual_variants(self.name, self.params)
        self.params.update(self.variant.to_params())
        self.layout = kids_layout(
            self.width,
            self.height,
            variant=self.variant.layout_variant,
        )
        theme = get_chrome_theme(self.name, self.variant.background_variant, self.palette)
        self.chrome = style_chrome(
            str(self.params.get("style") or "storybook"),
            dark=theme.dark,
            text=theme.text,
            muted=theme.muted_text,
            accent=theme.accent,
            card=theme.card,
            border=theme.border,
            short_side=min(self.width, self.height),
        )
        type_scale = float(self.chrome["type_scale"])
        self.font_lg = load_font(max(22, int(self.layout.hero_font * 0.42 * type_scale)))
        self.font_md = load_font(max(11, int(self.layout.md_font * type_scale)))
        self.font_sm = load_font(max(10, int(self.layout.sm_font * type_scale)))
        if bool(self.params.get("show_word_images", True)):
            for seg in self.segments:
                w = str(seg.get("word") or "")
                if w:
                    ensure_word_image(w)

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        t = frame_number / max(1, total_frames)
        seg = segment_at(self.segments, t)
        state = segment_state(seg, t, easing=str(self.params.get("easing") or "smooth"))
        page = int(seg.get("index") or 0) + 1
        total = max(1, len(self.segments))
        current = self._render_page(seg, page, total, state)
        outgoing = None
        if page > 1 and state["enter"] < 0.999:
            previous = self.segments[page - 2]
            outgoing = self._render_page(
                previous,
                page - 1,
                total,
                {"local": 1.0, "eased": 1.0, "enter": 1.0, "leave": 1.0 - state["enter"]},
            )
        img = composite_segment_layers(
            outgoing,
            current,
            enter=state["enter"],
            leave=1.0 - state["enter"],
            kind=str(seg.get("transition") or "page_turn"),
        )
        return np.array(img.convert("RGB"), dtype=np.uint8)

    def _render_page(
        self,
        seg: dict,
        page: int,
        total: int,
        state: dict[str, float],
    ) -> Image.Image:
        img = self._paper_page()
        draw = ImageDraw.Draw(img)
        title = str(self.lesson.get("title") or "Storybook")
        chrome = self.chrome
        draw_title_banner(
            draw,
            self.width,
            self.height,
            title,
            self.font_sm,
            layout=self.layout,
            count_label=f"{page}/{total}",
            fill=chrome["card_fill"][:3],
            outline=chrome["border"][:3],
            text_fill=chrome["text"],
            counter_fill=chrome["muted"],
            radius=int(chrome["card_radius"]),
        )
        headline = str(seg.get("headline") or seg.get("overlay_text") or "")
        body = str(seg.get("caption") or seg.get("body") or "")
        ly = self.layout
        paint_text(
            draw,
            (ly.stage.cx, ly.stage.y0 + int(ly.stage.h * 0.18)),
            headline,
            self.font_lg,
            chrome["text"],
            anchor="mm",
            max_width=ly.stage.w - 24,
        )
        if str(seg.get("word") or ""):
            bounce = int((1.0 - state["enter"]) * self.height * 0.025)
            paste_picture(img, seg, ly, bounce=bounce)
        if body:
            cap = ly.caption
            draw.rounded_rectangle(
                cap.xy,
                radius=max(8, int(chrome["card_radius"]) - 2),
                fill=chrome["card_fill"][:3],
                outline=chrome["border"][:3],
                width=int(chrome["stroke"]),
            )
            paint_text_block(
                draw,
                (cap.x0 + max(10, ly.gap * 2), cap.y0 + max(8, ly.gap)),
                body,
                self.font_md,
                chrome["muted"],
                max_width=cap.w - max(20, ly.gap * 4),
                max_height=cap.h - max(16, ly.gap * 2),
                spacing=max(3, ly.gap // 2),
            )
        return img

    def _paper_page(self) -> Image.Image:
        if self.variant.background_variant == "desk_stack":
            return self._classic_desk_page()
        return paint_background(
            self.name,
            self.width,
            self.height,
            self.seed,
            self.palette,
            variant=self.variant.background_variant,
        ).convert("RGBA")

    def _classic_desk_page(self) -> Image.Image:
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
        paper = Image.fromarray(page.astype(np.uint8)).convert("RGBA")
        desk = Image.new("RGBA", (w, h), (116, 82, 58, 255))
        draw = ImageDraw.Draw(desk, "RGBA")
        margin = int(min(w, h) * 0.04)
        for spread in range(4, 0, -1):
            offset = spread * max(1, margin // 10)
            alpha = 16 + spread * 9
            draw.rounded_rectangle(
                (margin + offset, margin + offset, w - margin + offset, h - margin + offset),
                radius=max(6, margin // 3),
                fill=(35, 22, 15, alpha),
            )
        sheet = paper.crop((margin, margin, w - margin, h - margin))
        desk.alpha_composite(sheet, (margin, margin))
        draw = ImageDraw.Draw(desk, "RGBA")
        draw.rounded_rectangle((margin, margin, w - margin, h - margin), radius=max(6, margin // 3), outline=(180, 140, 100, 230), width=3)
        for i in range(8):
            x = margin + 6 + i
            draw.line((x, margin + 4, x, h - margin - 4), fill=(160, 120, 90, 150))
        draw.line((w - margin - 2, margin + 8, w - margin - 2, h - margin - 8), fill=(255, 255, 255, 90), width=2)
        return desk
