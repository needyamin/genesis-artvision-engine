"""Central randomization system with deterministic seeding."""

from __future__ import annotations

import secrets
from dataclasses import dataclass, field
from typing import Any

import numpy as np

from app.art.edit_brain import rule_of_thirds_focus
from app.art.palette import Palette, generate_palette
from app.art.styles import list_styles, preferred_engines, sample_edit_look, sample_style_multiplier
from app.utils.validation import parse_resolution

# Random Engine (no explicit pick) uses these only. Education / ABC / explainer
# run when the user chooses that engine, or a style that prefers them.
VISUAL_ART_ENGINES = ("particles", "galaxy", "waves", "tunnel")


@dataclass
class ProjectSpec:
    """Fully specified randomized project ready for rendering."""

    project_id: str
    seed: int
    engine: str
    style: str
    width: int
    height: int
    fps: int
    duration: float
    params: dict[str, Any] = field(default_factory=dict)
    palette_name: str = ""
    palette_colors: list[list[float]] = field(default_factory=list)
    audio_enabled: bool = True
    thumbnail: bool = True

    @property
    def total_frames(self) -> int:
        return max(1, int(round(self.duration * self.fps)))

    def palette(self) -> Palette:
        colors = tuple(tuple(c) for c in self.palette_colors)  # type: ignore[misc]
        return Palette(name=self.palette_name, colors=colors)  # type: ignore[arg-type]

    def to_dict(self) -> dict[str, Any]:
        return {
            "project_id": self.project_id,
            "seed": self.seed,
            "engine": self.engine,
            "style": self.style,
            "width": self.width,
            "height": self.height,
            "fps": self.fps,
            "duration": self.duration,
            "params": self.params,
            "palette_name": self.palette_name,
            "palette_colors": self.palette_colors,
            "audio_enabled": self.audio_enabled,
            "thumbnail": self.thumbnail,
        }


# Per-engine parameter ranges (min, max) or discrete choices
ENGINE_PARAM_SPECS: dict[str, dict[str, Any]] = {
    "particles": {
        "count": (200, 1200),
        "size": (1.0, 5.0),
        "speed": (0.3, 2.5),
        "gravity": (-0.02, 0.05),
        "turbulence": (0.0, 1.5),
        "trail": (0.85, 0.98),
        "attraction": (0.0, 0.8),
    },
    "galaxy": {
        "star_count": (400, 2200),
        "arm_count": (2, 6),
        "spin": (0.1, 1.2),
        "noise_strength": (0.1, 0.8),
        "core_glow": (0.3, 1.0),
        "drift": (0.05, 0.4),
    },
    "waves": {
        "layers": (2, 7),
        "frequency": (0.5, 3.0),
        "amplitude": (0.05, 0.35),
        "speed": (0.3, 1.8),
        "distortion": (0.0, 0.8),
    },
    "tunnel": {
        "rings": (12, 48),
        "spokes": (8, 36),
        "speed": (0.5, 2.5),
        "twist": (0.0, 2.0),
        "pulse": (0.2, 1.2),
    },
    "alphabet_cartoon": {
        "mode": ["lesson", "lesson", "lesson", "spell", "focus", "chart"],
        "lesson_theme": [
            "letter_of_day", "letter_of_day",
            "phonics", "phonics",
            "dictionary", "dictionary",
            "real_world_math", "real_world_math", "real_world_math",
            "word_builder",
            "animal_friends",
            "count_fun",
        ],
        "columns": (5, 7),
        "bounce": (0.18, 0.38),
        "wobble": (0.04, 0.16),
        "letter_scale": (0.16, 0.22),
        "include_numbers": [False, False, True],
        "show_motifs": [True, True, False],
        "show_lowercase": [True, True, False],
        "background": ["notebook", "sky", "pastel", "pastel"],
        "sparkle": (0.06, 0.18),
        "pop_in": [True],
        "show_word_images": [True, True, True],
    },
    "hand_art": {
        "doodle_count": (8, 22),
        "stroke_width": (1, 4),
        "sketchiness": (0.3, 1.0),
        "paper_grain": (0.15, 0.55),
        "margin_scribbles": [True, True, False],
        "lesson_theme": ["draw_along", "sketch_practice", "doodle_story"],
        "show_captions": [True, True, True],
        "show_word_images": [True, True, True],
    },
    "kids_doodles": {
        "shape_count": (4, 8),
        "board_mode": ["colorful", "colorful", "chalkboard"],
        "lesson_theme": [
            "count_along", "real_world_math", "real_world_math",
            "dictionary", "word_stickers",
            "shape_fun", "color_rainbow",
        ],
        "show_captions": [True, True, True],
        "show_word_images": [True, True, True],
    },
    "infographic_explainer": {
        "domain": ["astronomy", "earth_science", "technology", "biology", "all"],
        "hud_density": (0.5, 1.0),
        "schematic_glow": (0.5, 1.0),
        "diagram_speed": (0.6, 1.4),
        "show_radar": [True, True, False],
        "metric_counter_speed": (0.8, 1.5),
    },
}


