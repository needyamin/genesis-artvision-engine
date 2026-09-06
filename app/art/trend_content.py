"""Offline trending-brief catalog — evergreen viral-curiosity topics.

When the AI advisor is on, OpenRouter can replace these with a currently
trending internet topic. Frames still render offline from the JSON.
"""

from __future__ import annotations

from typing import Any

import numpy as np

TRENDS: list[dict[str, Any]] = [
    {
        "id": "ai_assistants_everywhere",
        "title": "AI Assistants Go Mainstream",
        "subtitle": "Tech culture pulse",
        "domain": "tech",
        "domain_label": "TRENDING TECH",
        "hook": "Chatbots moved from novelty to daily work tools in a few product cycles.",
        "schematic_type": "ticker",
        "metrics": [
            {"label": "Use case", "val": "write + code", "unit": "everyday"},
            {"label": "Risk", "val": "hallucination", "unit": "check sources"},
        ],
        "segments": [
            {"phase": "HOOK", "headline": "From demo to desk", "body": "People now draft mail, code, and plans with a prompt box.", "data_point": "Daily habit", "voice_line": "AI assistants jumped from demos to daily desk tools."},
            {"phase": "WHY", "headline": "Why it spread", "body": "Better models plus simple chat made the jump easy.", "data_point": "Chat UI", "voice_line": "Better models plus a simple chat box made the jump easy for millions of people."},
            {"phase": "CATCH", "headline": "The catch", "body": "Fluent answers can still be wrong. Verify facts.", "data_point": "Trust but check", "voice_line": "Fluent answers can still be wrong. Treat them as drafts, not gospel."},
            {"phase": "NEXT", "headline": "What next", "body": "Tools plug into calendars, code, and browsers.", "data_point": "Agents", "voice_line": "Next wave: assistants plugged into calendars, codebases, and browsers."},
        ],
    },
    {
        "id": "short_video_era",
        "title": "The Short Video Era",
        "subtitle": "Culture feed",
        "domain": "culture",
        "domain_label": "TRENDING CULTURE",
        "hook": "Attention now arrives in fifteen-second loops.",
        "schematic_type": "ticker",
        "metrics": [
            {"label": "Format", "val": "9:16", "unit": "vertical"},
            {"label": "Hook window", "val": "1–3s", "unit": "to keep a thumb"},
        ],
        "segments": [
            {"phase": "HOOK", "headline": "Thumbs decide", "body": "Feeds rank clips by instant hold, not slow burn.", "data_point": "Retention", "voice_line": "Short video feeds rank clips by how fast they hold a thumb."},
            {"phase": "WHY", "headline": "Phones first", "body": "Vertical full-screen made TV-length feel heavy.", "data_point": "Mobile native", "voice_line": "Full-screen phones made long TV pacing feel heavy."},
            {"phase": "CATCH", "headline": "The cost", "body": "Trends burn fast. Context gets sliced away.", "data_point": "Context loss", "voice_line": "Trends burn fast, and context gets sliced away."},
            {"phase": "NEXT", "headline": "What next", "body": "Longer live and shoppable clips chase the same loop.", "data_point": "Live + shop", "voice_line": "Platforms now chase the same loop with live and shoppable clips."},
        ],
    },
    {
        "id": "heat_records",
        "title": "Heat Records Keep Falling",
        "subtitle": "Planet pulse",
        "domain": "science",
        "domain_label": "TRENDING SCIENCE",
        "hook": "Each year, more cities break all-time heat marks.",
        "schematic_type": "ticker",
        "metrics": [
            {"label": "Signal", "val": "extremes", "unit": "more often"},
            {"label": "Human cost", "val": "heat stress", "unit": "health + work"},
        ],
        "segments": [
            {"phase": "HOOK", "headline": "New normals", "body": "Record heat is showing up in places that felt mild.", "data_point": "More extremes", "voice_line": "Record heat is showing up in places that used to feel mild."},
            {"phase": "WHY", "headline": "Extra energy", "body": "A warmer atmosphere loads more heat into heat waves.", "data_point": "Physics", "voice_line": "A warmer atmosphere loads more energy into each heat wave."},
            {"phase": "CATCH", "headline": "Cities feel it first", "body": "Pavement and nights that never cool down.", "data_point": "Urban heat", "voice_line": "Cities feel it first: pavement, and nights that barely cool down."},
            {"phase": "NEXT", "headline": "What people do", "body": "Shade, water, and power grids become front-page news.", "data_point": "Adaptation", "voice_line": "Shade, drinking water, and power grids become front-page news."},
        ],
    },
    {
        "id": "space_tourism_talk",
        "title": "Space Tourism Talk",
        "subtitle": "Frontier hype",
        "domain": "tech",
        "domain_label": "TRENDING TECH",
        "hook": "Suborbital hops made space a luxury headline again.",
        "schematic_type": "ticker",
        "metrics": [
            {"label": "Altitude", "val": "~80–100", "unit": "km talks"},
            {"label": "Access", "val": "elite", "unit": "for now"},
        ],
        "segments": [
            {"phase": "HOOK", "headline": "Tickets as headlines", "body": "Private flights turned launches into celebrity news.", "data_point": "Media loop", "voice_line": "Private flights turned rocket launches into celebrity news."},
            {"phase": "WHY", "headline": "Reusable hardware", "body": "Cheaper boosters made more attempts possible.", "data_point": "Reuse", "voice_line": "Reusable boosters made more attempts possible, and cameras never left."},
            {"phase": "CATCH", "headline": "Still exclusive", "body": "Most people will only watch from the ground.", "data_point": "Cost wall", "voice_line": "It is still exclusive. Most people will only watch from the ground."},
            {"phase": "NEXT", "headline": "What next", "body": "Research flights and lunar plans keep the feed going.", "data_point": "Moon + labs", "voice_line": "Research flights and lunar plans keep the feed going."},
        ],
    },
    {
        "id": "creator_economy",
        "title": "The Creator Economy",
        "subtitle": "Work online",
        "domain": "culture",
        "domain_label": "TRENDING CULTURE",
        "hook": "A camera and a niche can look like a job, until the algorithm moves.",
        "schematic_type": "ticker",
        "metrics": [
            {"label": "Income mix", "val": "ads + shop", "unit": "unstable"},
            {"label": "Platform risk", "val": "high", "unit": "one policy shift"},
        ],
        "segments": [
            {"phase": "HOOK", "headline": "Niche as a shop", "body": "Creators sell attention, then products, then courses.", "data_point": "Funnel", "voice_line": "Creators sell attention first, then products and courses."},
            {"phase": "WHY", "headline": "Direct to fan", "body": "Platforms cut out old gatekeepers, then become new ones.", "data_point": "New gate", "voice_line": "Platforms cut out old gatekeepers, then became the new ones."},
            {"phase": "CATCH", "headline": "The algorithm tax", "body": "Reach can vanish overnight.", "data_point": "Volatility", "voice_line": "Reach can vanish overnight when a ranking rule changes."},
            {"phase": "NEXT", "headline": "What next", "body": "Owned lists and shops try to survive the feed.", "data_point": "Own the list", "voice_line": "Smart creators now try to own email lists and shops, not just the feed."},
        ],
    },
    {
        "id": "chip_race",
        "title": "The Chip Race",
        "subtitle": "Industrial pulse",
        "domain": "tech",
        "domain_label": "TRENDING TECH",
        "hook": "Advanced chips became a national-strategy story, not just a gadget spec.",
        "schematic_type": "ticker",
        "metrics": [
            {"label": "Node talk", "val": "nm scale", "unit": "marketing + physics"},
            {"label": "Bottleneck", "val": "fabs", "unit": "few plants"},
        ],
        "segments": [
            {"phase": "HOOK", "headline": "Silicon is geopolitics", "body": "Who can make the smallest, fastest chips is a headline.", "data_point": "Few fabs", "voice_line": "Who can make the smallest, fastest chips is now a geopolitics headline."},
            {"phase": "WHY", "headline": "AI needs compute", "body": "Training giant models eats specialized processors.", "data_point": "Accelerators", "voice_line": "Training giant models eats specialized processors, so demand spiked."},
            {"phase": "CATCH", "headline": "Long build times", "body": "A new factory takes years and huge capital.", "data_point": "Years to fab", "voice_line": "A new factory takes years and huge capital, so supply cannot snap overnight."},
            {"phase": "NEXT", "headline": "What next", "body": "Governments fund plants. Design still concentrates.", "data_point": "Subsidies", "voice_line": "Governments fund plants, but design talent still concentrates in a few hubs."},
        ],
    },
    {
        "id": "sleep_hacks",
        "title": "Sleep Hacks Go Viral",
        "subtitle": "Wellness feed",
        "domain": "health",
        "domain_label": "TRENDING HEALTH",
        "hook": "Every month a new bedtime ritual trends, some useful, some theater.",
        "schematic_type": "ticker",
        "metrics": [
            {"label": "Need", "val": "7–9h", "unit": "most adults"},
            {"label": "Best lever", "val": "schedule", "unit": "light + time"},
        ],
        "segments": [
            {"phase": "HOOK", "headline": "Night routines as content", "body": "Mouth tape, cold rooms, and gadgets fill For You pages.", "data_point": "Rituals", "voice_line": "Mouth tape, cold rooms, and sleep gadgets fill For You pages."},
            {"phase": "WHY", "headline": "People are tired", "body": "Screens stole evenings. People want a fix in a clip.", "data_point": "Sleep debt", "voice_line": "Screens stole evenings, and people want a fix that fits in a clip."},
            {"phase": "CATCH", "headline": "What actually works", "body": "Regular hours and dim light beat most gadgets.", "data_point": "Circadian", "voice_line": "Regular hours and dim evening light still beat most gadgets."},
            {"phase": "NEXT", "headline": "What next", "body": "Wearables will keep selling scores. Skepticism helps.", "data_point": "Scores ≠ sleep", "voice_line": "Wearables will keep selling sleep scores. Healthy skepticism helps."},
        ],
    },
    {
        "id": "ocean_plastic_talk",
        "title": "Ocean Plastic, Still News",
        "subtitle": "Planet pulse",
        "domain": "science",
        "domain_label": "TRENDING SCIENCE",
        "hook": "Cleanup boats trend. The bigger fight is still on land.",
        "schematic_type": "ticker",
        "metrics": [
            {"label": "Source", "val": "rivers + waste", "unit": "mostly land"},
            {"label": "Fix", "val": "design + bins", "unit": "before the beach"},
        ],
        "segments": [
            {"phase": "HOOK", "headline": "Viral cleanups", "body": "Net boats and beach hauls make powerful clips.", "data_point": "Visible trash", "voice_line": "Net boats and beach hauls make powerful clips."},
            {"phase": "WHY", "headline": "Why it persists", "body": "Cheap packaging plus weak collection keeps leaking.", "data_point": "Leakage", "voice_line": "Cheap packaging plus weak trash collection keeps plastic leaking to water."},
            {"phase": "CATCH", "headline": "Ocean is downstream", "body": "Most plastic starts as land waste, not a mid-sea dump.", "data_point": "Upstream", "voice_line": "Most plastic starts as land waste, not a mid-ocean dump."},
            {"phase": "NEXT", "headline": "What next", "body": "Better bins, less single-use, and honest recycling labels.", "data_point": "Policy + design", "voice_line": "Better bins, less single-use, and honest recycling labels matter more than one boat."},
        ],
    },
    {
        "id": "passwordless",
        "title": "Passwords Wanted Dead",
        "subtitle": "Security pulse",
        "domain": "tech",
        "domain_label": "TRENDING TECH",
        "hook": "Passkeys and device unlocks are trying to retire the sticky note password.",
        "schematic_type": "ticker",
        "metrics": [
            {"label": "Phish risk", "val": "high", "unit": "stolen secrets"},
            {"label": "Passkey idea", "val": "device key", "unit": "not typed"},
        ],
        "segments": [
            {"phase": "HOOK", "headline": "Typing is the weak link", "body": "People reuse passwords. Attackers know that.", "data_point": "Reuse", "voice_line": "People reuse passwords. Attackers already know that."},
            {"phase": "WHY", "headline": "Passkeys", "body": "A phone holds a key. Sites never see a typed secret.", "data_point": "Public-key", "voice_line": "A passkey lives on your phone. Sites never see a typed secret."},
            {"phase": "CATCH", "headline": "Migration pain", "body": "Old sites, shared family logins, and lost devices.", "data_point": "Recovery", "voice_line": "Old sites, shared family logins, and lost devices still make migration messy."},
            {"phase": "NEXT", "headline": "What next", "body": "More logins will look like a fingerprint, not a form.", "data_point": "Biometric UI", "voice_line": "More logins will look like a fingerprint prompt, not a password form."},
        ],
    },
    {
        "id": "city_15_minute",
        "title": "The 15-Minute City Debate",
        "subtitle": "Urban pulse",
        "domain": "culture",
        "domain_label": "TRENDING CULTURE",
        "hook": "A planning idea went from urbanism blog to conspiracy clip.",
        "schematic_type": "ticker",
        "metrics": [
            {"label": "Idea", "val": "nearby needs", "unit": "walk / bike"},
            {"label": "Fight", "val": "freedom vs plan", "unit": "online"},
        ],
        "segments": [
            {"phase": "HOOK", "headline": "A simple pitch", "body": "Daily needs within a short walk or bike ride.", "data_point": "Proximity", "voice_line": "The pitch is simple: daily needs within a short walk or bike ride."},
            {"phase": "WHY", "headline": "Why it trended", "body": "Climate, traffic, and housing collided in one slogan.", "data_point": "Slogan power", "voice_line": "Climate, traffic, and housing collided in one slogan, so it spread."},
            {"phase": "CATCH", "headline": "Online distortion", "body": "Some clips framed it as a lockdown, not a shop nearby.", "data_point": "Misread", "voice_line": "Some clips framed it as a lockdown, not as having a shop nearby."},
            {"phase": "NEXT", "headline": "What next", "body": "Cities still try mixed streets. The slogan may fade.", "data_point": "Zoning fights", "voice_line": "Cities still try mixed streets. The slogan may fade; the zoning fights will not."},
        ],
    },
]


