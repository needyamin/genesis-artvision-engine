"""Batch catalog curation via OpenRouter — expands offline education content."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.ai.client import AIClientError, chat_completion, has_api_key
from app.ai.prompts import SYSTEM_CURATE, curate_user_prompt
from app.ai.schemas import extract_json_object
from app.utils.logger import get_logger
from app.utils.paths import resolve_path

logger = get_logger("ai.curate")

ALPHABET = list("ABCDEFGHIJKLMNOPQRSTUVWXYZ")


def catalog_dir(config: dict[str, Any]) -> Path:
    ai = config.get("ai") or {}
    return resolve_path(ai.get("catalog_dir") or "./data/ai_catalogs")


def _normalize_letter_map(raw: Any) -> dict[str, list[str]]:
    if not isinstance(raw, dict):
        return {}
    out: dict[str, list[str]] = {}
    for key, values in raw.items():
        letter = str(key).strip().upper()
        if len(letter) != 1 or not letter.isalpha():
            continue
        if isinstance(values, str):
            values = [values]
        if not isinstance(values, list):
            continue
        cleaned = [str(v).strip() for v in values if str(v).strip()]
        if cleaned:
            out[letter] = cleaned
    return out


def parse_curate_payload(raw: str | dict[str, Any]) -> dict[str, dict[str, list[str]]]:
    data = extract_json_object(raw) if isinstance(raw, str) else dict(raw)
    return {
        "words": _normalize_letter_map(data.get("words")),
        "fun_facts": _normalize_letter_map(data.get("fun_facts")),
        "voice_lines": _normalize_letter_map(data.get("voice_lines")),
    }


def _merge_letter_maps(base: dict[str, list[str]], extra: dict[str, list[str]]) -> dict[str, list[str]]:
    merged = {k: list(v) for k, v in base.items()}
    for letter, values in extra.items():
        existing = merged.setdefault(letter, [])
        seen = {x.upper() for x in existing}
        for item in values:
            cmp = item.upper()
            if cmp not in seen:
                existing.append(item)
                seen.add(cmp)
    return merged


def load_catalog_file(path: Path) -> dict[str, dict[str, list[str]]]:
    if not path.is_file():
        return {"words": {}, "fun_facts": {}, "voice_lines": {}}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"words": {}, "fun_facts": {}, "voice_lines": {}}
    return {
        "words": _normalize_letter_map(data.get("words")),
        "fun_facts": _normalize_letter_map(data.get("fun_facts")),
        "voice_lines": _normalize_letter_map(data.get("voice_lines")),
    }


def save_catalog_file(path: Path, catalog: dict[str, dict[str, list[str]]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(catalog, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def merge_catalogs(
    existing: dict[str, dict[str, list[str]]],
    incoming: dict[str, dict[str, list[str]]],
) -> dict[str, dict[str, list[str]]]:
    return {
        "words": _merge_letter_maps(existing.get("words", {}), incoming.get("words", {})),
        "fun_facts": _merge_letter_maps(existing.get("fun_facts", {}), incoming.get("fun_facts", {})),
        "voice_lines": _merge_letter_maps(
            existing.get("voice_lines", {}), incoming.get("voice_lines", {})
        ),
    }


def curate_letters(
    config: dict[str, Any],
    letters: list[str] | None = None,
    *,
    chunk_size: int = 6,
) -> Path:
    """
    Call OpenRouter to expand catalogs for the given letters and merge onto disk.

    Returns the path to the written catalog file.
    """
    if not has_api_key(config):
        raise AIClientError(
            "Missing OPENROUTER_API_KEY. Add it to the project-root `.env` file "
            "(see `.env.example`)."
        )

    targets = [c.upper() for c in (letters or ALPHABET) if len(c) == 1 and c.isalpha()]
    if not targets:
        targets = list(ALPHABET)

    out_path = catalog_dir(config) / "education.json"
    catalog = load_catalog_file(out_path)

    for i in range(0, len(targets), chunk_size):
        chunk = targets[i : i + chunk_size]
        messages = [
            {"role": "system", "content": SYSTEM_CURATE},
            {"role": "user", "content": curate_user_prompt(chunk)},
        ]
        logger.info("Curating letters %s", ",".join(chunk))
        content = chat_completion(messages=messages, config=config, temperature=0.5)
        incoming = parse_curate_payload(content)
        catalog = merge_catalogs(catalog, incoming)

    save_catalog_file(out_path, catalog)
    logger.info("Wrote education catalog %s", out_path)
    return out_path
