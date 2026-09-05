# Genesis Artvision Engine

**by ANSNEW TECH**

Offline procedural art video factory. Press **GENERATE** and the app invents a seed, art engine, style, palette, motion, voice, and soundtrack — then encodes an MP4 locally with FFmpeg.

No topic, stock footage, prompt, or music library is required. Optional OpenRouter advice can suggest creative direction only. **Frames, pictures, voice, and audio stay on this machine.**

Full product article: open [`doc.html`](doc.html) in a browser.

## What it makes

| Family | Engines | What you get |
|--------|---------|----------------|
| Abstract art | `particles`, `galaxy`, `waves`, `tunnel` | Motion graphics with grade, camera, and procedural music |
| Kids learning | `alphabet_cartoon`, `kids_doodles`, `hand_art` | Alphabet, dictionary spelling + meaning, real-world add/take-away math, slow kids TTS |
| Documentary | `infographic_explainer` | Science HUD explainers with a calm narrator |

Seven looks: **abstract, cosmic, minimal, organic, digital, playful, documentary**. Kids engines stay broadcast-clean (no cosmic grain over letters). Each teaching beat keeps the **same letter, word, voice, and picture**.

## Requirements

- Python 3.11+ (tested on 3.14)
- FFmpeg on PATH
- Windows first (Linux/macOS should work with FFmpeg; kids voice prefers Windows SAPI)

## Installation

```bash
cd random_art_video_factory
python -m pip install -r requirements.txt
```

Install FFmpeg if needed:

- Windows: `winget install Gyan.FFmpeg`
- Or download from https://ffmpeg.org and add `bin` to PATH

Verify:

```bash
ffmpeg -version
python main.py --test
```

## Run GUI

```bash
python main.py
```

Click **GENERATE**. Leave Engine/Style on Random, or pick a kids / documentary engine on purpose.

## Run CLI

```bash
# One video
python main.py --generate

# Ten videos
python main.py --generate --count 10

# Custom settings
python main.py --generate --duration 30 --resolution 1920x1080 --fps 30

# Deterministic seed
python main.py --generate --seed 847293847

# Force engine / style
python main.py --generate --engine galaxy --style cosmic
python main.py --generate --engine alphabet_cartoon --style playful

# Fast developer test (320x180, 10fps, 3s)
python main.py --test

# No audio
python main.py --generate --no-audio --test
```

## How deterministic seeds work

Every project gets an integer seed. The `Randomizer` builds a `ProjectSpec` (engine, style, parameters, palette) from that seed using NumPy's `Generator`. Re-running with the same seed and the same resolution/fps/duration overrides reproduces the same video.

Example:

```bash
python main.py --generate --seed 12345 --resolution 1280x720 --fps 30 --duration 15
```

History stores seed + parameter JSON so you can re-generate from the GUI (**View History → Re-generate from Seed**).

## How to add a new art engine

1. Create `app/art/my_engine.py`
2. Subclass `ArtEngine`, set `name`, implement `render_frame`
3. Decorate with `@register_engine`
4. Import it from `ensure_engines_loaded()` in `app/art/base.py`
5. Add the name to `config.yaml` → `engines` and optionally `ENGINE_PARAM_SPECS` in `randomizer.py`

```python
from app.art.base import ArtEngine, register_engine
import numpy as np

@register_engine
class MyEngine(ArtEngine):
    name = "my_engine"
    description = "Example"

    def render_frame(self, frame_number, total_frames):
        frame = self._blank()
        # draw...
        return self._to_uint8(frame)
```

## Project structure

```
random_art_video_factory/
  main.py
  config.yaml
  doc.html        # full product article
  requirements.txt
  app/
    art/          # procedural engines + kids lessons
    audio/        # kids TTS, documentary voice, music
    ai/           # optional OpenRouter advisor (offline realize)
    core/         # randomizer, factory, scheduler
    database/     # SQLite history
    gui/          # PySide6 UI
    video/        # FFmpeg pipe renderer
    utils/
  assets/         # app icon, optional music, word cards
  output/         # generated MP4 + thumbnails
  temp/           # wiped after success
  tests/
```

## Troubleshooting

| Problem | Fix |
|--------|-----|
| `FFmpeg was not found` | Install FFmpeg and restart the terminal/app |
| GUI won't start | `pip install PySide6` |
| Slow renders | Use `--test`, lower resolution, or shorter duration |
| No audio in MP4 | Check logs; video still encodes if audio fails |
| Kids voice too fast / wrong word | Generate a **new** file after the teaching-lock update; old MP4s are not rewritten |
| Disk filling up | Use **Clean Temporary Files** or delete `temp/` |
| Reproduce a video | Use the seed from History / filename metadata in the DB |

## Tests

```bash
python -m pytest tests/ -q
python main.py --test
```

## Notes

- Assets in `assets/music` are optional; the app works with an empty assets folder.
- Kids pictures are drawn locally (`assets/education/words/` and `data/ai_scenes/`). Kids voice uses Windows SAPI when available, then an offline fallback.
- Optional **OpenRouter AI advisor** can suggest creative direction / expand kids catalogs. Rendering stays offline.

## Optional AI advisor (OpenRouter)

Suggestions only — no cloud image/video generation. Frame render, audio, and FFmpeg stay local.

### Where to put `OPENROUTER_API_KEY`

Because this repo is **public on GitHub**, never commit real keys.

1. Copy the example file in the **project root**:

```powershell
copy .env.example .env
```

2. Edit `.env` and paste your key:

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

3. Keep `.env` local only — it is listed in `.gitignore`. Commit `.env.example` (no secrets), never `.env`.

The app loads `.env` automatically from the project root (see `app/utils/dotenv.py`). You can still override with a real environment variable if set.

Get a key: [openrouter.ai/keys](https://openrouter.ai/keys).

### Using the advisor

1. **Preferred (cheap):** expand offline education catalogs once:

```bash
python main.py --curate
python main.py --curate --letters A,B,C
```

Writes `data/ai_catalogs/education.json`. Later generates use it with **no API calls**.

2. **Per-video advisor** (optional, costs per call; results cached under `data/ai_cache/`):

```bash
python main.py --generate --ai --engine alphabet_cartoon --count 1
```

Or enable **AI creative advisor (OpenRouter)** in the GUI Extras panel / set in `config.yaml`:

```yaml
ai:
  enabled: true
  per_video: true
  model: "openai/gpt-4o-mini"
```

Defaults keep `enabled: false` so the app remains fully offline. If Gemini models return HTTP 402, add OpenRouter credits or keep `openai/gpt-4o-mini`.

### How to generate more accurate creative videos

1. Put `OPENROUTER_API_KEY` in root `.env` (see `.env.example`).
2. Expand offline content cheaply once: `python main.py --curate`
3. Start the GUI and enable **AI creative advisor (OpenRouter)** in Extras.
4. Leave Engine/Style on **Random** (or pick a kids engine on purpose).
5. Press **GENERATE**. The Progress panel **AI creative director** box shows live status. The window stays responsive while the advisor runs.
6. Confirm the status bar: `AI applied`. Same seed regenerates the same cached look.
7. For cheap batches: curate often; use per-video AI only when you want a fresh creative-director pass.

The advisor cannot paint photoreal frames or replace the soundtrack with studio vocals. It suggests **image briefs and on-screen text** per beat. The **offline illustrator** draws those cards locally. Kids lessons **lock** letter, word, voice, and picture together so a suggestion cannot teach the wrong word.

---

© ANSNEW TECH — Genesis Artvision Engine
