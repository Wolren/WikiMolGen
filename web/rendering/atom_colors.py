"""
web/rendering/atom_colors.py
=============================
Atom color scheme management for 3D rendering.

Built-in schemes (CPK, Jmol, RasMol, etc.) + custom upload.
All values are applied directly to session state so that
build_3d_config() picks them up automatically.
"""

import streamlit as st

from wikimolgen.configs.loader import BULITIN_COLOR_TEMPLATES, COLOR_TEMPLATE_META

BUILTIN_SCHEMES: dict[str, dict] = dict(BULITIN_COLOR_TEMPLATES)


def get_scheme_display_name(key: str) -> str:
    """Return user-friendly display name for a scheme key."""
    return COLOR_TEMPLATE_META.get(key, {}).get("name", key)


def get_scheme_choices() -> list[str]:
    """Return the list of scheme choices for a selectbox."""
    custom_names = list(st.session_state.get("custom_atom_schemes", {}).keys())
    return ["None"] + list(BUILTIN_SCHEMES.keys()) + custom_names


def apply_scheme_to_session(choice: str) -> None:
    """Apply a built-in or custom atom color scheme to session state.

    Updates element_colors, stick_color, bg_color in session state
    so build_3d_config() picks them up during rendering.
    """
    if choice == "None":
        st.session_state["element_colors"] = {}
        st.session_state.pop("atom_color_choice", None)
        return

    if choice in st.session_state.get("custom_atom_schemes", {}):
        data = st.session_state.custom_atom_schemes[choice]
    elif choice in BUILTIN_SCHEMES:
        data = BUILTIN_SCHEMES[choice]
    else:
        return

    if "element_colors" in data:
        st.session_state["element_colors"] = dict(data["element_colors"])
    if data.get("stick_color"):
        st.session_state["stick_color"] = data["stick_color"]
    if data.get("bg_color"):
        st.session_state["bg_color"] = data["bg_color"]
    st.session_state["atom_color_choice"] = choice


def export_scheme_from_session() -> dict:
    """Export current atom color settings as a portable dict."""
    choice = st.session_state.get("atom_color_choice", "None")
    if choice != "None" and choice in st.session_state.get("custom_atom_schemes", {}):
        return dict(st.session_state.custom_atom_schemes[choice])
    return {
        "element_colors": dict(st.session_state.get("element_colors", {})),
        "stick_color": st.session_state.get("stick_color"),
        "bg_color": st.session_state.get("bg_color", "white"),
    }
