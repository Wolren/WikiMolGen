"""
wikimolgen.rendering.utils - Shared rendering utilities
========================================================

Pure utility functions used by multiple rendering backends.
No dependencies on Streamlit or other web packages.
"""

from pathlib import Path
from typing import Any

from PIL import Image, ImageEnhance


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


__all__ = ["autocrop_image"]
