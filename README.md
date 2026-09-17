# autotubenail

Python CLI thumbnail generator til YouTube livestreams. Erstatning for getstencil.com.

Fase 1 bygger Pillow-motoren. En Flutter-frontend kommer senere.

## Arkitektur

```
skabeloner/fælles/       — fælles skrifttyper og logoer
skabeloner/<serie>/      — seriespecifikke aktiver (overlays, logoer)
icons/                   — ikoner til `icons`-noder (roden uden --project)
backgrounds/               — 16:9 baggrundsbilleder (input)
projects/<navn>/         — brugerprojekt med egen config.json, baggrunde og icons/
output/                  — genererede thumbnails
config.json              — template/reference (kopieres til projects/)
config-icons.json        — template med en `icons`-node (default-liste)
generator.py             — CLI + ThumbnailGenerator-facade
nodes.py                 — node-klasserne (Rect, Image, Text, Group, Icons)
assets.py                — billed-/font-indlæsning inkl. SVG (cairosvg)
```

## Setup

```bash
uv sync
```

## Brug

```bash
uv run thumbnail --series <navn> [--bg <sti>] [--title <tekst>] [--text <id>=<tekst> ...] [--extra <sti>] [--icons [<id>=]<navn>...]
```

| Flag | Påkrævet | Beskrivelse |
|------|----------|-------------|
| `--project` | Nej | Projektnavn — læser `projects/<navn>/config.json` |
| `--series` | Ja | Nøgle i config, f.eks. `tomat-source` |
| `--bg` | Nej | Sti til 16:9 baggrundsbillede. Overstyrer `background`-feltet i config; uden begge fejler kommandoen |
| `--title` | Nej | Titeltekst (alias for `--text main=...`). Brug `\n` for linjeskift |
| `--text` | Nej | Tekst til en pladsholder-id: `--text main="..." --text subtitle="..."`. Repeatable. `--text` vinder over `--title` for samme id |
| `--extra` | Nej | Sti til ekstra logo (skaleres efter config) |
| `--icons` | Nej | Ikoner til en pladsholder-id: `--icons python,tomat` (default id `icons`) eller `--icons række=python,tomat`. Repeatable. Navnene slås op i `icons/`-mappen |

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

Hver serie har et `layers`-array med en træstruktur af lag. En serie kan også
deklarere en `background` (relativ sti — med `--project` løses den mod
projektfolderen):

