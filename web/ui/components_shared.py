"""
web/ui/components_shared.py
============================
Shared widget factories, callbacks, config saving, and validation
for the WikiMolGen Streamlit UI.
"""

import logging
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


# ============================================================================
# VALIDATION
# ============================================================================


def _validate_atom_scheme(data: dict) -> str | None:
    """Validate uploaded scheme data, return error message or ``None`` on success."""
    ec = data.get("element_colors")
    if ec is not None:
        if not isinstance(ec, dict):
            return "element_colors must be an object (dict)"
        for k, v in ec.items():
            if not isinstance(k, str) or not k.isascii() or len(k) > 2:
                return f"Invalid element symbol: {k!r}"
            if not isinstance(v, str):
                return f"Color for element {k!r} must be a string"
    name = data.get("name")
    if name is not None and (not isinstance(name, str) or len(name) > 100):
        return "Scheme name must be a string under 100 characters"
    return None


# ============================================================================
# CALLBACKS (Rotation slider / number input sync)
# ============================================================================


def _sync_slider_to_config(key: str) -> None:
    st.session_state[key] = st.session_state[f"{key}_slider"]
    st.session_state.config_changed = True


def _sync_input_to_slider(key: str) -> None:
    st.session_state[f"{key}_slider"] = st.session_state[key]
    st.session_state.config_changed = True


def _sync_number_input(key: str) -> None:
    """Sync number_input (key_input) to config key and slider."""
    val = st.session_state[f"{key}_input"]
    st.session_state[key] = val
    st.session_state[f"{key}_slider"] = val
    save_config_to_session("3d")


# ============================================================================
# WIDGET FACTORY (Auto-save wrapper helpers)
# ============================================================================


def _s(dim: str, *a: Any, **kw: Any) -> Any:
    kw.pop("on_change", None)
    call_kw = {**kw, "on_change": lambda: save_config_to_session(dim)}
    return st.slider(*a, **call_kw)


def _cb(dim: str, *a: Any, **kw: Any) -> Any:
    kw.pop("on_change", None)
    call_kw = {**kw, "on_change": lambda: save_config_to_session(dim)}
    return st.checkbox(*a, **call_kw)


def _ni(dim: str, *a: Any, **kw: Any) -> Any:
    kw.pop("on_change", None)
    call_kw = {**kw, "on_change": lambda: save_config_to_session(dim)}
    return st.number_input(*a, **call_kw)


def _sb(dim: str, *a: Any, **kw: Any) -> Any:
    kw.pop("on_change", None)
    call_kw = {**kw, "on_change": lambda: save_config_to_session(dim)}
    return st.selectbox(*a, **call_kw)


# Shorter aliases for common dimensions
_s2 = lambda *a, **kw: _s("2d", *a, **kw)
_s3 = lambda *a, **kw: _s("3d", *a, **kw)
_cb2 = lambda *a, **kw: _cb("2d", *a, **kw)
_cb3 = lambda *a, **kw: _cb("3d", *a, **kw)
_ni3 = lambda *a, **kw: _ni("3d", *a, **kw)
_sb3 = lambda *a, **kw: _sb("3d", *a, **kw)


# ============================================================================
# CONFIG SAVING (On setting changes)
# ============================================================================


def save_config_to_session(dimension: str = "2d") -> None:
    """Mark config as changed and save to session.

    Call this AFTER user modifies any setting.

    Parameters
    ----------
    dimension : str
        "2d", "3d", or "protein"
    """
    st.session_state.config_changed = True
    st.session_state.last_changed_dimension = dimension
