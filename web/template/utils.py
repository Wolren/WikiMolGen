"""
web/template/utils.py
=====================
Template utility functions for the web UI.

Handles validation, export, upload, and application of color and settings templates.
"""

import dataclasses
import json
from datetime import datetime
from typing import Any, Final

import streamlit as st

from wikimolgen.configs import Config2D, ConformerConfig, RenderConfig3D

# ── Validation ──────────────────────────────────────────────


def validate_color_template(data: dict) -> list[str]:
    """Validate a color template dict. Returns list of error messages (empty = valid)."""
    errors: list[str] = []
    if "name" in data and not isinstance(data["name"], str):
        errors.append("'name' must be a string")
    if "description" in data and not isinstance(data["description"], str):
        errors.append("'description' must be a string")
    ec = data.get("element_colors", {})
    if not isinstance(ec, dict):
        errors.append("'element_colors' must be an object (dict)")
    elif ec and not all(isinstance(k, str) and isinstance(v, str) for k, v in ec.items()):
        errors.append("'element_colors' keys and values must be strings")
    sc = data.get("stick_color")
    if sc is not None and not isinstance(sc, str):
        errors.append("'stick_color' must be a string or null")
    bg = data.get("bg_color", "white")
    if not isinstance(bg, str):
        errors.append("'bg_color' must be a string")
    return errors


def validate_settings_template(data: dict) -> list[str]:
    """Validate a settings template dict. Returns list of error messages (empty = valid)."""
    errors: list[str] = []
    if data.get("type") not in ("2d", "3d", "protein"):
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


def export_current_settings_as_template(gen_type: str) -> dict[str, Any]:
    """Build a settings template dict from the current session state."""
    if gen_type == "2D":
        defaults = {f.name: getattr(Config2D(), f.name) for f in dataclasses.fields(Config2D)}
        settings_dict = {}
        for key, default in defaults.items():
            settings_dict[key] = st.session_state.get(key, default)
        if settings_dict.get("auto_orient_2d", False):
            settings_dict["angle_degrees"] = None
    elif gen_type == "Protein":
        settings_dict = export_protein_settings()
    else:
        settings_dict = export_3d_settings()

    type_map = {"2D": "2d", "3D": "3d", "Protein": "protein"}
    return {
        "type": type_map.get(gen_type, "3d"),
        "name": f"Custom {gen_type}",
        "description": "Exported from web interface",
        "settings": settings_dict,
    }


def export_protein_settings() -> dict[str, Any]:
    """Collect protein rendering settings from session state."""
    return {
        "protein_color_scheme": st.session_state.get("protein_color_scheme", "Secondary Structure"),
        "helix_color": st.session_state.get("helix_color", "#3399FF"),
        "sheet_color": st.session_state.get("sheet_color", "#FFCC00"),
        "loop_color": st.session_state.get("loop_color", "#99AABB"),
        "cartoon_transparency": st.session_state.get("cartoon_transparency", 0.0),
        "cartoon_fancy": st.session_state.get("cartoon_fancy", True),
        "cartoon_sheets": st.session_state.get("cartoon_sheets", True),
        "show_ligand": st.session_state.get("show_ligand", False),
        "show_water": st.session_state.get("show_water", False),
        "ligand_style": st.session_state.get("ligand_style", "sticks"),
        "ligand_transparency": st.session_state.get("ligand_transparency", 0.0),
        "ligand_color": st.session_state.get("ligand_color", "element"),
        "ligand_single_color": st.session_state.get("ligand_single_color", "#FF6B6B"),
        "ligand_stick_radius": st.session_state.get("ligand_stick_radius", 0.25),
        "protein_width": st.session_state.get("protein_width", 1920),
        "protein_height": st.session_state.get("protein_height", 1080),
        "protein_antialias": st.session_state.get("protein_antialias", 2),
        "protein_specular": st.session_state.get("protein_specular", 1),
        "protein_ambient": st.session_state.get("protein_ambient", 0.4),
        "protein_bg": st.session_state.get("protein_bg", "black"),
        "protein_shininess": st.session_state.get("protein_shininess", 10),
        "protein_ray_shadows": st.session_state.get("protein_ray_shadows", True),
        "protein_ray_trace": st.session_state.get("protein_ray_trace", True),
        "protein_auto_orient": st.session_state.get("protein_auto_orient", True),
        "protein_autocrop": st.session_state.get("protein_autocrop", True),
        "protein_crop_margin": st.session_state.get("protein_crop_margin", 10),
    }


