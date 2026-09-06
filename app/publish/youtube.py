"""YouTube Data API v3 upload for a channel the user owns.

Uses Google's official OAuth installed-app flow and videos.insert /
thumbnails.set. This is not a scraper and does not bypass YouTube sign-in.
"""

from __future__ import annotations

import json
import os
import re
from datetime import date
from pathlib import Path
from typing import Any, Callable

from app.publish.seo import VideoSEO, build_video_seo
from app.publish.thumb_card import make_youtube_thumbnail
from app.utils.dotenv import load_dotenv
from app.utils.logger import get_logger
from app.utils.paths import resolve_path

logger = get_logger("publish.youtube")

SCOPES = [
    "https://www.googleapis.com/auth/youtube.upload",
    "https://www.googleapis.com/auth/youtube",
]

ProgressFn = Callable[[dict[str, Any]], None]


class YouTubePublishError(RuntimeError):
    """Raised when connect or upload fails."""


def friendly_google_error(exc: BaseException) -> str:
    """Turn Google API HttpError blobs into a short action the user can take."""
    text = str(exc)
    lowered = text.lower()
    if "youtube data api v3 has not been used" in lowered or "youtube.googleapis.com/overview" in lowered:
        match = re.search(r"https://console\.[^\s\"]+", text)
        link = match.group(0).rstrip(".,") if match else (
            "https://console.cloud.google.com/apis/library/youtube.googleapis.com"
        )
        return (
            "YouTube Data API v3 is off for this Google Cloud project.\n\n"
            "1. Open this page (same project as your OAuth client):\n"
            f"   {link}\n"
            "2. Click Enable.\n"
            "3. Wait 2–5 minutes for Google to propagate it.\n"
            "4. Generate again — the MP4 is already in output/.\n\n"
            "Connect used the right Google login; the Cloud project still needs the API switched on."
        )
    if "accessNotConfigured" in text or "ACCESS_TOKEN_SCOPE_INSUFFICIENT" in text:
        return (
            "Google refused YouTube access for this login.\n"
            "YouTube → Disconnect, then Connect / switch channel… and pick the Brand Account."
        )
    return text[:800]


def _yt_cfg(config: dict[str, Any]) -> dict[str, Any]:
    return dict(config.get("youtube") or {})


def client_secret_path(config: dict[str, Any]) -> Path:
    yt = _yt_cfg(config)
    return resolve_path(yt.get("client_secret") or "./data/youtube/client_secret.json")


def token_path(config: dict[str, Any]) -> Path:
    yt = _yt_cfg(config)
    return resolve_path(yt.get("token") or "./data/youtube/token.json")


def quota_path(config: dict[str, Any]) -> Path:
    return token_path(config).with_name("quota.json")


def channel_path(config: dict[str, Any]) -> Path:
    return token_path(config).with_name("channel.json")


def is_connected(config: dict[str, Any]) -> bool:
    path = token_path(config)
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(data.get("refresh_token") or data.get("token"))


def connected_channel(config: dict[str, Any]) -> dict[str, str] | None:
    """Return the saved destination channel (title, id, handle) if any."""
    path = channel_path(config)
    if not path.is_file():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None
    if not isinstance(data, dict) or not data.get("id"):
        return None
    return {
        "id": str(data.get("id") or ""),
        "title": str(data.get("title") or "YouTube channel"),
        "handle": str(data.get("handle") or ""),
        "url": str(data.get("url") or ""),
    }


def format_channel(info: dict[str, str] | None) -> str:
    if not info:
        return "no channel connected"
    title = info.get("title") or "YouTube channel"
    handle = str(info.get("handle") or "").strip()
    if handle and not handle.startswith("@"):
        handle = "@" + handle
    if handle:
        return f"{title} ({handle})"
    return title


def save_connected_channel(config: dict[str, Any], info: dict[str, str]) -> None:
    path = channel_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(info, indent=2), encoding="utf-8")


def disconnect_youtube(config: dict[str, Any]) -> None:
    for path in (token_path(config), channel_path(config)):
        try:
            path.unlink(missing_ok=True)
        except OSError:
            pass
    path = token_path(config)
    if not path.is_file():
        return False
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    return bool(data.get("refresh_token") or data.get("token"))


def missing_dependency_message() -> str:
    return (
        "YouTube upload needs extra packages.\n\n"
        "Run:\n  python -m pip install google-api-python-client google-auth-oauthlib google-auth-httplib2"
    )


def _google():
    try:
        from google.auth.transport.requests import Request
        from google.oauth2.credentials import Credentials
        from google_auth_oauthlib.flow import InstalledAppFlow
        from googleapiclient.discovery import build
        from googleapiclient.http import MediaFileUpload
    except ImportError as exc:  # pragma: no cover
        raise YouTubePublishError(missing_dependency_message()) from exc
    return Request, Credentials, InstalledAppFlow, build, MediaFileUpload


