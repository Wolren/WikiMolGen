"""Atom color scheme management for 3D rendering.

Built-in schemes (CPK, Jmol, RasMol, etc.) + custom upload.
Values are applied to session state so that ``build_3d_config``
picks them up automatically.
"""

from __future__ import annotations

from typing import Any

import streamlit as st

from wikimolgen.configs.loader import BUILTIN_COLOR_TEMPLATES, COLOR_TEMPLATE_META

BUILTIN_SCHEMES: dict[str, dict[str, Any]] = dict(BUILTIN_COLOR_TEMPLATES)
_NO_SCHEME = "None"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _resolve_scheme_data(choice: str) -> dict[str, Any] | None:
    """Return the scheme dict for *choice*, or ``None`` if not found."""
    if choice in st.session_state.get("custom_atom_schemes", {}):
        return st.session_state.custom_atom_schemes[choice]
    return BUILTIN_SCHEMES.get(choice)


def get_scheme_display_name(key: str) -> str:
    """Return user-friendly display name for a built-in scheme key."""
    return COLOR_TEMPLATE_META.get(key, {}).get("name", key)


def get_scheme_choices() -> list[str]:
    """Return scheme options for a selectbox, starting with ``"None"``."""
    custom_names = list(st.session_state.get("custom_atom_schemes", {}))
    return [_NO_SCHEME, *BUILTIN_SCHEMES, *custom_names]


def apply_scheme_to_session(choice: str) -> None:
    """Apply a built-in or custom atom color scheme to session state.

    Updates ``element_colors``, ``stick_color``, and ``bg_color``
    so that rendering config picks them up.
    """
    if choice == _NO_SCHEME:
        st.session_state["element_colors"] = {}
        st.session_state.pop("atom_color_choice", None)
        return

    data = _resolve_scheme_data(choice)
    if data is None:
        return

    if "element_colors" in data:
        st.session_state["element_colors"] = dict(data["element_colors"])
    if data.get("stick_color"):
        st.session_state["stick_color"] = data["stick_color"]
    st.session_state["atom_color_choice"] = choice


def export_scheme_from_session() -> dict[str, Any]:
    """Export current atom-color settings as a portable dictionary."""
    choice = st.session_state.get("atom_color_choice", _NO_SCHEME)
    if choice != _NO_SCHEME and choice in st.session_state.get("custom_atom_schemes", {}):
        return dict(st.session_state.custom_atom_schemes[choice])
    return {
        "element_colors": dict(st.session_state.get("element_colors", {})),
        "stick_color": st.session_state.get("stick_color"),
        "bg_color": st.session_state.get("bg_color", "white"),
    }
