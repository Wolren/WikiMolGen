"""
wikimolgen.rendering.utils - Shared rendering utilities
========================================================

Pure utility functions used by multiple rendering backends.
No dependencies on Streamlit or other web packages.
"""

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageEnhance, ImageMath

from wikimolgen.configs import ColorConfig, Config2D, Config3D, ConfigLoader


def autocrop_image(
    image_path: Path,
    margin: int = 10,
    contrast_factor: float = 1.15,
    make_transparent: bool = False,
) -> None:
    """Auto-crop PNG to molecule/protein bounds.

    Uses alpha channel by default.  When ``make_transparent`` is True, the
    image is expected to have a white background — white pixels are converted
    to transparent **before** cropping (so the new alpha channel drives
    ``getbbox`` correctly).

    Parameters
    ----------
    image_path : Path
        Path to PNG image.
    margin : int
        Margin around content in pixels (default: 10).
    contrast_factor : float
        Contrast enhancement factor for alpha detection (default: 1.15).
    make_transparent : bool
        If True, convert white-ish pixels to transparent before cropping
        (default: False).
    """
    if not image_path.exists():
        return

    img = Image.open(image_path).convert("RGBA")
    r, g, b, a = img.split()

    if make_transparent:
        thr = 240
        mask = ImageMath.eval(
            f"((r > {thr}) & (g > {thr}) & (b > {thr})) * 255",
            r=r,
            g=g,
            b=b,
        ).convert("L")
        a = ImageMath.eval("a & ~mask_int", a=a, mask_int=mask).convert("L")
        img = Image.merge("RGBA", (r, g, b, a))

    alpha = img.split()[-1]
    enhancer = ImageEnhance.Contrast(alpha)
    alpha = enhancer.enhance(contrast_factor)

    bbox = alpha.getbbox()
    if bbox is None:
        img.save(image_path)
        return

    left, top, right, bottom = bbox
    width, height = img.size

    left = max(0, left - margin)
    top = max(0, top - margin)
    right = min(width, right + margin)
    bottom = min(height, bottom + margin)

    img = img.crop((left, top, right, bottom))
    img = ImageEnhance.Contrast(img).enhance(contrast_factor)
    img.save(image_path)


def load_color_config(template: str | Path | ColorConfig | dict) -> ColorConfig:
    """Resolve a template identifier to a ColorConfig.

    Accepts:
    - ``str`` — built-in color template name or path to a JSON file
    - ``Path`` — path to a JSON file
    - ``dict`` — raw color config dictionary
    - ``ColorConfig`` — returned as-is
    """
    if isinstance(template, str):
        try:
            return ConfigLoader.load_color_template(template)
        except ValueError:
            p = Path(template)
            if p.exists():
                with open(p) as f:
                    data = json.load(f)
                return ColorConfig(**data)
            return ColorConfig()
    if isinstance(template, Path):
        with open(template) as f:
            data = json.load(f)
        return ColorConfig(**data)
    if isinstance(template, dict):
        return ColorConfig(
            element_colors=template.get("element_colors", {}),
            stick_color=template.get("stick_color"),
            bg_color=template.get("bg_color", "white"),
        )
    if isinstance(template, ColorConfig):
        return template
    return ColorConfig()


def resolve_settings_template(template: str | Path) -> Config2D | Config3D | None:
    """Try to resolve a settings template identifier to a config object.

    Accepts a built-in template name or a path to a JSON file.
    Returns ``None`` when the identifier cannot be resolved.
    """
    if isinstance(template, str):
        try:
            return ConfigLoader.load_template(template)
        except ValueError:
            p = Path(template)
            if p.exists():
                return ConfigLoader.load_from_file(p)
            return None
    if isinstance(template, Path):
        return ConfigLoader.load_from_file(template)
    return None


def hex_to_rgb(hex_color: str) -> tuple[float, float, float]:
    """Convert a hex color string to a normalized ``(R, G, B)`` tuple.

    Accepts ``"#RGB"``, ``"#RRGGBB"``, ``"RGB"``, or ``"RRGGBB"``.
    Values are normalized to the 0.0–1.0 range. Returns white on parse failure.
    """
    h = hex_color.lstrip("#")
    if len(h) == 3:
        h = "".join(c * 2 for c in h)
    try:
        return tuple(int(h[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    except (ValueError, IndexError):
        return (1.0, 1.0, 1.0)


__all__ = ["autocrop_image", "hex_to_rgb", "load_color_config", "resolve_settings_template"]