def oauth_setup_message(secret: Path) -> str:
    example = secret.with_name("oauth_client.example.json")
    return (
        "Missing YouTube OAuth client.\n\n"
        "Google does not ship this file — you create it once in Cloud Console:\n"
        "1. Open https://console.cloud.google.com/apis/credentials\n"
        "2. Enable YouTube Data API v3 for the project\n"
        "3. Create credentials → OAuth client ID → Application type: Desktop app\n"
        "4. Either download the JSON and save it as:\n"
        f"     {secret}\n"
        "   (see oauth_client.example.json next to that folder)\n"
        "   or put the two values in project-root .env:\n"
        "     YOUTUBE_CLIENT_ID=....apps.googleusercontent.com\n"
        "     YOUTUBE_CLIENT_SECRET=GOCSPX-...\n"
        "5. YouTube → Connect channel… again and sign in as the channel owner."
        + (f"\n\nTemplate:\n{example}" if example.is_file() else "")
    )


def installed_client_config(client_id: str, client_secret: str) -> dict[str, Any]:
    return {
        "installed": {
            "client_id": client_id.strip(),
            "client_secret": client_secret.strip(),
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "auth_provider_x509_cert_url": "https://www.googleapis.com/oauth2/v1/certs",
            "redirect_uris": ["http://localhost"],
        }
    }


