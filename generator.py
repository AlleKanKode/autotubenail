#!/usr/bin/env python3
"""Thumbnail generator — Python CLI engine for YouTube livestream thumbnails."""

import argparse
import json
import os
import sys

from PIL import Image, ImageDraw, ImageFont


class ThumbnailGenerator:
    """Generates thumbnails using layered compositing in Pillow."""

    def __init__(self, config_path="config.json"):
        self.config = self._load_config(config_path)

    # ── Helpers ──────────────────────────────────────────────────────

    @staticmethod
    def _load_config(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    @staticmethod
    def _load_image(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"File not found: {path}")
        return Image.open(path).convert("RGBA")

    @staticmethod
    def _composite(background, overlay, x, y):
        """Place a transparent PNG onto the background at (x, y)."""
        layer = Image.new("RGBA", background.size, (0, 0, 0, 0))
        layer.paste(overlay, (x, y))
        return Image.alpha_composite(background, layer)

    # ── Layer operations ─────────────────────────────────────────────

    def _load_and_resize_bg(self, path):
        img = self._load_image(path)
        return img.resize((1920, 1080), Image.LANCZOS)

    def _composite_overlays(self, image, series_config):
        for overlay in series_config.get("overlays", []):
            if "path" in overlay:
                img = self._load_image(overlay["path"])
            elif "color" in overlay:
                img = Image.new(
                    "RGBA",
                    (overlay["width"], overlay["height"]),
                    tuple(overlay["color"]),
                )
            else:
                continue
            image = self._composite(image, img, overlay["x"], overlay["y"])
        return image

    def _composite_logos(self, image, series_config):
        for logo in series_config.get("logos", []):
            img = self._load_image(logo["path"])
            image = self._composite(image, img, logo["x"], logo["y"])
        return image

    def _composite_extra_logo(self, image, series_config, extra_path):
        config = series_config.get("extra_logo")
        if not config:
            raise ValueError("Series has no 'extra_logo' configuration.")
        img = self._load_image(extra_path)
        img = img.resize((config["width"], config["height"]), Image.LANCZOS)
        return self._composite(image, img, config["x"], config["y"])

    def _render_text(self, image, series_config, title):
        settings = series_config["text_settings"]
        if not os.path.exists(settings["font"]):
            raise FileNotFoundError(f"Font not found: {settings['font']}")
        font = ImageFont.truetype(settings["font"], settings["size"])
        draw = ImageDraw.Draw(image)
        lines = title.split("\n")
        y = settings["y"]
        for line in lines:
            draw.text((settings["x"], y), line, fill=tuple(settings["color"]), font=font)
            y += settings["size"] + settings["line_spacing"]
        return image

    def _save_output(self, image, bg_path):
        os.makedirs("output", exist_ok=True)
        basename = os.path.splitext(os.path.basename(bg_path))[0]
        output_path = f"output/{basename}-c.jpg"
        image.convert("RGB").save(output_path, "JPEG", quality=85)
        return output_path

    # ── Main method ──────────────────────────────────────────────────

    def generate(self, series, bg_path, title, extra_path=None):
        if series not in self.config["series"]:
            raise ValueError(f"Series '{series}' not found in config.")
        series_config = self.config["series"][series]

        image = self._load_and_resize_bg(bg_path)
        image = self._composite_overlays(image, series_config)
        image = self._composite_logos(image, series_config)
        if extra_path:
            image = self._composite_extra_logo(image, series_config, extra_path)
        image = self._render_text(image, series_config, title)
        output_path = self._save_output(image, bg_path)
        return output_path


# ── CLI ──────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="Generate a YouTube thumbnail from a template."
    )
    parser.add_argument(
        "--series", required=True,
        help="Series key in config.json (e.g. 'tomat-source')"
    )
    parser.add_argument(
        "--bg", required=True,
        help="Path to a 16:9 background image"
    )
    parser.add_argument(
        "--title", required=True,
        help="Title text. Use \\n for line breaks."
    )
    parser.add_argument(
        "--project",
        help="Project name (reads projects/<name>/config.json)"
    )
    parser.add_argument(
        "--extra",
        help="Path to an extra logo (e.g. Python logo)"
    )
    args = parser.parse_args()

    try:
        config_path = f"projects/{args.project}/config.json" if args.project else "config.json"
        generator = ThumbnailGenerator(config_path)
        if args.project and not os.path.isabs(args.bg):
            bg_path = os.path.join("projects", args.project, args.bg)
        else:
            bg_path = args.bg
        output = generator.generate(
            series=args.series,
            bg_path=bg_path,
            title=args.title,
            extra_path=args.extra,
        )
        print(f"Thumbnail saved: {output}")
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
