# Test af autotubenail-motoren

Denne guide beskriver, hvordan man manuelt tester de funktioner, der blev
implementeret i refaktoreringen: node-klasserne i `nodes.py`, `distributed`-alignment,
baggrund fra config, SVG-understøttelse og teknologi-ikoner (`tech`-node).

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

`assets.load_image()` rasteriserer `.svg` via cairosvg. Der findes en testfil:
`skabeloner/tomat-source/python-200-200.svg`.

```bash
uv run python -c "
from assets import load_image
img = load_image('skabeloner/tomat-source/python-200-200.svg')
print(img.size, img.mode)   # (200, 200) RGBA
"
```

Integration: læg en `image`-node med `"path": "...svg"` i en config (eller brug
en `tech`-mapping, se næste afsnit) og kør en generering.

---

## 5. Teknologi-ikoner (`tech`-node)

`projects/tomatsource/config.json` indeholder en `tech`-node (id `tech`,
`height: 70`) i venstre panel og mappingen `"python"` → `python-200-200.svg`.

Enkelt ikon:

```bash
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=Tech" --text "subtitle=Ikoner" --tech tech=python
```

Forventet: `output/ts71-metal-raket-c.jpg`, python-ikonet i venstre panel
nederst. Kør med og uden `--tech` og sammenlign bunden af venstre panel:

```bash
uv run python - <<'EOF'
from generator import ThumbnailGenerator
from nodes import Node, RenderContext

gen = ThumbnailGenerator("projects/tomatsource/config.json")
sc = gen.config["series"]["tomat-source"]

def render(tech_names=None):
    img = gen._load_and_resize_bg("projects/tomatsource/backgrounds/ts71-metal-raket.jpg")
    ctx = RenderContext(
        texts={"main": "Tech", "subtitle": "Ikoner"},
        tech={"tech": tech_names} if tech_names else {},
        tech_map=sc.get("tech", {}),
    )
    for layer in sc["layers"]:
        img = Node.from_data(layer).render(img, 0, 0, ctx, (0, 0, img.width, img.height))
    return img

base, with_tech = render(), render(["python"])
diff = sum(1 for x in range(0, 200) for y in range(900, 1050)
           if base.getpixel((x, y)) != with_tech.getpixel((x, y)))
print("differing pixels:", diff)   # > 0, fx ~4000
EOF
```

Flere ikoner (liste) og ukendt navn (advarsel, ingen fejl):

```bash
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=To ikoner" --tech tech=python,python
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=Advarsel" --tech tech=findesikke   # Warning til stderr
```

Ikon-opslag uden mapping (fallback til `skabeloner/fælles/teknologier/`):

```bash
mkdir -p skabeloner/fælles/teknologier
cp skabeloner/python.png skabeloner/fælles/teknologier/pyfake.png
uv run python -c "
from assets import resolve_tech_icon
print(resolve_tech_icon('python', {}))      # skabeloner/fælles/teknologier/python.svg? kun hvis den findes
print(resolve_tech_icon('pyfake', {}))      # skabeloner/fælles/teknologier/pyfake.png
print(resolve_tech_icon('nope', {}))        # None
"
rm skabeloner/fælles/teknologier/pyfake.png
```

---

## 6. Fejlhåndtering

| Kommando | Forventet fejl |
|----------|----------------|
| `uv run thumbnail --series findes-ikke --bg backgrounds/test.png --title "test"` | `Error: Series 'findes-ikke' not found in config.` |
| `uv run thumbnail --series tomat-source --bg findes-ikke.png --title "test"` | `Error: File not found: ./findes-ikke.png` |
| `uv run thumbnail --series tomat-source --title "test"` | `Error: no background given. Pass --bg or set 'background' in config.` |
| `uv run thumbnail --project tomatsource --series tomat-source --tech barenavn` | `Error: --tech expects <id>=<names>, got 'barenavn'` |
| `uv run thumbnail --series tomat-source --bg backgrounds/test.png --text barenavn` | `Error: --text expects <id>=<text>, got 'barenavn'` |

Alle skal afslutte med exit-kode 1 (stderr).

---

## 7. Regressionstest — pixel-identitet med gamle motor

Refaktoreringen må ikke ændre udseendet. Den gamle motor kan hentes fra git
(uden at røre arbejdskopien) og sammenlignes pixel-for-pixel med den nye:

```bash
mkdir -p /tmp/opencode/old
git show HEAD:generator.py > /tmp/opencode/old/generator.py

uv run python - <<'EOF'
import sys
sys.path.insert(0, "/tmp/opencode/old")
from PIL import Image

import generator as old
from nodes import Node, RenderContext

texts = {"main": "Raket test", "subtitle": "Refaktoreret"}
cfg = "projects/tomatsource/config.json"

# GAMMEL motor (egen _render_layer / _load_and_resize_bg)
oldgen = old.ThumbnailGenerator(cfg)
img_old = oldgen._load_and_resize_bg("projects/tomatsource/backgrounds/ts71-metal-raket.jpg")
for layer in oldgen.config["series"]["tomat-source"]["layers"]:
    img_old = oldgen._render_layer(img_old, layer, 0, 0, texts, None)

# NY motor (node-klasserne)
newgen = old.ThumbnailGenerator(cfg)
img_new = newgen._load_and_resize_bg("projects/tomatsource/backgrounds/ts71-metal-raket.jpg")
ctx = RenderContext(texts=texts)
for layer in newgen.config["series"]["tomat-source"]["layers"]:
    img_new = Node.from_data(layer).render(img_new, 0, 0, ctx, (0, 0, img_new.width, img_new.height))

a = img_old.convert("RGB")
b = img_new.convert("RGB")
diff = sum(1 for x in range(a.width) for y in range(a.height) if a.getpixel((x, y)) != b.getpixel((x, y)))
print("differing pixels:", diff, "/", a.width * a.height)   # 0 / 2073600
EOF
```

Forventet: `differing pixels: 0 / 2073600`.

Bemærk: `projects/tomatsource/config.json` er opdateret med `background`,
`tech`-mapping og en `tech`-node. Uden `--tech` renderer `tech`-noden intet, så
pixel-identiteten holder. Den gamle motor forstår dog ikke `background`-feltet —
derfor angives baggrundsstien eksplicit i testen ovenfor.

---

## 8. Hurtig selvkontrol af kildekode

```bash
uv run python -m py_compile generator.py nodes.py assets.py
uv run thumbnail --help    # viser --bg (valgfri) og --tech
```