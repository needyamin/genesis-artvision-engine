"""SEO title, description, tags, and hashtags from a rendered ProjectSpec.

Metadata is taken from the actual video (title, beats, engine). It is not
clickbait that disagrees with the picture.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

_ENGINE_HASHTAGS = {
    "kids_storybook": ("KidsStory", "BedtimeStory", "StoryForKids", "ChildrensBook", "KidsLearning"),
    "how_it_works": ("HowItWorks", "Explainer", "ScienceExplained", "Education", "STEM"),
    "trend_brief": ("Trending", "Explained", "TodayOnTheInternet", "NewsExplained", "Culture"),
}

_ENGINE_SUFFIX = {
    "kids_storybook": "Bedtime Story for Kids",
    "how_it_works": "How It Works | Easy Explainer",
    "trend_brief": "What's Trending This Week",
}

_STOP = {
    "the", "a", "an", "and", "or", "of", "to", "in", "on", "for", "with", "from",
    "this", "that", "your", "our", "how", "why", "what", "week", "video",
}


@dataclass
class VideoSEO:
    title: str
    description: str
    tags: list[str]
    hashtags: list[str]
    category_id: str
    made_for_kids: bool
    thumbnail_title: str
    extra: dict[str, Any] = field(default_factory=dict)


def _clean_title(text: str, fallback: str) -> str:
    raw = " ".join(str(text or "").split())
    raw = raw.strip(" -|:")
    return (raw or fallback)[:90]


def _topic_title(spec: Any) -> str:
    params = getattr(spec, "params", None) or {}
    lesson = params.get("education_lesson") if isinstance(params, dict) else None
    topic = params.get("topic_data") if isinstance(params, dict) else None
    if isinstance(lesson, dict) and lesson.get("title"):
        return str(lesson["title"])
    if isinstance(topic, dict) and topic.get("title"):
        return str(topic["title"])
    if isinstance(params, dict) and params.get("ai_title"):
        return str(params["ai_title"])
    engine = str(getattr(spec, "engine", "") or "")
    return {
        "kids_storybook": "Kids Picture Book Story",
        "how_it_works": "How Everyday Things Work",
        "trend_brief": "This Week on the Internet",
    }.get(engine, "Original Art Video")


def _beats(spec: Any) -> list[str]:
    params = getattr(spec, "params", None) or {}
    bag = None
    if isinstance(params, dict):
        bag = params.get("education_lesson") or params.get("topic_data")
    segs = list((bag or {}).get("segments") or []) if isinstance(bag, dict) else []
    lines: list[str] = []
    for seg in segs:
        if not isinstance(seg, dict):
            continue
        line = str(
            seg.get("headline")
            or seg.get("overlay_text")
            or seg.get("voice_line")
            or seg.get("caption")
            or ""
        ).strip()
        if line:
            lines.append(line[:80])
    return lines[:8]


def _hashtag_token(word: str) -> str | None:
    token = re.sub(r"[^A-Za-z0-9]", "", word or "")
    if len(token) < 3 or token.lower() in _STOP:
        return None
    if token[:1].isdigit():
        return None
    return token[:24]


def build_video_seo(spec: Any) -> VideoSEO:
    """Build YouTube snippet fields from the finished project."""
    engine = str(getattr(spec, "engine", "") or "trend_brief")
    topic = _clean_title(_topic_title(spec), "Original Video")
    suffix = _ENGINE_SUFFIX.get(engine, "Original Video")
    if engine == "how_it_works" and not topic.lower().startswith("how"):
        title = f"How {topic} Works | Easy Explainer"
    elif engine == "kids_storybook":
        title = f"{topic} | {suffix}"
    else:
        title = f"{topic} | {suffix}"
    title = title[:100]

    beats = _beats(spec)
    hook = beats[0] if beats else f"A short original video: {topic}."
    bullets = "\n".join(f"• {line}" for line in beats[:6]) or f"• {topic}"

    base_tags = list(_ENGINE_HASHTAGS.get(engine, ("Original", "ArtVideo")))
    extra: list[str] = []
    for word in re.findall(r"[A-Za-z][A-Za-z0-9']{2,}", f"{topic} {' '.join(beats)}"):
        token = _hashtag_token(word)
        if token and token not in extra and token not in base_tags:
            extra.append(token)
        if len(extra) >= 8:
            break
    hashtags = [f"#{t}" for t in (base_tags + extra)[:12]]
    tags = (base_tags + extra + ["Genesis Artvision", "ANSNEW TECH"])[:20]

    kids = engine == "kids_storybook"
    audience = (
        "Made for children. Slow picture-book pages with matching voice."
        if kids
        else "Short educational explainer. Original pictures drawn on this machine."
    )
    prompt = ""
    params = getattr(spec, "params", None) or {}
    if isinstance(params, dict) and params.get("user_prompt"):
        prompt = f"Prompt: {str(params['user_prompt']).strip()[:240]}\n\n"

    description = (
        f"{hook}\n\n"
        f"{audience}\n\n"
        f"{prompt}"
        f"In this video:\n{bullets}\n\n"
        f"{' '.join(hashtags)}\n\n"
        "Created locally with Genesis Artvision Engine by ANSNEW TECH."
    )[:4900]

    category = "27" if engine in {"kids_storybook", "how_it_works"} else "24"
    thumb = topic[:42]
    return VideoSEO(
        title=title,
        description=description,
        tags=tags,
        hashtags=hashtags,
        category_id=category,
        made_for_kids=kids,
        thumbnail_title=thumb,
        extra={"topic": topic, "engine": engine},
    )
