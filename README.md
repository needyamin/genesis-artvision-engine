# Genesis Artvision Engine

**by ANSNEW TECH**

Offline procedural art video factory. Press **GENERATE** and the app invents a seed, engine, style, palette, motion, voice, and soundtrack — then encodes an MP4 locally with FFmpeg.

No topic, stock footage, prompt, or music library is required. Optional OpenRouter advice can suggest creative direction only. **Frames, pictures, voice, and audio stay on this machine.**

Full product article: open [`doc/doc.html`](doc/doc.html) in a browser.

## What it makes

Three engines, each with a matching look. Engine owns the **concept** (text, pictures, narration). Style owns the **grade and motion**.

| Engine | Style | What you get |
|--------|-------|----------------|
| `kids_storybook` — Kids Storybook | `storybook` | Picture-book pages: story title, page text, a drawn noun, slow kids voice |
| `how_it_works` — How It Works | `classroom` | Everyday classroom diagrams (water cycle, heartbeat, electricity…) plus a calm narrator |
| `trend_brief` — Trending Brief | `pulse` | Kinetic type about a current-web topic, documentary voice over a pulse bed |

If you leave Engine or Style on Random, they pair together. If you pick both by hand, the engine still decides the content.

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

Click **GENERATE**. Leave Engine/Style on Random, or pick a storybook / classroom / pulse pair on purpose.

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
python main.py --generate --engine kids_storybook --style storybook
python main.py --generate --engine how_it_works --style classroom
python main.py --generate --engine trend_brief --style pulse

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
5. Add the name to `config.yaml` → `engines` and `ENGINE_PARAM_SPECS` in `randomizer.py`

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
  doc/doc.html    # full product article
  requirements.txt
  app/
    art/          # storybook, how-it-works, trending-brief engines
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
| Story voice or picture feels wrong | Generate a **new** file; old MP4s are not rewritten |
| Disk filling up | Use **Clean Temporary Files** or delete `temp/` |
| Reproduce a video | Use the seed from History / filename metadata in the DB |

## Tests

```bash
python -m pytest tests/ -q
python main.py --test
```

## Notes

- Assets in `assets/music` are optional; the app works with an empty assets folder.
- Story pictures are drawn locally (`assets/education/words/` and `data/ai_scenes/`). Kids voice uses Windows SAPI when available, then an offline fallback.
- Optional **OpenRouter AI advisor** can suggest creative direction. Rendering stays offline.

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

1. **Preferred (cheap):** expand offline catalogs once:

```bash
python main.py --curate
```

Writes `data/ai_catalogs/education.json`. Later generates use cached direction with **no API calls** when per-video AI is off.

2. **Per-video advisor** (optional, costs per call; results cached under `data/ai_cache/`):

```bash
python main.py --generate --ai --engine kids_storybook --count 1
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
4. Leave Engine/Style on **Random**, or pick a matching pair (Kids Storybook + Storybook, How It Works + Classroom, Trending Brief + Pulse).
5. Press **GENERATE**. The Progress panel **AI creative director** box shows live status. The window stays responsive while the advisor runs.
6. Confirm the status bar: `AI applied`. Same seed regenerates the same cached look.
7. For cheap batches: curate often; use per-video AI only when you want a fresh creative-director pass.

The advisor cannot paint photoreal frames or replace the soundtrack with studio vocals. It suggests **image briefs and on-screen text** for the engine you chose. Each engine paints its own frames: story pages, classroom diagrams, or kinetic type.

---

© ANSNEW TECH — Genesis Artvision Engine
