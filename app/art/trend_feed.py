"""Public RSS headlines for Trending Brief — no HTML scraping."""

from __future__ import annotations

import hashlib
import html
import json
import re
import time
import urllib.error
import urllib.parse
import urllib.request
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any, Callable
from xml.etree import ElementTree as ET

import numpy as np

from app.utils.logger import get_logger
from app.utils.paths import resolve_path

logger = get_logger("art.trend_feed")

USER_AGENT = (
    "GenesisArtvisionEngine/1.0 "
    "(+https://github.com/ansnew-tech/genesis-artvision)"
)

DEFAULT_RSS_URLS = (
    "https://news.google.com/rss?hl=en-US&gl=US&ceid=US:en",
    "https://trends.google.com/trending/rss?geo=US",
    "https://feeds.bbci.co.uk/news/rss.xml",
    "https://feeds.npr.org/1001/rss.xml",
)

_TAG = re.compile(r"<[^>]+>")
_WS = re.compile(r"\s+")
_TITLE_NOISE = re.compile(r"[^a-z0-9]+")

FetchFn = Callable[[str, float], str]
ProgressFn = Callable[[dict[str, Any]], None]


def trend_feed_settings(config: dict[str, Any] | None) -> dict[str, Any]:
    tf = (config or {}).get("trend_feed") or {}
    urls = [str(u).strip() for u in (tf.get("rss_urls") or DEFAULT_RSS_URLS) if str(u).strip()]
    return {
        "enabled": bool(tf.get("enabled", True)),
        "cache_dir": str(tf.get("cache_dir") or "./data/trend_cache"),
        "cache_minutes": float(tf.get("cache_minutes") or 45),
        "timeout_sec": float(tf.get("timeout_sec") or 12),
        "rss_urls": urls or list(DEFAULT_RSS_URLS),
    }


def plain_text(value: Any) -> str:
    text = html.unescape(str(value or ""))
    text = _TAG.sub(" ", text)
    return _WS.sub(" ", text).strip()


def _local_tag(tag: str) -> str:
    return tag.rsplit("}", 1)[-1].lower() if tag else ""


def _child_text(node: ET.Element, *names: str) -> str:
    wanted = {n.lower() for n in names}
    for child in list(node):
        if _local_tag(child.tag) in wanted:
            text = plain_text("".join(child.itertext()))
            if text:
                return text
    return ""


def _link_from(node: ET.Element) -> str:
    for child in list(node):
        if _local_tag(child.tag) != "link":
            continue
        href = (child.attrib.get("href") or child.attrib.get("url") or "").strip()
        if href:
            return href
        text = plain_text("".join(child.itertext()))
        if text.startswith("http"):
            return text
    return ""


def _feed_label(feed_url: str, channel_title: str = "") -> str:
    title = plain_text(channel_title)
    if title:
        return title[:48]
    host = urllib.parse.urlparse(feed_url).netloc.lower()
    host = host.removeprefix("www.").removeprefix("feeds.")
    return host or "Live feed"


def _parse_published(raw: str) -> tuple[str, float]:
    text = plain_text(raw)
    if not text:
        return "", 0.0
    try:
        dt = parsedate_to_datetime(text)
        return dt.isoformat(), float(dt.timestamp())
    except (TypeError, ValueError, OverflowError):
        pass
    try:
        from datetime import datetime

        iso = text.replace("Z", "+00:00")
        dt = datetime.fromisoformat(iso)
        return dt.isoformat(), float(dt.timestamp())
    except (TypeError, ValueError, OverflowError):
        return text, 0.0


