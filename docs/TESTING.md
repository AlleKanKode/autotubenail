# Test af autotubenail-motoren

Denne guide beskriver, hvordan man manuelt tester de funktioner, der blev
implementeret i refaktoreringen: node-klasserne i `nodes.py`, `distributed`-alignment,
baggrund fra config, SVG-understøttelse og ikon-lister (`icons`-node).

Alle kommandoer køres fra projektroden. Kør først `uv sync` for at installere
afhængighederne (inkl. `cairosvg`).

---

## 1. Smoke test — basal generering

Kør den globale template:

```bash
uv run thumbnail --series tomat-source --bg backgrounds/test.png --title "Hej verden"
```

Forventet: `Thumbnail saved: output/test-c.jpg`

Verificér outputtet:

```bash
uv run python -c "
from PIL import Image
im = Image.open('output/test-c.jpg')
print(im.size, im.mode)   # (1920, 1080) RGB
"
```

| Tjek | Forventning |
|------|-------------|
| Størrelse | 1920×1080 |
| Format/mode | RGB (JPEG) |
| Navn | `{input}-c.jpg` i `output/` |
| Størrelse på disk | ~200 KB (kan variere med motivet) |

Med ekstra logo (`--extra`) og linjeskift (`\n`):

```bash
uv run thumbnail --series tomat-source --bg backgrounds/test.png --title "Test" --extra skabeloner/python.png
uv run thumbnail --series tomat-source --bg backgrounds/test.png --title "Re\nfactor\nkode"
```

---

## 2. Projekt-config og baggrund fra config

Projektet `tomatsource` har `"background": "backgrounds/ts71-metal-raket.jpg"` i
sin series-config, så `--bg` kan udelades:

```bash
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=Config bg" --text "subtitle=Uden --bg flag"
```

Forventet: `output/ts71-metal-raket-c.jpg` (baggrunden løst relativt til
`projects/tomatsource/`).

`--bg` overstyrer altid config-feltet:

```bash
uv run thumbnail --project tomatsource --series tomat-source --bg backgrounds/ts70-trae-raket.jpg \
  --text "main=Override" --text "subtitle=Bg vinder"
```

Forventet: `output/ts70-trae-raket-c.jpg`.

---

## 3. `distributed`-alignment

Testen sammenligner `left` og `distributed` med samme tekst: en distribueret
linje skal nå til højre kant af wrap-området, mens den sidste linje forbliver
venstrestillet.

```bash
uv run python - <<'EOF'
from PIL import Image
from nodes import TextNode, RenderContext

def render(align):
    img = Image.new("RGBA", (600, 300), (255, 255, 255, 255))
    node = TextNode({
        "type": "text", "id": "main", "value": "",
        "font": "skabeloner/fælles/Ubuntu-Bold.ttf", "size": 30,
        "color": [0, 0, 0], "align": align, "x": 20, "y": 20,
        "width": 560, "height": 250, "line_spacing": 5,
    })
    ctx = RenderContext(texts={"main": "en lang tekst der skal justeres til hojre kant nu"})
    return node.render(img, 0, 0, ctx, (0, 0, 600, 300))

def line_bands(img, dark=128):
    px = img.convert("L").load()
    has_dark = [False] * img.height
    maxx = [-1] * img.height
    for y in range(img.height):
        for x in range(img.width):
            if px[x, y] < dark:
                has_dark[y] = True
                maxx[y] = x
    bands = []
    start = prev = None
    for y in range(img.height):
        if has_dark[y]:
            start = start if start is not None else y
            prev = y
        elif start is not None and y - prev >= 3:
            bands.append((start, prev, max(maxx[start:prev + 1])))
            start = None
    if start is not None:
        bands.append((start, prev, max(maxx[start:prev + 1])))
    return bands

print("left:", line_bands(render("left")))
print("dist:", line_bands(render("distributed")))
print("box right edge:", 20 + 560)
EOF
```

Forventet output (tilnærmet):

```
left: [(26, 53, 563), (61, 82, 123)]
dist: [(26, 53, 578), (61, 82, 123)]
box right edge: 580
```

