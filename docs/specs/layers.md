# Opgave: Refakturering af Thumbnail Config til Træstruktureret Laghåndtering (Layers)

 Vi ønsker at opgradere vores JSON-konfiguration til vores automatiske thumbnail-generator. 

I nuværende version (`config.json`) er elementer opdelt i flade lister (`overlays`, `logos`, `text_settings`). Det skal ændres til en **træbaseret/hierarkisk lagstruktur**, så elementer kan grupperes, arve egenskaber (eller positioner/z-index) og skalere langt bedre.

---

## 1. Nuværende JSON Konfiguration

Den nuværende config.json :

```json
{
  "series": {
    "tomat-source": {
      "overlays": [
        { "color": [0, 0, 0, 199], "x": 0, "y": 0, "width": 400, "height": 1080 },
        { "path": "skabeloner/tomat-source/hoejre_bar.png", "x": 1200, "y": 0 }
      ],
      "logos": [
        { "path": "skabeloner/fælles/alle-kan-kode-logo.png", "x": 50, "y": 50 },
        { "path": "skabeloner/tomat-source/tomat_logo.png", "x": 1600, "y": 50 }
      ],
      "extra_logo": {
        "x": 1750,
        "y": 50,
        "width": 100,
        "height": 100
      },
      "text_settings": {
        "font": "skabeloner/fælles/Ubuntu-Bold.ttf",
        "size": 65,
        "color": [255, 255, 255],
        "x": 1300,
        "y": 400,
        "line_spacing": 15
      }
    }
  }
}
```



## 2. Kravene til den nye struktur

1. **Træstruktur / Børn (Children):**
   - Hvert lag skal kunne indeholde en `children`-array med under-elementer (nodes).
2. **Lagtyper (`type`):**
   - Objekter skal identificeres på en eksplicicit `type` (f.eks. `group`, `rect`, `image`, `text`, `text-area`).
3. **Renderings-rækkefølge (Z-index):**
   - Renderingsrækkefølgen defineres som udgangspunkt i den rækkefølge, lagene optræder i træet (Depth-First / bund-til-top), men tag højde for en valgfri `z_index` egenskab.
4. **Relativ/Absolut Positionering:**
   - Positioner (`x`, `y`) på børne-elementer skal fortolkes relativt til deres forælder (parent node).
5. **Bagudkompatibilitet & fleksibilitet:**
   - Strukturen skal gøre det nemt at tilføje/fjerne nye serier og nye typer af elementer fremover uden at bryde formatet.

## 3. Forventede Leverancer

Planlæg  følgende tre ting:

1. **Ny `config.json`:** En fuldt refaktoreret version af den oprindelige konfiguration, oversat til den nye træstruktur.
2. **Dokumentation / Schema-forklaring:** En kort oversigt over felterne i det nye format (f.eks. hvilke egenskaber en `text`-node vs. en `image`-node har).
3. **Pseudo-kode / Logik:** En beskrivelse af (eller pseudo-kode til), hvordan render-motoren skal traversere træet og beregne de endelige koordinater/renderinger.

---

## 4. Tilføjelser efter første implementering

### `icons`-node (ikon-lister)

En `icons`-node er en generisk pladsholder for en liste af ikoner (vandret eller
lodret). Den er domæne-uafhængig og kan bruges til teknologi-ikoner,
ingridienser eller hvad som helst:

```json
{ "type": "icons", "id": "icons", "x": 60, "y": 930,
  "height": 70, "spacing": 10, "direction": "horizontal",
  "icons": ["python", { "name": "tomat", "height": 40 }] }
```

- `id` matcher `--icons [<id>=]<navn1>,<navn2>` CLI (default `icons`).
- Navne slås op i projektets `icons/`-mappe (`icons/` i roden uden `--project`)
  som `<navn>.svg` eller `<navn>.png`. Opslaget er case-insensitive, og SVG
  foretrækkes hvis begge findes. Der findes **ingen eksplicit mapping**.
- Uden CLI bruges node'ens eget `icons`-felt; hvert element kan være en streng
  (navnet) eller et objekt med `name`/`path` + valgfri `width`/`height`.
- Node'ens `width`/`height` er standardstørrelse; et element i listen kan
  overskrive dem.
- `direction` er `horizontal` (default) eller `vertical` (`horz`/`vert` ok).
- `spacing` (default 10) er afstanden mellem ikonerne.
- Ikoner er typisk SVG eller PNG (se under Billedformater).

### `align: "distributed"`

`text`-noder understøtter nu fire `align`-værdier:
`left`, `center`, `right` og `distributed`.

`distributed` er fuld-justering: ordene i en linje spredes ud, så linjen fylder
hele wrap-bredden (`width` eller container-afgrænsningen). Den sidste linje i
et afsnit (og enkeltords-linjer) venstrestilles altid.

### `background` i series-config

En serie kan erklære en baggrund:

```json
{ "series": { "tomat-source": { "background": "backgrounds/intro.png", ... } } }
```

- Stien er relativ: med `--project <navn>` løses den mod `projects/<navn>/`,
  ellers mod roden.
- `--bg` CLI overstyrer altid `background`; angives ingen af dem, fejler kørslen.
- Kravet er at baggrundsbilleder bor i projektfolderen, ikke i skabelonsfolderen.

### Billedformater

`image`-noder og baggrunde kan være PNG, JPEG eller SVG. SVG rasteriseres via
`cairosvg` i `assets.load_image()` og returneres som RGBA, præcis som raster-
billeder. Dermed virker al skalerings-/composite-logik uændret.

### Modul-arkitektur (implementeret)

| Fil | Indhold |
|-----|---------|
| `nodes.py` | `Node` (basis: `x`, `y`, `width`, `height`, `z_index`, `visible`) + `RectNode`, `ImageNode`, `TextNode`, `GroupNode`, `IconNode`. Factory: `Node.from_data()`. Hver node har `bounds(ctx)` og `render(canvas, abs_x, abs_y, ctx, constraint)`. |
| `assets.py` | `load_image()` (inkl. SVG), `resolve_icon()` (case-insensitive opslag i `icons/`). |
| `generator.py` | `ThumbnailGenerator`-facade + CLI. |