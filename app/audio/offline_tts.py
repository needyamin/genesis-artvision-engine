"""Offline kids narration: Windows SAPI when available, procedural fallback otherwise."""

from __future__ import annotations

import hashlib
import logging
import subprocess
import sys
import threading
import wave
import xml.sax.saxutils as xml_escape
from pathlib import Path

import numpy as np

from app.audio.procedural_voice import synthesize_speech
from app.utils.paths import project_root

logger = logging.getLogger("audio.offline_tts")

_KEY_LOCKS_GUARD = threading.Lock()
_KEY_LOCKS: dict[str, threading.Lock] = {}


def _lock_for(key: str) -> threading.Lock:
    with _KEY_LOCKS_GUARD:
        lock = _KEY_LOCKS.get(key)
        if lock is None:
            lock = threading.Lock()
            _KEY_LOCKS[key] = lock
        return lock


def voice_cache_dir() -> Path:
    path = project_root() / "data" / "ai_voice"
    path.mkdir(parents=True, exist_ok=True)
    return path


def kids_narration_lines(seg: dict) -> list[str]:
    """Slow learning script: one idea per line so a child can repeat it."""
    lines: list[str] = []
    seen: set[str] = set()

    def add(raw: object) -> None:
        text = " ".join(str(raw or "").split()).strip()
        if not any(ch.isalnum() for ch in text):
            return
        key = text.lower()
        if key in seen:
            return
        seen.add(key)
        lines.append(text[:160])

    kind = str(seg.get("kind") or "").lower()
    word = str(seg.get("word") or "").strip()
    letter = str(seg.get("letter") or "").strip()

    if kind == "math" or seg.get("math_op"):
        add(seg.get("voice_line"))
        if not lines:
            left = int(seg.get("math_left") or 1)
            right = int(seg.get("math_right") or 1)
            op = str(seg.get("math_op") or "+")
            ans = int(seg.get("count") or (left + right if op != "-" else left - right))
            add(f"{left} {'take away' if op == '-' else 'plus'} {right} is {ans}.")
        add(seg.get("celebrate") or "You did the math! Great job!")
        return lines[:2]

    if seg.get("complete_alphabet"):
        add(seg.get("voice_line"))
        if letter and letter.lower() not in " ".join(lines).lower():
            add(f"This is the letter {letter}.")
        if word and f"say {word.lower()}" not in " ".join(lines).lower():
            add(f"Say {word.lower()}.")
        return lines[:2]

    if kind == "dictionary" or str(seg.get("spell_word") or "").strip():
        add(seg.get("voice_line"))
        add(seg.get("celebrate") or "Great job!")
        return lines[:2]

    add(seg.get("voice_line"))
    if letter and letter.lower() not in " ".join(lines).lower():
        add(f"This is the letter {letter}.")
    if word and word.lower() not in " ".join(lines).lower():
        add(f"Say {word.lower()} with me.")
    add(seg.get("celebrate") or "Great job!")
    return lines[:2]


def spell_aloud(word: str) -> str:
    letters = [ch for ch in str(word).upper() if ch.isalpha()]
    if not letters:
        return ""
    return ". ".join(letters) + "."


def documentary_narration_lines(seg: dict) -> list[str]:
    """Build a calm, engaging, informative scientific script for documentary segments."""
    voice_line = str(seg.get("voice_line") or "").strip()
    if voice_line:
        return [voice_line]
    headline = str(seg.get("headline") or "").strip()
    body = str(seg.get("body") or "").strip()
    res = []
    if headline:
        res.append(headline)
    if body:
        res.append(body)
    return res[:2]


def speak_documentary(
    lines: list[str],
    *,
    sample_rate: int = 44100,
    pitch: float = 1.0,
    speed: float = 0.98,
    seed: int = 0,
) -> np.ndarray:
    """Narrate documentary lines with calm cadence and clear articulation."""
    return speak_narration(
        lines,
        sample_rate=sample_rate,
        pitch=pitch,
        speed=speed,
        seed=seed,
        kids=False,
    )