class Randomizer:
    """Creates reproducible ProjectSpec instances from seeds and config."""

    def __init__(self, config: dict[str, Any]) -> None:
        self.config = config
        self.engines = list(config.get("engines") or list(ENGINE_PARAM_SPECS.keys()))
        self.styles = list(config.get("styles") or list_styles())

    @staticmethod
    def new_seed() -> int:
        return secrets.randbelow(2**31 - 1) + 1

    def create_project(
        self,
        seed: int | None = None,
        *,
        engine: str | None = None,
        style: str | None = None,
        resolution: str | None = None,
        fps: int | None = None,
        duration: float | None = None,
        audio_enabled: bool | None = None,
        thumbnail: bool | None = None,
        random_resolution: bool = False,
        random_fps: bool = False,
        random_duration: bool = False,
    ) -> ProjectSpec:
        seed = int(seed) if seed is not None else self.new_seed()
        rng = np.random.default_rng(seed)

        style_chosen = style is not None
        style_name = style or str(rng.choice(self.styles))
        if engine:
            engine_name = engine
        elif style_chosen:
            preferred = preferred_engines(style_name)
            engine_pool = [e for e in (preferred or self.engines) if e in self.engines] or self.engines
            engine_name = str(rng.choice(engine_pool))
        else:
            visual = [e for e in VISUAL_ART_ENGINES if e in self.engines] or self.engines
            engine_name = str(rng.choice(visual))

        if random_resolution or resolution in (None, "random", "Random"):
            res = str(rng.choice(self.config.get("resolutions", ["1920x1080"])))
        else:
            res = resolution or str(self.config.get("resolution", "1920x1080"))
        width, height = parse_resolution(res)

        if random_fps or fps is None:
            # When explicitly random or omitted with random mode, pick from options
            if random_fps:
                fps_val = int(rng.choice(self.config.get("fps_options", [24, 30, 60])))
            else:
                fps_val = int(self.config.get("fps", 30))
        else:
            fps_val = int(fps)

        dur_cfg = self.config.get("duration", {})
        if random_duration or duration is None:
            if random_duration:
                options = list(dur_cfg.get("options", [10, 15, 30, 60]))
                duration_val = float(rng.choice(options))
            else:
                duration_val = float(dur_cfg.get("default", 30))
        else:
            duration_val = float(duration)

        multipliers = sample_style_multiplier(rng, style_name)
        params = self._sample_engine_params(rng, engine_name, multipliers)
        params["style_multipliers"] = multipliers
        params["blur"] = float(rng.uniform(0.0, 0.6) * multipliers["glow"])
        params["glow"] = multipliers["glow"]
        params["animation_speed"] = multipliers["speed"]
        params["contrast"] = multipliers["contrast"]
        params["_duration"] = duration_val
        params["style"] = style_name
        params.update(_edit_look(rng, engine_name, style_name, seed))

        palette = generate_palette(rng, style_name)

        project_id = f"art_{seed:08d}"
        audio = (
            self.config.get("audio", {}).get("enabled", True)
            if audio_enabled is None
            else audio_enabled
        )
        thumbs = (
            self.config.get("output", {}).get("thumbnail", True)
            if thumbnail is None
            else thumbnail
        )

        return ProjectSpec(
            project_id=project_id,
            seed=seed,
            engine=engine_name,
            style=style_name,
            width=width,
            height=height,
            fps=fps_val,
            duration=duration_val,
            params=params,
            palette_name=palette.name,
            palette_colors=[list(c) for c in palette.colors],
            audio_enabled=bool(audio),
            thumbnail=bool(thumbs),
        )

    def _sample_engine_params(
        self,
        rng: np.random.Generator,
        engine: str,
        multipliers: dict[str, float],
    ) -> dict[str, Any]:
        specs = ENGINE_PARAM_SPECS.get(engine, {})
        params: dict[str, Any] = {}
        density = multipliers.get("density", 0.6)
        speed_m = multipliers.get("speed", 1.0)

        for key, spec in specs.items():
            if isinstance(spec, list):
                choice = rng.choice(np.asarray(spec, dtype=object))
                params[key] = choice.item() if hasattr(choice, "item") else choice
                if isinstance(spec[0], str):
                    params[key] = str(params[key])
                elif isinstance(spec[0], bool):
                    params[key] = bool(params[key])
                continue
            lo, hi = spec
            # Bias density-related counts upward/downward
            if key in {
                "count",
                "star_count",
                "particle_count",
                "shape_count",
                "sites",
                "line_count",
                "rings",
                "layers",
            }:
                mid = lo + (hi - lo) * density
                span = (hi - lo) * 0.25
                value = float(rng.uniform(max(lo, mid - span), min(hi, mid + span)))
            elif key in {"speed", "spin", "zoom_speed", "rotation_speed", "z_speed", "drift"}:
                mid = lo + (hi - lo) * min(1.0, speed_m / 1.5)
                span = (hi - lo) * 0.3
                value = float(rng.uniform(max(lo, mid - span), min(hi, mid + span)))
            else:
                value = float(rng.uniform(lo, hi))

            if isinstance(lo, int) and isinstance(hi, int):
                params[key] = int(round(value))
            else:
                params[key] = value
        return params


KIDS_ENGINES = frozenset({"alphabet_cartoon", "hand_art", "kids_doodles"})


def _edit_look(
    rng: np.random.Generator,
    engine: str,
    style: str,
    seed: int,
) -> dict[str, Any]:
    """Kids engines lock to broadcast; every other pair uses the style's own edit."""
    fx, fy = rule_of_thirds_focus(seed)
    if engine in KIDS_ENGINES:
        look = sample_edit_look(rng, "playful")
        look["focus_x"] = 0.5
        look["focus_y"] = 0.5
        look["camera_push"] = 0.0
        look["grain"] = 0.0
        return look
    look = sample_edit_look(rng, style)
    look["focus_x"] = fx
    look["focus_y"] = fy
    if engine == "infographic_explainer" and style not in {"documentary", "cosmic", "digital"}:
        look["edit_feel"] = "documentary"
    return look
