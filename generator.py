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

    def _node_bounds(self, node, extra_path):
        """Return (width, height) of a node, or None if it has no measurable size.

        A node with explicit width/height is always measurable. Text without
        explicit size wraps to the box of its container, so it returns None.
        """
        if "width" in node and "height" in node:
            return node["width"], node["height"]
        node_type = node["type"]
        if node_type == "rect":
            return node.get("width"), node.get("height")
        if node_type == "image":
            path = extra_path if node.get("dynamic") else node.get("path")
            if not path:
                return None
            img = self._load_image(path)
            if "width" in node:
                ratio = node["width"] / img.width
                return node["width"], round(img.height * ratio)
            if "height" in node:
                ratio = node["height"] / img.height
                return round(img.width * ratio), node["height"]
            return img.width, img.height
        if node_type == "group":
            return self._group_bounds(node, extra_path)
        return None

    def _group_bounds(self, node, extra_path):
        """Return a group's bounding box.

        An explicit width/height on the group wins. Otherwise the size is
        inferred from the furthest extent reached by any measurable child.
        Returns None if the group has no measurable children, so the text
        falls back to the constraint inherited from its parent.
        """
        if "width" in node and "height" in node:
            return node["width"], node["height"]
        extents = []
        for child in node.get("children", []):
            if child.get("visible") is False:
                continue
            bounds = self._node_bounds(child, extra_path)
            if bounds is None:
                continue
            extents.append((child.get("x", 0) + bounds[0], child.get("y", 0) + bounds[1]))
        if not extents:
            return None
        return max(e[0] for e in extents), max(e[1] for e in extents)

    # ── Tree renderer ────────────────────────────────────────────────

    def _render_layer(self, image, node, abs_x, abs_y, texts, extra_path, constraint=None):
        if node.get("visible") is False:
            return image

        if constraint is None:
            constraint = (0, 0, image.width, image.height)

        node_x = abs_x + node.get("x", 0)
        node_y = abs_y + node.get("y", 0)

        if node["type"] == "group":
            bounds = self._group_bounds(node, extra_path)
            group_constraint = (node_x, node_y, bounds[0], bounds[1]) if bounds else constraint
            children = sorted(node.get("children", []), key=lambda c: c.get("z_index", 0))
            for child in children:
                image = self._render_layer(image, child, node_x, node_y, texts, extra_path, group_constraint)
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
                if "width" in node and "height" in node:
                    w, h = node["width"], node["height"]
                elif "width" in node:
                    ratio = node["width"] / img.width
                    w, h = node["width"], round(img.height * ratio)
                else:
                    ratio = node["height"] / img.height
                    w, h = round(img.width * ratio), node["height"]
                img = img.resize((w, h), Image.LANCZOS)
            return self._composite(image, img, node_x, node_y)

        if node["type"] == "text":
            return self._render_text(image, node, node_x, node_y, texts, constraint)

        return image

    def _wrap_text(self, text, font, draw, max_width):
        """Wrap text to a maximum width, honouring explicit \\n line breaks.

        Words are filled greedily; a single word wider than the box is broken
        into pieces so it never exceeds the given width.
        """
        lines = []
        for paragraph in text.split("\n"):
            current = ""
            for word in paragraph.split(" "):
                candidate = f"{current} {word}" if current else word
                if draw.textlength(candidate, font=font) <= max_width:
                    current = candidate
                    continue
                if current:
                    lines.append(current)
                while draw.textlength(word, font=font) > max_width and len(word) > 1:
                    lo, hi = 1, len(word)
                    while lo < hi:
                        mid = (lo + hi + 1) // 2
                        if draw.textlength(word[:mid], font=font) <= max_width:
                            lo = mid
                        else:
                            hi = mid - 1
                    lines.append(word[:lo])
                    word = word[lo:]
                current = word
            if current:
                lines.append(current)
        return lines

    def _render_text(self, image, node, node_x, node_y, texts, constraint):
        node_id = node.get("id", "main")
        content = texts.get(node_id, node.get("value", ""))
        if not os.path.exists(node["font"]):
            raise FileNotFoundError(f"Font not found: {node['font']}")

        c_x, c_y, c_w, c_h = constraint
        base_size = node.get("size", 40)
        line_spacing = node.get("line_spacing", 0)
        align = node.get("align", "left")
        color = tuple(node["color"])
        max_width = node.get("width", c_x + c_w - node_x)
        max_height = node.get("height", c_y + c_h - node_y)
        min_size = max(10, base_size // 4)

        draw = ImageDraw.Draw(image)

        size = base_size
        while size > min_size:
            font = ImageFont.truetype(node["font"], size)
            lines = self._wrap_text(content, font, draw, max_width)
            if len(lines) * (size + line_spacing) <= max_height:
                break
            size -= 4

        font = ImageFont.truetype(node["font"], size)
        lines = self._wrap_text(content, font, draw, max_width)
        total_height = len(lines) * (size + line_spacing)
        if total_height > max_height:
            overflow = total_height - max_height
            print(f"Warning: text overflows its area by {overflow}px at minimum size.", file=sys.stderr)

        y = node_y
        for line in lines:
            line_width = draw.textlength(line, font=font)
            if align == "center":
                x = node_x + max_width / 2 - line_width / 2
            elif align == "right":
                x = node_x + max_width - line_width
            else:
                x = node_x
            draw.text((x, y), line, fill=color, font=font)
            y += size + line_spacing
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

    def generate(self, series, bg_path, title=None, extra_path=None, texts=None):
        if series not in self.config["series"]:
            raise ValueError(f"Series '{series}' not found in config.")
        series_config = self.config["series"][series]

        if texts is None:
            texts = {}
        if title is not None and "main" not in texts:
            texts["main"] = title

        image = self._load_and_resize_bg(bg_path)
        layers = sorted(series_config.get("layers", []), key=lambda l: l.get("z_index", 0))
        for layer in layers:
            image = self._render_layer(image, layer, 0, 0, texts, extra_path)
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
    args = parser.parse_args()

    texts = {}
    for item in args.text:
        if "=" not in item:
            print(f"Error: --text expects <id>=<text>, got '{item}'", file=sys.stderr)
            sys.exit(1)
        node_id, value = item.split("=", 1)
        texts[node_id] = value

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
            texts=texts,
        )
        print(f"Thumbnail saved: {output}")
    except (FileNotFoundError, ValueError, KeyError) as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
