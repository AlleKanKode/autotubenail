#!/usr/bin/env python3
"""Thumbnail generator — Python CLI engine for YouTube livestream thumbnails."""

import argparse
import json
import os
import sys

from PIL import Image

from assets import load_image
from nodes import Node, RenderContext


class ThumbnailGenerator:
    """Generates thumbnails using a tree of node objects."""

    def __init__(self, config_path="config.json"):
        self.config = self._load_config(config_path)

    @staticmethod
    def _load_config(path):
        if not os.path.exists(path):
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)

    def _load_and_resize_bg(self, path):
        img = load_image(path)
        return img.resize((1920, 1080), Image.LANCZOS)

    def _save_output(self, image, bg_path):
        os.makedirs("output", exist_ok=True)
        basename = os.path.splitext(os.path.basename(bg_path))[0]
        output_path = f"output/{basename}-c.jpg"
        image.convert("RGB").save(output_path, "JPEG", quality=85)
        return output_path

    def generate(self, series, bg_path, title=None, extra_path=None, texts=None,
                 icons=None, icons_dir=None):
        if series not in self.config["series"]:
            raise ValueError(f"Series '{series}' not found in config.")
        series_config = self.config["series"][series]

        if texts is None:
            texts = {}
        if title is not None and "main" not in texts:
            texts["main"] = title

        ctx = RenderContext(
            texts=texts, extra_path=extra_path, icons=icons, icons_dir=icons_dir
        )
        image = self._load_and_resize_bg(bg_path)
        constraint = (0, 0, image.width, image.height)
        layers = sorted(series_config.get("layers", []), key=lambda l: l.get("z_index", 0))
        for layer in layers:
            node = Node.from_data(layer)
            image = node.render(image, 0, 0, ctx, constraint)
        return self._save_output(image, bg_path)


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
        "--bg",
        help="Path to a 16:9 background image (overrides the series' config)"
    )
    parser.add_argument(
        "--title",
        help="Title text (alias for --text main=...). Use \\n for line breaks."
    )
    parser.add_argument(
        "--text", action="append", default=[],
        help="Text for a placeholder id, as <id>=<text>. Repeatable."
    )
    parser.add_argument(
        "--project",
        help="Project name (reads projects/<name>/config.json)"
    )
    parser.add_argument(
        "--extra",
        help="Path to an extra logo (e.g. Python logo)"
    )
    parser.add_argument(
        "--icons", action="append", default=[],
        help="Icons for a placeholder id, as [<id>=]<name1>,<name2>. Repeatable."
    )
    args = parser.parse_args()

    texts = {}
    for item in args.text:
        if "=" not in item:
            print(f"Error: --text expects <id>=<text>, got '{item}'", file=sys.stderr)
            sys.exit(1)
        node_id, value = item.split("=", 1)
        texts[node_id] = value

    icons = {}
    for item in args.icons:
        node_id, value = item.split("=", 1) if "=" in item else ("icons", item)
        names = [name.strip() for name in value.split(",") if name.strip()]
        if not names:
            print(f"Error: --icons expects at least one name, got '{item}'", file=sys.stderr)
            sys.exit(1)
        icons[node_id] = names

    try:
        config_path = f"projects/{args.project}/config.json" if args.project else "config.json"
        generator = ThumbnailGenerator(config_path)
        if args.series not in generator.config["series"]:
            raise ValueError(f"Series '{args.series}' not found in config.")
        series_config = generator.config["series"][args.series]

        base = f"projects/{args.project}" if args.project else "."

        bg_path = args.bg or series_config.get("background")
        if not bg_path:
            print("Error: no background given. Pass --bg or set 'background' in config.", file=sys.stderr)
            sys.exit(1)
        if not os.path.isabs(bg_path):
            bg_path = os.path.join(base, bg_path)

        output = generator.generate(
            series=args.series,
            bg_path=bg_path,
            title=args.title,
            extra_path=args.extra,
            texts=texts,
            icons=icons,
            icons_dir=os.path.join(base, "icons"),
        )
        print(f"Thumbnail saved: {output}")
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()