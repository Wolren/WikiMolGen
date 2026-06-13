"""
web/ui/icons.py
===============
Inline SVG icon helpers.

Renders Lucide-style stroke icons (24x24 viewBox, 2px stroke, rounded caps/joins)
that:

- inherit color from CSS ``currentColor`` (so they adapt to the active theme);
- scale crisply at any size;
- have zero runtime dependencies.

The icons are returned as HTML snippets (``<span class="wk-icon">…</span>``)
suitable for ``st.markdown(..., unsafe_allow_html=True)``.

Usage
-----

.. code-block:: python

    from ui.icons import icon, header

    st.markdown(header("folder", "Templates"), unsafe_allow_html=True)
    with st.expander("Templates", expanded=False):
        ...
"""

from html import escape
from typing import Final

_VIEWBOX: Final[str] = "0 0 24 24"
_STROKE_WIDTH: Final[str] = "2"
_STROKE_LINECAP: Final[str] = "round"
_STROKE_LINEJOIN: Final[str] = "round"

_ICON_DEFS: Final[dict[str, str]] = {  # noqa: E501  (SVG path data)
    "folder": (
        '<path d="M20 20a2 2 0 0 0 2-2V8a2 2 0 0 0-2-2h-7.93a2 2 0 0 1-1.66-.9l-.82-1.2A2 2 0 0 0 7.93 3H4a2 2 0 0 0-2 2v13a2 2 0 0 0 2 2Z"/>'  # noqa: E501
    ),
    "ruler": (
        '<path d="M21.3 8.7 8.7 21.3a1 1 0 0 1-1.4 0L2.7 16.7a1 1 0 0 1 0-1.4L15.3 2.7a1 1 0 0 1 1.4 0l4.6 4.6a1 1 0 0 1 0 1.4Z"/>'  # noqa: E501
        '<path d="m7.5 10.5 2 2"/>'
        '<path d="m10.5 7.5 2 2"/>'
        '<path d="m13.5 4.5 2 2"/>'
        '<path d="m4.5 13.5 2 2"/>'
    ),
    "palette": (
        '<circle cx="13.5" cy="6.5" r=".5" fill="currentColor"/>'
        '<circle cx="17.5" cy="10.5" r=".5" fill="currentColor"/>'
        '<circle cx="8.5" cy="7.5" r=".5" fill="currentColor"/>'
        '<circle cx="6.5" cy="12.5" r=".5" fill="currentColor"/>'
        '<path d="M12 2C6.5 2 2 6.5 2 12s4.5 10 10 10c.926 0 1.648-.746 1.648-1.688 0-.437-.18-.835-.437-1.125-.29-.289-.438-.652-.438-1.125a1.64 1.64 0 0 1 1.668-1.668h1.996c3.051 0 5.555-2.503 5.555-5.554C21.965 6.012 17.461 2 12 2Z"/>'  # noqa: E501
    ),
    "lightbulb": (
        '<path d="M15 14c.2-1 .7-1.7 1.5-2.5 1-.9 1.5-2.2 1.5-3.5A6 6 0 0 0 6 8c0 1 .2 2.2 1.5 3.5.7.7 1.3 1.5 1.5 2.5"/>'  # noqa: E501
        '<path d="M9 18h6"/>'
        '<path d="M10 22h4"/>'
    ),
    "cloud-fog": (
        '<path d="M16 17H7"/>'
        '<path d="M17 21H9"/>'
        '<path d="M3 13a4 4 0 0 1 4-4h.5A6 6 0 0 1 17 9a4 4 0 0 1 0 8H6"/>'
    ),
    "settings-2": (
        '<path d="M20 7h-9"/>'
        '<path d="M14 17H5"/>'
        '<circle cx="17" cy="17" r="3"/>'
        '<circle cx="7" cy="7" r="3"/>'
    ),
    "trash": (
        '<path d="M3 6h18"/>'
        '<path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6"/>'
        '<path d="M8 6V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>'
        '<line x1="10" y1="11" x2="10" y2="17"/>'
        '<line x1="14" y1="11" x2="14" y2="17"/>'
    ),
    "check": ('<path d="M20 6 9 17l-5-5"/>'),
    "x": ('<path d="M18 6 6 18"/><path d="m6 6 12 12"/>'),
    "check-circle": ('<path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/><path d="m9 11 3 3L22 4"/>'),
    "alert-triangle": (
        '<path d="m21.73 18-8-14a2 2 0 0 0-3.48 0l-8 14A2 2 0 0 0 4 21h16a2 2 0 0 0 1.73-3Z"/>'
        '<line x1="12" y1="9" x2="12" y2="13"/>'
        '<line x1="12" y1="17" x2="12.01" y2="17"/>'
    ),
    "info": (
        '<circle cx="12" cy="12" r="10"/>'
        '<line x1="12" y1="16" x2="12" y2="12"/>'
        '<line x1="12" y1="8" x2="12.01" y2="8"/>'
    ),
    "bulb": (
        '<path d="M9 18h6"/>'
        '<path d="M10 22h4"/>'
        '<path d="M12 2a7 7 0 0 0-4 12.7c.6.5 1 1.2 1 2v.3a1 1 0 0 0 1 1h4a1 1 0 0 0 1-1V17a3 3 0 0 1 1-2A7 7 0 0 0 12 2Z"/>'  # noqa: E501
    ),
    "rotate-ccw": (
        '<path d="M3 12a9 9 0 1 0 9-9 9.75 9.75 0 0 0-6.74 2.74L3 8"/><path d="M3 3v5h5"/>'
    ),
    "archive": (
        '<rect x="2" y="3" width="20" height="5" rx="1"/>'
        '<path d="M4 8v11a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V8"/>'
        '<path d="M10 12h4"/>'
    ),
    "link": (
        '<path d="M10 13a5 5 0 0 0 7.54.54l3-3a5 5 0 0 0-7.07-7.07l-1.72 1.71"/>'
        '<path d="M14 11a5 5 0 0 0-7.54-.54l-3 3a5 5 0 0 0 7.07 7.07l1.71-1.71"/>'
    ),
    "database": (
        '<ellipse cx="12" cy="5" rx="9" ry="3"/>'
        '<path d="M3 5v14a9 3 0 0 0 18 0V5"/>'
        '<path d="M3 12a9 3 0 0 0 18 0"/>'
    ),
    "atom": (
        '<circle cx="12" cy="12" r="1"/>'
        '<path d="M20.2 20.2c2.04-2.03.02-7.36-4.5-11.9-4.54-4.52-9.87-6.54-11.9-4.5-2.04 2.03-.02 7.36 4.5 11.9 4.54 4.52 9.87 6.54 11.9 4.5Z"/>'  # noqa: E501
        '<path d="M15.7 15.7c4.52-4.54 6.54-9.87 4.5-11.9-2.03-2.04-7.36-.02-11.9 4.5-4.52 4.54-6.54 9.87-4.5 11.9 2.03 2.04 7.36.02 11.9-4.5Z"/>'  # noqa: E501
    ),
}


