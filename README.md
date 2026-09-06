# Genesis Artvision Engine
By
**ANSNEW TECH**

<img width="1919" height="1032" alt="Image" src="https://github.com/user-attachments/assets/6f5960bd-ee4a-48bd-988a-caff2d8663ed" />

Offline procedural video factory. Press **GENERATE VIDEO** and the app invents a seed, engine, style, palette, background, layout, motion, voice, and soundtrack, then encodes an MP4 locally with FFmpeg.

No stock footage, prompt, or music library is required. Optional OpenRouter advice can suggest creative direction only. Frames, pictures, voice, and audio stay on this machine.

## What it makes

Three engines. The engine owns the concept. The style owns grade, chrome, and motion. Each new seed also picks a procedural background and a safe layout. Those names are stored in the project spec so History can reprint the same picture.

| Engine | Style | What you get |
|--------|-------|----------------|
| `kids_storybook` — Kids Storybook | `storybook` | Picture-book pages, a drawn noun, and a slow kids voice |
| `how_it_works` — How It Works | `classroom` | Classroom diagrams plus a calm narrator |
| `trend_brief` — Trending Brief | `pulse` | Kinetic type, ticker, and documentary voice over a pulse bed |

Leave Engine and Style on Random and they pair together. Each seed still varies the backdrop and layout (desk, window, chalkboard, aurora, radar, mirrored cards, and so on).

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

The window is a two-pane studio: settings across the top, Activity beside Preview, transport and quick actions always visible.

- **Edit preset:** Draft, Standard, or Master
- **Captions:** SRT sidecar, burned, both, or off
- **New prompt:** `Ctrl+P`, then `Ctrl+Enter` to submit
- **Shortcuts:** `Ctrl+Enter` generate, `Esc` stop, `Ctrl+Shift+P` pause, `Ctrl+Shift+R` resume, `Ctrl+H` history, `Ctrl+O` output

When a render finishes, the result card shows the thumbnail, seed, local path, captions, manifest, and either a `youtu.be` link or a short YouTube error.

## Run CLI

```bash
python main.py --generate
python main.py --generate --count 10
python main.py --generate --duration 30 --resolution 1920x1080 --fps 30
python main.py --generate --seed 847293847
python main.py --generate --engine kids_storybook --style storybook
python main.py --generate --engine how_it_works --style classroom
python main.py --generate --engine trend_brief --style pulse
python main.py --test
python main.py --prompt "A bedtime story about a brave orange cat who finds the moon"
python main.py --prompt "Explain how rain is made" --ai
python main.py --generate --edit-preset master --captions both --edit-intensity 1.15
python main.py --generate --youtube --engine how_it_works
python main.py --generate --no-audio --test
```

## Seeds and replay

Every project gets an integer seed. The same seed with the same resolution, fps, and duration reproduces the same video, including the stored background and layout variants.

History stores the complete specification. **Make again from seed** replays those stored parameters instead of the current GUI controls. Older projects without variant fields keep the original desk, whiteboard, or neon look.

## Delivery files

Each successful render can write a matched set in `output/`:

- `.mp4` — H.264/AAC video
- `.srt` — narration-synchronized captions
- `.json` — spec, editorial plan, AI hash, and QC report
- `.jpg` — thumbnail when enabled

QC checks muxed streams, resolution, FPS, frame count, A/V drift, caption timing, loudness, silence, clipping, and sampled black or frozen frames. A broken soundtrack stops the export.

## YouTube upload

The factory can upload the finished MP4 to your channel with an SEO title, hashtags, and a 1280×720 thumbnail. This uses Google’s official OAuth + YouTube Data API.

1. Enable **YouTube Data API v3** and create a Desktop OAuth client.
2. Save `data/youtube/client_secret.json` (copy from `data/youtube/oauth_client.example.json`) or set `YOUTUBE_CLIENT_ID` / `YOUTUBE_CLIENT_SECRET` in `.env`.
3. In the GUI: **YouTube → Connect / switch channel…** and pick the Brand Account.
4. Check **Upload to YouTube**. Default privacy is **Unlisted**.

Quota is about 6 uploads per day (`youtube.daily_limit` in `config.yaml`). Kids Storybook is marked Made for Kids.

## Optional AI advisor

Suggestions only. Rendering stays local.

```powershell
copy .env.example .env
```

```env
OPENROUTER_API_KEY=sk-or-v1-your-key-here
```

```bash
python main.py --curate
python main.py --generate --ai --engine kids_storybook --count 1
```

Or enable **AI advisor** in the GUI. Defaults keep `ai.enabled: false`.

## Project structure

```
random_art_video_factory/
  main.py
  config.yaml
  requirements.txt
  app/
    art/          # engines, layouts, backgrounds, typography
    audio/        # voice, music, mastering
    ai/           # optional OpenRouter advisor
    core/         # randomizer, factory, scheduler
    database/     # SQLite history
    gui/          # PySide6 studio
    publish/      # YouTube upload and SEO thumb
    video/        # FFmpeg, captions, QC
    utils/
  assets/         # app icons only
  data/youtube/   # OAuth example; tokens stay local
  output/         # generated MP4 + sidecars
  temp/
  tests/
```

Word cards and AI scenes are drawn on demand and cached locally. They are not shipped in the repo.

## Tests

```bash
python -m pytest tests/ -q
python main.py --test
```

## Troubleshooting

| Problem | Fix |
|--------|-----|
| `FFmpeg was not found` | Install FFmpeg and restart the terminal |
| GUI will not start | `pip install PySide6` |
| Slow renders | Use `--test`, Draft, or a shorter duration |
| Soundtrack generation failed | Check the log and TTS/FFmpeg; export stops so a silent file is not treated as finished |
| Disk filling up | **File → Clean temp files** or delete `temp/` |
| Reproduce a video | Use the seed from History |
| YouTube 403 | Enable YouTube Data API v3 on the same Cloud project as the OAuth client |
| Wrong YouTube channel | **YouTube → Connect / switch channel…** and pick the Brand Account |

---

© ANSNEW TECH — Genesis Artvision Engine
