"""Tunnel / hyperspace art engine."""

from __future__ import annotations

import numpy as np

from app.art.base import ArtEngine, register_engine
from app.art.edit_brain import beat_pulse, director_time, style_motion


@register_engine
class TunnelEngine(ArtEngine):
    name = "tunnel"
    description = "Perspective tunnel animation"

    def _on_setup(self) -> None:
        ys = np.linspace(-1, 1, self.height, dtype=np.float32)
        xs = np.linspace(-1, 1, self.width, dtype=np.float32)
        self.xx, self.yy = np.meshgrid(xs, ys)
        # Aspect ratio compensation
        aspect = self.width / max(1, self.height)
        self.xx = self.xx * aspect
        self.r = np.sqrt(self.xx ** 2 + self.yy ** 2) + 1e-4
        self.a = np.arctan2(self.yy, self.xx)

    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        assert self.palette is not None
        t_lin = frame_number / max(1, total_frames)
        t = director_time(t_lin, str(self.params.get("edit_feel") or "cinematic"))
        style_key = str(self.params.get("style") or "digital")
        sm = style_motion(style_key)
        anim = float(self.params.get("animation_speed", 1.0))
        speed = float(self.params.get("speed", 1.2)) * anim * 0.62 * sm.speed
        twist = float(self.params.get("twist", 0.8)) * sm.twist
        rings = int(self.params.get("rings", 24))
        spokes = int(self.params.get("spokes", 16))
        pulse = float(self.params.get("pulse", 0.6)) * (0.6 + sm.pulse)
        kick = beat_pulse(
            t_lin,
            float(self.params.get("bpm") or 100.0),
            float(self.params.get("_duration") or 30.0),
        )

        # 3D Camera Banking Roll & Drift
        cam_roll = np.sin(t * speed * 2.0) * 0.28 * twist
        cam_dx = np.sin(t * speed * 1.6) * 0.08
        cam_dy = np.cos(t * speed * 1.2) * 0.06

        curr_x = self.xx - cam_dx
        curr_y = self.yy - cam_dy
        r_cam = np.sqrt(curr_x ** 2 + curr_y ** 2) + 1e-4
        a_cam = np.arctan2(curr_y, curr_x) - cam_roll

        # Polygonal Conduit Geometry (Hexagon for digital/abstract, smooth for cosmic/organic)
        if style_key in {"digital", "abstract"}:
            n_sides = 6.0  # Hexagonal conduit
            theta_poly = (a_cam % (2.0 * np.pi / n_sides)) - (np.pi / n_sides)
            r_geom = r_cam * (np.cos(theta_poly) / np.cos(np.pi / n_sides))
        else:
            r_geom = r_cam

        depth = 1.0 / np.maximum(0.04, r_geom)
        u = depth + t * speed * 8.5
        v = a_cam / np.pi + twist * depth * 0.18 + t * speed * 0.35

        # Wall ribbing and panels
        wall_pattern = (
            0.5
            + 0.5 * np.sin(u * rings * 0.5)
            * np.sin(v * spokes * np.pi)
            * (0.82 + 0.18 * np.sin(t * pulse * 4.5) + sm.pulse * kick * 0.18)
        )

        # Depth fog falloff
        fog = np.clip(1.0 - r_cam * 0.62, 0.0, 1.0)
        value = wall_pattern * fog
        lut = self.palette.array(256)
        idx = np.clip(((value + t * 0.2) % 1.0) * 255.0, 0, 255).astype(np.int32)
        rgb = lut[idx].astype(np.float32) * fog[..., None]

        # Neon conduit rib edges
        rib_accent = (np.sin(u * rings * 0.5) > 0.92).astype(np.float32) * (0.6 + kick * 0.4)
        neon_color = np.asarray(self.palette.sample((t + 0.35) % 1.0), dtype=np.float32)
        rgb += rib_accent[..., None] * neon_color * 140.0

        # Volumetric Exit Bloom & God-Ray Light Shafts
        light_shafts = (
            np.clip(np.cos(a_cam * 8.0 + t * 3.0), 0.0, 1.0) ** 2.0
            * np.exp(-r_cam * 3.5)
            * sm.glow
            * 90.0
        )
        glow_core = np.exp(-r_cam * 4.8) * float(self.params.get("glow", 0.5)) * sm.glow * 255.0
        exit_color = np.asarray(self.palette.sample((t + 0.6) % 1.0), dtype=np.float32)

        rgb += glow_core[..., None] * exit_color
        rgb += light_shafts[..., None] * exit_color

        return self._to_uint8(rgb)
