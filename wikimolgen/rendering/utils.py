"""
wikimolgen.rendering.utils - Shared rendering utilities
========================================================

Pure utility functions used by multiple rendering backends.
No dependencies on Streamlit or other web packages.
"""

import json
from pathlib import Path
from typing import Any

from PIL import Image, ImageEnhance

from wikimolgen.configs import ColorConfig, Config2D, Config3D, ConfigLoader


def autocrop_image(image_path: Path, margin: int = 10, contrast_factor: float = 1.15) -> None:
    """Auto-crop PNG to molecule/protein bounds using alpha channel only.

    Keeps transparency untouched — works for both molecule and protein renders.

    Parameters
    ----------
    image_path : Path
        Path to PNG image.
    margin : int
        Margin around content in pixels (default: 10).
    contrast_factor : float
        Contrast enhancement factor for alpha detection (default: 1.15).
    """
    if not image_path.exists():
        return

    img = Image.open(image_path).convert("RGBA")
    alpha = img.split()[-1]

    enhancer = ImageEnhance.Contrast(alpha)
    alpha = enhancer.enhance(contrast_factor)

    bbox = alpha.getbbox()
    if bbox is None:
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


__all__ = ["autocrop_image", "load_color_config", "resolve_settings_template"]