def parse_feed(xml_text: str, feed_url: str = "") -> list[dict[str, Any]]:
    """Parse RSS 2.0 or Atom XML into headline dicts. Fail soft on junk."""
    text = (xml_text or "").strip()
    if not text:
        return []
    try:
        root = ET.fromstring(text)
    except ET.ParseError as exc:
        logger.warning("Could not parse feed %s: %s", feed_url, exc)
        return []

    items: list[ET.Element] = []
    channel_title = ""
    for node in root.iter():
        name = _local_tag(node.tag)
        if name in {"item", "entry"}:
            items.append(node)
        elif name in {"channel", "feed"} and not channel_title:
            channel_title = _child_text(node, "title")
    if not channel_title and _local_tag(root.tag) in {"feed", "rss"}:
        channel_title = _child_text(root, "title")

    feed = _feed_label(feed_url, channel_title)
    headlines: list[dict[str, Any]] = []
    for item in items:
        title = _child_text(item, "title")
        if not title:
            continue
        description = _child_text(item, "description", "summary", "content")
        published_raw = _child_text(item, "pubdate", "published", "updated", "date")
        published, stamp = _parse_published(published_raw)
        source = _child_text(item, "source") or feed
        headlines.append(
            {
                "title": title,
                "description": description,
                "url": _link_from(item),
                "published": published,
                "published_ts": stamp,
                "feed": source,
                "feed_url": feed_url,
            }
        )
    return headlines