Kontrol: i `dist` rækker første linje helt ud mod `580`, mens sidste linje har
samme højre kant som `left` (`123`).

Alternativ integrationstest via config (kræver at en `text`-node har
`"align": "distributed"`):

```bash
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=justeret tekst der fylder hele linjen" --text "subtitle=distributed"
```

---

## 4. SVG-understøttelse

Den hurtigste måde at teste SVG er at indsætte python-ikonet i thumbnailet.
Ikonet ligger i `projects/tomatsource/icons/python.svg`, og der ligger en
`icons`-node klar nederst i venstre panel. Én kommando tester dermed både
ikon-listen og SVG-rasteriseringen:

```bash
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=Python ikon" --text "subtitle=SVG test" \
  --icons python
```

Forventet: `output/ts71-metal-raket-c.jpg` (config'ens `background` bruges
automatisk). Åbn filen og tjek at python-logoet (blå/gul) står nederst i det
sorte venstre panel (~x 20–90, y 930–1000).

Check direkte at cairosvg rasteriserer SVG'en:

```bash
uv run python -c "
from assets import load_image
img = load_image('projects/tomatsource/icons/python.svg')
print(img.size, img.mode)   # (200, 200) RGBA
"
```

Variant — **SVG i en `image`-node** (`--extra`-banen):

```bash
uv run thumbnail --series tomat-source --bg backgrounds/test.png \
  --title "SVG" --extra projects/tomatsource/icons/python.svg
```

Forventet: python-logoet øverst højre (100×100).

---

## 5. Ikon-lister (`icons`-node)

> Der findes også en dedikeret guide: [test-icons.md](test-icons.md).

`projects/tomatsource/config.json` har en `icons`-node (id `icons`,
`height: 70`) i venstre panel. Navne slås op i `projects/tomatsource/icons/`
(`python.svg`, `tomat.png`) — case-insensitive, SVG og PNG kan blandes frit.

Enkelt ikon:

```bash
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=Ikon" --text "subtitle=Et ikon" --icons python
```

Forventet: `output/ts71-metal-raket-c.jpg`, ikonet i venstre panel nederst. Kør
med og uden `--icons` og sammenlign bunden af venstre panel:

```bash
uv run python - <<'EOF'
from generator import ThumbnailGenerator
from nodes import Node, RenderContext

gen = ThumbnailGenerator("projects/tomatsource/config.json")
sc = gen.config["series"]["tomat-source"]

def render(icons=None):
    img = gen._load_and_resize_bg("projects/tomatsource/backgrounds/ts71-metal-raket.jpg")
    ctx = RenderContext(texts={"main": "Ikon", "subtitle": "Liste"},
                        icons=icons or {}, icons_dir="projects/tomatsource/icons")
    for layer in sc["layers"]:
        img = Node.from_data(layer).render(img, 0, 0, ctx, (0, 0, img.width, img.height))
    return img

base, with_icons = render(), render({"icons": ["python"]})
diff = sum(1 for x in range(0, 200) for y in range(900, 1050)
           if base.getpixel((x, y)) != with_icons.getpixel((x, y)))
print("differing pixels:", diff)   # > 0, fx ~4000
EOF
```

Flere ikoner (liste) og ukendt navn (advarsel, ingen fejl):

```bash
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=To ikoner" --icons python,tomat
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=Advarsel" --icons findesikke   # Warning til stderr
```

Retning (vandret/lodret) og størrelser sættes i config — se
[test-icons.md](test-icons.md).

### Hurtig test via `ts2.sh`

`ts2.sh` virker som `ts.sh`, men tager også valgfrie ikon-navne som argumenter.
Navnene samles til en liste og sendes til `--icons`:

```bash
./ts2.sh "Python live" "Raket opsendelse" python tomat
```

- Uden ikoner opfører scriptet sig præcis som `ts.sh`.
- Ukendt navn → `Warning: no icon found for '<navn>' in ...` på stderr (de
  øvrige ikoner indsættes stadig).
- Baggrunden er `ts72-liftoff.jpeg` → output: `output/ts72-liftoff-c.jpg`.

### Template med default-ikoner: `config-icons.json`