def _timed_segments(raw: list[dict[str, Any]]) -> list[dict[str, Any]]:
    n = max(1, len(raw))
    step = 1.0 / n
    out: list[dict[str, Any]] = []
    for i, seg in enumerate(raw):
        t0 = i * step
        t1 = min(1.0, (i + 1) * step)
        out.append(
            {
                "index": i,
                "total_segments": n,
                "t0": float(t0),
                "t1": float(t1),
                "phase": str(seg.get("phase") or "BEAT"),
                "headline": str(seg.get("headline") or seg.get("overlay_text") or f"Beat {i + 1}"),
                "body": str(seg.get("body") or seg.get("caption") or ""),
                "data_point": str(seg.get("data_point") or seg.get("fact") or ""),
                "voice_line": str(seg.get("voice_line") or seg.get("headline") or ""),
            }
        )
    return out


def _topic_dict(base: dict[str, Any], seed: int, duration: float, segments: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "id": base.get("id", "trend"),
        "domain": base.get("domain", "culture"),
        "domain_label": base.get("domain_label", "TRENDING"),
        "title": base.get("title", "Trending Brief"),
        "subtitle": base.get("subtitle", ""),
        "hook": base.get("hook", ""),
        "schematic_type": base.get("schematic_type", "ticker"),
        "metrics": list(base.get("metrics") or []),
        "duration": float(duration),
        "seed": int(seed),
        "segments": segments,
    }


