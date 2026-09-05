"""Core package."""

from app.core.randomizer import ProjectSpec, Randomizer

__all__ = ["ProjectSpec", "Randomizer", "GenerateResult", "VideoFactory"]


def __getattr__(name: str):
    if name in {"GenerateResult", "VideoFactory"}:
        from app.core.generator import GenerateResult, VideoFactory

        return {"GenerateResult": GenerateResult, "VideoFactory": VideoFactory}[name]
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
