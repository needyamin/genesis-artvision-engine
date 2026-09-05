"""Galaxy / starfield art engine."""

from __future__ import annotations

import cv2
import numpy as np

from app.art.base import ArtEngine, register_engine
from app.art.edit_brain import beat_pulse, director_time, style_motion


@register_engine
class GalaxyEngine(ArtEngine):
    name = "galaxy"
    description = "Spiral galaxy / starfield"

    def _on_setup(self) -> None:
        assert self.rng is not None
        n = int(self.params.get("star_count", 1500))
        arms = int(self.params.get("arm_count", 4))
        # Spiral distribution with realistic disk density falloff
        self.r = (self.rng.power(1.6, n)).astype(np.float32)
        # Logarithmic winding
        arm_assignment = (np.arange(n) % arms) * (2.0 * np.pi / arms)
        arm_scatter = self.rng.normal(0.0, 0.18, n).astype(np.float32)
        self.theta = (arm_assignment + self.r * 4.2 + arm_scatter).astype(np.float32)
        # Vertical thickness of galactic disk (thicker at core, thin at edges)
        self.z0 = (self.rng.normal(0.0, 0.05, n) * (1.1 - self.r * 0.6)).astype(np.float32)

        self.sizes = self.rng.uniform(0.6, 2.8, n).astype(np.float32)
        self.hue = self.rng.random(n).astype(np.float32)
        self.bright = self.rng.uniform(0.35, 1.0, n).astype(np.float32)

        # Star populations: 0=bulge (warm/dense), 1=arm population, 2=supergiant (diffraction spikes)
        self.is_supergiant = (self.bright > 0.94) & (self.r > 0.25)

        bg_n = max(60, n // 3)
        self.bg_x = self.rng.random(bg_n).astype(np.float32)
        self.bg_y = self.rng.random(bg_n).astype(np.float32)
        self.bg_b = self.rng.uniform(0.12, 0.55, bg_n).astype(np.float32)
        self.cx = float(self.params.get("focus_x", 0.5))
        self.cy = float(self.params.get("focus_y", 0.48))

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t_lin = frame_number / max(1, total_frames)
        t = director_time(t_lin, str(self.params.get("edit_feel") or "cinematic"))
        sm = style_motion(str(self.params.get("style") or "cosmic"))
        spin = float(self.params.get("spin", 0.6)) * float(self.params.get("animation_speed", 1.0)) * 0.68 * sm.speed
        drift = float(self.params.get("drift", 0.2)) * sm.speed
        img = self._to_uint8(self._blank())

        # Distant background field with gentle scintillation
        bx = (self.bg_x * self.width).astype(np.int32) % self.width
        by = (self.bg_y * self.height).astype(np.int32) % self.height
        twinkle = 6.0 + 10.0 * sm.pulse
        tw = 0.55 + 0.45 * np.sin(t * twinkle + self.bg_b * 10)
        for i in range(0, len(bx), max(1, len(bx) // 800)):
            v = int(255 * tw[i] * self.bg_b[i])
            img[by[i], bx[i]] = (v, v, min(255, v + 20))

        # 3D Galactic Disk Projection with pitch tilt
        tilt_angle = np.deg2rad(float(self.params.get("tilt", 56.0)) * (0.85 + sm.tilt * 0.3))
        cos_tilt = float(np.cos(tilt_angle))
        sin_tilt = float(np.sin(tilt_angle))

        # Differential Keplerian rotation: inner regions rotate faster than outer spiral arms
        keplerian_spin = spin * (0.6 + 0.4 / (self.r + 0.3))
        current_theta = self.theta + t * keplerian_spin * np.pi * 2

        rr = self.r * (0.42 + 0.05 * np.sin(t * drift * 8.0))
        x3d = rr * np.cos(current_theta)
        y3d = rr * np.sin(current_theta)
        z3d = self.z0

        # Project 3D coordinates to 2D screen with aspect-ratio compensation
        aspect = self.width / max(1, self.height)
        xp = self.cx + x3d * 0.95
        yp = self.cy + (y3d * cos_tilt - z3d * sin_tilt) * 0.95 * aspect

        xs = np.clip((xp * self.width).astype(np.int32), 0, self.width - 1)
        ys = np.clip((yp * self.height).astype(np.int32), 0, self.height - 1)

        # Multi-layer Volumetric Core Bulge (HDR falloff)
        core_scale = float(self.params.get("core_glow", 0.6)) * sm.core
        pulse = beat_pulse(
            t_lin,
            float(self.params.get("bpm") or 80.0),
            float(self.params.get("_duration") or 30.0),
        )
        core_pt = (int(self.width * self.cx), int(self.height * self.cy))
        core_color = self.palette.as_uint8(0.12 + t * 0.1)

        # Draw multi-tiered atmospheric core glow
        for glow_rad_ratio, alpha_factor in [(0.14, 0.15), (0.07, 0.35), (0.03, 0.65)]:
            radius = max(6, int(min(self.width, self.height) * glow_rad_ratio * core_scale))
            core_layer = np.zeros_like(img)
            cv2.ellipse(
                core_layer,
                core_pt,
                (radius, max(4, int(radius * cos_tilt * aspect))),
                0,
                0,
                360,
                core_color,
                -1,
                lineType=cv2.LINE_AA,
            )
            alpha = alpha_factor * (0.8 + sm.pulse * pulse * 0.4)
            img = cv2.addWeighted(img, 1.0, core_layer, alpha, 0)

        # Render Stars with Spectral Palette and Supergiant Spikes
        for i in range(len(xs)):
            # Core stars are warmer/golden; outer arm stars are luminous spectral hues
            spectral_bias = float(0.1 if self.r[i] < 0.22 else (self.hue[i] + t) % 1.0)
            color = self.palette.as_uint8(spectral_bias)
            scale = float(self.bright[i])
            c = tuple(int(ch * scale) for ch in color)
            r = 1 if self.sizes[i] < 1.6 else 2
            pt = (int(xs[i]), int(ys[i]))
            cv2.circle(img, pt, r, c, -1, lineType=cv2.LINE_AA)

            # Astrophotography diffraction cross spikes for the brightest supergiants
            if self.is_supergiant[i] and scale > 0.85:
                spike_len = int(4 + self.sizes[i] * 2.5)
                spike_col = tuple(int(ch * 0.7) for ch in c)
                cv2.line(img, (pt[0] - spike_len, pt[1]), (pt[0] + spike_len, pt[1]), spike_col, 1, lineType=cv2.LINE_AA)
                cv2.line(img, (pt[0], pt[1] - spike_len), (pt[0], pt[1] + spike_len), spike_col, 1, lineType=cv2.LINE_AA)

        return img
