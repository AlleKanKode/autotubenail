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
        layer = Image.new("RGBA", background.size, (0, 0, 0, 0))
        layer.paste(overlay, (x, y))
        return Image.alpha_composite(background, layer)

    # ── Tree renderer ────────────────────────────────────────────────

    def _render_layer(self, image, node, abs_x, abs_y, title, extra_path):
        if node.get("visible") is False:
            return image

        node_x = abs_x + node.get("x", 0)
        node_y = abs_y + node.get("y", 0)

        if node["type"] == "group":
            children = sorted(node.get("children", []), key=lambda c: c.get("z_index", 0))
            for child in children:
                image = self._render_layer(image, child, node_x, node_y, title, extra_path)
            return image

        if node["type"] == "rect":
            img = Image.new("RGBA", (node["width"], node["height"]), tuple(node["color"]))
            return self._composite(image, img, node_x, node_y)

        if node["type"] == "image":
            path = extra_path if node.get("dynamic") else node.get("path")
            if not path:
                return image
            img = self._load_image(path)
            if "width" in node or "height" in node:
                w = node.get("width", img.width)
                h = node.get("height", img.height)
                img = img.resize((w, h), Image.LANCZOS)
            return self._composite(image, img, node_x, node_y)

        if node["type"] == "text":
            content = title if title else node.get("value", "")
            if not os.path.exists(node["font"]):
                raise FileNotFoundError(f"Font not found: {node['font']}")
            font = ImageFont.truetype(node["font"], node["size"])
            draw = ImageDraw.Draw(image)
            lines = content.split("\n")
            align = node.get("align", "left")
            y = node_y
            for line in lines:
                line_width = draw.textlength(line, font=font)
                if align == "center":
                    x = node_x - line_width // 2
                elif align == "right":
                    x = node_x - line_width
                else:
                    x = node_x
                draw.text((x, y), line, fill=tuple(node["color"]), font=font)
                y += node["size"] + node.get("line_spacing", 0)
            return image

        return image

    def _load_and_resize_bg(self, path):
        img = self._load_image(path)
        return img.resize((1920, 1080), Image.LANCZOS)

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
        layers = sorted(series_config.get("layers", []), key=lambda l: l.get("z_index", 0))
        for layer in layers:
            image = self._render_layer(image, layer, 0, 0, title, extra_path)
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