def load_client_config(config: dict[str, Any]) -> dict[str, Any]:
    """Load Desktop OAuth client from JSON file or .env."""
    load_dotenv()
    secret = client_secret_path(config)
    if secret.is_file():
        try:
            data = json.loads(secret.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise YouTubePublishError(f"OAuth client file is not valid JSON:\n{secret}\n{exc}") from exc
        blob = data.get("installed") or data.get("web") or {}
        if not blob.get("client_id") or "YOUR_CLIENT_ID" in str(blob.get("client_id")):
            raise YouTubePublishError(oauth_setup_message(secret))
        return data
    client_id = os.environ.get("YOUTUBE_CLIENT_ID", "").strip()
    client_secret = os.environ.get("YOUTUBE_CLIENT_SECRET", "").strip()
    if client_id and client_secret and "YOUR_CLIENT_ID" not in client_id:
        cfg = installed_client_config(client_id, client_secret)
        secret.parent.mkdir(parents=True, exist_ok=True)
        secret.write_text(json.dumps(cfg, indent=2), encoding="utf-8")
        logger.info("Wrote YouTube OAuth client JSON from .env → %s", secret)
        return cfg
    raise YouTubePublishError(oauth_setup_message(secret))


def _channels_from_api(build, creds) -> list[dict[str, str]]:
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    resp = youtube.channels().list(part="snippet", mine=True).execute()
    out: list[dict[str, str]] = []
    for item in resp.get("items") or []:
        snippet = item.get("snippet") or {}
        custom = str(snippet.get("customUrl") or "").strip()
        handle = custom if custom.startswith("@") else (f"@{custom}" if custom else "")
        cid = str(item.get("id") or "")
        title = str(snippet.get("title") or "YouTube channel")
        if not cid:
            continue
        out.append(
            {
                "id": cid,
                "title": title,
                "handle": handle,
                "url": f"https://www.youtube.com/channel/{cid}",
                "studio": f"https://studio.youtube.com/channel/{cid}",
            }
        )
    return out


def connect_youtube(config: dict[str, Any], *, force: bool = True) -> dict[str, str]:
    """Open a browser so the user can pick which Google / Brand Account to upload to."""
    client_config = load_client_config(config)
    Request, Credentials, InstalledAppFlow, build, _media = _google()
    token = token_path(config)
    token.parent.mkdir(parents=True, exist_ok=True)
    if force:
        try:
            token.unlink(missing_ok=True)
        except OSError:
            pass
    creds = None
    if token.is_file() and not force:
        creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if creds and creds.valid and not force:
        channels = _channels_from_api(build, creds)
        info = channels[0] if channels else {"id": "", "title": "Connected"}
        if info.get("id"):
            save_connected_channel(config, info)
        return info
    if creds and creds.expired and creds.refresh_token and not force:
        creds.refresh(Request())
    else:
        flow = InstalledAppFlow.from_client_config(client_config, SCOPES)
        creds = flow.run_local_server(
            port=0,
            prompt="select_account",
            access_type="offline",
        )
    token.write_text(creds.to_json(), encoding="utf-8")
    try:
        channels = _channels_from_api(build, creds)
    except Exception as exc:  # noqa: BLE001
        raise YouTubePublishError(friendly_google_error(exc)) from exc
    if not channels:
        raise YouTubePublishError(
            "Signed in, but YouTube did not return a channel. "
            "On the Google picker, choose the Brand Account for the channel you want — "
            "not only your Gmail. Then Connect again."
        )
    info = channels[0]
    save_connected_channel(config, info)
    logger.info("YouTube connected as %s (%s)", info.get("title"), info.get("id"))
    return info


def _credentials(config: dict[str, Any]):
    Request, Credentials, InstalledAppFlow, build, MediaFileUpload = _google()
    token = token_path(config)
    if not token.is_file():
        raise YouTubePublishError("YouTube is not connected. Use YouTube → Connect channel first.")
    creds = Credentials.from_authorized_user_file(str(token), SCOPES)
    if creds and creds.expired and creds.refresh_token:
        creds.refresh(Request())
        token.write_text(creds.to_json(), encoding="utf-8")
    if not creds or not creds.valid:
        raise YouTubePublishError("YouTube login expired. Connect the channel again.")
    return creds, build, MediaFileUpload


def _today_uploads(config: dict[str, Any]) -> int:
    path = quota_path(config)
    if not path.is_file():
        return 0
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return 0
    if str(data.get("date")) != date.today().isoformat():
        return 0
    try:
        return int(data.get("uploads") or 0)
    except (TypeError, ValueError):
        return 0


def _note_upload(config: dict[str, Any]) -> None:
    path = quota_path(config)
    path.parent.mkdir(parents=True, exist_ok=True)
    today = date.today().isoformat()
    n = _today_uploads(config) + 1
    path.write_text(json.dumps({"date": today, "uploads": n}), encoding="utf-8")


def publish_to_youtube(
    *,
    video_path: Path,
    spec: Any,
    config: dict[str, Any],
    thumbnail_path: Path | None = None,
    privacy: str | None = None,
    on_progress: ProgressFn | None = None,
) -> dict[str, str]:
    """Upload one MP4 with SEO snippet + custom thumbnail. Returns id/url."""
    path = Path(video_path)
    if not path.is_file():
        raise YouTubePublishError(f"Video file not found: {path}")
    yt = _yt_cfg(config)
    daily = int(yt.get("daily_limit") or 6)
    used = _today_uploads(config)
    if used >= daily:
        raise YouTubePublishError(
            f"Daily YouTube upload limit reached ({daily}). "
            "Default API quota is about 6 uploads/day. Raise youtube.daily_limit in config.yaml "
            "only if Google granted a higher quota."
        )
    privacy_status = str(privacy or yt.get("privacy") or "unlisted").strip().lower()
    if privacy_status not in {"public", "unlisted", "private"}:
        privacy_status = "unlisted"

    seo = build_video_seo(spec)
    creds, build, MediaFileUpload = _credentials(config)
    youtube = build("youtube", "v3", credentials=creds, cache_discovery=False)
    dest = connected_channel(config)
    if not dest:
        channels = _channels_from_api(build, creds)
        if channels:
            dest = channels[0]
            save_connected_channel(config, dest)
    dest_label = format_channel(dest)

    if on_progress:
        on_progress(
            {
                "phase": "youtube",
                "message": f"Uploading to {dest_label}: {seo.title[:50]}",
                "seed": getattr(spec, "seed", None),
                "engine": getattr(spec, "engine", None),
                "style": getattr(spec, "style", None),
            }
        )

    body = {
        "snippet": {
            "title": seo.title,
            "description": seo.description,
            "tags": seo.tags,
            "categoryId": seo.category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": bool(seo.made_for_kids),
        },
    }
    media = MediaFileUpload(str(path), mimetype="video/mp4", resumable=True, chunksize=8 * 1024 * 1024)
    request = youtube.videos().insert(part="snippet,status", body=body, media_body=media)
    response = None
    try:
        while response is None:
            status, response = request.next_chunk()
            if status and on_progress:
                pct = int(status.progress() * 100)
                on_progress(
                    {
                        "phase": "youtube",
                        "message": f"Uploading to {dest_label}… {pct}%",
                        "percent": pct,
                        "seed": getattr(spec, "seed", None),
                        "engine": getattr(spec, "engine", None),
                        "style": getattr(spec, "style", None),
                    }
                )
    except Exception as exc:  # noqa: BLE001
        raise YouTubePublishError(friendly_google_error(exc)) from exc
    video_id = str(response.get("id") or "")
    if not video_id:
        raise YouTubePublishError("YouTube did not return a video id.")
    url = f"https://youtu.be/{video_id}"
    _note_upload(config)

    badge = {
        "kids_storybook": "Kids Story",
        "how_it_works": "How It Works",
        "trend_brief": "Trending Now",
    }.get(str(getattr(spec, "engine", "")), "")
    thumb_dest = path.with_name(path.stem + ".yt.jpg")
    try:
        make_youtube_thumbnail(
            Path(thumbnail_path) if thumbnail_path else path.with_suffix(".jpg"),
            thumb_dest,
            title=seo.thumbnail_title,
            badge=badge,
        )
        youtube.thumbnails().set(
            videoId=video_id,
            media_body=MediaFileUpload(str(thumb_dest), mimetype="image/jpeg"),
        ).execute()
    except Exception as exc:  # noqa: BLE001
        logger.warning("Custom thumbnail skipped (channel may need verification): %s", exc)

    logger.info("Uploaded %s -> %s", path.name, url)
    if on_progress:
        on_progress(
            {
                "phase": "youtube",
                "message": f"Uploaded: {url}",
                "youtube_url": url,
                "youtube_id": video_id,
                "seed": getattr(spec, "seed", None),
                "engine": getattr(spec, "engine", None),
                "style": getattr(spec, "style", None),
            }
        )
    return {"id": video_id, "url": url, "title": seo.title, "privacy": privacy_status, "channel": dest_label}
