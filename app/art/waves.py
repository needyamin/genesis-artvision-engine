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
        self.freqs = self.rng.uniform(0.5, 3.0, self.layers_n).astype(np.float32)
        self.amps = self.rng.uniform(0.3, 1.0, self.layers_n).astype(np.float32)
        self.phases = self.rng.random(self.layers_n).astype(np.float32) * np.pi * 2
        self.dirs = self.rng.uniform(0, np.pi * 2, self.layers_n).astype(np.float32)

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t_lin = frame_number / max(1, total_frames)
        t = director_time(t_lin, str(self.params.get("edit_feel") or "cinematic"))
        sm = style_motion(str(self.params.get("style") or "organic"))
        anim = float(self.params.get("animation_speed", 1.0))
        speed = float(self.params.get("speed", 1.0)) * anim * 0.65 * sm.speed
        freq = float(self.params.get("frequency", 1.5))
        amp = float(self.params.get("amplitude", 0.2))
        distortion = float(self.params.get("distortion", 0.3)) * 0.55 * sm.noise

        field = np.zeros((self.height, self.width), dtype=np.float32)
        for i in range(self.layers_n):
            dx = np.cos(self.dirs[i])
            dy = np.sin(self.dirs[i])
            phase = self.phases[i] + t * speed * np.pi * 2 * (0.5 + self.freqs[i])
            wave = np.sin((self.xx * dx + self.yy * dy) * np.pi * 2 * freq * self.freqs[i] + phase)
            if distortion > 0:
                warp = np.sin(self.yy * 6 + t * 2.2) * distortion * 0.04
                wave = np.sin(
                    (self.xx * dx + warp + self.yy * dy) * np.pi * 2 * freq * self.freqs[i] + phase
                )
            field += wave * self.amps[i] * amp
        norm = (field - field.min()) / (field.max() - field.min() + 1e-6)
        lut = self.palette.array(256)
        idx = np.clip((norm * 255), 0, 255).astype(np.int32)
        rgb = lut[idx]
        # Soft highlight ridges
        ridges = (np.abs(np.gradient(norm)[0]) + np.abs(np.gradient(norm)[1]))
        ridges = ridges / (ridges.max() + 1e-6)
        pulse = beat_pulse(
            t_lin,
            float(self.params.get("bpm") or 90.0),
            float(self.params.get("_duration") or 30.0),
        )
        rgb = rgb + ridges[..., None] * (sm.ridge + sm.pulse * pulse * 0.12)
        return self._to_uint8(rgb * float(self.params.get("contrast", 0.85)) * (0.92 + 0.08 * sm.glow))
