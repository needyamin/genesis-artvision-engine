# Genesis Artvision Engine

**by ANSNEW TECH**


<img width="1919" height="1029" alt="Image" src="https://github.com/user-attachments/assets/1a8a2434-921b-4fb6-9760-3efe0ac7d756" />

Offline procedural art video factory. Press **GENERATE** and the app invents a seed, engine, style, palette, motion, voice, and soundtrack — then encodes an MP4 locally with FFmpeg.

No topic, stock footage, prompt, or music library is required. Optional OpenRouter advice can suggest creative direction only. **Frames, pictures, voice, and audio stay on this machine.**

Full product article: open [`doc/doc.html`](doc/doc.html) in a browser.

<img width="1919" height="1030" alt="Image" src="https://github.com/user-attachments/assets/a3253e61-7d3d-4df4-a5b9-d2148ee5daa4" />

## What it makes

Three engines, each with a matching look. Engine owns the **concept** (text, pictures, narration). Style owns the **grade and motion**.

| Engine | Style | What you get |
|--------|-------|----------------|
| `kids_storybook` — Kids Storybook | `storybook` | Picture-book pages: story title, page text, a drawn noun, slow kids voice |
| `how_it_works` — How It Works | `classroom` | Everyday classroom diagrams (water cycle, heartbeat, electricity…) plus a calm narrator |
| `trend_brief` — Trending Brief | `pulse` | Kinetic type about an evergreen or AI-suggested topic, documentary voice over a pulse bed |

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

The home screen uses a balanced two-pane production layout. A compact full-width control deck keeps every project setting visible without scrolling; Activity and QC sit beside an aspect-correct preview below it. The preview no longer dominates the window, and pane sizes are restored at startup. Click **GENERATE VIDEO**; leave Engine/Style on Random, or choose a storybook / classroom / pulse pair.

Choose an **Edit preset**: Draft for quick previews, Standard for normal publishing, or Master for stronger finishing, slower encoding, and burned plus sidecar captions. You can separately choose caption mode and edit intensity. The automatic director measures narration, validates reading speed, weights important beats, drives true scene-to-scene transitions and responsive motion, mixes to a consistent loudness target, and checks the completed package before reporting success.

Open **New prompt** from the right rail or `Ctrl+P`. Type what you want, choose **Offline** or **AI suggestion**, and submit with the button or `Ctrl+Enter`. The app picks an engine, times the voice, and encodes Full HD (or 4K). Same prompt words make the same seed.

Studio shortcuts: `Ctrl+Enter` generate, `Esc` stop, `Ctrl+Shift+P` pause, `Ctrl+Shift+R` resume, `Ctrl+P` prompt, `Ctrl+H` history, and `Ctrl+O` output.

When a render finishes, a **result card** shows the thumbnail, seed, local path, and either a `youtu.be` link or a short YouTube error — not a raw 403 dump.

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

# From a written prompt (offline plan)
python main.py --prompt "A bedtime story about a brave orange cat who finds the moon"

# Prompt + OpenRouter plan
python main.py --prompt "Explain how rain is made" --ai

# Broadcast master with burned captions plus SRT
python main.py --generate --edit-preset master --captions both --edit-intensity 1.15

# Generate then upload to your YouTube channel (connect in the GUI first)
python main.py --generate --youtube --engine how_it_works