def speak_narration(
    lines: list[str],
    *,
    sample_rate: int = 44100,
    pitch: float = 1.10,
    speed: float = 0.86,
    seed: int = 0,
    kids: bool = True,
) -> np.ndarray:
    """Speak several short lines as one clip. Prefers Windows TTS, then formant synth."""
    cleaned = [" ".join(str(line).split()).strip() for line in lines if str(line).strip()]
    if not cleaned:
        return np.zeros(1, dtype=np.float32)
    # Kids: a bit under normal pace so words stay clear, not drawn-out.
    # speed 0.86 → SAPI Rate about -1.
    sapi_rate = int(np.clip(round((float(speed) - 1.0) * 10.0), -8, 5))
    if kids:
        sapi_rate = min(max(sapi_rate, -2), 0)
    pitch_pct = int(np.clip(round((float(pitch) - 1.0) * 100.0), 0, 18))
    wav = _sapi_cached(cleaned, sapi_rate=sapi_rate, pitch_pct=pitch_pct, kids=kids)
    if wav is not None:
        return _resample_mono(wav, 44100, sample_rate)
    chunks: list[np.ndarray] = []
    pause = np.zeros(max(1, int((0.32 if kids else 0.28) * sample_rate)), dtype=np.float32)
    for i, line in enumerate(cleaned):
        chunks.append(
            synthesize_speech(
                line,
                sample_rate=sample_rate,
                pitch=pitch,
                speed=min(speed, 0.92) if kids else speed,
                seed=seed + i * 17,
            )
        )
        if i < len(cleaned) - 1:
            chunks.append(pause)
    audio = np.concatenate(chunks).astype(np.float32)
    peak = float(np.max(np.abs(audio)) + 1e-9)
    return (audio / peak * 0.86).astype(np.float32)


def speak_text(
    text: str,
    *,
    sample_rate: int = 44100,
    pitch: float = 1.10,
    speed: float = 0.86,
    seed: int = 0,
) -> np.ndarray:
    return speak_narration([text], sample_rate=sample_rate, pitch=pitch, speed=speed, seed=seed, kids=True)


def _sapi_cached(lines: list[str], *, sapi_rate: int, pitch_pct: int, kids: bool = False) -> np.ndarray | None:
    if sys.platform != "win32":
        return None
    key = hashlib.md5(
        "|".join(lines).encode("utf-8") + f"|{sapi_rate}|{pitch_pct}|k{int(kids)}|v3".encode()
    ).hexdigest()
    wav_path = voice_cache_dir() / f"{key}.wav"
    with _lock_for(key):
        if wav_path.exists() and wav_path.stat().st_size > 44:
            try:
                return _load_wav_mono(wav_path, 44100)
            except Exception:
                logger.debug("Could not read cached TTS wav %s", wav_path)
        try:
            _powershell_sapi(lines, wav_path, sapi_rate=sapi_rate, pitch_pct=pitch_pct, kids=kids)
            if wav_path.exists() and wav_path.stat().st_size > 44:
                return _load_wav_mono(wav_path, 44100)
        except Exception as exc:  # noqa: BLE001
            logger.info("Windows TTS unavailable, using offline voice: %s", exc)
        return None


def _ssml_for(lines: list[str], pitch_pct: int, *, kids: bool = False) -> str:
    parts: list[str] = []
    gap = "380ms" if kids else "420ms"
    letter_gap = "220ms" if kids else "180ms"
    for i, line in enumerate(lines):
        parts.append(_ssml_line(line, letter_gap=letter_gap))
        if i < len(lines) - 1:
            parts.append(f'<break time="{gap}"/>')
    body = "".join(parts)
    pitch = f"{pitch_pct:+d}%"
    rate = "-10%" if kids else "medium"
    return (
        '<?xml version="1.0" encoding="utf-8"?>'
        '<speak version="1.0" xmlns="http://www.w3.org/2001/10/synthesis" xml:lang="en-US">'
        f'<prosody pitch="{pitch}" rate="{rate}">{body}</prosody>'
        "</speak>"
    )


