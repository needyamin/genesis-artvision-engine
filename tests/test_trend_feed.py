"""Offline tests for live Trending Brief RSS + summary (no network)."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from app.ai.trend_summarize import extractive_brief, summarize_live_story
from app.art.trend_feed import (
    attach_live_trend,
    collect_headlines,
    parse_feed,
    pick_story,
    should_attach_live_trend,
)
from app.core.randomizer import ProjectSpec
from app.utils.paths import ensure_directories
from app.utils.validation import load_config

RSS_XML = """<?xml version="1.0"?>
<rss version="2.0">
  <channel>
    <title>BBC News</title>
    <item>
      <title>Storm hits coast</title>
      <link>https://example.com/storm</link>
      <description>High winds closed roads &lt;b&gt;overnight&lt;/b&gt;. Ferries stayed in port.</description>
      <pubDate>Sun, 06 Sep 2026 12:00:00 GMT</pubDate>
    </item>
    <item>
      <title>City opens new park</title>
      <link>https://example.com/park</link>
      <description>Families filled the lawn after the ribbon cutting.</description>
      <pubDate>Sun, 06 Sep 2026 11:00:00 GMT</pubDate>
    </item>
  </channel>
</rss>
"""

ATOM_XML = """<?xml version="1.0"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Example Feed</title>
  <entry>
    <title>Atom headline</title>
    <link href="https://example.com/atom"/>
    <updated>2026-09-07T01:00:00Z</updated>
    <summary>Atom summary text about the story.</summary>
  </entry>
