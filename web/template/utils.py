"""
web/template/utils.py
=====================
Preset utility functions for the web UI.

Handles validation, export, upload, and application of settings presets.
Presets are full config snapshots per mode (2D/3D/Protein).
"""

import dataclasses
import json
from datetime import datetime
from typing import Any, Final

import streamlit as st

from wikimolgen.configs import Config2D, ConformerConfig, ProteinConfig, RenderConfig3D

# ── Validation ──────────────────────────────────────────────


def validate_preset(data: dict) -> list[str]:
    """Validate a preset dict. Returns list of error messages (empty = valid)."""
    errors: list[str] = []
    if str(data.get("type", "")).lower() not in ("2d", "3d", "protein"):
        errors.append("'type' must be '2d', '3d', or 'protein'")
    if "name" in data and not isinstance(data["name"], str):
        errors.append("'name' must be a string")
    if "description" in data and not isinstance(data["description"], str):
        errors.append("'description' must be a string")
    settings = data.get("settings")
    if settings is not None and not isinstance(settings, dict):
        errors.append("'settings' must be an object (dict)")
    return errors


# Max upload size: 1 MB (prevents OOM on large/malicious files)
MAX_UPLOAD_SIZE: Final[int] = 1_048_576


def validate_uploaded_json(uploaded_file) -> tuple[dict[str, Any] | None, str | None]:
    """Parse uploaded JSON file into a dict.

    Returns (parsed_dict, error_message).
    On success error_message is None; on failure parsed_dict is None.
    """
    try:
        raw = uploaded_file.read(MAX_UPLOAD_SIZE + 1)
        if len(raw) > MAX_UPLOAD_SIZE:
            return (
                None,
                f"File too large ({len(raw):,} bytes). Maximum is {MAX_UPLOAD_SIZE:,} bytes.",
            )
        data = json.loads(raw)
        if not isinstance(data, dict):
            return None, "Uploaded file must contain a JSON object (dict)"
        return data, None
    except json.JSONDecodeError as e:
        return None, f"Invalid JSON: {e}"


# ── Export ──────────────────────────────────────────────────


def export_current_as_preset(gen_type: str, name: str | None = None) -> dict[str, Any]:
    """Build a preset dict from the current session state."""
    if gen_type == "2D":
        defaults = {f.name: getattr(Config2D(), f.name) for f in dataclasses.fields(Config2D)}
        settings_dict = {}
        for key, default in defaults.items():
            settings_dict[key] = st.session_state.get(key, default)
        if settings_dict.get("auto_orient_2d", False):
            settings_dict["angle_degrees"] = None
    elif gen_type == "Protein":
        settings_dict = export_protein_preset()
    else:
        settings_dict = export_3d_preset()

    return {
        "type": gen_type.lower() if gen_type.lower() in ("2d", "3d", "protein") else "3d",
        "name": name or f"Custom {gen_type}",
        "description": "Exported from web interface",
        "settings": settings_dict,
    }


def export_protein_preset() -> dict[str, Any]:
    """Collect protein rendering settings from session state."""
    defaults = {f.name: getattr(ProteinConfig(), f.name) for f in dataclasses.fields(ProteinConfig)}
    settings = {}
    for key, default in defaults.items():
        settings[key] = st.session_state.get(key, default)
    return settings


def export_3d_preset() -> dict[str, Any]:
    """Collect 3D rendering and conformer settings from session state."""
    defaults = {
        f.name: getattr(RenderConfig3D(), f.name) for f in dataclasses.fields(RenderConfig3D)
    } | {f.name: getattr(ConformerConfig(), f.name) for f in dataclasses.fields(ConformerConfig)}
    settings = {}
    for key, default in defaults.items():
        settings[key] = st.session_state.get(key, default)

    settings["atom_color_choice"] = st.session_state.get("atom_color_choice", "None")

    for key in ("ray_shadows", "depth_cue"):
        val = settings.get(key)
        if isinstance(val, bool):
            settings[key] = int(val)

    return settings


# ── Upload ─────────────────────────────────────────────────


def load_uploaded_preset(uploaded_file) -> dict[str, Any] | None:
    """Parse an uploaded JSON file and return ``{name, data}`` or ``None`` on failure.

    The returned dict has two keys:

    ``name``
        Extracted from the file's ``"name"`` field, or an auto-generated fallback.
    ``data``
        The full parsed dict.

    On failure ``st.error`` is called and ``None`` is returned.
    """
    parsed, err = validate_uploaded_json(uploaded_file)
    if err:
        st.error(f"Failed to load preset: {err}")
        return None
    assert parsed is not None
    preset_name = parsed.get("name", f"Custom_{datetime.now().strftime('%H%M%S')}")
    return {"name": preset_name, "data": parsed}


def apply_preset_to_session(template_data: dict[str, Any]) -> None:
    """Apply a preset's settings into session state so live widgets reflect loaded values."""
    settings = template_data.get("settings", template_data)
    for key, value in settings.items():
        clean_key = key
        if clean_key.startswith("render_"):
            clean_key = clean_key[7:]
        elif clean_key.startswith("conformer_"):
            clean_key = clean_key[10:]

        if clean_key not in st.session_state:
            continue
        current = st.session_state[clean_key]
        if isinstance(current, bool) and isinstance(value, int):
            value = bool(value)
        st.session_state[clean_key] = value