def _ssml_line(line: str, *, letter_gap: str) -> str:
    """Pause after single letters so C. A. T. is easy to hear."""
    tokens = str(line).split()
    out: list[str] = []
    for token in tokens:
        stripped = token.strip(".,!?")
        safe = xml_escape.escape(token)
        if len(stripped) == 1 and stripped.isalnum():
            spoken = stripped.upper() if stripped.isalpha() else stripped
            out.append(f'{xml_escape.escape(spoken)}<break time="{letter_gap}"/>')
        else:
            out.append(safe + " ")
    return "".join(out)


def _powershell_sapi(lines: list[str], wav_path: Path, *, sapi_rate: int, pitch_pct: int, kids: bool = False) -> None:
    wav_path.parent.mkdir(parents=True, exist_ok=True)
    ssml_path = wav_path.with_suffix(".ssml")
    ps1_path = wav_path.with_suffix(".ps1")
    ssml_path.write_text(_ssml_for(lines, pitch_pct, kids=kids), encoding="utf-8")
    wav = str(wav_path.resolve()).replace("'", "''")
    ssml_file = str(ssml_path.resolve()).replace("'", "''")
    script = f"""
$ErrorActionPreference = 'Stop'
Add-Type -AssemblyName System.Speech
$speak = New-Object System.Speech.Synthesis.SpeechSynthesizer
$speak.Rate = {int(sapi_rate)}
$speak.Volume = 100
try {{
  $female = $speak.GetInstalledVoices() |
    Where-Object {{ $_.Enabled -and $_.VoiceInfo.Gender -eq 'Female' }} |
    Select-Object -First 1
  if ($female) {{ $speak.SelectVoice($female.VoiceInfo.Name) }}
}} catch {{}}
$speak.SetOutputToWaveFile('{wav}')
$ssml = [System.IO.File]::ReadAllText('{ssml_file}')
try {{
  $speak.SpeakSsml($ssml)
}} catch {{
  $plain = [regex]::Replace($ssml, '<[^>]+>', ' ')
  $speak.Speak($plain)
}}
$speak.Dispose()
"""
    ps1_path.write_text(script, encoding="utf-8")
    flags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-File", str(ps1_path)],
        check=False,
        timeout=90,
        capture_output=True,
        creationflags=flags,
    )
    if result.returncode != 0:
        err = (result.stderr or result.stdout or b"").decode("utf-8", errors="replace")[:400]
        raise RuntimeError(err or f"powershell TTS failed ({result.returncode})")
    for extra in (ssml_path, ps1_path):
        extra.unlink(missing_ok=True)


def _load_wav_mono(path: Path, target_sr: int) -> np.ndarray:
    with wave.open(str(path), "rb") as wf:
        sr = int(wf.getframerate() or target_sr)
        channels = max(1, int(wf.getnchannels()))
        width = int(wf.getsampwidth())
        raw = wf.readframes(wf.getnframes())
    if width == 2:
        data = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32768.0
    elif width == 1:
        data = (np.frombuffer(raw, dtype=np.uint8).astype(np.float32) - 128.0) / 128.0
    elif width == 4:
        data = np.frombuffer(raw, dtype=np.int32).astype(np.float32) / 2147483648.0
    else:
        raise ValueError(f"unsupported wav sample width {width}")
    if channels > 1:
        data = data.reshape(-1, channels).mean(axis=1)
    if sr != target_sr and len(data) > 1:
        data = _resample_mono(data, sr, target_sr)
    peak = float(np.max(np.abs(data)) + 1e-9)
    return (data / peak * 0.88).astype(np.float32)


def _resample_mono(data: np.ndarray, src_sr: int, target_sr: int) -> np.ndarray:
    if src_sr == target_sr or len(data) < 2:
        return data.astype(np.float32)
    x_old = np.linspace(0.0, 1.0, len(data), dtype=np.float64)
    n_new = max(1, int(round(len(data) * target_sr / src_sr)))
    x_new = np.linspace(0.0, 1.0, n_new, dtype=np.float64)
    return np.interp(x_new, x_old, data).astype(np.float32)
