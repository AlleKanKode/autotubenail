# Test af ikon-lister (`icons`-node)

Dette dokument er en praktisk testguide for den generiske ikon-liste:
`icons`-noden i config, `icons/`-mappen, `--icons` CLI-flaget, retning
(vandret/lodret) og størrelser. Funktionen er domæne-uafhængig — den kan bruges
til teknologi-ikoner, ingridienser eller noget helt tredje.

Forudsætning: kør `uv sync` først. Alle kommandoer køres fra projektroden.

---

## Kort: sådan virker ikon-lister

1. En **`icons`-node** i config er en pladsholder for en liste af ikoner:
   ```json
   { "type": "icons", "id": "icons", "x": 20, "y": 930,
     "height": 70, "spacing": 10, "direction": "horizontal" }
   ```
2. **Ikon-navne** slås op i projektets **`icons/`-mappe** som `<navn>.svg`
   eller `<navn>.png`. Opslaget er **case-insensitive**, og SVG foretrækkes,
   hvis begge findes. Der bruges ingen eksplicit mapping.
3. **`--icons [<id>=]<navn1>,<navn2>`** (repeatable) bestemmer hvilke ikoner der
   indsættes. Uden id bruges default-id `icons`. Uden `--icons` og uden config'ens
   egen `icons`-liste tegnes intet.
4. **Størrelse** angives i config (ikke på kommandolinjen): node'ens
   `width`/`height` er standard, og hvert element i `icons`-listen kan overskrive
   med sin egen `width`/`height`.
5. **`direction`**: `horizontal` (default) eller `vertical`. Forkortelserne
   `horz`/`vert` accepteres også.

---

## Test 1 — Grundlæggende: ét ikon fra `icons/`

Projektet `tomatsource` har `projects/tomatsource/icons/python.svg` (SVG) og en
`icons`-node nederst i venstre panel:

```bash
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=Ikon" --text "subtitle=Et ikon" \
  --icons python
```

Forventet: `Thumbnail saved: output/ts71-metal-raket-c.jpg` (config'ens
`background` bruges automatisk). Python-logoet står nederst i det sorte venstre
panel (~x 20–90, y 930–1000).

Åbn og se efter:

```bash
xdg-open output/ts71-metal-raket-c.jpg
```

Root-template (ikonet hentes fra `icons/python.png`):

```bash
uv run thumbnail --series tomat-source --bg backgrounds/test.png \
  --title "Ikon" --icons python
```

---

## Test 2 — Baseline: uden ikoner tegnes intet

```bash
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=Ingen ikoner" --text "subtitle=Baseline"
```

Forventet: output uden fejl, tomt i bunden af venstre panel.

---

## Test 3 — Liste af ikoner (blandet SVG og PNG)

`projects/tomatsource/icons/` indeholder både `python.svg` og `tomat.png`:

```bash
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=Liste" --text "subtitle=svg+png" \
  --icons python,tomat
```

Forventet: to ikoner side om side (70 px høje, 10 px mellemrum) — SVG og PNG
kan blandes frit.

---

## Test 4 — Case-insensitive navne

```bash
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=Case" --text "subtitle=Stort og småt" \
  --icons Python,TOMAT
```

Forventet: samme resultat som Test 3 — filnavne matches uden hensyn til
store/små bogstaver.

---

## Test 5 — Retning: vandret og lodret

Vandret er default. Lodret sættes i config på noden:

```json
{ "type": "icons", "id": "icons", "x": 20, "y": 930, "height": 70,
  "spacing": 10, "direction": "vertical" }
```

Objektiv kontrol (vandret er bredere end høj, lodret er højere end bred):

```bash
uv run python - <<'EOF'
from PIL import Image
from nodes import IconNode, RenderContext

ICONS = "projects/tomatsource/icons"

def render(direction):
    img = Image.new("RGBA", (400, 400), (255, 255, 255, 255))
    node = IconNode({"type": "icons", "id": "icons", "x": 10, "y": 10,
                     "height": 70, "spacing": 10, "direction": direction})
    ctx = RenderContext(icons={"icons": ["python", "tomat"]}, icons_dir=ICONS)
    return node.render(img, 0, 0, ctx, (0, 0, 400, 400))

def bbox(img):
    px = img.load()
    xs, ys = [], []
    for x in range(img.width):
        for y in range(img.height):
            if px[x, y][:3] != (255, 255, 255):
                xs.append(x); ys.append(y)
    return (min(xs), min(ys), max(xs), max(ys))

print("horizontal:", bbox(render("horizontal")))   # fx (10, 10, 159, 79)
print("vertical:  ", bbox(render("vertical")))     # fx (10, 10, 79, 159)
EOF
```

Forventet: vandret bbox er bred (max_x − min_x > max_y − min_y), lodret er høj.

---

## Test 6 — Størrelse: liste-niveau og per ikon

Node'ens `width`/`height` er standard for alle; et element i `icons`-listen kan
overskrive:

```json
{ "type": "icons", "id": "icons", "x": 60, "y": 930, "height": 70, "spacing": 10,
  "icons": [
    { "name": "python", "height": 40 },
    "tomat"
  ] }
```

