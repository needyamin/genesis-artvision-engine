"""OpenAI-compatible chat client (OpenRouter / Ollama) via stdlib urllib."""

from __future__ import annotations

import json
import os
import urllib.error
import urllib.request
from typing import Any

from app.utils.dotenv import load_dotenv
from app.utils.logger import get_logger

logger = get_logger("ai.client")

ENV_API_KEY = "OPENROUTER_API_KEY"
_DOTENV_LOADED = False


def _ensure_dotenv() -> None:
    global _DOTENV_LOADED
    if _DOTENV_LOADED:
        return
    _DOTENV_LOADED = True
    load_dotenv()


class AIClientError(RuntimeError):
    """Raised when the remote advisor call fails."""


def get_api_key(config: dict[str, Any] | None = None) -> str | None:
    """Resolve API key from root `.env`, environment, or config (optional)."""
    _ensure_dotenv()
    key = os.environ.get(ENV_API_KEY, "").strip()
    if key:
        return key
    if config:
        key = str(config.get("ai", {}).get("api_key") or "").strip()
        return key or None
    return None


def has_api_key(config: dict[str, Any] | None = None) -> bool:
    return bool(get_api_key(config))


def chat_completion(
    *,
    messages: list[dict[str, str]],
    config: dict[str, Any],
    temperature: float = 0.4,
) -> str:
    """
    Call OpenAI-compatible chat completions and return assistant text.

    Uses OPENROUTER_API_KEY from project-root `.env` or the environment.
    """
    ai = config.get("ai") or {}
    api_key = get_api_key(config)
    if not api_key:
        raise AIClientError(
            f"Missing {ENV_API_KEY}. Put it in a root `.env` file "
            f"(see `.env.example`) or set the environment variable."
        )

    base_url = str(ai.get("base_url") or "https://openrouter.ai/api/v1").rstrip("/")
    model = str(ai.get("model") or "openai/gpt-4o-mini")
    timeout = float(ai.get("timeout_sec") or 20)
    url = f"{base_url}/chat/completions"

    body: dict[str, Any] = {
        "model": model,
        "messages": messages,
        "temperature": temperature,
        "response_format": {"type": "json_object"},
    }
    payload = json.dumps(body).encode("utf-8")

    headers = {
        "Content-Type": "application/json",
        "Authorization": f"Bearer {api_key}",
        "HTTP-Referer": "https://github.com/ansnew-tech/genesis-artvision",
        "X-Title": "Genesis Artvision Engine",
    }

    req = urllib.request.Request(url, data=payload, headers=headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            raw = resp.read().decode("utf-8")
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")[:500]
        raise AIClientError(f"HTTP {exc.code}: {detail}") from exc
    except urllib.error.URLError as exc:
        raise AIClientError(f"Network error: {exc.reason}") from exc
    except TimeoutError as exc:
        raise AIClientError(f"Timed out after {timeout}s") from exc

    try:
        data = json.loads(raw)
        content = data["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError, json.JSONDecodeError) as exc:
        raise AIClientError(f"Unexpected response shape: {raw[:300]}") from exc

    if not isinstance(content, str) or not content.strip():
        raise AIClientError("Empty assistant content")
    return content