```json
{
  "series": {
    "<name>": {
      "background": "backgrounds/intro.png",
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
        { "type": "icons", "id": "icons", "x": 60, "y": 930, "height": 70, "spacing": 10, "direction": "horizontal" },
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
| `image` | Billedfil (PNG/JPEG/SVG). `dynamic: true` = path fra `--extra` CLI. `width`/`height` valgfri skalering — angiv begge for præcis størrelse, eller én for proportionel skalering | `path`, `dynamic`, `width`, `height` |
| `text` | Tekst. Wrapper altid; auto-shrinker font ved overflow. `value` overstyres af `--text <id>=<tekst>` CLI (default id `main`) | `id`, `value`, `font`, `size`, `color`, `align`, `line_spacing` |
| `icons` | Pladsholder for en liste af ikoner (vandret eller lodret). Navne slås op i `icons/`-mappen (`<navn>.svg|.png`, case-insensitive). Fyldes af `--icons [<id>=]<navn1>,<navn2>` (default id `icons`), evt. fra `icons` i config | `id`, `icons`, `direction`, `spacing`, `width`, `height` |

### Fælles felter

| Felt | Default | Beskrivelse |
|------|---------|-------------|
| `x`,`y` | `0` | Position relativ til forælder |
| `width`,`height` | `-` | Valgfri fast afgrænsning. Gælder alle typer: `rect`/`image` sætter størrelse, `group` overskriver sin infererede boks, `text` definerer sit eget wrap-område. Angives de ikke, afgrænses objektet af sin container |
| `z_index` | `0` | Overrider depth-first orden (højere = øverst) |
| `visible` | `true` | `false` = springes over |

### Positionering

Alle `x`,`y` er relative til forælderens position. Root-lag har forælder = (0, 0).

### Tekst og wrapping

Tekst wrapper altid og begrænses af sin container:

- **Med egen `width`/`height`** definerer teksten sit eget wrap-område. Det
  bruges fx til at holde flere tekstblokke (fx titel og subtitel) adskilt,
  så de aldrig overlapper hinanden.
- **I en gruppe uden egen `width`/`height`** udledes gruppens areal automatisk
  fra dens målbare børn (`rect`, `image`, næstede grupper). Teksten må aldrig
  overskride det areal: lange ord linjebrydes, og er teksten højere end
  området, formindskes fonten iterativt til den passer (minimum `max(10, size/4)`).
- **Uden for en gruppe** er begrænsningen baggrundsbilledet (1920×1080), målt
  fra tekstens `x`/`y` til billedets kant.
- `\n` i teksten laver stadig manuelle (tvungne) linjeskift oven på wrappingen.
- `align` (`left`/`center`/`right`/`distributed`) regnes relativt til wrap-området.
  `distributed` spreder ordene ud, så linjen (undtagen den sidste) fylder hele
  bredden.
- Overskrider teksten alligevel arealet ved minimums-fonten, tegnes den og en
  advarsel printes til stderr.

### Ikon-lister

En `icons`-node er en pladsholder for en liste af ikoner — domæne-uafhængigt.
Den kan bruges til teknologi-ikoner, ingridienser eller hvad som helst. Hvilke
ikoner der indsættes bestemmes af `--icons [<id>=]<navn1>,<navn2>` CLI
(repeatable; default id `icons`). Uden CLI bruges node'ens eget `icons`-felt,
hvis det er sat.

Navnene slås op i projektets `icons/`-mappe (`icons/` i roden uden `--project`)
som `<navn>.svg` eller `<navn>.png` — case-insensitive, SVG foretrækkes hvis
begge findes. Der findes ingen eksplicit mapping: læg blot filen i `icons/`.

Størrelse angives i config: node'ens `width`/`height` er standard, og hvert
element i `icons`-listen kan overskrive med sin egen `width`/`height`:

```json
{ "type": "icons", "id": "icons", "x": 60, "y": 930,
  "height": 70, "spacing": 10, "direction": "horizontal",
  "icons": ["python", { "name": "tomat", "height": 40 }] }
```

- `direction`: `horizontal` (default) eller `vertical` (`horz`/`vert` accepteres).
- `spacing`: afstand mellem ikonerne (default 10).

```bash
# Ikoner i icons-pladsholderen (default id "icons")
uv run thumbnail --project tomatsource --series tomat-source --icons python,tomat
```

### Baggrund

En serie kan erklære `"background": "backgrounds/intro.png"`. Stien løses mod
projektfolderen med `--project`, ellers mod roden. `--bg` CLI overstyrer altid
config-verdien; angives ingen af dem, fejler kommandoen.

### Billedformater

`image`-noder og baggrunde kan være PNG, JPEG eller SVG. SVG rasteriseres med
cairosvg (tilføjet via `uv add cairosvg`).

### Renderingsrækkefølge

Første lag i `layers`-arrayet = nederst. `z_index` kan overstyre.

## Output

- Format: JPEG, quality=85 (~200 KB)
- Størrelse: 1920×1080
- Navn: `{input}-c.jpg` i `output/`
- Mappen `output/` oprettes automatisk

## Test

Se `docs/TESTING.md` for den fulde testguide (distributed-alignment, SVG,
ikon-lister, baggrund fra config, fejlhåndtering og pixel-regressionstest).
Se `docs/test-icons.md` for en dedikeret ikon-liste-testguide. Hurtige smoke tests:

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

# Baggrund fra config (kræver "background" i seriens config)
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=Config bg" --text "subtitle=Uden --bg"

# Ikon-liste (SVG + PNG fra icons/ mappen)
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=Ikoner" --text "subtitle=Liste" --icons python,tomat

# Distribueret (fuld-justeret) tekst
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=justeret tekst der fylder hele linjen" --text "subtitle=distributed"

# Fejlhåndtering — manglende serie
uv run thumbnail --series findes-ikke --bg backgrounds/test.png --title "test"

# Fejlhåndtering — manglende fil
uv run thumbnail --series tomat-source --bg findes-ikke.png --title "test"
```