</feed>
"""

STORY = {
    "title": "Storm hits coast",
    "description": "High winds closed roads overnight. Ferries stayed in port.",
    "url": "https://example.com/storm",
    "published": "2026-09-06T12:00:00+00:00",
    "published_ts": 1757160000.0,
    "feed": "BBC News",
    "feed_url": "https://feeds.bbci.co.uk/news/rss.xml",
}


def _spec(**params) -> ProjectSpec:
    return ProjectSpec(
        project_id="test",
        seed=11,
        engine="trend_brief",
        style="pulse",
        width=320,
        height=180,
        fps=10,
        duration=12.0,
        params=dict(params),
    )


def _cfg(tmp_path: Path, **overrides) -> dict:
    config = load_config()
    tf = dict(config.get("trend_feed") or {})
    tf["cache_dir"] = str(tmp_path / "trend_cache")
    tf["rss_urls"] = [
        "https://example.com/news.xml",
        "https://example.com/viral.xml",
    ]
    tf.update(overrides)
    config["trend_feed"] = tf
    return config


def test_parse_rss_and_atom_and_strips_html():
    rss = parse_feed(RSS_XML, "https://feeds.bbci.co.uk/news/rss.xml")
    assert len(rss) == 2
    assert rss[0]["title"] == "Storm hits coast"
    assert rss[0]["url"] == "https://example.com/storm"
    assert "overnight" in rss[0]["description"]
    assert "<b>" not in rss[0]["description"]
    assert rss[0]["feed"] == "BBC News"
    assert rss[0]["published_ts"] > 0

    atom = parse_feed(ATOM_XML, "https://example.com/atom.xml")
    assert atom[0]["title"] == "Atom headline"
    assert atom[0]["url"] == "https://example.com/atom"
    assert "Atom summary" in atom[0]["description"]


def test_parse_feed_fails_soft_on_junk():
    assert parse_feed("not xml", "https://example.com") == []
    assert parse_feed("", "") == []


def test_collect_headlines_uses_cache(tmp_path: Path):
    config = _cfg(tmp_path)
    calls = {"n": 0}

    def fetch(url: str, timeout: float) -> str:
        calls["n"] += 1
        return RSS_XML

    first = collect_headlines(config, fetch_text=fetch)
    second = collect_headlines(config, fetch_text=fetch)
    assert [row["title"] for row in first] == ["Storm hits coast", "City opens new park"]
    assert [row["title"] for row in second] == [row["title"] for row in first]
    assert calls["n"] == 2


def test_pick_story_is_seed_stable():
    headlines = parse_feed(RSS_XML)
    a = pick_story(headlines, 42)
    b = pick_story(headlines, 42)
    c = pick_story(headlines, 99)
    assert a is not None and b is not None
    assert a["title"] == b["title"]
    assert c is not None


def test_extractive_brief_is_easy_four_beat():
    topic = extractive_brief(STORY, [], seed=3, duration=16.0)
    assert topic["id"].startswith("live_")
    assert topic["domain_label"] == "TRENDING NOW"
    assert topic["live"] is True
    assert topic["summary_mode"] == "extractive"
    assert topic["subtitle"].startswith("Live brief")
    phases = [seg["phase"] for seg in topic["segments"]]
    assert phases == ["HOOK", "WHY", "CATCH", "NEXT"]
    assert "Storm" in topic["title"]
    assert topic["sources"][0]["url"] == STORY["url"]
    for seg in topic["segments"]:
        assert seg["headline"]
        assert seg["voice_line"]
        assert len(seg["voice_line"].split()) <= 22


def test_summarize_uses_openrouter_when_key_present():
    payload = json.dumps(
        {
            "title": "Coastal Storm Brief",
            "fun_facts": ["High winds closed roads overnight."],
            "voice_lines": [
                "A coastal storm closed roads overnight.",
                "News feeds are circulating the storm tonight.",
                "Early reports only list the first road closures.",
                "Watch the source as crews reopen the coast.",
            ],
            "metrics": [{"label": "Signal", "val": "storm", "unit": "live"}],
            "visual_beats": [
                {"phase": "HOOK", "overlay_text": "Storm on the coast", "caption": "High winds closed roads.", "fact": "Live", "voice_line": "A coastal storm closed roads overnight."},
                {"phase": "WHY", "overlay_text": "Why it spread", "caption": "Feeds are pushing the storm.", "fact": "BBC", "voice_line": "News feeds are circulating the storm tonight."},
                {"phase": "CATCH", "overlay_text": "Early facts", "caption": "Details are still arriving.", "fact": "Check", "voice_line": "Early reports only list the first road closures."},
                {"phase": "NEXT", "overlay_text": "What next", "caption": "Watch for reopenings.", "fact": "Watch", "voice_line": "Watch the source as crews reopen the coast."},
            ],
        }
    )
    config = {"ai": {"enabled": True}}
    with patch("app.ai.trend_summarize.has_api_key", return_value=True):
        with patch("app.ai.trend_summarize.chat_completion", return_value=payload) as mock_chat:
            topic = summarize_live_story(STORY, [], config, seed=1, duration=16.0)
    mock_chat.assert_called_once()
    assert topic["title"] == "Coastal Storm Brief"
    assert topic["summary_mode"] == "openrouter"
    assert topic["segments"][0]["headline"] == "Storm on the coast"


def test_summarize_falls_back_when_ai_fails():
    config = {"ai": {"enabled": True}}
    with patch("app.ai.trend_summarize.has_api_key", return_value=True):
        with patch("app.ai.trend_summarize.chat_completion", side_effect=RuntimeError("nope")):
            topic = summarize_live_story(STORY, [], config, seed=1, duration=16.0)
    assert topic["summary_mode"] == "extractive"
    assert topic["title"]


def test_should_attach_skips_replay_prompt_and_other_engines():
    config = {"trend_feed": {"enabled": True, "rss_urls": ["https://example.com/rss"]}}
    assert should_attach_live_trend(_spec(), config) is True
    assert should_attach_live_trend(_spec(_replay_locked=True), config) is False
    assert should_attach_live_trend(_spec(user_prompt="brief this meme"), config) is False
    assert should_attach_live_trend(_spec(topic_data={"segments": [{"phase": "HOOK"}]}), config) is False
    other = _spec()
    other.engine = "how_it_works"
    assert should_attach_live_trend(other, config) is False
    assert should_attach_live_trend(_spec(), {"trend_feed": {"enabled": False, "rss_urls": ["https://x"]}}) is False


def test_attach_live_trend_writes_topic_and_sources(tmp_path: Path):
    spec = _spec()
    config = _cfg(tmp_path)
    messages: list[str] = []
    with patch("app.ai.trend_summarize.has_api_key", return_value=False):
        ok = attach_live_trend(
            spec,
            config,
            headlines=parse_feed(RSS_XML),
            on_progress=lambda ev: messages.append(str(ev.get("message") or "")),
        )
    assert ok is True
    topic = spec.params["topic_data"]
    assert topic["live"] is True
    assert spec.params["live_trend"] is True
    assert spec.params["sources"]
    assert any("Fetching today's headlines" in m for m in messages)
    assert any(m.startswith("Briefing:") for m in messages)


def test_attach_live_trend_falls_back_when_empty():
    spec = _spec()
    assert attach_live_trend(spec, {"trend_feed": {"enabled": True, "rss_urls": ["https://x"]}}, headlines=[]) is False
    assert "topic_data" not in spec.params


def test_attach_live_trend_skips_when_replay_locked():
    spec = _spec(_replay_locked=True)
    assert attach_live_trend(spec, {"trend_feed": {"enabled": True, "rss_urls": ["https://x"]}}, headlines=[STORY]) is False


def test_config_defaults_include_trend_feed():
    config = load_config()
    tf = config["trend_feed"]
    assert tf["enabled"] is True
    assert tf["rss_urls"]
    paths = ensure_directories(config)
    assert paths["trend_cache"].exists()
