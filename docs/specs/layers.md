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