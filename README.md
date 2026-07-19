# autotubenail

Python CLI thumbnail generator til YouTube livestreams. Erstatning for getstencil.com.

Fase 1 bygger Pillow-motoren. En Flutter-frontend kommer senere.

## Arkitektur

```
skabeloner/fælles/       — fælles skrifttyper og logoer
skabeloner/<serie>/      — seriespecifikke aktiver (overlays, logoer)
backgrounds/               — 16:9 baggrundsbilleder (input)
projects/<navn>/         — brugerprojekt med egen config.json
output/                  — genererede thumbnails
config.json              — template/reference (kopieres til projects/)
generator.py             — Pillow-motoren (OOP)
```

## Setup

```bash
uv sync
```

## Brug

```bash
uv run thumbnail --serie <navn> --bg <sti> --titel "<tekst>" [--ekstra <sti>]
```

| Flag | Påkrævet | Beskrivelse |
|------|----------|-------------|
| `--project` | Nej | Projektnavn — læser `projects/<navn>/config.json` |
| `--serie` | Ja | Nøgle i config, f.eks. `tomat-source` |
| `--bg` | Ja | Sti til 16:9 baggrundsbillede |
| `--titel` | Ja | Titeltekst. Brug `\n` for linjeskift |
| `--ekstra` | Nej | Sti til ekstra logo (skaleres efter config) |

Uden `--project` bruges rodens `config.json` (template). Med `--project` bruges `projects/<navn>/config.json`.

### Eksempler

```bash
# Global template
uv run thumbnail --serie tomat-source --bg backgrounds/intro.png --titel "Hej verden"

# Med ekstra logo
uv run thumbnail --serie tomat-source --bg backgrounds/intro.png \
  --titel "Re\nfactor\nkode\npiv\nbilligt" \
  --ekstra skabeloner/python.png

# Projekt-specifik config
cp config.json projects/min-serie/
# rediger projects/min-serie/config.json
uv run thumbnail --project min-serie --serie min-serie --bg ...
```

## Config

`config.json` i roden er en template/reference. Kopier den til `projects/<navn>/config.json` og rediger.

Serier defineres således:

```json
{
  "series": {
    "<name>": {
      "overlays": [
        { "path": "...",  "x": 0, "y": 0 },
        { "color": [20, 20, 40, 200], "x": 0, "y": 700, "width": 1920, "height": 380 }
      ],
      "logos": [
        { "path": "...", "x": 50, "y": 50 }
      ],
      "extra_logo": {
        "x": 1750, "y": 50,
        "width": 100, "height": 100
      },
      "text_settings": {
        "font": "...",
        "size": 65,
        "color": [255, 255, 255],
        "x": 1300, "y": 400,
        "line_spacing": 15
      }
    }
  }
}
```

Overlay kan være en fil (`path`) eller en solid farve (`color` med RGBA + `width`/`height`).

Lag-rækkefølge: baggrund → overlays → logos → extra_logo → tekst.

## Output

- Format: JPEG, quality=85 (~200 KB)
- Størrelse: 1920×1080
- Navn: `{input}-c.jpg` i `output/`
- Mappen `output/` oprettes automatisk

## Test

```bash
# Smoke test (global template)
uv run thumbnail --serie tomat-source --bg backgrounds/test.png --titel "Hej verden"

# Linjeskift
uv run thumbnail --serie tomat-source --bg backgrounds/test.png \
  --titel "Re\nfactor\nkode"

# Med ekstra logo
uv run thumbnail --serie tomat-source --bg backgrounds/test.png \
  --titel "Test" --ekstra skabeloner/python.png

# Projekt-specifik config
mkdir -p projects/my-test && cp config.json projects/my-test/
uv run thumbnail --project my-test --serie tomat-source \
  --bg backgrounds/test.png --titel "Projekt test"

# Fejlhåndtering — manglende serie
uv run thumbnail --serie findes-ikke --bg backgrounds/test.png --titel "test"

# Fejlhåndtering — manglende fil
uv run thumbnail --serie tomat-source --bg findes-ikke.png --titel "test"
```
