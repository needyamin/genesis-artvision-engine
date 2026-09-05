"""Quick OpenRouter connectivity check (no key printing)."""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from app.ai.client import get_api_key
from app.utils.dotenv import load_dotenv
from app.utils.validation import load_config


def main() -> int:
    load_dotenv()
    cfg = load_config()
    ai = cfg.get("ai") or {}
    key = get_api_key(cfg)
    print("ai.enabled =", ai.get("enabled"))
    print("ai.per_video =", ai.get("per_video"))
    print("ai.model =", ai.get("model"))
    print("key_present =", bool(key))
    print(
        "advisor_would_run =",
        bool(ai.get("enabled") and ai.get("per_video") and key),
    )
    if not key:
        print("openrouter_reachable = False")
        print("reason = missing key in .env")
        return 1

    models = [
        str(ai.get("model") or ""),
        "google/gemini-2.5-flash",
        "google/gemini-3.8-flash",
        "google/gemini-flash-1.5",
        "openai/gpt-4o-mini",
    ]
    # de-dupe preserve order
    seen: set[str] = set()
    ordered = []
    for m in models:
        if m and m not in seen:
            seen.add(m)
            ordered.append(m)

    base = str(ai.get("base_url") or "https://openrouter.ai/api/v1").rstrip("/")
    url = f"{base}/chat/completions"
    working = None
    last_err = ""
    for model in ordered:
        body = json.dumps(
            {
                "model": model,
                "messages": [
                    {"role": "system", "content": "Reply with JSON only."},
                    {"role": "user", "content": '{"ok":true}'},
                ],
                "temperature": 0,
                "response_format": {"type": "json_object"},
            }
        ).encode("utf-8")
        req = urllib.request.Request(
            url,
            data=body,
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {key}",
                "HTTP-Referer": "https://github.com/ansnew-tech/genesis-artvision",
                "X-Title": "Genesis Artvision Engine",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=25) as resp:
                raw = resp.read().decode("utf-8")
            data = json.loads(raw)
            content = data["choices"][0]["message"]["content"]
            print("tried_model =", model, "-> OK")
            print("sample =", (content or "")[:80].replace("\n", " "))
            working = model
            break
        except urllib.error.HTTPError as exc:
            detail = exc.read().decode("utf-8", errors="replace")[:180]
            print("tried_model =", model, "-> HTTP", exc.code)
            last_err = detail
        except Exception as exc:  # noqa: BLE001
            print("tried_model =", model, "-> ERR", type(exc).__name__)
            last_err = str(exc)[:180]

    if working:
        print("openrouter_reachable = True")
        print("recommended_model =", working)
        return 0
    print("openrouter_reachable = False")
    print("last_error =", last_err)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
