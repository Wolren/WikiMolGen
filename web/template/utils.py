"""
web/utils.py
======================
Template management utilities for WikiMolGen web interface.
Handles template export, import, and application to generators.
"""

import json
from datetime import datetime
from typing import Dict, Any, Optional, Union

import streamlit as st

from wikimolgen.predefined_templates import ColorStyleTemplate, SettingsTemplate


def export_current_settings_as_template(gen_type: str) -> Dict[str, Any]:
    """
    Export current UI settings as a template dictionary.

    Parameters
    ----------
    gen_type : str
        Generator type: "2D" or "3D"

    Returns
    -------
    Dict[str, Any]
        Template dictionary ready for JSON export
    """
    if gen_type == "2D":
        settings_dict = {
            "scale": st.session_state.get("scale", 30.0),
            "margin": st.session_state.get("margin", 0.8),
            "bond_length": st.session_state.get("bond_length", 50.0),
            "min_font_size": st.session_state.get("min_font_size", 36),
            "padding": st.session_state.get("padding", 0.07),
            "use_bw_palette": st.session_state.get("use_bw", True),
            "transparent_background": st.session_state.get("transparent", True),
            "auto_orient_2d": st.session_state.get("auto_orient_2d", True),
        }
        template_dict = {
            "type": "settings",
            "name": "Custom 2D",
            "description": "Exported from web interface",
            "dimension": "2D",
            "settings": settings_dict
        }
    else:
        settings_dict = {
            "auto_orient_3d": st.session_state.get("auto_orient_3d", True),
            "x_rotation": st.session_state.get("x_rot_slider", 0.0),
            "y_rotation": st.session_state.get("y_rot_slider", 0.0),
            "z_rotation": st.session_state.get("z_rot_slider", 0.0),
            "stick_radius": st.session_state.get("stick_radius", 0.2),
            "sphere_scale": st.session_state.get("sphere_scale", 0.3),
            "stick_ball_ratio": st.session_state.get("stick_ball_ratio", 1.8),
            "ray_trace_mode": 1 if st.session_state.get("ray_trace", False) else 0,
            "ray_shadows": 1 if st.session_state.get("ray_shadows", False) else 0,
            "stick_transparency": st.session_state.get("stick_transparency", 0.0),
            "sphere_transparency": st.session_state.get("sphere_transparency", 0.0),
            "valence": st.session_state.get("valence", 0.0),
            "antialias": st.session_state.get("antialias", 2),
            "ambient": st.session_state.get("ambient", 0.25),
            "specular": st.session_state.get("specular", 1.0),
            "direct": st.session_state.get("direct", 0.45),
            "reflect": st.session_state.get("reflect", 0.45),
            "shininess": st.session_state.get("shininess", 30),
            "depth_cue": 1 if st.session_state.get("depth_cue", False) else 0,
            "width": st.session_state.get("width", 1800),
            "height": st.session_state.get("height", 1600),
            "auto_crop": st.session_state.get("auto_crop", True),
            "crop_margin": st.session_state.get("crop_margin", 10),
        }
        template_dict = {
            "type": "settings",
            "name": "Custom 3D",
            "description": "Exported from web interface",
            "dimension": "3D",
            "settings": settings_dict
        }

    return template_dict


def export_color_template() -> Dict[str, Any]:
    """
    Export current color settings as a color template.

    Returns
    -------
    Dict[str, Any]
        Color template dictionary ready for JSON export
    """
    color_dict = {
        "type": "color_style",
        "name": f"Custom Colors - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Exported from web interface",
        "element_colors": {},
        "stick_color": None,
        "use_bw_palette": st.session_state.get("use_bw", False),
        "transparent_background": st.session_state.get("transparent", False),
    }
    return color_dict


