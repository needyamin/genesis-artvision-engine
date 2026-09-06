"""Trending Brief engine — kinetic type on a procedural backdrop the engine owns."""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from app.art.base import ArtEngine, register_engine
from app.art.fonts import load_font, paint_text
from app.art.trend_content import build_trend_topic


def _rgba(c: tuple[int, int, int], a: int = 255) -> tuple[int, int, int, int]:
    return (int(c[0]), int(c[1]), int(c[2]), a)


@register_engine
class TrendBriefEngine(ArtEngine):
    name = "trend_brief"
    description = "Internet trending topic brief with kinetic type"
    parallel_frames = True

    def _on_setup(self) -> None:
        assert self.rng is not None
        duration = float(self.params.get("_duration", 30.0))
        topic = self.params.get("topic_data")
        if not isinstance(topic, dict):
            topic = build_trend_topic(
                self.seed,
                duration,
                topic_id=str(self.params.get("topic_id") or "") or None,
                params=self.params,
            )
        self.topic = topic
        self.params["topic_data"] = topic
        self.energy = float(self.params.get("energy", 0.85))
        self.ticker_speed = float(self.params.get("ticker_speed", 1.0))
        self.c_bg = (8, 10, 18)
        self.c_accent = (0, 230, 180)
        self.c_hot = (255, 80, 120)
        if self.palette is not None and len(self.palette.colors) >= 3:
            self.c_bg = tuple(max(0, min(40, int(c * 40))) for c in self.palette.colors[0])[:3]
            self.c_accent = tuple(int(c * 255) for c in self.palette.colors[1])[:3]
            self.c_hot = tuple(int(c * 255) for c in self.palette.colors[2])[:3]
        n = 80
        self.px = self.rng.random(n).astype(np.float32)
        self.py = self.rng.random(n).astype(np.float32)
        self.ps = self.rng.uniform(0.08, 0.35, n).astype(np.float32)

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        t = frame_number / max(1, total_frames)
        segments = list(self.topic.get("segments") or [])
        seg = segments[-1] if segments else {}
        idx = max(0, len(segments) - 1)
        for i, s in enumerate(segments):
            if float(s.get("t0", 0)) <= t < float(s.get("t1", 1)):
                seg = s
                idx = i
                break
        frame = self._backdrop(t)
        img = Image.fromarray(frame)
        draw = ImageDraw.Draw(img, "RGBA")
        self._ticker(draw, t)
        self._headline(draw, t, idx, max(1, len(segments)))
        self._beat_card(draw, seg, t)
        return np.array(img.convert("RGB"), dtype=np.uint8)

    def _backdrop(self, t: float) -> np.ndarray:
        h, w = self.height, self.width
        yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        xx = np.linspace(0, 1, w, dtype=np.float32)[None, :]
        pulse = 0.5 + 0.5 * np.sin((xx * 8 + yy * 3 + t * self.energy * 6) * np.pi)
        r = self.c_bg[0] + pulse * 18
        g = self.c_bg[1] + pulse * 22
        b = self.c_bg[2] + pulse * 28
        frame = np.stack([r, g, b], axis=-1)
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        py = ((self.py + t * self.ps) % 1.0 * h).astype(np.int32)
        px = ((self.px + np.sin(t * 4 + self.ps) * 0.04) % 1.0 * w).astype(np.int32)
        for i in range(len(self.px)):
            x, y = int(px[i]), int(py[i])
            if 0 <= x < w and 0 <= y < h:
                frame[y, x] = self.c_accent
        scan = int((t * 1.8 % 1.0) * h)
        if 0 <= scan < h:
            frame[scan, :] = np.clip(frame[scan, :].astype(np.int16) + 28, 0, 255).astype(np.uint8)
        return frame

    def _ticker(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        bar_h = int(self.height * 0.055)
        draw.rectangle((0, 0, self.width, bar_h), fill=_rgba(self.c_hot, 220))
        f = load_font(max(11, int(self.height * 0.022)))
        label = str(self.topic.get("domain_label") or "TRENDING NOW")
        hook = str(self.topic.get("hook") or self.topic.get("title") or "")
        text = f"  ●  {label}   {hook}   ●  {label}   {hook}"
        shift = int((t * self.width * 0.35 * self.ticker_speed) % max(40, self.width * 0.5))
        paint_text(draw, (20 - shift, bar_h // 2), text[:120], f, (255, 255, 255), anchor="lm", max_width=self.width * 2)

    def _headline(self, draw: ImageDraw.ImageDraw, t: float, idx: int, n: int) -> None:
        title = str(self.topic.get("title") or "Trending Brief")
        f_lg = load_font(max(18, int(self.height * 0.048)))
        f_sm = load_font(max(12, int(self.height * 0.022)))
        y = int(self.height * 0.14)
        shake = int(2 * math.sin(t * math.tau * 8) * self.energy)
        paint_text(draw, (int(self.width * 0.06) + shake, y), title[:48], f_lg, (245, 250, 255), anchor="lm", max_width=int(self.width * 0.88))
        sub = str(self.topic.get("subtitle") or "")
        if sub:
            paint_text(draw, (int(self.width * 0.06), y + int(self.height * 0.06)), sub[:40], f_sm, self.c_accent, anchor="lm")
        paint_text(draw, (int(self.width * 0.94), y + 8), f"{idx + 1}/{n}", f_sm, (200, 210, 220), anchor="rm")

    def _beat_card(self, draw: ImageDraw.ImageDraw, seg: dict, t: float) -> None:
        x0 = int(self.width * 0.08)
        y0 = int(self.height * 0.40)
        x1 = int(self.width * 0.92)
        y1 = int(self.height * 0.90)
        draw.rounded_rectangle((x0, y0, x1, y1), radius=18, fill=(12, 16, 28, 210), outline=_rgba(self.c_accent, 180), width=2)
        f_ph = load_font(max(12, int(self.height * 0.022)))
        f_h = load_font(max(18, int(self.height * 0.038)))
        f_b = load_font(max(14, int(self.height * 0.028)))
        paint_text(draw, (x0 + 24, y0 + 28), str(seg.get("phase") or "NOW"), f_ph, self.c_hot, anchor="lm")
        paint_text(draw, (x0 + 24, y0 + 70), str(seg.get("headline") or "")[:52], f_h, (250, 252, 255), anchor="lm", max_width=x1 - x0 - 48)
        paint_text(draw, (x0 + 24, y0 + 130), str(seg.get("body") or "")[:140], f_b, (200, 210, 220), anchor="lm", max_width=x1 - x0 - 48)
        point = str(seg.get("data_point") or "")
        if point:
            paint_text(draw, (x0 + 24, y1 - 36), point[:48], f_ph, self.c_accent, anchor="lm", max_width=x1 - x0 - 48)
        metrics = list(self.topic.get("metrics") or [])
        if metrics:
            mx = x1 - 24
            for i, m in enumerate(metrics[:2]):
                label = f"{m.get('label', '')}  {m.get('val', '')} {m.get('unit', '')}"
                paint_text(draw, (mx, y1 - 36 - i * 22), label[:36], f_ph, (180, 190, 200), anchor="rm")
