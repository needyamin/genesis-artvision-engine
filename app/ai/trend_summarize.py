"""Turn a live RSS story into a short HOOK / WHY / CATCH / NEXT brief."""

from __future__ import annotations

import re
from typing import Any

from app.ai.client import chat_completion, has_api_key
from app.ai.schemas import extract_json_object
from app.art.trend_content import _timed_segments, _topic_dict
from app.utils.logger import get_logger

logger = get_logger("ai.trend_summarize")

PHASES = ("HOOK", "WHY", "CATCH", "NEXT")

_SENTENCE_SPLIT = re.compile(r"(?<=[.!?])\s+")
_SLUG = re.compile(r"[^a-z0-9]+")

SYSTEM_LIVE_BRIEF = """You brief a kinetic news video from RSS headlines only.
Return ONLY a JSON object. No markdown.
Use ONLY facts present in the provided headlines and descriptions.
Do not invent events, numbers, quotes, people, or outcomes.
Write a short easy brief a viewer can follow in about 20 seconds.
Each voice_line is 12 to 18 words. Each caption is one sentence.
Phases must be HOOK, WHY, CATCH, NEXT in that order.
JSON keys: title, fun_facts (hook first), voice_lines, metrics [{label, val, unit}],
visual_beats [{phase, overlay_text, caption, fact, voice_line}]."""


def _clip_words(text: str, limit: int) -> str:
    words = [w for w in (text or "").split() if w]
    if len(words) <= limit:
        return " ".join(words)
    clipped = " ".join(words[:limit]).rstrip(".,;:")
    return clipped + "."


def _sentences(text: str) -> list[str]:
    clean = " ".join((text or "").split())
    if not clean:
        return []
    parts = [p.strip() for p in _SENTENCE_SPLIT.split(clean) if p.strip()]
    return parts or [clean]


def _short_title(title: str) -> str:
    text = " ".join((title or "").split())
    if " - " in text and len(text) > 52:
        text = text.rsplit(" - ", 1)[0].strip()
    return text[:72] or "Trending Now"


def _slug(title: str) -> str:
    slug = _SLUG.sub("_", (title or "trend").lower()).strip("_")
    return (slug[:40] or "trend").strip("_")


def _when_chip(story: dict[str, Any]) -> str:
    published = str(story.get("published") or "")
    if not published:
        return "today"
    if "T" in published:
        return published.split("T", 1)[0]
    return published[:16] or "today"


def extractive_segments(story: dict[str, Any]) -> list[dict[str, str]]:
    title = _short_title(str(story.get("title") or "Trending Now"))
    sentences = _sentences(str(story.get("description") or ""))
    first = sentences[0] if sentences else title
    second = sentences[1] if len(sentences) > 1 else ""
    feed = str(story.get("feed") or "the live feed")
    hook_body = first if first != title else f"{title} is on the live news feed."
    why_body = f"{feed} is circulating this headline right now."
    catch_body = second or "Public headlines only give the first facts. Details can still shift."
    next_body = "Follow the source as this story develops."
    return [
        {
            "phase": "HOOK",
            "headline": title,
            "body": hook_body,
            "data_point": "Live",
            "voice_line": _clip_words(f"{title}. {first}" if first != title else title, 18),
        },
        {
            "phase": "WHY",
            "headline": "Why it is circulating",
            "body": why_body,
            "data_point": feed[:24] or "Feed",
            "voice_line": _clip_words(f"It is circulating now because {feed} put it on the live feed.", 18),
        },
        {
            "phase": "CATCH",
            "headline": "What we know",
            "body": catch_body,
            "data_point": "Early facts",
            "voice_line": _clip_words(catch_body, 18),
        },
        {
            "phase": "NEXT",
            "headline": "What to watch",
            "body": next_body,
            "data_point": "Updates",
            "voice_line": "Watch the source for updates as the story develops.",
        },
    ]


def extractive_brief(
    story: dict[str, Any],
    related: list[dict[str, Any]] | None,
    *,
    seed: int,
    duration: float,
) -> dict[str, Any]:
    title = _short_title(str(story.get("title") or "Trending Now"))
    sentences = _sentences(str(story.get("description") or ""))
    hook = sentences[0] if sentences else title
    feed = str(story.get("feed") or "Live feed")
    topic = _topic_dict(
        {
            "id": f"live_{_slug(title)}",
            "title": title,
            "subtitle": f"Live brief · {feed[:28]}",
            "domain": "culture",
            "domain_label": "TRENDING NOW",
            "hook": hook,
            "schematic_type": "ticker",
            "metrics": [
                {"label": "Source", "val": feed[:20] or "RSS", "unit": "live RSS"},
                {"label": "When", "val": _when_chip(story), "unit": "published"},
            ],
        },
        seed,
        duration,
        _timed_segments(extractive_segments(story)),
    )
    return _stamp_live(topic, story, related, mode="extractive")


def _stamp_live(
    topic: dict[str, Any],
    story: dict[str, Any],
    related: list[dict[str, Any]] | None,
    *,
    mode: str,
) -> dict[str, Any]:
    sources = [_source_row(story)]
    for row in related or []:
        item = _source_row(row)
        if item["url"] and item["url"] in {s.get("url") for s in sources}:
            continue
        if item["title"] and item["title"] in {s.get("title") for s in sources}:
            continue
        sources.append(item)
        if len(sources) >= 4:
            break
    topic["live"] = True
    topic["summary_mode"] = mode
    topic["sources"] = sources
    return topic


