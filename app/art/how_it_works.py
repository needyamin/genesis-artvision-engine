"""How It Works engine — everyday classroom diagrams the engine paints itself."""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from app.art.base import ArtEngine, register_engine
from app.art.fonts import load_font, paint_text
from app.art.how_it_works_content import build_how_it_works_topic


def _rgb(c: tuple[int, int, int], a: int = 255) -> tuple[int, int, int, int]:
    return (int(c[0]), int(c[1]), int(c[2]), a)


@register_engine
class HowItWorksEngine(ArtEngine):
    name = "how_it_works"
    description = "Everyday how-it-works classroom explainer"
    parallel_frames = True

    def _on_setup(self) -> None:
        assert self.rng is not None
        duration = float(self.params.get("_duration", 30.0))
        topic = self.params.get("topic_data")
        if not isinstance(topic, dict):
            topic = build_how_it_works_topic(
                self.seed,
                duration,
                topic_id=str(self.params.get("topic_id") or "") or None,
                params=self.params,
            )
        self.topic = topic
        self.params["topic_data"] = topic
        self.board = str(self.params.get("board", "whiteboard"))
        self.c_ink = (40, 55, 70)
        self.c_accent = (30, 110, 170)
        self.c_chalk = (245, 248, 252)
        if self.palette is not None and len(self.palette.colors) >= 2:
            self.c_accent = tuple(int(c * 255) for c in self.palette.colors[1])[:3]

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        t = frame_number / max(1, total_frames)
        segments = list(self.topic.get("segments") or [])
        seg = segments[-1] if segments else {}
        for s in segments:
            if float(s.get("t0", 0)) <= t < float(s.get("t1", 1)):
                seg = s
                break
        img = self._board()
        draw = ImageDraw.Draw(img, "RGBA")
        self._header(draw, t, int(seg.get("index") or 0), max(1, len(segments)))
        box = (
            int(self.width * 0.06),
            int(self.height * 0.16),
            int(self.width * 0.52),
            int(self.height * 0.88),
        )
        self._diagram(
            draw,
            str(self.topic.get("schematic_type") or "cycle"),
            box,
            t,
        )
        self._cards(draw, seg)
        return np.array(img.convert("RGB"), dtype=np.uint8)

    def _board(self) -> Image.Image:
        if self.board == "chalkboard":
            base = np.full((self.height, self.width, 3), (42, 78, 52), dtype=np.uint8)
        else:
            top = np.array((236, 242, 248), dtype=np.float32)
            bot = np.array((210, 220, 230), dtype=np.float32)
            yy = np.linspace(0, 1, self.height, dtype=np.float32)[:, None, None]
            base = np.clip(top * (1 - yy) + bot * yy, 0, 255).astype(np.uint8)
            base = np.broadcast_to(base, (self.height, self.width, 3)).copy()
        return Image.fromarray(base)

    def _header(self, draw: ImageDraw.ImageDraw, t: float, idx: int, n: int) -> None:
        pad = int(self.width * 0.04)
        hud_h = int(self.height * 0.12)
        draw.rectangle((0, 0, self.width, hud_h), fill=(255, 255, 255, 230))
        draw.line((0, hud_h, self.width, hud_h), fill=_rgb(self.c_accent, 160), width=3)
        f_sm = load_font(max(12, int(self.height * 0.022)))
        f_lg = load_font(max(16, int(self.height * 0.036)))
        paint_text(draw, (pad, int(hud_h * 0.32)), str(self.topic.get("domain_label") or "HOW IT WORKS"), f_sm, self.c_accent, anchor="lm")
        paint_text(draw, (pad, int(hud_h * 0.72)), str(self.topic.get("title") or "How It Works"), f_lg, self.c_ink, anchor="lm", max_width=int(self.width * 0.7))
        bar_w = int(self.width * 0.22)
        bx0, by0 = self.width - pad - bar_w, int(hud_h * 0.42)
        draw.rounded_rectangle((bx0, by0, bx0 + bar_w, by0 + 10), radius=4, outline=_rgb(self.c_accent, 180), width=1)
        draw.rounded_rectangle((bx0, by0, bx0 + int(bar_w * t), by0 + 10), radius=4, fill=_rgb(self.c_accent, 200))
        paint_text(draw, (bx0 + bar_w, by0 - 8), f"{idx + 1}/{n}", f_sm, self.c_ink, anchor="rm")

    def _cards(self, draw: ImageDraw.ImageDraw, seg: dict) -> None:
        x0 = int(self.width * 0.56)
        y0 = int(self.height * 0.18)
        x1 = int(self.width * 0.96)
        y1 = int(self.height * 0.88)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=16, fill=(255, 255, 255, 235), outline=_rgb(self.c_accent, 140), width=2)
        f_phase = load_font(max(11, int(self.height * 0.02)))
        f_head = load_font(max(16, int(self.height * 0.034)))
        f_body = load_font(max(13, int(self.height * 0.026)))
        pad = 16
        paint_text(draw, (x0 + pad, y0 + 22), str(seg.get("phase") or "STEP"), f_phase, self.c_accent, anchor="lm")
        paint_text(draw, (x0 + pad, y0 + 58), str(seg.get("headline") or ""), f_head, self.c_ink, anchor="lm", max_width=x1 - x0 - 32)
        paint_text(draw, (x0 + pad, y0 + 110), str(seg.get("body") or ""), f_body, (70, 80, 90), anchor="lm", max_width=x1 - x0 - 32)
        point = str(seg.get("data_point") or "")
        if point:
            by = y1 - 48
            draw.rounded_rectangle((x0 + pad, by, x1 - pad, by + 32), radius=8, fill=_rgb(self.c_accent, 30))
            paint_text(draw, (x0 + pad + 8, by + 16), point[:42], f_body, self.c_accent, anchor="lm", max_width=x1 - x0 - 48)

    def _diagram(self, draw: ImageDraw.ImageDraw, kind: str, box: tuple[int, int, int, int], t: float) -> None:
        x0, y0, x1, y1 = box
        cx, cy = (x0 + x1) // 2, (y0 + y1) // 2
        r = int(min(x1 - x0, y1 - y0) * 0.32)
        draw.rounded_rectangle(box, radius=18, fill=(255, 255, 255, 40), outline=_rgb(self.c_accent, 80), width=1)
        kind = kind.lower()
        if kind == "heart":
            self._heart(draw, cx, cy, r, t)
        elif kind == "circuit":
            self._circuit(draw, x0, y0, x1, y1, t)
        elif kind == "rainbow":
            self._rainbow(draw, cx, cy + r // 3, r, t)
        elif kind == "plant":
            self._plant(draw, cx, y1 - 20, r, t)
        elif kind == "spin":
            self._earth(draw, cx, cy, r, t)
        elif kind == "wave":
            self._waves(draw, x0, y0, x1, y1, t)
        elif kind == "field":
            self._field(draw, cx, cy, r, t)
        elif kind == "heat":
            self._heat(draw, cx, cy, r, t)
        else:
            self._cycle(draw, cx, cy, r, t)

    def _cycle(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, t: float) -> None:
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=_rgb(self.c_accent, 200), width=5)
        ang = t * math.tau
        x = cx + int(math.cos(ang) * r)
        y = cy + int(math.sin(ang) * r)
        draw.ellipse((x - 10, y - 10, x + 10, y + 10), fill=_rgb(self.c_accent, 230))
        labels = [str(x) for x in (self.topic.get("diagram_labels") or []) if str(x).strip()]
        if len(labels) < 4:
            labels = [str(s.get("phase") or f"Step {i + 1}") for i, s in enumerate(self.topic.get("segments") or [])]
        if len(labels) < 4:
            labels = ["Sun", "Cloud", "Rain", "Sea"]
        labels = labels[:4]
        for i, lab in enumerate(labels):
            a = i * math.tau / 4 - math.pi / 2
            paint_text(
                draw,
                (cx + int(math.cos(a) * (r + 28)), cy + int(math.sin(a) * (r + 28))),
                lab[:10],
                load_font(max(11, int(self.height * 0.02))),
                self.c_ink,
                anchor="mm",
            )

    def _heart(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, t: float) -> None:
        pulse = 1.0 + 0.08 * math.sin(t * math.tau * 4)
        rr = int(r * pulse)
        draw.ellipse((cx - rr, cy - rr // 2, cx, cy + rr // 2), fill=_rgb((200, 70, 80), 200))
        draw.ellipse((cx, cy - rr // 2, cx + rr, cy + rr // 2), fill=_rgb((200, 70, 80), 200))
        draw.polygon([(cx - rr, cy), (cx + rr, cy), (cx, cy + int(rr * 1.15))], fill=_rgb((200, 70, 80), 200))

    def _circuit(self, draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, t: float) -> None:
        y = (y0 + y1) // 2
        draw.line((x0 + 20, y, x1 - 20, y), fill=_rgb(self.c_accent, 200), width=4)
        gap = int((x1 - x0) * (0.35 + 0.1 * math.sin(t * math.tau)))
        mx = x0 + 20 + gap
        on = math.sin(t * math.tau * 2) > 0
        draw.rectangle((mx - 8, y - 18, mx + 8, y + 18), outline=_rgb(self.c_accent, 220), width=3)
        if on:
            draw.line((mx - 8, y, mx + 8, y), fill=_rgb((240, 200, 40), 255), width=3)

    def _rainbow(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, t: float) -> None:
        colors = [(220, 60, 60), (240, 140, 40), (240, 210, 50), (70, 180, 80), (50, 120, 220), (90, 70, 200)]
        for i, col in enumerate(colors):
            rr = r - i * 7
            draw.arc((cx - rr, cy - rr, cx + rr, cy + rr), start=200, end=340, fill=_rgb(col, 220), width=6)

    def _plant(self, draw: ImageDraw.ImageDraw, cx: int, yb: int, r: int, t: float) -> None:
        grow = 0.45 + 0.55 * min(1.0, t * 1.4)
        top = yb - int(r * 2 * grow)
        draw.line((cx, yb, cx, top), fill=_rgb((50, 130, 70), 230), width=6)
        draw.ellipse((cx - 18, top - 22, cx + 22, top + 10), fill=_rgb((80, 170, 90), 220))
        draw.polygon([(cx - 30, yb), (cx + 30, yb), (cx, yb + 18)], fill=_rgb((140, 100, 60), 200))

    def _earth(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, t: float) -> None:
        draw.ellipse((cx - r, cy - r, cx + r, cy + r), outline=_rgb(self.c_accent, 220), width=4)
        ang = t * math.tau
        draw.pieslice((cx - r, cy - r, cx + r, cy + r), start=int(math.degrees(ang)), end=int(math.degrees(ang) + 180), fill=_rgb((240, 210, 70), 80))
        draw.ellipse((cx - 8, cy - r - 28, cx + 8, cy - r - 12), fill=_rgb((240, 210, 70), 230))

    def _waves(self, draw: ImageDraw.ImageDraw, x0: int, y0: int, x1: int, y1: int, t: float) -> None:
        mid = (y0 + y1) // 2
        pts = []
        for x in range(x0 + 10, x1 - 10, 8):
            y = mid + int(22 * math.sin((x * 0.04) + t * math.tau * 2))
            pts.append((x, y))
        if len(pts) > 1:
            draw.line(pts, fill=_rgb(self.c_accent, 220), width=4)

    def _field(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, t: float) -> None:
        draw.ellipse((cx - r - 20, cy - 12, cx - r + 12, cy + 12), fill=_rgb((40, 80, 180), 230))
        draw.ellipse((cx + r - 12, cy - 12, cx + r + 20, cy + 12), fill=_rgb((180, 50, 50), 230))
        for i in range(5):
            yy = cy - r // 2 + i * (r // 4)
            draw.arc((cx - r, yy - 20, cx + r, yy + 20), start=20, end=160, fill=_rgb(self.c_accent, 140), width=2)

    def _heat(self, draw: ImageDraw.ImageDraw, cx: int, cy: int, r: int, t: float) -> None:
        draw.rounded_rectangle((cx - r // 2, cy - r, cx + r // 2, cy + r), radius=8, outline=_rgb(self.c_accent, 200), width=3)
        glow = int(80 + 80 * abs(math.sin(t * math.tau * 3)))
        draw.rectangle((cx - 8, cy - r + 20, cx + 8, cy + r - 20), fill=(255, glow, 40, 200))
