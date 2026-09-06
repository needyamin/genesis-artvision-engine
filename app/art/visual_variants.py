"""Deterministic visual-variant selection and replay-safe resolution.

New projects should call :func:`select_visual_variants` and persist the
returned values. Engines replaying a stored project should call
:func:`resolve_visual_variants`; missing fields intentionally resolve to the
classic look rather than being re-randomized.
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from typing import Any, Mapping


VISUAL_VARIANT_VERSION = 1

BACKGROUND_VARIANTS: dict[str, tuple[str, ...]] = {
    "kids_storybook": (
        "desk_stack",
        "cozy_corner",
        "window_day",
        "craft_mat",
        "night_lamp",
        "open_spread",
    ),
    "how_it_works": (
        "whiteboard",
        "chalkboard",
        "poster_wall",
        "worksheet",
        "lab_bench",
        "projection",
    ),
    "trend_brief": (
        "neon_ridge",
        "grid_pulse",
        "aurora_bands",
        "static_fizz",
        "mesh_glow",
        "radar_sweep",
    ),
}

LAYOUT_VARIANTS: dict[str, tuple[str, ...]] = {
    "kids_storybook": ("classic_split", "picture_first", "hero_center"),
    "how_it_works": ("split_right", "split_left", "stacked", "diagram_focus"),
    "trend_brief": ("broadcast", "card_emphasis", "full_bleed"),
}

CLASSIC_BACKGROUND_VARIANTS: dict[str, str] = {
    "kids_storybook": "desk_stack",
    "how_it_works": "whiteboard",
    "trend_brief": "neon_ridge",
}

CLASSIC_LAYOUT_VARIANTS: dict[str, str] = {
    "kids_storybook": "classic_split",
    "how_it_works": "split_right",
    "trend_brief": "broadcast",
}


@dataclass(frozen=True)
class VisualVariantSelection:
    """A complete visual selection suitable for storing in ``params``."""

    background_variant: str
    layout_variant: str
    visual_variant_version: int = VISUAL_VARIANT_VERSION

    def to_params(self) -> dict[str, str | int]:
        return {
            "background_variant": self.background_variant,
            "layout_variant": self.layout_variant,
            "visual_variant_version": self.visual_variant_version,
        }


def background_variants(engine: str) -> tuple[str, ...]:
    """Return the registered background names for an engine."""
    return _registry_for(BACKGROUND_VARIANTS, engine, "background")


def layout_variants(engine: str) -> tuple[str, ...]:
    """Return the registered layout names for an engine."""
    return _registry_for(LAYOUT_VARIANTS, engine, "layout")


def validate_variant_name(engine: str, kind: str, name: str) -> str:
    """Validate and return one background or layout variant name."""
    registries = {"background": BACKGROUND_VARIANTS, "layout": LAYOUT_VARIANTS}
    if kind not in registries:
        raise ValueError(f"Unknown visual variant kind: {kind}")
    choices = _registry_for(registries[kind], engine, kind)
    value = str(name).strip()
    if value not in choices:
        raise ValueError(
            f"Unknown {kind} variant for {engine}: {value}. "
            f"Expected one of: {', '.join(choices)}"
        )
    return value


def select_visual_variants(
    engine: str,
    seed: int,
    visual_variation: Mapping[str, Any] | None = None,
    *,
    background_variant: str | None = None,
    layout_variant: str | None = None,
) -> VisualVariantSelection:
    """Select variants for a new project using stable, independent salts.

    Explicit names override configuration and seeded selection. If visual
    variation is disabled, unspecified values use the classic variants.
    """
    config = visual_variation or {}
    enabled = bool(config.get("enabled", True))
    version = int(config.get("version", VISUAL_VARIANT_VERSION))

    background = _select_kind(
        engine,
        int(seed),
        "background",
        background_variants(engine),
        CLASSIC_BACKGROUND_VARIANTS[engine],
        config,
        enabled,
        background_variant,
        version,
    )
    layout = _select_kind(
        engine,
        int(seed),
        "layout",
        layout_variants(engine),
        CLASSIC_LAYOUT_VARIANTS[engine],
        config,
        enabled,
        layout_variant,
        version,
    )
    return VisualVariantSelection(background, layout, version)


def resolve_visual_variants(
    engine: str,
    params: Mapping[str, Any] | None,
) -> VisualVariantSelection:
    """Resolve persisted engine params without randomizing legacy projects.

    ``board`` remains a legacy alias for How It Works whiteboard/chalkboard.
    An explicit ``background_variant`` always takes precedence over the alias.
    """
    values = params or {}
    background = values.get("background_variant")
    if background is None and engine == "how_it_works":
        board = str(values.get("board") or "").strip()
        if board in {"whiteboard", "chalkboard"}:
            background = board
    if background is None:
        background = CLASSIC_BACKGROUND_VARIANTS[engine]

    layout = values.get("layout_variant")
    if layout is None:
        layout = CLASSIC_LAYOUT_VARIANTS[engine]

    version_value = values.get("visual_variant_version")
    version = 0 if version_value is None else int(version_value)
    return VisualVariantSelection(
        validate_variant_name(engine, "background", str(background)),
        validate_variant_name(engine, "layout", str(layout)),
        version,
    )


def _registry_for(
    registry: Mapping[str, tuple[str, ...]],
    engine: str,
    kind: str,
) -> tuple[str, ...]:
    try:
        return registry[engine]
    except KeyError as exc:
        raise ValueError(f"Unknown engine for visual {kind} variants: {engine}") from exc


def _select_kind(
    engine: str,
    seed: int,
    kind: str,
    registered: tuple[str, ...],
    classic: str,
    config: Mapping[str, Any],
    enabled: bool,
    explicit: str | None,
    version: int,
) -> str:
    if explicit is not None:
        return validate_variant_name(engine, kind, explicit)
    if not enabled:
        return classic

    section_name = "backgrounds" if kind == "background" else "layouts"
    section = config.get(section_name) or {}
    configured = section.get(engine) if isinstance(section, Mapping) else None
    weighted = _configured_weights(registered, configured)
    return _salted_weighted_choice(
        weighted,
        seed=seed,
        salt=f"visual-variant-v{version}:{engine}:{kind}",
    )


def _configured_weights(
    registered: tuple[str, ...],
    configured: Any,
) -> tuple[tuple[str, float], ...]:
    if configured is None:
        return tuple((name, 1.0) for name in registered)
    if not isinstance(configured, Mapping):
        raise ValueError("Visual variant weights must be a name-to-weight mapping")

    unknown = set(configured).difference(registered)
    if unknown:
        raise ValueError(f"Unknown visual variants: {', '.join(sorted(map(str, unknown)))}")
    weighted = tuple((name, float(configured.get(name, 0.0))) for name in registered)
    if any(weight < 0 for _, weight in weighted):
        raise ValueError("Visual variant weights must be non-negative")
    if not any(weight > 0 for _, weight in weighted):
        raise ValueError("At least one visual variant weight must be positive")
    return weighted


def _salted_weighted_choice(
    weighted: tuple[tuple[str, float], ...],
    *,
    seed: int,
    salt: str,
) -> str:
    digest = hashlib.blake2b(
        f"{seed}:{salt}".encode("utf-8"),
        digest_size=8,
        person=b"art-variant",
    ).digest()
    unit = int.from_bytes(digest, "big") / float(1 << 64)
    total = sum(weight for _, weight in weighted)
    target = unit * total
    cumulative = 0.0
    for name, weight in weighted:
        cumulative += weight
        if target < cumulative:
            return name
    return weighted[-1][0]