```bash
uv run python - <<'EOF'
from PIL import Image
from nodes import IconNode, RenderContext

ICONS = "projects/tomatsource/icons"
img = Image.new("RGBA", (400, 400), (255, 255, 255, 255))
node = IconNode({
    "type": "icons", "id": "icons", "x": 10, "y": 10, "height": 70, "spacing": 10,
    "direction": "horizontal",
    "icons": [{"name": "python", "height": 40}, "tomat"],
})
ctx = RenderContext(icons={"icons": ["python", "tomat"]}, icons_dir=ICONS)
out = node.render(img, 0, 0, ctx, (0, 0, 400, 400))
px = out.load()
xs = [x for x in range(400) for y in range(400) if px[x, y][:3] != (255, 255, 255)]
print("python skaleret til 40px, tomat til 70px -> bbox max_x:", max(xs))  # fx 129
EOF
```

Forventet: python-ikonet er 40 px, tomat 70 px (bbox `max_x` ~129 i stedet for
~159 som ved ens størrelse).

---

## Test 7 — Ukendt navn → advarsel

```bash
uv run thumbnail --project tomatsource --series tomat-source \
  --text "main=Advarsel" --icons python,findesikke
```

Forventet:

- `Warning: no icon found for 'findesikke' in projects/tomatsource/icons.` på stderr.
- Thumbnail genereres alligevel (exit 0).

---

## Test 8 — Id: default og eksplicit

- Uden `=` bruges default-id `icons` (matcher en node uden/med `id: "icons"`):
  ```bash
  uv run thumbnail --project tomatsource --series tomat-source --icons python
  ```
- Med `=` rammes en bestemt node, hvis config'en har flere lister:
  ```bash
  uv run thumbnail --project tomatsource --series tomat-source --icons icons=python
  ```

Flere lister i samme config (fx ingridienser) bruger hvert sit id og hver sin
pladsholder — samme mekanisme, blot forskellige navne.

---

## Test 9 — `config-icons.json` (template med default-liste)

`config-icons.json` er en kopi af `config.json` med en `icons`-node, der har en
default-liste (`["python"]`). Den kan testes direkte via motorens API:

```bash
uv run python - <<'EOF'
from generator import ThumbnailGenerator
from nodes import Node, RenderContext

def render(cfg, icons=None):
    gen = ThumbnailGenerator(cfg)
    sc = gen.config["series"]["tomat-source"]
    img = gen._load_and_resize_bg("backgrounds/test.png")
    ctx = RenderContext(texts={"main": "Template"}, icons=icons or {}, icons_dir="icons")
    for layer in sc["layers"]:
        img = Node.from_data(layer).render(img, 0, 0, ctx, (0, 0, img.width, img.height))
    return img

plain = render("config.json")             # ingen default -> intet ikon
default = render("config-icons.json")     # default ["python"] -> ikon
diff = sum(1 for x in range(0, 300) for y in range(900, 1050)
           if plain.getpixel((x, y)) != default.getpixel((x, y)))
print("config-icons.json default-ikon forskel:", diff)   # > 0, fx ~4900
EOF
```

Forventet: `> 0` (default-listen tegnes uden `--icons`).

Til brug i et projekt:

```bash
mkdir -p projects/min-serie
cp config-icons.json projects/min-serie/config.json
mkdir -p projects/min-serie/icons   # læg ikonerne her
```

---

## Test 10 — `ts2.sh` (hurtig integration)

`ts2.sh` virker som `ts.sh`, men tager valgfrie ikon-navne som argumenter:

```bash
./ts2.sh "Python live" "Raket opsendelse" python tomat
```

Forventet: `output/ts72-liftoff-c.jpg`, to ikoner i venstre panel nederst.
Uden ikoner opfører scriptet sig som `ts.sh`; ved for få argumenter vises
brugshjælp og exit-kode 1.

---

## Test 11 — Fejlhåndtering

| Kommando | Forventet resultat |
|----------|--------------------|
| `uv run thumbnail --project tomatsource --series tomat-source --icons ,` | `Error: --icons expects at least one name, got ','` (exit 1) |

---

## Sådan tilføjer du et nyt ikon

1. Læg filen i projektets `icons/`-mappe: `projects/<navn>/icons/<ikon>.svg`
   eller `.png` (eller `icons/` i roden uden `--project`).
2. Brug navnet (uden filendelse) på kommandolinjen:
   `uv run thumbnail --project tomatsource --series tomat-source --icons <ikon>`.
3. Ingen config-ændring nødvendig — så længe pladsholderen (`icons`-noden) findes.

---

## Accept-kriterier (tjekliste)

- [ ] `--icons python` indsætter ikonet fra `icons/` (Test 1)
- [ ] Uden ikoner tegnes intet (Test 2)
- [ ] `--icons python,tomat` blander SVG og PNG side om side (Test 3)
- [ ] `--icons Python,TOMAT` matcher case-insensitive (Test 4)
- [ ] `direction` vandret/lodret virker (Test 5)
- [ ] Liste-størrelse + per-ikon overstyring virker (Test 6)
- [ ] Ukendt navn giver advarsel, men thumbnail genereres (Test 7)
- [ ] Default-id og eksplicit id virker (Test 8)
- [ ] `config-icons.json` tegner default-listen (Test 9)
- [ ] `ts2.sh` tager ikon-navne som argumenter (Test 10)
- [ ] Tom liste giver klar fejlbesked (Test 11)