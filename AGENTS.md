# AGENTS.md — autotubenail

## Status
Phase 1 engine implemented. See `prompt.md` (Danish) for full requirements.

## Project
Python CLI thumbnail generator using Pillow. Replaces getstencil.com. Phase 1 builds the engine only; a Flutter frontend comes later.

## Setup (Brug UV)
```bash
uv sync
```

## CLI
```bash
uv run thumbnail --series <navn> --bg <sti> --title "<tekst>" --extra <sti>
```

Alternativt: `uv run python generator.py ...`.

- `--project`: project name; reads `projects/<name>/config.json` instead of root `config.json`
- `--series`: key in config.json (e.g. `tomat-source`)
- `--bg`: path to 16:9 background image
- `--title`: title text; `\n` for line breaks
- `--extra`: optional extra logo (e.g. Python logo)

## Planned directory structure
```
skabeloner/fælles/       — shared fonts + logos
skabeloner/tomat-source/ — series-specific assets
backgrounds/             — 16:9 background images (global template)
output/                  — generated thumbnails
config.json              — template/reference (copy to projects/)
projects/<name>/         — per-project config.json
generator.py             — OOP Pillow engine
```

## Key requirements (from prompt)
- Layer compositing: background → overlays → logos → text → optional extra logo
- Force background to 1920×1080; support alpha-composite for PNGs
- Text: config-driven font/size/color/position/line spacing; `\n` line breaks
- Output: RGBA→RGB, JPEG quality=85 (~200 KB target), filename `{input}-c.jpg`
- Code must be clean, OOP, well-documented (stream audience)

## Config structure
```json
{ "series": { "<name>": { "overlays": [...], "logos": [...], "text_settings": {...} } } }
```

## Source of truth
All requirements are in `prompt.md` (Danish). Do not deviate without user confirmation.

## Build order (per prompt §5)
1. JSON parsing + CLI argument handling
2. Pillow layer compositing
3. Dynamic text rendering with line breaks
4. JPEG compression + file naming
