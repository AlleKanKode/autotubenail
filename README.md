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
uv run thumbnail --series <navn> --bg <sti> --title "<tekst>" [--extra <sti>]
```

| Flag | Påkrævet | Beskrivelse |
|------|----------|-------------|
| `--project` | Nej | Projektnavn — læser `projects/<navn>/config.json` |
| `--series` | Ja | Nøgle i config, f.eks. `tomat-source` |
| `--bg` | Ja | Sti til 16:9 baggrundsbillede |
| `--title` | Ja | Titeltekst. Brug `\n` for linjeskift |
| `--extra` | Nej | Sti til ekstra logo (skaleres efter config) |

Uden `--project` bruges rodens `config.json` (template). Med `--project` bruges `projects/<navn>/config.json`.

### Eksempler

```bash
# Global template
uv run thumbnail --series tomat-source --bg backgrounds/intro.png --title "Hej verden"

# Med ekstra logo
uv run thumbnail --series tomat-source --bg backgrounds/intro.png \
  --title "Re\nfactor\nkode\npiv\nbilligt" \
  --extra skabeloner/python.png

# Projekt-specifik config
cp config.json projects/min-serie/
# rediger projects/min-serie/config.json
uv run thumbnail --project min-serie --series min-serie --bg ...
```

## Config

`config.json` i roden er en template/reference. Kopier den til `projects/<navn>/config.json` og rediger.

Hver serie har et `layers`-array med en træstruktur af lag:

```json
{
  "series": {
    "<name>": {
      "layers": [
        { "type": "rect", "color": [0, 0, 0, 199], "x": 0, "y": 0, "width": 400, "height": 1080 },
        { "type": "image", "path": "...", "x": 1200, "y": 0 },
        {
          "type": "group", "x": 0, "y": 0,
          "children": [
            { "type": "image", "path": "...", "x": 50, "y": 50 }
          ]
        },
        { "type": "image", "dynamic": true, "x": 1750, "y": 50, "width": 100, "height": 100 },
        { "type": "text", "value": "", "font": "...", "size": 65, "color": [255,255,255], "align": "left", "x": 1300, "y": 400, "line_spacing": 15 }
      ]
    }
  }
}
```

### Lagtyper

| Type | Beskrivelse | Specifikke felter |
|------|-------------|-------------------|
| `group` | Container med børn. `x`,`y` forskydes relativt til forælder | `children` |
| `rect` | Solid RGBA-rektangel | `color`, `width`, `height` |
| `image` | Billedfil (PNG). `dynamic: true` = path fra `--extra` CLI. `width`/`height` valgfri skalering — angiv begge for præcis størrelse, eller én for proportionel skalering | `path`, `dynamic`, `width`, `height` |
| `text` | Tekst. Wrapper altid til sin container; auto-shrinker font ved overflow. `value` overstyres af `--title` CLI | `value`, `font`, `size`, `color`, `align`, `line_spacing` |

### Fælles felter

| Felt | Default | Beskrivelse |
|------|---------|-------------|
| `x`,`y` | `0` | Position relativ til forælder |
| `z_index` | `0` | Overrider depth-first orden (højere = øverst) |
| `visible` | `true` | `false` = springes over |

### Positionering

Alle `x`,`y` er relative til forælderens position. Root-lag har forælder = (0, 0).

### Tekst og wrapping

Tekst wrapper altid og begrænses af det objekt (gruppe) den indgår i:

- **I en gruppe** udledes gruppens areal (bredde × højde) automatisk fra dens
  ikke-tekst børn (`rect`, `image`, næstede grupper). Teksten må aldrig
  overskride det areal: lange ord linjebrydes, og er teksten højere end
  gruppen, formindskes fonten iterativt til den passer (minimum `max(10, size/4)`).
- **Uden for en gruppe** er begrænsningen baggrundsbilledet (1920×1080), målt
  fra tekstens `x`/`y` til billedets kant.
- `\n` i titlen laver stadig manuelle (tvungne) linjeskift oven på wrappingen.
- `align` (`left`/`center`/`right`) regnes relativt til containeren.
- Overskrider teksten alligevel arealet ved minimums-fonten, tegnes den og en
  advarsel printes til stderr.

### Renderingsrækkefølge

Første lag i `layers`-arrayet = nederst. `z_index` kan overstyre.

## Output

- Format: JPEG, quality=85 (~200 KB)
- Størrelse: 1920×1080
- Navn: `{input}-c.jpg` i `output/`
- Mappen `output/` oprettes automatisk

## Test

```bash
# Smoke test (global template)
uv run thumbnail --series tomat-source --bg backgrounds/test.png --title "Hej verden"

# Linjeskift
uv run thumbnail --series tomat-source --bg backgrounds/test.png \
  --title "Re\nfactor\nkode"

# Med ekstra logo
uv run thumbnail --series tomat-source --bg backgrounds/test.png \
  --title "Test" --extra skabeloner/python.png

# Projekt-specifik config
mkdir -p projects/my-test && cp config.json projects/my-test/
uv run thumbnail --project my-test --series tomat-source \
  --bg backgrounds/test.png --title "Projekt test"

# Fejlhåndtering — manglende serie
uv run thumbnail --series findes-ikke --bg backgrounds/test.png --title "test"

# Fejlhåndtering — manglende fil
uv run thumbnail --series tomat-source --bg findes-ikke.png --title "test"
```
