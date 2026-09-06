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

# Engine owns the concept. Default style is the matching look for that concept.
ENGINE_DEFAULT_STYLE = {
    "kids_storybook": "storybook",
    "how_it_works": "classroom",
    "trend_brief": "pulse",
}


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

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectSpec":
        """Restore the complete stored specification for an exact history replay."""
        required = {"project_id", "seed", "engine", "style", "width", "height", "fps", "duration"}
        missing = required.difference(data)
        if missing:
            raise ValueError(f"Stored project is missing: {', '.join(sorted(missing))}")
        return cls(
            project_id=str(data["project_id"]),
            seed=int(data["seed"]),
            engine=str(data["engine"]),
            style=str(data["style"]),
            width=int(data["width"]),
            height=int(data["height"]),
            fps=int(data["fps"]),
            duration=float(data["duration"]),
            params=dict(data.get("params") or {}),
            palette_name=str(data.get("palette_name") or ""),
            palette_colors=[list(c) for c in (data.get("palette_colors") or [])],
            audio_enabled=bool(data.get("audio_enabled", True)),
            thumbnail=bool(data.get("thumbnail", True)),
        )


# Per-engine parameter ranges (min, max) or discrete choices
ENGINE_PARAM_SPECS: dict[str, dict[str, Any]] = {
    "kids_storybook": {
        "show_word_images": [True, True, True],
        "paper_warmth": (0.35, 0.90),
        "page_turn": (0.4, 1.0),
    },
    "how_it_works": {
        "board": ["whiteboard", "whiteboard", "chalkboard"],
        "diagram_speed": (0.5, 1.4),
    },
    "trend_brief": {
        "energy": (0.55, 1.20),
        "ticker_speed": (0.45, 1.40),
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
        edit_preset: str | None = None,
        caption_mode: str | None = None,
        edit_intensity: float | None = None,
    ) -> ProjectSpec:
        seed = int(seed) if seed is not None else self.new_seed()
        rng = np.random.default_rng(seed)

        style_chosen = style is not None
        engine_chosen = engine is not None

        if engine_chosen and style_chosen:
            engine_name = engine
            style_name = style
        elif engine_chosen:
            engine_name = engine
            style_name = ENGINE_DEFAULT_STYLE.get(engine_name) or str(rng.choice(self.styles))
        elif style_chosen:
            style_name = style
            preferred = preferred_engines(style_name)
            engine_pool = [e for e in (preferred or self.engines) if e in self.engines] or self.engines
            engine_name = str(rng.choice(engine_pool))
        else:
            engine_name = str(rng.choice(self.engines))
            style_name = ENGINE_DEFAULT_STYLE.get(engine_name) or str(rng.choice(self.styles))

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
        editing = self.config.get("editing") or {}
        preset_name = str(edit_preset or editing.get("default_preset") or "standard")
        preset = dict((editing.get("presets") or {}).get(preset_name) or {})
        chosen_intensity = preset.get("motion_scale", 1.0) if edit_intensity is None else edit_intensity
        motion_scale = max(0.25, min(2.0, float(chosen_intensity)))
        params["edit_preset"] = preset_name
        params["render_quality"] = str(preset.get("quality") or "standard")
        preset_caption = preset.get("caption_mode")
        if preset_caption is None:
            preset_caption = "sidecar" if bool(preset.get("captions", True)) else "off"
        selected_caption = str(caption_mode or preset_caption).strip().lower()
        if selected_caption not in {"off", "sidecar", "burn", "both"}:
            selected_caption = "sidecar"
        params["caption_mode"] = selected_caption
        params["motion_scale"] = motion_scale
        for key in ("camera_push", "animation_speed", "diagram_speed", "ticker_speed"):
            if key in params:
                params[key] = float(params[key]) * motion_scale

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
        del multipliers

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
            value = float(rng.uniform(lo, hi))

            if isinstance(lo, int) and isinstance(hi, int):
                params[key] = int(round(value))
            else:
                params[key] = value
        return params


KIDS_ENGINES = frozenset({"kids_storybook"})
TOPIC_BRIEF_ENGINES = frozenset({"how_it_works", "trend_brief"})


def _edit_look(
    rng: np.random.Generator,
    engine: str,
    style: str,
    seed: int,
) -> dict[str, Any]:
    """Kids storybook uses the storybook edit; topic engines use the chosen style."""
    fx, fy = rule_of_thirds_focus(seed)
    if engine in KIDS_ENGINES:
        look = sample_edit_look(rng, "storybook")
        look["focus_x"] = 0.5
        look["focus_y"] = 0.5
        look["camera_push"] = 0.0
        look["grain"] = 0.0
        return look
    look = sample_edit_look(rng, style)
    look["focus_x"] = fx
    look["focus_y"] = fy
    if engine == "how_it_works" and style != "classroom":
        look["edit_feel"] = "documentary"
    return look
