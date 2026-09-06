"""Tests for YouTube SEO + thumbnail card (no live API)."""

from __future__ import annotations

from pathlib import Path

import numpy as np
from PIL import Image

from app.core.randomizer import ProjectSpec
from app.publish.seo import build_video_seo
from app.publish.thumb_card import YOUTUBE_THUMB, make_youtube_thumbnail


def _spec(engine: str, **params) -> ProjectSpec:
    return ProjectSpec(
        project_id="art_1",
        seed=1,
        engine=engine,
        style="storybook" if engine == "kids_storybook" else "classroom" if engine == "how_it_works" else "pulse",
        width=320,
        height=180,
        fps=10,
        duration=8.0,
        params=params,
    )


def test_kids_seo_title_and_made_for_kids():
    seo = build_video_seo(
        _spec(
            "kids_storybook",
            education_lesson={
                "title": "Luna the Cat",
                "segments": [
                    {"headline": "Meet Luna", "voice_line": "This is Luna the cat."},
                    {"headline": "The moon", "voice_line": "Luna finds the moon."},
                ],
            },
        )
    )
    assert "Luna the Cat" in seo.title
    assert len(seo.title) <= 100
    assert seo.made_for_kids is True
    assert seo.category_id == "27"
    assert any(tag.startswith("#") for tag in seo.hashtags)
    assert "BedtimeStory" in " ".join(seo.hashtags) or "KidsStory" in " ".join(seo.hashtags)
    assert "Meet Luna" in seo.description


def test_how_it_works_seo_starts_with_how():
    seo = build_video_seo(
        _spec(
            "how_it_works",
            topic_data={
                "title": "The Water Cycle",
                "segments": [{"headline": "Sun lifts the water", "voice_line": "Water rises as vapor."}],
            },
        )
    )
    assert seo.title.lower().startswith("how")
    assert seo.made_for_kids is False
    assert "#HowItWorks" in seo.hashtags


def test_trend_seo_not_kids():
    seo = build_video_seo(
        _spec(
            "trend_brief",
            topic_data={"title": "AI Agents", "segments": [{"headline": "Why it is everywhere"}]},
        )
    )
    assert "AI Agents" in seo.title
    assert seo.made_for_kids is False
    assert seo.category_id == "24"


def test_youtube_thumbnail_is_1280x720(tmp_path: Path):
    src = tmp_path / "src.jpg"
    Image.fromarray(np.zeros((180, 320, 3), dtype=np.uint8)).save(src, format="JPEG")
    dest = tmp_path / "yt.jpg"
    out = make_youtube_thumbnail(src, dest, title="Luna the Cat", badge="Kids Story")
    assert out.is_file()
    img = Image.open(out)
    assert img.size == YOUTUBE_THUMB
    assert dest.stat().st_size < 1_800_000


def test_connected_channel_roundtrip(tmp_path: Path):
    from app.publish.youtube import (
        connected_channel,
        format_channel,
        save_connected_channel,
    )

    cfg = {"youtube": {"token": str(tmp_path / "token.json")}}
    save_connected_channel(
        cfg,
        {
            "id": "UCabc",
            "title": "Luna Kids",
            "handle": "@lunakids",
            "url": "https://www.youtube.com/channel/UCabc",
        },
    )
    info = connected_channel(cfg)
    assert info is not None
    assert info["id"] == "UCabc"
    assert "Luna Kids" in format_channel(info)
    assert "@lunakids" in format_channel(info)


def test_load_client_config_from_env(tmp_path: Path, monkeypatch):
    from app.publish.youtube import installed_client_config, load_client_config

    secret = tmp_path / "client_secret.json"
    monkeypatch.setenv("YOUTUBE_CLIENT_ID", "abc.apps.googleusercontent.com")
    monkeypatch.setenv("YOUTUBE_CLIENT_SECRET", "GOCSPX-test")
    cfg = {"youtube": {"client_secret": str(secret), "token": str(tmp_path / "token.json")}}
    loaded = load_client_config(cfg)
    assert loaded["installed"]["client_id"] == "abc.apps.googleusercontent.com"
    assert secret.is_file()
    built = installed_client_config("x", "y")
    assert built["installed"]["token_uri"].startswith("https://oauth2.googleapis.com")


def test_placeholder_oauth_file_is_rejected(tmp_path: Path):
    from app.publish.youtube import YouTubePublishError, load_client_config

    secret = tmp_path / "client_secret.json"
    secret.write_text(
        '{"installed": {"client_id": "YOUR_CLIENT_ID.apps.googleusercontent.com", "client_secret": "YOUR_CLIENT_SECRET"}}',
        encoding="utf-8",
    )
    cfg = {"youtube": {"client_secret": str(secret)}}
    try:
        load_client_config(cfg)
        raise AssertionError("placeholder file should fail")
    except YouTubePublishError as exc:
        assert "OAuth client" in str(exc)


def test_friendly_error_when_api_disabled():
    from app.publish.youtube import friendly_google_error

    raw = (
        'HttpError 403 "YouTube Data API v3 has not been used in project 1038241240575 before '
        'or it is disabled. Enable it by visiting '
        'https://console.developers.google.com/apis/api/youtube.googleapis.com/overview?project=1038241240575 '
        'then retry."'
    )
    msg = friendly_google_error(RuntimeError(raw))
    assert "Enable" in msg
    assert "youtube.googleapis.com" in msg
