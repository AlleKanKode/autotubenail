# autotubenail

Python CLI thumbnail generator til YouTube livestreams. Erstatning for getstencil.com.

Fase 1 bygger Pillow-motoren. En Flutter-frontend kommer senere.

## Arkitektur

```
skabeloner/fælles/       — fælles skrifttyper og logoer
skabeloner/<serie>/      — seriespecifikke aktiver (overlays, logoer)
baggrunde/               — 16:9 baggrundsbilleder (input)
output/                  — genererede thumbnails
config.json              — layout-definitioner pr. serie
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
| `--serie` | Ja | Nøgle i `config.json`, f.eks. `tomat-source` |
| `--bg` | Ja | Sti til 16:9 baggrundsbillede |
| `--titel` | Ja | Titeltekst. Brug `\n` for linjeskift |
| `--ekstra` | Nej | Sti til ekstra logo (skaleres efter config) |

### Eksempler

```bash
uv run thumbnail --serie tomat-source --bg baggrunde/intro.png --titel "Hej verden"
uv run thumbnail --serie tomat-source --bg baggrunde/intro.png \
  --titel "Re\nfactor\nkode\npiv\nbilligt" \
  --ekstra skabeloner/python.png
```

## Config

Serier defineres i `config.json`:

```json
{
  "serier": {
    "<navn>": {
      "overlays": [
        { "sti": "...", "x": 0, "y": 0 }
      ],
      "logoer": [
        { "sti": "...", "x": 50, "y": 50 }
      ],
      "ekstra_logo": {
        "x": 1750, "y": 50,
        "bredde": 100, "hoejde": 100
      },
      "tekst_opsætning": {
        "skrifttype": "...",
        "størrelse": 65,
        "farve": [255, 255, 255],
        "x": 1300, "y": 400,
        "linjeafstand": 15
      }
    }
  }
}
```

Lag-rækkefølge: baggrund → overlays → logoer → ekstra_logo → tekst.

## Output

- Format: JPEG, quality=85 (~200 KB)
- Størrelse: 1920×1080
- Navn: `{input}-c.jpg` i `output/`
- Mappen `output/` oprettes automatisk

## Test

```bash
# Smoke test
uv run thumbnail --serie tomat-source --bg baggrunde/test.png --titel "Hej verden"

# Linjeskift
uv run thumbnail --serie tomat-source --bg baggrunde/test.png \
  --titel "Re\nfactor\nkode"

# Med ekstra logo
uv run thumbnail --serie tomat-source --bg baggrunde/test.png \
  --titel "Test" --ekstra skabeloner/python.png

# Fejlhåndtering — manglende serie
uv run thumbnail --serie findes-ikke --bg baggrunde/test.png --titel "test"

# Fejlhåndtering — manglende fil
uv run thumbnail --serie tomat-source --bg findes-ikke.png --titel "test"
```