def _svg(name: str, size: int = 16, stroke: int | None = None) -> str:
    """Build a raw ``<svg>`` element for the given icon name."""
    if name not in _ICON_DEFS:
        raise KeyError(f"Unknown icon: {name!r}. Available: {sorted(_ICON_DEFS)}")
    body = _ICON_DEFS[name]
    sw = str(stroke) if stroke is not None else _STROKE_WIDTH
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
        f'viewBox="{_VIEWBOX}" fill="none" stroke="currentColor" '
        f'stroke-width="{sw}" stroke-linecap="{_STROKE_LINECAP}" '
        f'stroke-linejoin="{_STROKE_LINEJOIN}" aria-hidden="true">'
        f"{body}</svg>"
    )


def icon(name: str, size: int = 16, stroke: int | None = None) -> str:
    """Return an inline icon wrapped in ``<span class="wk-icon">``.

    Parameters
    ----------
    name
        Icon identifier (see :data:`_ICON_DEFS`).
    size
        Pixel width/height. The icon is vector, so it scales without loss.
    stroke
        Override stroke width in pixels. Defaults to ``2`` (Lucide).
    """
    return f'<span class="wk-icon">{_svg(name, size=size, stroke=stroke)}</span>'


def header(name: str, text: str, size: int = 16) -> str:
    """Return an icon + text header, rendered as a single markdown block.

    Designed to be placed immediately before a ``st.expander`` or ``st.subheader``
    when you want a clean visual cue. Style is controlled by the
    ``.wk-section-header`` class in ``wiki_theme.css``.
    """
    label = escape(text)
    return (
        f'<div class="wk-section-header">'
        f'<span class="wk-section-header__icon">{_svg(name, size=size)}</span>'
        f'<span class="wk-section-header__text">{label}</span>'
        f"</div>"
    )


__all__ = ["icon", "header"]
