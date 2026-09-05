"""Wave / liquid-like art engine."""

from __future__ import annotations

import numpy as np

from app.art.base import ArtEngine, register_engine
from app.art.edit_brain import beat_pulse, director_time, style_motion


@register_engine
class WavesEngine(ArtEngine):
    name = "waves"
    description = "Layered wave / liquid interference patterns"

    def _on_setup(self) -> None:
        assert self.rng is not None
        self.layers_n = int(self.params.get("layers", 4))
        ys = np.linspace(0, 1, self.height, dtype=np.float32)
        xs = np.linspace(0, 1, self.width, dtype=np.float32)
        self.xx, self.yy = np.meshgrid(xs, ys)
        self.freqs = self.rng.uniform(0.6, 2.8, self.layers_n).astype(np.float32)
        self.amps = self.rng.uniform(0.4, 1.0, self.layers_n).astype(np.float32)
        self.phases = self.rng.random(self.layers_n).astype(np.float32) * np.pi * 2
        self.dirs = self.rng.uniform(0, np.pi * 2, self.layers_n).astype(np.float32)

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t_lin = frame_number / max(1, total_frames)
        t = director_time(t_lin, str(self.params.get("edit_feel") or "cinematic"))
        style_key = str(self.params.get("style") or "organic")
        sm = style_motion(style_key)
        anim = float(self.params.get("animation_speed", 1.0))
        speed = float(self.params.get("speed", 1.0)) * anim * 0.65 * sm.speed
        freq = float(self.params.get("frequency", 1.5))
        amp = float(self.params.get("amplitude", 0.2))
        warp_strength = sm.warp * float(self.params.get("distortion", 0.35))

        # Multi-octave Inigo Quilez style domain warping (fBM)
        # Octave 1: coarse displacement field q
        qx = np.sin(self.xx * 3.2 + self.yy * 1.8 + t * speed * 1.5)
        qy = np.cos(self.xx * 1.5 + self.yy * 3.0 - t * speed * 1.2)
        # Octave 2: finer domain warp r
        rx = np.sin((self.xx + qx * 0.25 * warp_strength) * 6.0 + t * speed * 2.0)
        ry = np.cos((self.yy + qy * 0.25 * warp_strength) * 6.0 - t * speed * 1.8)

        # Coordinate evaluation with domain warp
        eval_x = self.xx + (qx * 0.15 + rx * 0.08) * warp_strength
        eval_y = self.yy + (qy * 0.15 + ry * 0.08) * warp_strength

        field = np.zeros((self.height, self.width), dtype=np.float32)
        for i in range(self.layers_n):
            dx = float(np.cos(self.dirs[i]))
            dy = float(np.sin(self.dirs[i]))
            phase = self.phases[i] + t * speed * np.pi * 2.0 * (0.5 + self.freqs[i])
            wave = np.sin((eval_x * dx + eval_y * dy) * np.pi * 2.0 * freq * self.freqs[i] + phase)
            field += wave * self.amps[i] * amp

        f_min, f_max = float(field.min()), float(field.max())
        norm = (field - f_min) / max(1e-6, f_max - f_min)

        # Palette indexing through Look-Up Table
        lut = self.palette.array(256)
        idx = np.clip((norm * 255.0), 0, 255).astype(np.int32)
        rgb = lut[idx].astype(np.float32)

        # Surface normal and specular caustic glints
        gy, gx = np.gradient(norm)
        slope = np.sqrt(gx * gx + gy * gy) + 1e-6
        # Light vector drifting across scene
        lx = np.cos(t * np.pi * 2.0 * 0.3)
        ly = np.sin(t * np.pi * 2.0 * 0.3)
        dot_nl = np.clip((-gx * lx - gy * ly) / slope, 0.0, 1.0)
        specular = np.power(dot_nl, 18.0) * sm.caustic * 180.0

        # Style-specific aesthetic overlays
        if style_key == "documentary":
            # Bathymetric / topographic contour isolines
            contour = ((norm * 14.0) % 1.0 < 0.06).astype(np.float32)
            rgb += contour[..., None] * 42.0
        elif style_key == "digital":
            # Scanlines and digital cyber grid
            grid_x = ((self.xx * 40.0) % 1.0 < 0.04).astype(np.float32)
            grid_y = ((self.yy * 40.0) % 1.0 < 0.04).astype(np.float32)
            grid = np.maximum(grid_x, grid_y)
            rgb += grid[..., None] * 38.0

        # Ridge highlights and specular caustics
        pulse = beat_pulse(
            t_lin,
            float(self.params.get("bpm") or 90.0),
            float(self.params.get("_duration") or 30.0),
        )
        norm_ridges = slope / (slope.max() + 1e-6)
        rgb += norm_ridges[..., None] * (sm.ridge * 120.0 + sm.pulse * pulse * 25.0)
        rgb += specular[..., None]

        contrast = float(self.params.get("contrast", 0.85))
        return self._to_uint8(np.clip(rgb * contrast * (0.92 + 0.08 * sm.glow), 0.0, 255.0))