def _source_row(row: dict[str, Any]) -> dict[str, str]:
    return {
        "title": str(row.get("title") or ""),
        "url": str(row.get("url") or ""),
        "published": str(row.get("published") or ""),
        "feed": str(row.get("feed") or ""),
    }


def _story_block(story: dict[str, Any], label: str) -> str:
    bits = [f"{label}: {story.get('title') or ''}"]
    if story.get("description"):
        bits.append(f"Description: {story.get('description')}")
    if story.get("feed"):
        bits.append(f"Feed: {story.get('feed')}")
    if story.get("published"):
        bits.append(f"Published: {story.get('published')}")
    if story.get("url"):
        bits.append(f"URL: {story.get('url')}")
    return "\n".join(bits)


def _ai_user_prompt(story: dict[str, Any], related: list[dict[str, Any]]) -> str:
    lines = [
        "Write a 4-beat kinetic brief from this live RSS story.",
        "Do not add facts that are not in the text below.",
        "",
        _story_block(story, "CHOSEN STORY"),
    ]
    if related:
        lines.append("")
        lines.append("Related headlines for context only:")
        for i, row in enumerate(related[:3], start=1):
            lines.append(_story_block(row, f"RELATED {i}"))
    return "\n".join(lines)


def _beats_from_ai(data: dict[str, Any], voices: list[str]) -> list[dict[str, str]]:
    raw: list[dict[str, str]] = []
    beats = data.get("visual_beats") or data.get("segment_plan") or []
    if isinstance(beats, list):
        for i, beat in enumerate(beats):
            if not isinstance(beat, dict):
                continue
            raw.append(
                {
                    "phase": str(beat.get("phase") or PHASES[min(i, 3)]),
                    "headline": str(beat.get("overlay_text") or beat.get("headline") or beat.get("title") or ""),
                    "body": str(beat.get("caption") or beat.get("body") or ""),
                    "data_point": str(beat.get("fact") or beat.get("data_point") or ""),
                    "voice_line": str(beat.get("voice_line") or (voices[i] if i < len(voices) else "")),
                }
            )
    return raw


def _merge_phases(ai_raw: list[dict[str, str]], fallback: list[dict[str, str]]) -> list[dict[str, str]]:
    by_phase = {str(row.get("phase") or "").upper(): row for row in ai_raw if row.get("headline") or row.get("body")}
    merged: list[dict[str, str]] = []
    for phase, default in zip(PHASES, fallback):
        chosen = by_phase.get(phase) or default
        merged.append(
            {
                "phase": phase,
                "headline": str(chosen.get("headline") or default["headline"]),
                "body": str(chosen.get("body") or default["body"]),
                "data_point": str(chosen.get("data_point") or default["data_point"]),
                "voice_line": str(chosen.get("voice_line") or default["voice_line"]),
            }
        )
    return merged


def _brief_from_ai(
    data: dict[str, Any],
    story: dict[str, Any],
    related: list[dict[str, Any]],
    *,
    seed: int,
    duration: float,
) -> dict[str, Any] | None:
    title = _short_title(str(data.get("title") or story.get("title") or "Trending Now"))
    facts = [str(f) for f in (data.get("fun_facts") or []) if str(f).strip()]
    voices = [str(v) for v in (data.get("voice_lines") or []) if str(v).strip()]
    fallback = extractive_segments(story)
    segments = _merge_phases(_beats_from_ai(data, voices), fallback)
    if not any(seg.get("headline") for seg in segments):
        return None
    feed = str(story.get("feed") or "Live feed")
    metrics = data.get("metrics") if isinstance(data.get("metrics"), list) else []
    if not metrics:
        metrics = [
            {"label": "Source", "val": feed[:20] or "RSS", "unit": "live RSS"},
            {"label": "When", "val": _when_chip(story), "unit": "published"},
        ]
    topic = _topic_dict(
        {
            "id": f"live_{_slug(title)}",
            "title": title,
            "subtitle": f"Live brief · {feed[:28]}",
            "domain": "culture",
            "domain_label": "TRENDING NOW",
            "hook": facts[0] if facts else str(story.get("description") or title),
            "schematic_type": "ticker",
            "metrics": metrics,
        },
        seed,
        duration,
        _timed_segments(segments),
    )
    return _stamp_live(topic, story, related, mode="openrouter")


def summarize_live_story(
    story: dict[str, Any],
    related: list[dict[str, Any]] | None,
    config: dict[str, Any],
    *,
    seed: int,
    duration: float,
) -> dict[str, Any]:
    """Prefer OpenRouter wording when a key is set; always have an extractive fallback."""
    related = list(related or [])
    if has_api_key(config):
        try:
            raw = chat_completion(
                messages=[
                    {"role": "system", "content": SYSTEM_LIVE_BRIEF},
                    {"role": "user", "content": _ai_user_prompt(story, related)},
                ],
                config=config,
                temperature=0.2,
            )
            data = extract_json_object(raw)
            topic = _brief_from_ai(data, story, related, seed=seed, duration=duration)
            if topic:
                return topic
        except Exception as exc:  # noqa: BLE001 — wording polish must never abort a render
            logger.warning("Live trend AI summary failed; using extractive brief: %s", exc)
    return extractive_brief(story, related, seed=seed, duration=duration)