`config-icons.json` er en kopi af `config.json` med en `icons`-node, der har en
default-liste (`["python"]`) — klar til at blive udvidet eller overstyret via
`--icons`. Brug den som udgangspunkt for nye serier:

```bash
mkdir -p projects/min-serie/icons
cp config-icons.json projects/min-serie/config.json
# læg ikoner i projects/min-serie/icons/
uv run thumbnail --project min-serie --series tomat-source \
  --bg backgrounds/test.png --text "main=Ikoner" --icons python
```

Uden `--icons` tegner default-listen; er hverken `--icons` eller `icons`-feltet
sat, tegnes intet — ikonerne er netop valgfrie.

---

## 6. Fejlhåndtering

| Kommando | Forventet fejl |
|----------|----------------|
| `uv run thumbnail --series findes-ikke --bg backgrounds/test.png --title "test"` | `Error: Series 'findes-ikke' not found in config.` |
| `uv run thumbnail --series tomat-source --bg findes-ikke.png --title "test"` | `Error: File not found: ./findes-ikke.png` |
| `uv run thumbnail --series tomat-source --title "test"` | `Error: no background given. Pass --bg or set 'background' in config.` |
| `uv run thumbnail --project tomatsource --series tomat-source --icons ,` | `Error: --icons expects at least one name, got ','` |
| `uv run thumbnail --series tomat-source --bg backgrounds/test.png --text barenavn` | `Error: --text expects <id>=<text>, got 'barenavn'` |

Alle skal afslutte med exit-kode 1 (stderr).

---

## 7. Regressionstest — pixel-identitet med gamle motor

Refaktoreringen må ikke ændre udseendet. Den oprindelige (pre-refaktorering)
motor hentes fra git — commit `14a4474` — uden at røre arbejdskopien, og
sammenlignes pixel-for-pixel med den nye:

```bash
mkdir -p /tmp/opencode/old
git show 14a4474:generator.py > /tmp/opencode/old/generator.py

uv run python - <<'EOF'
import importlib.util
from PIL import Image

# GAMMEL motor (pre-refaktorering) lastes fra /tmp
spec = importlib.util.spec_from_file_location("old_generator", "/tmp/opencode/old/generator.py")
old = importlib.util.module_from_spec(spec)
spec.loader.exec_module(old)

# NY motor
from generator import ThumbnailGenerator
from nodes import Node, RenderContext

cfg = "projects/tomatsource/config.json"
bg = "projects/tomatsource/backgrounds/ts71-metal-raket.jpg"
texts = {"main": "Raket test", "subtitle": "Refaktoreret"}

oldgen = old.ThumbnailGenerator(cfg)
img_old = oldgen._load_and_resize_bg(bg)
for layer in oldgen.config["series"]["tomat-source"]["layers"]:
    img_old = oldgen._render_layer(img_old, layer, 0, 0, texts, None)

newgen = ThumbnailGenerator(cfg)
img_new = newgen._load_and_resize_bg(bg)
ctx = RenderContext(texts=texts)
for layer in newgen.config["series"]["tomat-source"]["layers"]:
    img_new = Node.from_data(layer).render(img_new, 0, 0, ctx, (0, 0, img_new.width, img_new.height))

a, b = img_old.convert("RGB"), img_new.convert("RGB")
diff = sum(1 for x in range(a.width) for y in range(a.height) if a.getpixel((x, y)) != b.getpixel((x, y)))
print("differing pixels:", diff, "/", a.width * a.height)   # 0 / 2073600
EOF
```

Forventet: `differing pixels: 0 / 2073600`.

Bemærk: `projects/tomatsource/config.json` er opdateret med `background` og en
`icons`-node. Uden `--icons` renderer `icons`-noden intet (ingen default-liste),
og den gamle motor springer ukendte node-typer over — så pixel-identiteten
holder. Den gamle motor forstår dog ikke `background`-feltet, derfor angives
baggrundsstien eksplicit i testen ovenfor.

---

## 8. Hurtig selvkontrol af kildekode

```bash
uv run python -m py_compile generator.py nodes.py assets.py
uv run thumbnail --help    # viser --bg (valgfri) og --icons
```