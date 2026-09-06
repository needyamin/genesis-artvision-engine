"""Stable kids-video layout. Every HUD piece has its own box and must not overlap."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Box:
    x0: int
    y0: int
    x1: int
    y1: int

    @property
    def w(self) -> int:
        return max(1, self.x1 - self.x0)

    @property
    def h(self) -> int:
        return max(1, self.y1 - self.y0)

    @property
    def cx(self) -> int:
        return (self.x0 + self.x1) // 2

    @property
    def cy(self) -> int:
        return (self.y0 + self.y1) // 2

    @property
    def xy(self) -> tuple[int, int]:
        return (self.x0, self.y0, self.x1, self.y1)

    def inset(self, px: int) -> "Box":
        px = max(0, int(px))
        return Box(self.x0 + px, self.y0 + px, self.x1 - px, self.y1 - px)

    def contains(self, x: float, y: float, pad: int = 0) -> bool:
        return (self.x0 + pad) <= x <= (self.x1 - pad) and (self.y0 + pad) <= y <= (self.y1 - pad)

    def overlaps(self, other: "Box", gap: int = 0) -> bool:
        return not (
            self.x1 + gap <= other.x0
            or other.x1 + gap <= self.x0
            or self.y1 + gap <= other.y0
            or other.y1 + gap <= self.y0
        )


@dataclass(frozen=True)
class KidsLayout:
    width: int
    height: int
    margin: int
    gap: int
    title: Box
    counter: Box
    stage: Box
    picture: Box
    caption: Box
    hero_font: int
    letter_font: int
    md_font: int
    sm_font: int
    picture_size: int
    orientation: str

    @property
    def letter_xy(self) -> tuple[int, int]:
        return self.stage.cx, self.stage.cy

    @property
    def picture_xy(self) -> tuple[int, int]:
        return self.picture.cx, self.picture.cy

    @property
    def dots_y(self) -> int:
        return self.caption.y1 - max(12, int(self.caption.h * 0.14))

    @property
    def bubble_xy(self) -> tuple[int, int]:
        """Praise/quiz sits in the caption, never on the letter."""
        return self.caption.cx, self.caption.y0 + max(18, int(self.caption.h * 0.22))


def kids_layout(width: int, height: int) -> KidsLayout:
    """Build a 3-band kids frame: title, stage+picture, caption.

    Landscape / square: letter card on the left, picture on the right.
    Portrait: letter card on top, picture under it.
    """
    w, h = max(64, int(width)), max(64, int(height))
    short = min(w, h)
    margin = max(6, int(short * 0.03))
    gap = max(4, int(short * 0.015))
    title_h = max(24, int(h * 0.075))
    caption_h = max(40, int(h * 0.20))
    chrome = margin * 2 + title_h + caption_h + gap * 2
    if chrome > int(h * 0.62):
        scale = (h * 0.62) / max(1, chrome)
        margin = max(4, int(margin * scale))
        title_h = max(18, int(title_h * scale))
        caption_h = max(28, int(caption_h * scale))
        gap = max(3, int(gap * scale))

    title = Box(margin, margin, w - margin, margin + title_h)
    counter_w = max(48, min(int(short * 0.13), title.w // 4))
    counter_h = max(16, min(int(title_h * 0.58), title.h - 4))
    counter = Box(
        title.x1 - counter_w - 8,
        max(title.y0 + 2, title.cy - counter_h // 2),
        title.x1 - 8,
        min(title.y1 - 2, title.cy + counter_h // 2),
    )
    caption = Box(margin, h - margin - caption_h, w - margin, h - margin)
    content_top = title.y1 + gap
    content_bot = max(content_top + 24, caption.y0 - gap)
    content = Box(margin, content_top, w - margin, content_bot)

    if (w / max(1, h)) <= 0.86:
        orientation = "portrait"
        pic_h = min(max(36, int(content.h * 0.32)), content.h - 24)
        stage = Box(content.x0, content.y0, content.x1, content.y1 - pic_h - gap)
        picture = Box(content.x0, min(stage.y1 + gap, content.y1 - 8), content.x1, content.y1)
    else:
        orientation = "landscape" if (w / max(1, h)) >= 1.25 else "square"
        pic_w = min(max(40, int(content.w * 0.34)), content.w - 32)
        stage = Box(content.x0, content.y0, content.x1 - pic_w - gap, content.y1)
        picture = Box(min(stage.x1 + gap, content.x1 - 8), content.y0, content.x1, content.y1)

    if stage.y1 < stage.y0:
        stage = Box(stage.x0, stage.y0, stage.x1, stage.y0 + 8)
    if picture.y1 < picture.y0:
        picture = Box(picture.x0, picture.y0, picture.x1, picture.y0 + 8)
    if stage.x1 < stage.x0:
        stage = Box(stage.x0, stage.y0, stage.x0 + 8, stage.y1)
    if picture.x1 < picture.x0:
        picture = Box(picture.x0, picture.y0, picture.x0 + 8, picture.y1)

    hero_font = max(22, int(min(stage.w, stage.h) * 0.50))
    letter_font = max(16, int(min(stage.w, stage.h) * 0.20))
    md_font = max(12, int(short * 0.042))
    sm_font = max(11, int(short * 0.030))
    picture_size = max(24, int(min(picture.w, picture.h) * 0.84))
    return KidsLayout(
        width=w,
        height=h,
        margin=margin,
        gap=gap,
        title=title,
        counter=counter,
        stage=stage,
        picture=picture,
        caption=caption,
        hero_font=hero_font,
        letter_font=letter_font,
        md_font=md_font,
        sm_font=sm_font,
        picture_size=picture_size,
        orientation=orientation,
    )
