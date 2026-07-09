# PROMPT: Udvikling af modulær Thumbnail-Generator (Fase 1: Python Motor)

## 1. Kontext & Formål
## 1. Kontext & Formål
Jeg skal bygge mit eget, uafhængige system til at automatisere dannelsen af YouTube livestream-thumbnails. Systemet skal erstatte en ekstern cloud-tjeneste (getstencil.com), som lukker. 

Det langsigtede mål er en todelt arkitektur (Decoupled Architecture):
1. **Frontend:** En Flutter-app (cross-platform GUI til Linux/Pop!_OS, macOS og Windows), hvor jeg visuelt kan oprette skabeloner via drag-and-drop og skrive titler. Denne app genererer en instruktionsfil i JSON-format.
2. **Backend:** Et lynhurtigt Python-script (motoren), der læser JSON-instruktionerne, manipulerer billedet og spytter det færdige resultat ud.

I denne første fase skal vi udelukkende bygge **Python CLI-motoren**. Projektet udvikles live på streamen "Tomat Source" under kanalen "Alle Kan Kodes", så koden skal være ren, objektorienteret, veldokumenteret og let for seerne at forstå.

*Bemærk: AI-billederne leveres i et rent 16:9 format uden synlige vandmærker, så vi skal IKKE lave billed-inpainting eller pixel-manipulation af baggrunden.*

---

## 2. Arkitektur & Mappestruktur
Projektet skal struktureres således fra start for at sikre total genanvendelighed og udvidelse til andre serier eller skabeloner via konfiguration:

```text
thumbnail-generator/
│
├── skabeloner/
│   ├── fælles/
│   │   ├── Ubuntu-Bold.ttf
│   │   └── alle-kan-kode-logo.png
│   ├── tomat-source/
│   │   ├── venstre_bar.png
│   │   ├── hoejre_bar.png
│   │   └── tomat_logo.png
│
├── baggrunde/                    # Her placeres rå 16:9 billeder fra Gemini
├── output/                       # Her lander de færdige, komprimerede JPG'er
│
├── config.json                   # Indeholder layout-koordinater og serie-definitioner
└── generator.py                  # Selve Python-motoren (Objektorienteret / Klasse)
```



## 3. Krav til config.json (Skabelon-kontrakten)

Konfigurationsfilen skal være hjertet i genanvendeligheden. Den skal definere præcise koordinater (x, y, bredde, hoejde) for de enkelte serier.

Her er den struktur, som config.json skal have fra start:


```json
{
  "serier": {
    "tomat-source": {
      "overlays": [
        { "sti": "skabeloner/tomat-source/venstre_bar.png", "x": 0, "y": 0 },
        { "sti": "skabeloner/tomat-source/hoejre_bar.png", "x": 1200, "y": 0 }
      ],
      "logoer": [
        { "sti": "skabeloner/fælles/alle-kan-kode-logo.png", "x": 50, "y": 50 },
        { "sti": "skabeloner/tomat-source/tomat_logo.png", "x": 1600, "y": 50 }
      ],
      "tekst_opsætning": {
        "skrifttype": "skabeloner/fælles/Ubuntu-Bold.ttf",
        "størrelse": 65,
        "farve": [255, 255, 255],
        "x": 1300,
        "y": 400,
        "linjeafstand": 15
      }
    }
  }
}
```

## 4. Funktionelle Krav til Python-motoren (generator.py)

1. **Lag-baseret grafik-sammensætning (Pillow):** Scriptet skal indlæse baggrundsbilledet fra `/baggrunde/` i Pillow (PIL) og tvinge det til en præcis 1080p opløsning (1920x1080). Derefter skal følgende klistres på i lag (alfa-composite/transparens skal understøttes fuldt ud):
   - Modulære gennemsigtige overlays (PNG-bjælker defineret under den valgte serie i JSON).
   - Faste logoer (Kanal-logo, serie-logo defineret i JSON).
   - Dynamiske produkt-/emne-logoer (f.eks. et Python-logo sendt med som CLI-argument).
2. **Dynamisk Tekst-rendering:** Scriptet skal kunne modtage en titeltekst som argument og understøtte \n for manuelle linjeskift. Teksten skal skrives på billedet ud fra de indstillinger for font, størrelse, farve, start-koordinat (X/Y) og linjeafstand, som er defineret i JSON-filen.
3. **Komprimering & Navngivning:** Det færdige billede skal konverteres fra RGBA til RGB, komprimeres til en JPEG (mål: ca. 200 KB for optimal og hurtig YouTube-upload, typisk ved brug af `quality=85` i Pillow) og gemmes i `/output/`. Filnavnet skal matche inputfilen, men med `-c` tilføjet til sidst (f.eks. hvis input er `intro.png`, skal output være `intro-c.jpg`).
4. **CLI-Argumenter (Interface):** Scriptet skal være platformuafhængigt og kunne kaldes direkte fra terminalen med følgende argument-struktur: python generator.py --serie tomat-source --bg baggrunde/billede.png --titel "Re\n-factor\nkode\npiv\nbilligt" --ekstra skabeloner/python.png

## 5. Din Opgave som Agent Nu:

1. **Analysér kravene:** Bekræft, at du har forstået den todelte arkitektur samt de præcise krav til Pillow-motoren og den tilhørende JSON-struktur.
2. **Beskriv planen:** Giv mig en overskuelig, trinvist køreplan for, hvordan vi opbygger denne klassebaserede motor live på streamen (f.eks. Trin 1: JSON-parsing & argument-håndtering, Trin 2: Pillow grafik-komposition med lag, Trin 3: Dynamisk tekst-rendering med linjeskift, Trin 4: JPEG-konvertering og fil-komprimering).
3. **Afvent min godkendelse:** Når jeg har godkendt din køreplan, går vi i gang med at skrive koden modul for modul, så jeg kan forklare logikken til mine seere undervejs.

Giv mig din analyse og din foreslåede køreplan nu.
