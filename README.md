# Genesis Artvision Engine

**by ANSNEW TECH**

Offline procedural art video generator. No cloud APIs, no AI models, no user prompts.

The app invents a seed, style, art engine, colors, motion, and audio — then encodes an MP4 with FFmpeg.

## Requirements

- Python 3.11+ (tested on 3.14)
- FFmpeg on PATH
- Windows first (Linux/macOS should work with FFmpeg installed)

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

Click **GENERATE**. No topic, image, prompt, or music required.

## Run CLI

```bash
# One video
python main.py --generate

# Ten videos
python main.py --generate --count 10

# One hundred videos
python main.py --generate --count 100

# Custom settings
python main.py --generate --duration 30 --resolution 1920x1080 --fps 30

# Deterministic seed
python main.py --generate --seed 847293847

# Force engine / style
python main.py --generate --engine galaxy --style cosmic

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
  requirements.txt
  app/
    art/          # procedural engines
    audio/        # procedural WAV generation
    core/         # randomizer, factory, scheduler
    database/     # SQLite history
    gui/          # PySide6 UI
    video/        # FFmpeg pipe renderer
    utils/
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
| Disk filling up | Use **Clean Temporary Files** or delete `temp/` |
| Reproduce a video | Use the seed from History / filename metadata in the DB |

## Tests

```bash
python -m pytest tests/ -q
python main.py --test
```

## Notes

- Assets in `assets/music` are optional; the app works with an empty assets folder.
- Designed so local AI modules could be added later as optional plugins — none are required now.

---

© ANSNEW TECH — Genesis Artvision Engine
