# Todo

## Færdigt

- [x] Basis objekt til x,y position + bredde, højde (Node-klassen i `nodes.py`)
- [x] Classes for de enkelte objekter (RectNode, ImageNode, TextNode, GroupNode, IconNode)
- [x] Gitignore ignorerer `__pycache__` (verificeret)
- [x] Tekst-alignment: left, right, center og distributed
- [x] Baggrundsbilleder i projektfolderen (`background`-felt, projekt-relative stier)
- [x] SVG-support (cairosvg i `assets.py`)
- [x] Generisk ikon-liste i stedet for "tech":
  - [x] Node-type `icons`; navne slås op i projektets `icons/`-mappe
  - [x] Case-insensitive navne og både SVG og PNG
  - [x] Størrelse på liste-niveau og per ikon (i config)
  - [x] `--icons [<id>=]<navn1>,<navn2>` CLI
  - [x] `direction` (vandret/lodret) og `spacing`
- [x] Rettet todo-dokumentet til korrekt markdown
- [x] Opdateret `docs/test-icons.md` med hvordan ikon-lister testes

## Åbent

- [ ] Dokumentér koden: kommentarer/docstrings på alle funktioner