def export_3d_settings() -> dict[str, Any]:
    """Collect 3D rendering and conformer settings from session state."""
    defaults = {
        f.name: getattr(RenderConfig3D(), f.name) for f in dataclasses.fields(RenderConfig3D)
    } | {f.name: getattr(ConformerConfig(), f.name) for f in dataclasses.fields(ConformerConfig)}
    settings = {}
    for key, default in defaults.items():
        if key == "element_colors":
            continue  # handled separately by color template system
        settings[key] = st.session_state.get(key, default)

    # Override with rotation slider values (stored under different session keys)
    for slider, canonical in [
        ("x_rot_slider", "x_rotation"),
        ("y_rot_slider", "y_rotation"),
        ("z_rot_slider", "z_rotation"),
    ]:
        if slider in st.session_state:
            settings[canonical] = st.session_state[slider]

    # Convert bool session values to int for dataclass compatibility
    for key in ("ray_shadows", "depth_cue"):
        val = settings.get(key)
        if isinstance(val, bool):
            settings[key] = int(val)

    return settings


def export_color_template() -> dict[str, Any]:
    """Build a color template dict from the current session state."""
    uploaded = st.session_state.get("uploaded_color_template")
    if isinstance(uploaded, dict):
        return {
            "name": uploaded.get(
                "name", f"Custom Colors - {datetime.now().strftime('%Y%m%d_%H%M%S')}"
            ),
            "description": uploaded.get("description", "Exported from web interface"),
            "element_colors": uploaded.get("element_colors", {}),
            "stick_color": uploaded.get("stick_color"),
            "bg_color": uploaded.get("bg_color", st.session_state.get("bg_color", "white")),
        }
    return {
        "name": f"Custom Colors - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Exported from web interface",
        "element_colors": {},
        "stick_color": None,
        "bg_color": st.session_state.get("bg_color", "white"),
    }


# ── Upload ─────────────────────────────────────────────────


def load_custom_template(uploaded_file, template_type: str) -> dict[str, Any] | None:
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
        st.error(f"Failed to load {template_type} template: {err}")
        return None
    template_name = parsed.get("name", f"Custom_{datetime.now().strftime('%H%M%S')}")
    return {"name": template_name, "data": parsed}


def save_template_to_session(
    template_name: str, template_data: dict[str, Any], template_type: str
) -> None:
    """Store a parsed template into session state.

    For ``"settings"`` templates the individual setting keys are applied to
    ``st.session_state`` so that any live widgets immediately reflect the
    loaded values.
    """
    if template_type == "color":
        if template_name in st.session_state.custom_color_templates:
            st.warning(f"Overwriting existing color template: {template_name!r}")
        st.session_state.custom_color_templates[template_name] = template_data
        st.session_state.uploaded_color_template = template_data
    elif template_type == "settings":
        if template_name in st.session_state.custom_settings_templates:
            st.warning(f"Overwriting existing settings template: {template_name!r}")
        st.session_state.custom_settings_templates[template_name] = template_data
        st.session_state.uploaded_settings_template = template_data
        settings = template_data.get("settings", template_data)
        for key, value in settings.items():
            if key in st.session_state:
                st.session_state[key] = value
        # Sync canonical rotation keys to slider session keys
        for canonical, slider in [
            ("x_rotation", "x_rot_slider"),
            ("y_rotation", "y_rot_slider"),
            ("z_rotation", "z_rot_slider"),
        ]:
            if canonical in settings and slider in st.session_state:
                st.session_state[slider] = settings[canonical]
        st.session_state.template_applied_once = True


# ── Apply ──────────────────────────────────────────────────


def apply_templates_to_generator(gen: Any, gen_type: str) -> bool:
    """Apply selected/uploaded templates to a generator instance.

    Returns ``True`` if any template was applied.
    """
    if st.session_state.get("template_applied_once", False):
        return False

    template_applied = False

    # Color template from selector (Templates section or Rendering section)
    color_choice = (
        st.session_state.get("atom_color_template")
        or st.session_state.get("tmpl_color_selector")
        or st.session_state.get("color_template_selector", "None")
    )
    if color_choice != "None":
        try:
            if color_choice in st.session_state.custom_color_templates:
                gen.load_color_template(st.session_state.custom_color_templates[color_choice])
            else:
                gen.load_color_template(color_choice)
            template_applied = True
        except Exception as e:
            st.warning(f"Color template error: {e}")

    # Uploaded color template
    if st.session_state.uploaded_color_template:
        try:
            gen.load_color_template(st.session_state.uploaded_color_template)
            template_applied = True
        except Exception as e:
            st.warning(f"Uploaded color template error: {e}")

    # Settings template from selector
    settings_choice = st.session_state.get("settings_template_selector", "None")
    if settings_choice != "None":
        try:
            if settings_choice in st.session_state.custom_settings_templates:
                st.session_state.template_applied_once = True
                gen.load_settings_template(
                    st.session_state.custom_settings_templates[settings_choice]
                )
                template_applied = True
            else:
                gen.load_settings_template(settings_choice)
                template_applied = True
        except Exception as e:
            st.warning(f"Settings template error: {e}")

    # Uploaded settings template
    if st.session_state.uploaded_settings_template:
        try:
            gen.load_settings_template(st.session_state.uploaded_settings_template)
            template_applied = True
        except Exception as e:
            st.warning(f"Uploaded settings template error: {e}")

    return template_applied
