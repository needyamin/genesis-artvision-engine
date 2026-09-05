"""Optional AI creative advisor (OpenRouter) — suggestions only; render stays offline."""

from app.ai.advisor import apply_creative_direction, maybe_enrich_spec, suggest_for_spec
from app.ai.schemas import CreativeDirection

__all__ = [
    "CreativeDirection",
    "apply_creative_direction",
    "maybe_enrich_spec",
    "suggest_for_spec",
]
