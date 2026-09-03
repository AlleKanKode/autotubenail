"""Asset loading helpers: images (PNG/JPEG/SVG) and fonts."""

import io
import os

from PIL import Image


def load_image(path):
    """Load an image as RGBA. SVG files are rasterized via cairosvg."""
    if not os.path.exists(path):
        raise FileNotFoundError(f"File not found: {path}")
    if path.lower().endswith(".svg"):
        return _load_svg(path)
    return Image.open(path).convert("RGBA")


def _load_svg(path):
    try:
        import cairosvg
    except ImportError as exc:
        raise RuntimeError(
            "cairosvg is required to render SVG files. "
            "Install it with: uv add cairosvg"
        ) from exc
    png = cairosvg.svg2png(url=path)
    return Image.open(io.BytesIO(png)).convert("RGBA")


def resolve_tech_icon(name, tech_map):
    """Resolve a technology name to an icon file path.

    An explicit mapping in the config wins; otherwise a fallback lookup in
    ``skabeloner/fælles/teknologier/<name>.svg|.png`` is attempted.
    """
    if name in tech_map:
        return tech_map[name]
    for ext in (".svg", ".png"):
        candidate = os.path.join("skabeloner", "fælles", "teknologier", name + ext)
        if os.path.exists(candidate):
            return candidate
    return None