def fetch_feed_text(url: str, timeout_sec: float) -> str:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept": "application/rss+xml, application/atom+xml, application/xml, text/xml, */*",
        },
        method="GET",
    )
    with urllib.request.urlopen(req, timeout=float(timeout_sec)) as resp:
        return resp.read().decode("utf-8", errors="replace")


def _cache_path(cache_dir: Path, urls: list[str]) -> Path:
    key = hashlib.sha256("|".join(urls).encode("utf-8")).hexdigest()[:16]
    return cache_dir / f"headlines_{key}.json"


def load_cached_headlines(cache_dir: Path, urls: list[str], cache_minutes: float) -> list[dict[str, Any]] | None:
    path = _cache_path(cache_dir, urls)
    if not path.is_file():
        return None
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    fetched_at = float(payload.get("fetched_at") or 0)
    age_min = (time.time() - fetched_at) / 60.0
    if age_min > max(1.0, float(cache_minutes)):
        return None
    rows = payload.get("headlines")
    if not isinstance(rows, list) or not rows:
        return None
    return [row for row in rows if isinstance(row, dict) and row.get("title")]


def save_cached_headlines(cache_dir: Path, urls: list[str], headlines: list[dict[str, Any]]) -> None:
    cache_dir.mkdir(parents=True, exist_ok=True)
    path = _cache_path(cache_dir, urls)
    payload = {"fetched_at": time.time(), "headlines": headlines}
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def collect_headlines(
    config: dict[str, Any] | None,
    *,
    fetch_text: FetchFn | None = None,
) -> list[dict[str, Any]]:
    settings = trend_feed_settings(config)
    urls = list(settings["rss_urls"])
    cache_dir = resolve_path(settings["cache_dir"])
    cached = load_cached_headlines(cache_dir, urls, settings["cache_minutes"])
    if cached:
        return cached

    fetch = fetch_text or fetch_feed_text
    headlines: list[dict[str, Any]] = []
    timeout = float(settings["timeout_sec"])
    for url in urls:
        try:
            xml_text = fetch(url, timeout)
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError, OSError) as exc:
            logger.warning("Trend feed failed %s: %s", url, exc)
            continue
        except Exception as exc:  # noqa: BLE001 — one feed must never abort the rest
            logger.warning("Trend feed failed %s: %s", url, exc)
            continue
        headlines.extend(parse_feed(xml_text, url))

    unique = dedupe_headlines(headlines)
    if unique:
        try:
            save_cached_headlines(cache_dir, urls, unique)
        except OSError as exc:
            logger.warning("Could not cache trend headlines: %s", exc)
    return unique


def norm_title(title: str) -> str:
    return _TITLE_NOISE.sub(" ", (title or "").lower()).strip()


def dedupe_headlines(headlines: list[dict[str, Any]]) -> list[dict[str, Any]]:
    seen: set[str] = set()
    out: list[dict[str, Any]] = []
    for row in headlines:
        key = norm_title(str(row.get("title") or ""))
        if not key or key in seen:
            continue
        seen.add(key)
        out.append(row)
    return out


def pick_story(headlines: list[dict[str, Any]], seed: int, *, pool_size: int = 24) -> dict[str, Any] | None:
    unique = dedupe_headlines(headlines)
    if not unique:
        return None
    ranked = sorted(unique, key=lambda row: float(row.get("published_ts") or 0.0), reverse=True)
    pool = ranked[: max(1, int(pool_size))]
    rng = np.random.default_rng(int(seed))
    return dict(pool[int(rng.integers(0, len(pool)))])


def related_headlines(
    headlines: list[dict[str, Any]],
    chosen: dict[str, Any],
    *,
    limit: int = 3,
) -> list[dict[str, Any]]:
    chosen_title = norm_title(str(chosen.get("title") or ""))
    chosen_words = {w for w in chosen_title.split() if len(w) > 3}
    related: list[dict[str, Any]] = []
    for row in headlines:
        if norm_title(str(row.get("title") or "")) == chosen_title:
            continue
        words = {w for w in norm_title(str(row.get("title") or "")).split() if len(w) > 3}
        if chosen_words and words.intersection(chosen_words):
            related.append(row)
        if len(related) >= limit:
            return related
    if len(related) < limit:
        for row in headlines:
            if norm_title(str(row.get("title") or "")) == chosen_title:
                continue
            if row in related:
                continue
            related.append(row)
            if len(related) >= limit:
                break
    return related


def should_attach_live_trend(spec: Any, config: dict[str, Any] | None) -> bool:
    if getattr(spec, "engine", "") != "trend_brief":
        return False
    params = getattr(spec, "params", None) or {}
    if params.get("_replay_locked"):
        return False
    if str(params.get("user_prompt") or "").strip():
        return False
    existing = params.get("topic_data")
    if isinstance(existing, dict) and existing.get("segments"):
        return False
    return bool(trend_feed_settings(config)["enabled"])


def attach_live_trend(
    spec: Any,
    config: dict[str, Any] | None,
    *,
    on_progress: ProgressFn | None = None,
    fetch_text: FetchFn | None = None,
    headlines: list[dict[str, Any]] | None = None,
) -> bool:
    """Fetch a current headline, summarize it, and store topic_data. Fail soft."""
    if not should_attach_live_trend(spec, config):
        return False

    def _emit(message: str) -> None:
        if not on_progress:
            return
        on_progress(
            {
                "phase": "trend",
                "seed": getattr(spec, "seed", None),
                "engine": getattr(spec, "engine", None),
                "style": getattr(spec, "style", None),
                "message": message,
            }
        )

    _emit("Fetching today's headlines…")
    try:
        pool = list(headlines) if headlines is not None else collect_headlines(config, fetch_text=fetch_text)
        story = pick_story(pool, int(getattr(spec, "seed", 0) or 0))
        if not story:
            logger.info("No live headlines; using catalog fallback")
            return False
        related = related_headlines(pool, story)
        from app.ai.trend_summarize import summarize_live_story

        topic = summarize_live_story(
            story,
            related,
            config or {},
            seed=int(getattr(spec, "seed", 0) or 0),
            duration=float(getattr(spec, "duration", 30.0) or 30.0),
        )
    except Exception as exc:  # noqa: BLE001 — live news must never abort a render
        logger.warning("Live trend attach failed: %s", exc)
        return False

    if not isinstance(topic, dict) or not topic.get("segments"):
        return False

    spec.params["topic_data"] = topic
    spec.params["sources"] = list(topic.get("sources") or [])
    spec.params["live_trend"] = True
    spec.params["live_trend_summary"] = topic.get("summary_mode") or "extractive"
    title = str(topic.get("title") or story.get("title") or "Live brief")
    _emit(f"Briefing: {title}")
    logger.info("Live trend brief: %s", title)
    return True
