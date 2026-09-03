"""Layer node tree — OOP model for the thumbnail generator.

Each layer in the config becomes a Node object. Nodes know their own bounds
and how to render themselves onto a canvas, so the engine only has to walk
the tree once and let every node draw itself.
"""

import os
import sys

from PIL import Image, ImageDraw, ImageFont

from assets import load_image, resolve_tech_icon


class RenderContext:
    """Shared state passed down the tree while rendering.

    Attributes:
        texts: dict mapping placeholder id -> text content.
        extra_path: path to the dynamic image injected via --extra.
        tech: dict mapping placeholder id -> list of tech names (--tech).
        tech_map: dict mapping tech name -> icon file path (from config).
    """

    def __init__(self, texts=None, extra_path=None, tech=None, tech_map=None):
        self.texts = texts or {}
        self.extra_path = extra_path
        self.tech = tech or {}
        self.tech_map = tech_map or {}


def composite(canvas, overlay, x, y):
    """Paste an RGBA overlay onto a canvas at (x, y) with alpha compositing."""
    layer = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    layer.paste(overlay, (x, y))
    return Image.alpha_composite(canvas, layer)


class Node:
    """Base layer node: position (x, y) and size (width, height).

    Every concrete node type extends this class. Children inherit the
    container's coordinate system; x/y are relative to the parent.
    """

    def __init__(self, data, parent=None):
        self.data = data
        self.parent = parent
        self.x = data.get("x", 0)
        self.y = data.get("y", 0)
        self.width = data.get("width")
        self.height = data.get("height")
        self.visible = data.get("visible", True)
        self.z_index = data.get("z_index", 0)

    @classmethod
    def from_data(cls, data, parent=None):
        """Factory: build the right node subclass from a config dict."""
        node_type = data.get("type")
        if node_type == "rect":
            return RectNode(data, parent)
        if node_type == "image":
            return ImageNode(data, parent)
        if node_type == "text":
            return TextNode(data, parent)
        if node_type == "group":
            return GroupNode(data, parent)
        if node_type == "tech":
            return TechNode(data, parent)
        raise ValueError(f"Unknown node type: {node_type}")

    def bounds(self, ctx):
        """Return (width, height) or None if the node has no measurable size.

        A node with explicit width and height is always measurable. Other
        types override this to infer their size.
        """
        if self.width is not None and self.height is not None:
            return self.width, self.height
        return None

    def render(self, canvas, abs_x, abs_y, ctx, constraint=None):
        """Render this node onto the canvas.

        Args:
            canvas: RGBA image being built.
            abs_x, abs_y: absolute origin of this node (parent's position).
            ctx: shared RenderContext.
            constraint: (x, y, w, h) box the node is confined to.
        """
        if not self.visible:
            return canvas
        if constraint is None:
            constraint = (0, 0, canvas.width, canvas.height)
        return self._render(canvas, abs_x + self.x, abs_y + self.y, ctx, constraint)

    def _render(self, canvas, node_x, node_y, ctx, constraint):
        raise NotImplementedError


class RectNode(Node):
    """A solid RGBA rectangle."""

    def __init__(self, data, parent=None):
        super().__init__(data, parent)
        self.color = tuple(data["color"])

    def bounds(self, ctx):
        if self.width is not None and self.height is not None:
            return self.width, self.height
        return None

    def _render(self, canvas, node_x, node_y, ctx, constraint):
        if self.width is None or self.height is None:
            raise ValueError("rect node requires width and height")
        img = Image.new("RGBA", (self.width, self.height), self.color)
        return composite(canvas, img, node_x, node_y)


class ImageNode(Node):
    """A raster image (PNG/JPEG/SVG). dynamic images take --extra's path."""

    def __init__(self, data, parent=None):
        super().__init__(data, parent)
        self.dynamic = data.get("dynamic", False)
        self.path = data.get("path")

    def _resolve_path(self, ctx):
        return ctx.extra_path if self.dynamic else self.path

    def _scaled(self, img):
        if self.width is None and self.height is None:
            return img
        if self.width is not None and self.height is not None:
            return img.resize((self.width, self.height), Image.LANCZOS)
        if self.width is not None:
            ratio = self.width / img.width
            return img.resize((self.width, round(img.height * ratio)), Image.LANCZOS)
        ratio = self.height / img.height
        return img.resize((round(img.width * ratio), self.height), Image.LANCZOS)

    def bounds(self, ctx):
        if self.width is not None and self.height is not None:
            return self.width, self.height
        path = self._resolve_path(ctx)
        if not path:
            return None
        img = load_image(path)
        if self.width is not None:
            ratio = self.width / img.width
            return self.width, round(img.height * ratio)
        if self.height is not None:
            ratio = self.height / img.height
            return round(img.width * ratio), self.height
        return img.width, img.height

    def _render(self, canvas, node_x, node_y, ctx, constraint):
        path = self._resolve_path(ctx)
        if not path:
            return canvas
        img = self._scaled(load_image(path))
        return composite(canvas, img, node_x, node_y)


