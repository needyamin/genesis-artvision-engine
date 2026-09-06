"""Trending Brief engine — kinetic type on a procedural backdrop the engine owns."""

from __future__ import annotations

import math

import numpy as np
from PIL import Image, ImageDraw

from app.art.base import ArtEngine, register_engine
from app.art.brief_layout import brief_layout, composite_segment_layers, paint_text_block
from app.art.edit_brain import beat_pulse, style_motion
from app.art.editorial import segment_state
from app.art.fonts import load_font, paint_text
from app.art.procedural_backgrounds import get_chrome_theme, paint_background
from app.art.styles import style_chrome
from app.art.trend_content import build_trend_topic
from app.art.visual_variants import resolve_visual_variants


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
        self.variant = resolve_visual_variants(self.name, self.params)
        self.params.update(self.variant.to_params())
        self.energy = float(self.params.get("energy", 0.85))
        self.ticker_speed = float(self.params.get("ticker_speed", 1.0))
        self.motion = style_motion(str(self.params.get("style") or "pulse"))
        caption_band = str(self.params.get("caption_mode") or "").lower() in {"burn", "both"}
        self.layout = brief_layout(
            self.width,
            self.height,
            ticker=True,
            caption_band=caption_band,
            engine=self.name,
            variant=self.variant.layout_variant,
        )
        theme = get_chrome_theme(self.name, self.variant.background_variant, self.palette)
        self.chrome = style_chrome(
            str(self.params.get("style") or "pulse"),
            dark=theme.dark,
            text=theme.text,
            muted=theme.muted_text,
            accent=theme.accent,
            card=theme.card,
            border=theme.border,
            short_side=min(self.width, self.height),
        )
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
        state = segment_state(seg, t, easing=str(self.params.get("easing") or "snappy"))
        bpm = float(self.params.get("bpm") or 128.0)
        pulse = beat_pulse(t, bpm=bpm, duration=float(self.params.get("_duration") or 30.0))
        frame = self._backdrop(t, pulse)
        img = Image.fromarray(frame).convert("RGBA")
        draw = ImageDraw.Draw(img, "RGBA")
        self._ticker(draw, t)
        self._headline(draw, t, idx, max(1, len(segments)))
        current = self._segment_layer(seg, state, pulse, idx)
        outgoing = None
        if idx > 0 and state["enter"] < 0.999:
            previous = segments[idx - 1]
            previous_state = {"local": 1.0, "eased": 1.0, "enter": 1.0, "leave": 1.0 - state["enter"]}
            outgoing = self._segment_layer(previous, previous_state, pulse, idx - 1)
        content = composite_segment_layers(
            outgoing,
            current,
            enter=state["enter"],
            leave=1.0 - state["enter"],
            kind=str(seg.get("transition") or "dissolve"),
        )
        img.alpha_composite(content)
        return np.array(img.convert("RGB"), dtype=np.uint8)

    def _backdrop(self, t: float, beat: float = 0.0) -> np.ndarray:
        if self.variant.background_variant != "neon_ridge":
            motion_t = t * max(0.35, self.energy * self.motion.speed)
            image = paint_background(
                self.name,
                self.width,
                self.height,
                self.seed,
                self.palette,
                variant=self.variant.background_variant,
                t=motion_t,
                beat=beat * self.motion.pulse,
            )
            return np.asarray(image.convert("RGB"), dtype=np.uint8)
        return self._classic_neon_ridge(t, beat)

    def _classic_neon_ridge(self, t: float, beat: float = 0.0) -> np.ndarray:
        h, w = self.height, self.width
        yy = np.linspace(0, 1, h, dtype=np.float32)[:, None]
        xx = np.linspace(0, 1, w, dtype=np.float32)[None, :]
        motion_speed = self.energy * self.motion.speed
        depth = np.zeros((h, w), dtype=np.float32)
        layers = max(2, int(self.motion.depth_layers))
        for layer in range(layers):
            scale = float(layer + 1)
            phase = t * motion_speed * (1.4 + scale * 0.7)
            ridge = np.sin((xx * (2.5 + scale * 2.2) + yy * (1.2 + scale) + phase) * np.pi)
            cross = np.cos((yy * (3.0 + scale) - xx * (0.8 + scale * 0.3) - phase * 0.7) * np.pi)
            depth += (ridge * 0.5 + cross * 0.5 + 1.0) * (0.5 / scale)
        depth /= max(0.1, sum(1.0 / (i + 1) for i in range(layers)))
        depth = np.clip(depth + beat * self.motion.pulse * 0.30, 0.0, 1.6)
        r = self.c_bg[0] + depth * 16 + yy * 5
        g = self.c_bg[1] + depth * 23
        b = self.c_bg[2] + depth * 34 + xx * 7
        frame = np.stack([r, g, b], axis=-1)
        frame = np.clip(frame, 0, 255).astype(np.uint8)
        py = ((self.py + t * self.ps * motion_speed) % 1.0 * h).astype(np.int32)
        px = ((self.px + np.sin(t * 4 * motion_speed + self.ps) * (0.025 + self.ps * 0.08)) % 1.0 * w).astype(np.int32)
        for i in range(len(self.px)):
            x, y = int(px[i]), int(py[i])
            if 0 <= x < w and 0 <= y < h:
                radius = 1 + (i % layers)
                y0, y1 = max(0, y - radius), min(h, y + radius + 1)
                x0, x1 = max(0, x - radius), min(w, x + radius + 1)
                alpha = 0.20 + 0.13 * (i % layers)
                frame[y0:y1, x0:x1] = np.clip(
                    frame[y0:y1, x0:x1].astype(np.float32) * (1.0 - alpha)
                    + np.asarray(self.c_accent, dtype=np.float32) * alpha,
                    0,
                    255,
                ).astype(np.uint8)
        scan = int((t * 1.8 % 1.0) * h)
        if 0 <= scan < h:
            frame[scan, :] = np.clip(frame[scan, :].astype(np.int16) + 28, 0, 255).astype(np.uint8)
        return frame

    def _ticker(self, draw: ImageDraw.ImageDraw, t: float) -> None:
        bar_h = self.layout.ticker.h
        draw.rectangle((0, 0, self.width, bar_h), fill=_rgba(self.c_hot, 220))
        f = load_font(max(11, int(self.height * 0.022)))
        label = str(self.topic.get("domain_label") or "TRENDING NOW")
        hook = str(self.topic.get("hook") or self.topic.get("title") or "")
        text = f"  ●  {label}   {hook}   ●  {label}   {hook}"
        shift = int((t * self.width * 0.35 * self.ticker_speed) % max(40, self.width * 0.5))
        paint_text(draw, (20 - shift, bar_h // 2), text, f, (255, 255, 255), anchor="lm", max_width=self.width * 2)

    def _headline(self, draw: ImageDraw.ImageDraw, t: float, idx: int, n: int) -> None:
        title = str(self.topic.get("title") or "Trending Brief")
        f_lg = load_font(self.layout.title_font)
        f_sm = load_font(self.layout.small_font)
        box = self.layout.header
        y = box.y0 + int(box.h * 0.34)
        shake = int(2 * math.sin(t * math.tau * 8) * self.energy)
        paint_text(draw, (box.x0 + shake, y), title, f_lg, (245, 250, 255), anchor="lm", max_width=int(box.w * 0.82))
        sub = str(self.topic.get("subtitle") or "")
        if sub:
            paint_text(draw, (box.x0, y + int(box.h * 0.35)), sub, f_sm, self.c_accent, anchor="lm", max_width=int(box.w * 0.82))
        paint_text(draw, (box.x1, y + 8), f"{idx + 1}/{n}", f_sm, (200, 210, 220), anchor="rm")

    def _segment_layer(
        self,
        seg: dict,
        state: dict[str, float],
        beat: float,
        index: int,
    ) -> Image.Image:
        del state
        layer = Image.new("RGBA", (self.width, self.height), (0, 0, 0, 0))
        draw = ImageDraw.Draw(layer, "RGBA")
        card = self.layout.card
        x0, y0, x1, y1 = card.xy
        border_alpha = int(150 + 80 * beat)
        draw.rounded_rectangle(
            (x0, y0, x1, y1),
            radius=int(self.chrome["card_radius"]),
            fill=self.chrome["card_fill"],
            outline=_rgba(self.c_accent, border_alpha),
            width=int(self.chrome["stroke"]),
        )
        f_ph = load_font(self.layout.small_font)
        f_h = load_font(self.layout.headline_font)
        f_b = load_font(self.layout.body_font)
        pad = self.layout.pad
        paint_text(draw, (x0 + pad, y0 + pad), str(seg.get("phase") or "NOW"), f_ph, self.c_hot, anchor="la")
        head_y = y0 + pad + int(self.layout.headline_font * 1.5)
        used = paint_text_block(
            draw,
            (x0 + pad, head_y),
            str(seg.get("headline") or ""),
            f_h,
            self.chrome["text"],
            max_width=card.w - pad * 2,
            max_height=max(24, int(card.h * 0.26)),
        )
        body_y = head_y + used + self.layout.gap
        paint_text_block(
            draw,
            (x0 + pad, body_y),
            str(seg.get("body") or ""),
            f_b,
            self.chrome["muted"],
            max_width=card.w - pad * 2,
            max_height=max(24, y1 - body_y - pad * 3),
            spacing=max(3, self.layout.small_font // 4),
        )
        point = str(seg.get("data_point") or "")
        if point:
            paint_text(draw, (x0 + pad, y1 - pad), point, f_ph, self.c_accent, anchor="lb", max_width=card.w - pad * 2)
        self._visual_panel(draw, seg, index, beat)
        return layer

    def _visual_panel(self, draw: ImageDraw.ImageDraw, seg: dict, index: int, beat: float) -> None:
        box = self.layout.visual
        draw.rounded_rectangle(
            box.xy,
            radius=max(8, int(self.chrome["card_radius"]) - 2),
            fill=(8, 12, 24, 145),
            outline=_rgba(self.c_hot, 90),
            width=1,
        )
        pad = self.layout.pad
        kind = self.variant.layout_variant
        if kind == "full_bleed":
            self._visual_wave(draw, box, index, beat, pad)
        elif kind == "card_emphasis":
            self._visual_tiles(draw, box, index, beat, pad)
        else:
            self._visual_bars(draw, box, index, beat, pad)
        label = str(seg.get("phase") or "SIGNAL").upper()
        paint_text(draw, (box.x1 - pad, box.y0 + pad), label, load_font(self.layout.small_font), (225, 235, 245), anchor="ra", max_width=box.w // 2)
        metrics = list(self.topic.get("metrics") or [])
        if metrics:
            mx = box.x1 - pad
            for i, m in enumerate(metrics[:2]):
                label = f"{m.get('label', '')}  {m.get('val', '')} {m.get('unit', '')}"
                paint_text(draw, (mx, box.y1 - pad - i * (self.layout.small_font + 6)), label, load_font(self.layout.small_font), (180, 190, 200), anchor="rb", max_width=box.w // 2)

    def _visual_bars(self, draw: ImageDraw.ImageDraw, box, index: int, beat: float, pad: int) -> None:
        bars = 5
        baseline = box.y1 - pad
        usable_h = max(10, box.h - pad * 2)
        bar_w = max(5, (box.w - pad * 2) // (bars * 2))
        for i in range(bars):
            value = 0.28 + 0.62 * (0.5 + 0.5 * math.sin((index + 1) * 1.7 + i * 1.3))
            value *= 0.92 + beat * 0.08
            bx = box.x0 + pad + i * bar_w * 2
            top = baseline - int(usable_h * value)
            draw.rounded_rectangle((bx, top, bx + bar_w, baseline), radius=max(2, bar_w // 3), fill=_rgba(self.c_accent, 110 + i * 20))

    def _visual_tiles(self, draw: ImageDraw.ImageDraw, box, index: int, beat: float, pad: int) -> None:
        cols, rows = 2, 2
        gap = max(4, pad // 2)
        cell_w = max(8, (box.w - pad * 2 - gap) // cols)
        cell_h = max(8, (box.h - pad * 2 - gap) // rows)
        for i in range(cols * rows):
            cx, cy = i % cols, i // cols
            x0 = box.x0 + pad + cx * (cell_w + gap)
            y0 = box.y0 + pad + cy * (cell_h + gap)
            pulse = 90 + int(80 * (0.5 + 0.5 * math.sin(index + i + beat * 4)))
            draw.rounded_rectangle(
                (x0, y0, x0 + cell_w, y0 + cell_h),
                radius=max(4, int(self.chrome["card_radius"]) // 2),
                fill=_rgba(self.c_accent if i % 2 == 0 else self.c_hot, pulse),
            )

    def _visual_wave(self, draw: ImageDraw.ImageDraw, box, index: int, beat: float, pad: int) -> None:
        mid = box.cy
        pts = []
        for x in range(box.x0 + pad, box.x1 - pad, max(4, box.w // 40)):
            y = mid + int((box.h * 0.18) * math.sin(x * 0.08 + index + beat * 6))
            pts.append((x, y))
        if len(pts) > 1:
            draw.line(pts, fill=_rgba(self.c_accent, 210), width=max(2, pad // 3))
        for i, (x, y) in enumerate(pts[:: max(1, len(pts) // 8)]):
            r = 2 + (i + int(beat * 3)) % 3
            draw.ellipse((x - r, y - r, x + r, y + r), fill=_rgba(self.c_hot, 200))
