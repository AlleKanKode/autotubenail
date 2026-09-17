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


def resolve_icon(name, icons_dir):
    """Resolve an icon name to a file in the ``icons`` folder.

    The lookup is case-insensitive and accepts both ``.svg`` and ``.png``
    (SVG is preferred when both exist). A name may be given with or without
    its extension. Returns the full path, or None if no icon matches.
    """
    if not icons_dir or not os.path.isdir(icons_dir):
        return None

    base = name.lower()
    for ext in (".svg", ".png"):
        if base.endswith(ext):
            base = base[: -len(ext)]
            break

    for ext in (".svg", ".png"):
        exact = os.path.join(icons_dir, base + ext)
        if os.path.exists(exact):
            return exact

    for ext in (".svg", ".png"):
        for entry in sorted(os.listdir(icons_dir)):
            stem, entry_ext = os.path.splitext(entry)
            if stem.lower() == base and entry_ext.lower() == ext:
                return os.path.join(icons_dir, entry)
    return None