class TextNode(Node):
    """Dynamic text: wraps, auto-shrinks, honours explicit line breaks."""

    def __init__(self, data, parent=None):
        super().__init__(data, parent)
        self.node_id = data.get("id", "main")
        self.value = data.get("value", "")
        self.font = data.get("font")
        self.size = data.get("size", 40)
        self.color = tuple(data["color"])
        self.align = data.get("align", "left")
        self.line_spacing = data.get("line_spacing", 0)

    @staticmethod
    def _wrap_text(text, font, draw, max_width):
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

    @staticmethod
    def _draw_distributed(draw, font, line, x, y, max_width, color):
        """Draw a line justified to fill max_width by spreading word gaps."""
        words = line.split(" ")
        word_widths = [draw.textlength(word, font=font) for word in words]
        total = sum(word_widths)
        if len(words) < 2 or total >= max_width:
            draw.text((x, y), line, fill=color, font=font)
            return
        extra = (max_width - total) / (len(words) - 1)
        cursor = x
        for i, word in enumerate(words):
            draw.text((cursor, y), word, fill=color, font=font)
            cursor += word_widths[i]
            if i < len(words) - 1:
                cursor += extra

    def _render(self, canvas, node_x, node_y, ctx, constraint):
        if not self.font:
            raise ValueError("text node requires a 'font'")
        if not os.path.exists(self.font):
            raise FileNotFoundError(f"Font not found: {self.font}")

        content = ctx.texts.get(self.node_id, self.value)
        c_x, c_y, c_w, c_h = constraint
        max_width = self.width if self.width is not None else c_x + c_w - node_x
        max_height = self.height if self.height is not None else c_y + c_h - node_y
        min_size = max(10, self.size // 4)

        draw = ImageDraw.Draw(canvas)

        size = self.size
        while size > min_size:
            font = ImageFont.truetype(self.font, size)
            lines = self._wrap_text(content, font, draw, max_width)
            if len(lines) * (size + self.line_spacing) <= max_height:
                break
            size -= 4

        font = ImageFont.truetype(self.font, size)
        lines = self._wrap_text(content, font, draw, max_width)
        total_height = len(lines) * (size + self.line_spacing)
        if total_height > max_height:
            overflow = total_height - max_height
            print(
                f"Warning: text overflows its area by {overflow}px at minimum size.",
                file=sys.stderr,
            )

        last_index = len(lines) - 1
        y = node_y
        for index, line in enumerate(lines):
            line_width = draw.textlength(line, font=font)
            if self.align == "distributed" and index != last_index and len(line.split(" ")) > 1:
                self._draw_distributed(draw, font, line, node_x, y, max_width, self.color)
            elif self.align == "center":
                x = node_x + max_width / 2 - line_width / 2
                draw.text((x, y), line, fill=self.color, font=font)
            elif self.align == "right":
                x = node_x + max_width - line_width
                draw.text((x, y), line, fill=self.color, font=font)
            else:
                draw.text((node_x, y), line, fill=self.color, font=font)
            y += size + self.line_spacing
        return canvas


class GroupNode(Node):
    """Container that renders children relative to its own position."""

    def __init__(self, data, parent=None):
        super().__init__(data, parent)
        self.children = [Node.from_data(child, self) for child in data.get("children", [])]

    def bounds(self, ctx):
        if self.width is not None and self.height is not None:
            return self.width, self.height
        extents = []
        for child in self.children:
            if not child.visible:
                continue
            child_bounds = child.bounds(ctx)
            if child_bounds is None or child_bounds[0] is None or child_bounds[1] is None:
                continue
            extents.append((child.x + child_bounds[0], child.y + child_bounds[1]))
        if not extents:
            return None
        return max(e[0] for e in extents), max(e[1] for e in extents)

    def _render(self, canvas, node_x, node_y, ctx, constraint):
        bounds = self.bounds(ctx)
        group_constraint = (node_x, node_y, bounds[0], bounds[1]) if bounds else constraint
        for child in sorted(self.children, key=lambda c: c.z_index):
            canvas = child.render(canvas, node_x, node_y, ctx, group_constraint)
        return canvas


class TechNode(Node):
    """Placeholder that renders a row of technology icons.

    The row is filled from ``ctx.tech[self.node_id]`` (set via --tech),
    falling back to ``icons`` in the config. Each name is resolved to an
    icon file through ``ctx.tech_map`` or the shared technologies folder.
    """

    def __init__(self, data, parent=None):
        super().__init__(data, parent)
        self.node_id = data.get("id", "tech")
        self.spacing = data.get("spacing", 10)
        self.defaults = data.get("icons", [])

    def _icon_paths(self, ctx):
        names = ctx.tech.get(self.node_id, self.defaults)
        paths = []
        for name in names:
            path = resolve_tech_icon(name, ctx.tech_map)
            if path:
                paths.append(path)
            else:
                print(f"Warning: no icon found for technology '{name}'.", file=sys.stderr)
        return paths

    def _render(self, canvas, node_x, node_y, ctx, constraint):
        paths = self._icon_paths(ctx)
        if not paths:
            return canvas
        if self.height is None:
            raise ValueError("tech node requires a 'height' so icons can be scaled")
        cursor = node_x
        for path in paths:
            img = load_image(path)
            ratio = self.height / img.height
            w = round(img.width * ratio)
            img = img.resize((w, self.height), Image.LANCZOS)
            canvas = composite(canvas, img, cursor, node_y)
            cursor += w + self.spacing
        return canvas