# No audio
python main.py --generate --no-audio --test
```

## How deterministic seeds work

Every project gets an integer seed. The `Randomizer` builds a `ProjectSpec` (engine, style, parameters, palette) from that seed using NumPy's `Generator`. Re-running with the same seed and the same resolution/fps/duration overrides reproduces the same video.

Example:

```bash
python main.py --generate --seed 12345 --resolution 1280x720 --fps 30 --duration 15
```

History stores the complete project specification. **Make again from seed** replays those stored parameters instead of using the current GUI controls.

## Professional delivery files

Each successful render can produce a matched set in `output/`:

- `.mp4` — final H.264/AAC video
- `.srt` — narration-synchronized captions
- `.json` — reproducibility manifest containing the full spec, editorial shot plan, AI prompt hash, future source-provenance fields, and QC report
- `.jpg` — thumbnail when enabled

The QC pass verifies muxed stream presence, exact resolution/FPS/frame count, A/V drift, SRT timing and overlap, integrated loudness, silence/clipping risk, sampled black/frozen frames, and manifest completeness. A broken soundtrack or structurally invalid package stops the export instead of silently creating an unfinished video.

## Broadcast procedural editing

- Headlines and body copy use fitted multiline typography rather than fixed character cuts.
- Brief layouts adapt independently to 16:9, 9:16, and square safe zones.
- Dissolve, push, flash, and page-turn transitions composite outgoing and incoming scenes.
- Trend Brief uses deterministic multi-depth motion; How It Works draws diagrams progressively; Storybook uses layered paper and page depth.
- OpenRouter may suggest shot purpose, hierarchy, emphasis, transitions, and sound cues. Those suggestions are validated, cached by prompt/model, and realized entirely with local procedural rendering.
- Audio cues share the same shot markers and BPM as the visual edit; final audio is padded or trimmed to the exact frame-authoritative duration.

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
    gui/          # PySide6 dark studio UI
    publish/      # YouTube Data API upload + SEO thumb
    video/        # FFmpeg pipe renderer
    utils/
  data/youtube/   # OAuth example only — tokens stay gitignored
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
| Soundtrack generation failed | Check the log and TTS/FFmpeg setup; the export stops so a silent file is not mistaken for a finished video |
| Story voice or picture feels wrong | Generate a **new** file; old MP4s are not rewritten |
| Disk filling up | Use **File → Clean temp files** or delete `temp/` |
| Reproduce a video | Use the seed from History / filename metadata in the DB |
| YouTube 403 / API not used | Enable **YouTube Data API v3** on the same Google Cloud project as your OAuth client, wait 2–5 minutes, then generate again (the MP4 is already in `output/`) |
| Wrong YouTube channel | **YouTube → Connect / switch channel…** and pick the Brand Account, not only Gmail |

## Tests

```bash
python -m pytest tests/ -q
python main.py --test
```

## Notes

- Assets in `assets/music` are optional; the app works with an empty assets folder.
- Story pictures are drawn locally (`assets/education/words/` and `data/ai_scenes/`). Kids voice uses Windows SAPI when available, then an offline fallback.
- Optional **OpenRouter AI advisor** can suggest creative direction. Rendering stays offline.
- Optional **YouTube upload** uses the official YouTube Data API after you connect your own channel.
  
<img width="1262" height="379" alt="Image" src="https://github.com/user-attachments/assets/5a0efc7b-50fb-46fd-ba9b-65c6162fd4a6" />

## YouTube auto-upload

The factory can create a video and then upload it to **your** channel with an SEO title, description hashtags, tags, and a 1280×720 thumbnail. This uses Google’s official OAuth + `videos.insert` / `thumbnails.set`. It does not scrape YouTube or bypass sign-in.

1. In [Google Cloud Console](https://console.cloud.google.com/apis/credentials) create a project, enable **YouTube Data API v3**, and create an OAuth client ID of type **Desktop app**.
2. Put the credentials in **either** place (both are gitignored):
   - Download the JSON → save as `data/youtube/client_secret.json` (copy from `data/youtube/oauth_client.example.json`), **or**
   - Add to `.env`:

```env
YOUTUBE_CLIENT_ID=123456789.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=GOCSPX-your-secret
```

3. `python -m pip install google-api-python-client google-auth-oauthlib google-auth-httplib2` (already in `requirements.txt`)
4. Run the GUI → **YouTube → Connect / switch channel…** and sign in as the channel owner. If you have several channels, pick the **Brand Account** whose name matches the one you want.
5. Check **Upload to YouTube**. Privacy defaults to **Unlisted** so you can review in YouTube Studio before going public.
6. Press **GENERATE VIDEO**. After the MP4 is saved, the app uploads title + hashtags + thumbnail. The result card shows the channel and `youtu.be` link, or a short fix if Google refuses.

Default API quota is about **6 uploads per day** (`youtube.daily_limit` in `config.yaml`). Kids Storybook is marked Made for Kids because that is YouTube’s rule for that engine.

Keep listings honest: titles and hashtags come from the actual story or topic on screen.

<img width="1313" height="456" alt="Image" src="https://github.com/user-attachments/assets/45ecb7ef-bc3d-47a7-ab68-7e0ca2c66570" />

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

Writes `data/ai_catalogs/education.json` for catalog curation. The current render engines still use their embedded catalogs; runtime catalog ingestion and verified public web sources are planned for the next content-source milestone.

2. **Per-video advisor** (optional, costs per call; results cached under `data/ai_cache/`):

```bash
python main.py --generate --ai --engine kids_storybook --count 1
```

Or enable **AI advisor** in the GUI Output panel / set in `config.yaml`:

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
3. Start the GUI and enable **AI advisor** in the Output panel.
4. Leave Engine/Style on **Random**, or pick a matching pair (Kids Storybook + Storybook, How It Works + Classroom, Trending Brief + Pulse).
5. Press **GENERATE VIDEO**. The Progress panel **AI** box shows live status. The window stays responsive while the advisor runs.
6. Confirm the status bar: `AI applied`. Same seed regenerates the same cached look.
7. For cheap batches: curate often; use per-video AI only when you want a fresh creative-director pass.

The advisor cannot paint photoreal frames or replace the soundtrack with studio vocals. It suggests **image briefs and on-screen text** for the engine you chose. Each engine paints its own frames: story pages, classroom diagrams, or kinetic type.

The application does **not** currently scrape or verify live internet sources. OpenRouter is used only for optional creative direction. A future source layer will use public feeds/pages with citations and provenance while keeping rendering local.

---

© ANSNEW TECH — Genesis Artvision Engine
