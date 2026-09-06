"""Art engine base interface and registry."""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any, Type

import numpy as np

from app.art.palette import Palette


class ArtEngine(ABC):
    """Common interface for all procedural art engines."""

    name: str = "base"
    description: str = "Base art engine"
    # False when frame N depends on canvas/state from frame N-1 (cannot paint in parallel).
    parallel_frames: bool = True

    def __init__(self) -> None:
        self.width: int = 1280
        self.height: int = 720
        self.fps: int = 30
        self.seed: int = 0
        self.params: dict[str, Any] = {}
        self.palette: Palette | None = None
        self.rng: np.random.Generator | None = None
        self._ready = False

    def setup(
        self,
        width: int,
        height: int,
        fps: int,
        seed: int,
        params: dict[str, Any],
        palette: Palette,
    ) -> None:
        """Initialize engine state for a render session."""
        self.width = width
        self.height = height
        self.fps = fps
        self.seed = seed
        self.params = dict(params)
        self.palette = palette
        self.rng = np.random.default_rng(seed)
        self._on_setup()
        self._ready = True

    def _on_setup(self) -> None:
        """Optional subclass hook after setup fields are assigned."""

    @abstractmethod
    def render_frame(self, frame_number: int, total_frames: int) -> np.ndarray:
        """Render a single uint8 RGB frame of shape (height, width, 3)."""

    def cleanup(self) -> None:
        """Release resources after rendering."""
        self._ready = False
        self.rng = None

    def _blank(self, color: tuple[float, float, float] | None = None) -> np.ndarray:
        """Create a blank RGB float frame."""
        if color is None and self.palette is not None:
            color = self.palette.colors[0]
        if color is None:
            color = (0.02, 0.02, 0.05)
        frame = np.empty((self.height, self.width, 3), dtype=np.float32)
        frame[..., 0] = color[0]
        frame[..., 1] = color[1]
        frame[..., 2] = color[2]
        return frame

    @staticmethod
    def _to_uint8(frame: np.ndarray) -> np.ndarray:
        return np.clip(frame * 255.0, 0, 255).astype(np.uint8)

    def _color(self, t: float) -> np.ndarray:
        assert self.palette is not None
        return np.asarray(self.palette.sample(t), dtype=np.float32)


_REGISTRY: dict[str, Type[ArtEngine]] = {}


def register_engine(cls: Type[ArtEngine]) -> Type[ArtEngine]:
    """Decorator to register an art engine class by its ``name`` attribute."""
    key = cls.name
    if not key or key == "base":
        raise ValueError(f"Engine {cls} must define a unique name")
    _REGISTRY[key] = cls
    return cls


def get_engine(name: str) -> ArtEngine:
    """Instantiate a registered engine by name."""
    ensure_engines_loaded()
    if name not in _REGISTRY:
        raise KeyError(f"Unknown art engine: {name}. Available: {list(_REGISTRY)}")
    return _REGISTRY[name]()


def list_engines() -> list[str]:
    """Return registered engine names."""
    ensure_engines_loaded()
    return sorted(_REGISTRY.keys())


_LOADED = False


def ensure_engines_loaded() -> None:
    """Import all built-in engines so they register themselves."""
    global _LOADED
    if _LOADED:
        return
    from app.art import (  # noqa: F401
        how_it_works,
        kids_storybook,
        trend_brief,
    )

    _LOADED = True
