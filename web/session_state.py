"""
web/session_state.py
=====================
Centralized session state initialization and default values for WikiMolGen web interface.
"""

import streamlit as st
from typing import Dict, Any


def get_2d_defaults() -> Dict[str, Any]:
    """Get default values for 2D rendering settings."""
    return {
        "auto_orient_2d": True,
        "angle_2d": 180,
        "scale": 30.0,
        "margin": 0.5,
        "bond_length": 45.0,
        "min_font_size": 36,
        "padding": 0.03,
        "use_bw": True,
        "transparent": True,
    }


def get_3d_defaults() -> Dict[str, Any]:
    """Get default values for 3D rendering settings."""
    return {
        "auto_orient_3d": True,
        "x_rot_slider": 0.0,
        "y_rot_slider": 200.0,
        "z_rot_slider": 0.0,
        "stick_radius": 0.2,
        "sphere_scale": 0.3,
        "stick_ball_ratio": 1.8,
        "ray_trace": False,
        "ray_shadows": False,
        "stick_transparency": 0.0,
        "sphere_transparency": 0.0,
        "valence": 0.0,
        "antialias": 2,
        "ambient": 0.25,
        "specular": 1.0,
        "direct": 0.45,
        "reflect": 0.45,
        "shininess": 30,
        "depth_cue": False,
        "width": 1320,
        "height": 990,
        "crop_margin": 10,
    }


def get_session_defaults() -> Dict[str, Any]:
    """
    Get all default session state values.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing all default session state variables.
    """
    defaults = {
        # Core state
        "rendered_structure": False,
        "compound_data": None,
        "last_image_html": None,
        "last_drugbox": None,
        "last_chembox": None,
        "last_output_path": None,
        "last_compound": None,
        "last_compound_fetched": None,  # Track last compound fetched from PubChem

        # File download state
        "last_file_data": None,
        "last_file_name": None,
        "last_file_mime": None,

        # PubChem data
        "pubchem_data": None,

        # Template state
        "uploaded_color_template": None,
        "uploaded_settings_template": None,
        "custom_color_templates": {},
        "custom_settings_templates": {},
        "template_applied_once": False,

        # UI state
        "structure_type": "2D",
        "manual_generate": False,
        "save_filename": "",

        # Template selectors
        "color_template_selector": "None",
        "settings_template_selector": "None",
    }

    # Add 2D and 3D defaults
    defaults.update(get_2d_defaults())
    defaults.update(get_3d_defaults())

    return defaults


def initialize_session_state() -> None:
    """
    Initialize Streamlit session state with default values.

    Only sets values for keys that don't already exist in session state,
    preserving user modifications across reruns.
    """
    defaults = get_session_defaults()

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_to_defaults(dimension: str = "all") -> None:
    """
    Reset session state to default values.

    Parameters
    ----------
    dimension : str, optional
        Which settings to reset: "2D", "3D", or "all" (default: "all")
    """
    if dimension == "2D" or dimension == "all":
        for key, value in get_2d_defaults().items():
            st.session_state[key] = value

    if dimension == "3D" or dimension == "all":
        for key, value in get_3d_defaults().items():
            st.session_state[key] = value

    if dimension == "all":
        st.session_state.template_applied_once = False
        st.session_state.uploaded_color_template = None
        st.session_state.uploaded_settings_template = None