def load_custom_template(
        uploaded_file,
        template_type: str
) -> Optional[Dict[str, Any]]:
    """
    Load a custom template from uploaded JSON file.

    Parameters
    ----------
    uploaded_file : UploadedFile
        Streamlit uploaded file object
    template_type : str
        Type of template: "color" or "settings"

    Returns
    -------
    Optional[Dict[str, Any]]
        Template data dictionary, or None if loading failed
    """
    try:
        template_data = json.load(uploaded_file)
        template_name = template_data.get(
            'name',
            f'Custom_{datetime.now().strftime("%H%M%S")}'
        )
        return {"name": template_name, "data": template_data}
    except Exception as e:
        st.error(f"Failed to load {template_type} template: {e}")
        return None


def save_template_to_session(
        template_name: str,
        template_data: Dict[str, Any],
        template_type: str
) -> None:
    """
    Save template to session state for persistence.

    Parameters
    ----------
    template_name : str
        Name of the template
    template_data : Dict[str, Any]
        Template data dictionary
    template_type : str
        Type: "color" or "settings"
    """
    if template_type == "color":
        st.session_state.custom_color_templates[template_name] = template_data
        st.session_state.uploaded_color_template = template_data
    elif template_type == "settings":
        st.session_state.custom_settings_templates[template_name] = template_data
        st.session_state.uploaded_settings_template = template_data

        # Sync settings to UI sliders
        for key, value in template_data.get("settings", {}).items():
            if key in st.session_state:
                st.session_state[key] = value
        st.session_state.template_applied_once = True


def apply_templates_to_generator(
        gen: Union['MoleculeGenerator2D', 'MoleculeGenerator3D'],
        gen_type: str
) -> bool:
    """
    Apply selected template to a molecule generator.

    Parameters
    ----------
    gen : MoleculeGenerator2D or MoleculeGenerator3D
        Generator instance to apply template to
    gen_type : str
        Generator type: "2D" or "3D"

    Returns
    -------
    bool
        True if any template was applied, False otherwise
    """
    # Skip if template already applied once (allows manual override)
    if st.session_state.get("template_applied_once", False):
        return False

    template_applied = False

    # Apply color template
    color_choice = st.session_state.get('color_template_selector', 'None')
    if color_choice != "None":
        try:
            if color_choice in st.session_state.custom_color_templates:
                color_tmpl = ColorStyleTemplate(
                    st.session_state.custom_color_templates[color_choice]
                )
                gen.load_color_template(color_tmpl)
            else:
                gen.load_color_template(color_choice)
            template_applied = True
        except Exception as e:
            st.warning(f"Color template error: {e}")

    # Apply uploaded color template
    if st.session_state.uploaded_color_template:
        try:
            color_tmpl = ColorStyleTemplate(
                st.session_state.uploaded_color_template
            )
            gen.load_color_template(color_tmpl)
            template_applied = True
        except Exception as e:
            st.warning(f"Uploaded color template error: {e}")

    # Apply settings template
    settings_choice = st.session_state.get('settings_template_selector', 'None')
    if settings_choice != "None":
        try:
            if settings_choice in st.session_state.custom_settings_templates:
                settings_tmpl = SettingsTemplate(
                    st.session_state.custom_settings_templates[settings_choice]
                )
                if settings_tmpl.dimension == gen_type:
                    gen.load_settings_template(settings_tmpl)
                    template_applied = True
            elif gen_type == "2D" and "2d" in settings_choice.lower():
                gen.load_settings_template(settings_choice)
                template_applied = True
            elif gen_type == "3D" and "3d" in settings_choice.lower():
                gen.load_settings_template(settings_choice)
                template_applied = True
        except Exception as e:
            st.warning(f"Settings template error: {e}")

    # Apply uploaded settings template
    if st.session_state.uploaded_settings_template:
        try:
            settings_tmpl = SettingsTemplate(
                st.session_state.uploaded_settings_template
            )
            if settings_tmpl.dimension == gen_type:
                gen.load_settings_template(settings_tmpl)
                template_applied = True
        except Exception as e:
            st.warning(f"Uploaded settings template error: {e}")

    return template_applied
