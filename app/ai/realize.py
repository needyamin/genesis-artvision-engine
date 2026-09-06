"""Turn AI visual-beat suggestions into offline images + on-screen text assets."""

from __future__ import annotations

from typing import Any, Callable

from app.core.randomizer import KIDS_ENGINES
from app.art.offline_illustrator import ensure_brief_image, parse_image_brief
from app.utils.logger import get_logger

logger = get_logger("ai.realize")

ProgressFn = Callable[[dict[str, Any]], None]


def _emit(on_progress: ProgressFn | None, payload: dict[str, Any]) -> None:
    if on_progress:
        on_progress(payload)


def _beats_from_spec(spec: Any) -> list[dict[str, Any]]:
    params = spec.params or {}
    lesson = params.get("education_lesson")
    if isinstance(lesson, dict) and lesson.get("segments"):
        return lesson["segments"]
    beats = params.get("ai_visual_beats") or params.get("ai_segment_plan") or []
    if isinstance(beats, list) and beats:
        return [dict(b) for b in beats if isinstance(b, dict)]
    words = [str(w) for w in (params.get("focus_words") or []) if str(w).strip()]
    lines = [str(v) for v in (params.get("ai_voice_lines") or []) if str(v).strip()]
    n = max(len(words), len(lines), 0)
    if n <= 0:
        return []
    out: list[dict[str, Any]] = []
    for i in range(n):
        word = words[i % len(words)] if words else "STAR"
        line = lines[i % len(lines)] if lines else f"Look at the {word.lower()}"
        out.append(
            {
                "word": word,
                "overlay_text": line[:48],
                "image_brief": f"a friendly {word.lower()} in bright colors",
            }
        )
    return out


def _merge_beat_into_segment(seg: dict[str, Any], beat: dict[str, Any]) -> None:
    """Kids lessons keep letter/word/voice. AI may only add a matching picture brief."""
    word = str(seg.get("word") or beat.get("word") or "").strip()
    brief = str(beat.get("image_brief") or beat.get("image") or "").strip()
    if brief:
        token = "".join(ch for ch in word.lower() if ch.isalpha())
        blob = brief.lower().replace("-", "")
        if not token or token in brief.lower().replace("-", " ") or token in blob:
            seg["image_brief"] = brief
        elif word:
            seg["image_brief"] = f"a friendly {word.lower()} kids can recognize"
    # Never copy letter, word, voice_line, overlay_text, fact, or motif from AI
    # into an already-built kids segment — those mismatches are what kids see/hear.


def realize_visual_assets(
    spec: Any,
    *,
    on_progress: ProgressFn | None = None,
) -> Any:
    """
    Draw offline images and lock on-screen text from AI suggestions.

    Runs on the worker thread. Emits per-beat GUI progress; does not block Qt.
    """
    params = spec.params or {}
    if getattr(spec, "engine", "") not in KIDS_ENGINES:
        return spec
    if not (
        params.get("ai_applied")
        or params.get("ai_visual_beats")
        or params.get("ai_segment_plan")
        or (isinstance(params.get("education_lesson"), dict) and params["education_lesson"].get("segments"))
    ):
        return spec
    lesson = params.get("education_lesson")
    planned = [dict(b) for b in (params.get("ai_visual_beats") or params.get("ai_segment_plan") or []) if isinstance(b, dict)]
    items = _beats_from_spec(spec)
    if planned:
        for i, seg in enumerate(items):
            if i < len(planned):
                _merge_beat_into_segment(seg, planned[i])

    if not items:
        return spec

    _emit(
        on_progress,
        {
            "phase": "ai",
            "ai_status": "realize",
            "seed": spec.seed,
            "engine": spec.engine,
            "style": spec.style,
            "message": f"Offline illustrator drawing {len(items)} suggested image(s) and titles…",
            "detail": f"Offline illustrator: {len(items)} beats (image + text).",
        },
    )

    realized: list[dict[str, Any]] = []
    log_lines = ["AI suggestions → offline images & text:"]
    for i, item in enumerate(items):
        word = str(item.get("word") or item.get("motif") or "").strip() or "STAR"
        brief = str(item.get("image_brief") or "").strip() or f"a friendly {word.lower()} in bright colors"
        overlay = str(item.get("overlay_text") or item.get("line") or item.get("title") or "").strip()
        caption = str(item.get("caption") or item.get("fact") or "").strip()
        kids_lesson = isinstance(lesson, dict) and lesson.get("segments") is items
        if kids_lesson:
            parsed = parse_image_brief(brief, fallback_word=word)
            if parsed.get("subject") and word and parsed["subject"] != word.upper().split()[0]:
                brief = f"a friendly {word.lower()} kids can recognize"
            if not overlay:
                overlay = word.upper()[:18] if word else parsed["label"].title()
        else:
            parsed = parse_image_brief(brief, fallback_word=word)
            if not overlay:
                overlay = parsed["label"].title()

        _emit(
            on_progress,
            {
                "phase": "ai",
                "ai_status": "image",
                "seed": spec.seed,
                "engine": spec.engine,
                "style": spec.style,
                "message": f"Drawing image {i + 1}/{len(items)}: {brief}",
                "detail": f"Image {i + 1}: {brief}",
            },
        )
        path = ensure_brief_image(
            brief,
            word=word,
            seed=int(spec.seed) + i * 17,
            label=(word[:18] if kids_lesson and word else overlay[:18]) or word,
        )
        item["image_brief"] = brief
        item["image_path"] = str(path)
        if not kids_lesson:
            item["overlay_text"] = overlay[:48]
            if caption:
                item["caption"] = caption[:72]
            if overlay and not item.get("line"):
                item["line"] = overlay
        elif word:
            item["image_brief"] = brief

        _emit(
            on_progress,
            {
                "phase": "ai",
                "ai_status": "text",
                "seed": spec.seed,
                "engine": spec.engine,
                "style": spec.style,
                "message": f"On-screen text {i + 1}/{len(items)}: {overlay}",
                "detail": f"Text {i + 1}: {overlay}" + (f" — {caption}" if caption else ""),
            },
        )
        log_lines.append(f"{i + 1}. IMAGE: {brief}")
        log_lines.append(f"    TEXT: {overlay}" + (f" / {caption}" if caption else ""))
        realized.append(dict(item))

    params["ai_visual_beats"] = realized
    params["ai_assets_ready"] = True
    if isinstance(lesson, dict) and lesson.get("segments") is items:
        params["education_lesson"] = lesson
    title = str(params.get("ai_title") or (realized[0].get("title") if realized else "") or "").strip()
    if title:
        params["ai_title"] = title
    summary = params.get("ai_summary") or "AI applied."
    params["ai_summary"] = str(summary).rstrip() + "\n" + "\n".join(log_lines[:20])

    _emit(
        on_progress,
        {
            "phase": "ai",
            "ai_status": "applied",
            "seed": spec.seed,
            "engine": spec.engine,
            "style": spec.style,
            "message": "AI images and text are ready for this video.",
            "detail": params["ai_summary"],
        },
    )
    logger.info("Realized %s offline scene(s) for seed=%s", len(realized), spec.seed)
    return spec
