#!/usr/bin/env python3
"""Thumbnail-generator — Python CLI-motor til YouTube livestream-thumbnails."""

import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont


class ThumbnailGenerator:
    """Genererer thumbnails vha. lag-baseret komposition i Pillow."""

    def __init__(self, config_path="config.json"):
        self.config = self._indlæs_config(config_path)

    # ── Hjælpemetoder ────────────────────────────────────────────────

    @staticmethod
    def _indlæs_config(sti):
        if not os.path.exists(sti):
            raise FileNotFoundError(f"Config-filen findes ikke: {sti}")
        with open(sti, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _indlæs_billede(sti):
        if not os.path.exists(sti):
            raise FileNotFoundError(f"Filen findes ikke: {sti}")
        return Image.open(sti).convert("RGBA")

    @staticmethod
    def _komposér(baggrund, overlay, x, y):
        """Læg et transparent PNG oven på baggrunden på (x, y)."""
        lag = Image.new("RGBA", baggrund.size, (0, 0, 0, 0))
        lag.paste(overlay, (x, y))
        return Image.alpha_composite(baggrund, lag)

    # ── Lag-operationer ──────────────────────────────────────────────

    def _load_and_resize_bg(self, sti):
        img = self._indlæs_billede(sti)
        return img.resize((1920, 1080), Image.LANCZOS)

    def _composite_overlays(self, billede, serie_config):
        for overlay in serie_config.get("overlays", []):
            if "path" in overlay:
                img = self._indlæs_billede(overlay["path"])
            elif "color" in overlay:
                img = Image.new(
                    "RGBA",
                    (overlay["width"], overlay["height"]),
                    tuple(overlay["color"]),
                )
            else:
                continue
            billede = self._komposér(billede, img, overlay["x"], overlay["y"])
        return billede

    def _composite_logos(self, billede, serie_config):
        for logo in serie_config.get("logos", []):
            img = self._indlæs_billede(logo["path"])
            billede = self._komposér(billede, img, logo["x"], logo["y"])
        return billede

    def _composite_extra_logo(self, billede, serie_config, ekstra_sti):
        konfig = serie_config.get("extra_logo")
        if not konfig:
            raise ValueError("Serien har ingen 'extra_logo'-konfiguration.")
        img = self._indlæs_billede(ekstra_sti)
        img = img.resize((konfig["width"], konfig["height"]), Image.LANCZOS)
        return self._komposér(billede, img, konfig["x"], konfig["y"])

    def _render_text(self, billede, serie_config, titel):
        ops = serie_config["text_settings"]
        if not os.path.exists(ops["font"]):
            raise FileNotFoundError(f"Skrifttypen findes ikke: {ops['font']}")
        font = ImageFont.truetype(ops["font"], ops["size"])
        draw = ImageDraw.Draw(billede)
        linjer = titel.split("\n")
        y = ops["y"]
        for linje in linjer:
            draw.text((ops["x"], y), linje, fill=tuple(ops["color"]), font=font)
            y += ops["size"] + ops["line_spacing"]
        return billede

    def _save_output(self, billede, bg_sti):
        os.makedirs("output", exist_ok=True)
        basename = os.path.splitext(os.path.basename(bg_sti))[0]
        output_sti = f"output/{basename}-c.jpg"
        billede.convert("RGB").save(output_sti, "JPEG", quality=85)
        return output_sti

    # ── Hovedmetode ──────────────────────────────────────────────────

    def generate(self, serie, bg_sti, titel, ekstra_sti=None):
        if serie not in self.config["series"]:
            raise ValueError(f"Serien '{serie}' findes ikke i config.")
        serie_config = self.config["series"][serie]

        billede = self._load_and_resize_bg(bg_sti)
        billede = self._composite_overlays(billede, serie_config)
        billede = self._composite_logos(billede, serie_config)
        if ekstra_sti:
            billede = self._composite_extra_logo(billede, serie_config, ekstra_sti)
        billede = self._render_text(billede, serie_config, titel)
        output_sti = self._save_output(billede, bg_sti)
        return output_sti


# ── CLI ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generér en YouTube-thumbnail ud fra en skabelon."
    )
    parser.add_argument(
        "--serie", required=True,
        help="Serienavn (nøgle i config.json, f.eks. 'tomat-source')"
    )
    parser.add_argument(
        "--bg", required=True,
        help="Sti til 16:9 baggrundsbillede"
    )
    parser.add_argument(
        "--titel", required=True,
        help="Titeltekst. Brug \\n for linjeskift."
    )
    parser.add_argument(
        "--project",
        help="Projektnavn (læser projects/<navn>/config.json)"
    )
    parser.add_argument(
        "--ekstra",
        help="Sti til ekstra logo (f.eks. Python-logo)"
    )
    args = parser.parse_args()

    try:
        config_sti = f"projects/{args.project}/config.json" if args.project else "config.json"
        generator = ThumbnailGenerator(config_sti)
        if args.project and not os.path.isabs(args.bg):
            bg_sti = os.path.join("projects", args.project, args.bg)
        else:
            bg_sti = args.bg
        output = generator.generate(
            serie=args.serie,
            bg_sti=bg_sti,
            titel=args.titel,
            ekstra_sti=args.ekstra,
        )
        print(f"Thumbnail gemt: {output}")
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"Fejl: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