def _from_ai(params: dict[str, Any], seed: int, duration: float) -> dict[str, Any] | None:
    title = str(params.get("ai_title") or "").strip()
    facts = [str(f) for f in (params.get("ai_fun_facts") or []) if str(f).strip()]
    voices = [str(v) for v in (params.get("ai_voice_lines") or []) if str(v).strip()]
    beats = params.get("ai_segment_plan") or params.get("ai_visual_beats") or []
    if not title and not beats and not facts and not voices:
        return None
    raw: list[dict[str, Any]] = []
    if isinstance(beats, list) and beats:
        for i, beat in enumerate(beats[:8]):
            if not isinstance(beat, dict):
                continue
            raw.append(
                {
                    "phase": str(beat.get("phase") or f"BEAT {i + 1}"),
                    "headline": str(beat.get("overlay_text") or beat.get("headline") or beat.get("title") or f"Beat {i + 1}"),
                    "body": str(beat.get("caption") or beat.get("body") or beat.get("fact") or ""),
                    "data_point": str(beat.get("fact") or beat.get("data_point") or ""),
                    "voice_line": str(beat.get("voice_line") or (voices[i] if i < len(voices) else "")),
                }
            )
    elif facts or voices:
        lines = facts or voices
        for i, line in enumerate(lines[:6]):
            raw.append(
                {
                    "phase": f"BEAT {i + 1}",
                    "headline": line[:48],
                    "body": line,
                    "data_point": "",
                    "voice_line": voices[i] if i < len(voices) else line,
                }
            )
    if not raw:
        raw = [{"phase": "HOOK", "headline": title or "Trending", "body": "", "data_point": "", "voice_line": title}]
    metrics = params.get("ai_metrics") if isinstance(params.get("ai_metrics"), list) else []
    return _topic_dict(
        {
            "id": "ai_trend",
            "title": title or "Trending Brief",
            "subtitle": "Internet pulse",
            "domain": "culture",
            "domain_label": "TRENDING NOW",
            "hook": facts[0] if facts else title,
            "schematic_type": "ticker",
            "metrics": list(metrics),
        },
        seed,
        duration,
        _timed_segments(raw),
    )


def build_trend_topic(
    seed: int,
    duration: float,
    *,
    topic_id: str | None = None,
    params: dict[str, Any] | None = None,
) -> dict[str, Any]:
    params = params or {}
    existing = params.get("topic_data")
    if isinstance(existing, dict) and existing.get("segments"):
        topic = dict(existing)
        topic["duration"] = float(duration)
        topic["seed"] = int(seed)
        if topic["segments"] and "t0" not in topic["segments"][0]:
            topic["segments"] = _timed_segments(topic["segments"])
        return topic
    ai_topic = _from_ai(params, seed, duration)
    if ai_topic:
        return ai_topic
    rng = np.random.default_rng(seed)
    if topic_id:
        match = next((t for t in TRENDS if t["id"] == topic_id), None)
        chosen = match or TRENDS[int(rng.integers(0, len(TRENDS)))]
    else:
        chosen = TRENDS[int(rng.integers(0, len(TRENDS)))]
    return _topic_dict(chosen, seed, duration, _timed_segments(list(chosen["segments"])))
