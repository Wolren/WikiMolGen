import logging
from dataclasses import asdict
from typing import Any, Literal

import streamlit as st

from wikimolgen.configs import ConfigLoader

logger = logging.getLogger(__name__)


def get_2d_defaults() -> dict[str, Any]:
    cfg = ConfigLoader.get_2d_config()
    return cfg.to_dict()


def get_3d_defaults() -> dict[str, Any]:
    cfg = ConfigLoader.get_3d_config()
    d = asdict(cfg.render) if hasattr(cfg, 'render') else {}
    d["x_rot_slider"] = 0.0
    d["y_rot_slider"] = 0.0
    d["z_rot_slider"] = 0.0
    d["ray_trace"] = bool(cfg.render.ray_trace_mode)
    d["ray_shadows"] = bool(cfg.render.ray_shadows)
    d["depth_cue"] = bool(cfg.render.depth_cue)
    return d


def get_session_defaults() -> dict[str, Any]:
    defaults = {
        "rendered_structure": False,
        "compound_data": None,
        "last_image_html": None,
        "last_output_path": None,
        "last_compound": None,
        "last_compound_fetched": None,
        "last_file_data": None,
        "last_file_name": None,
        "last_file_mime": None,
        "download_filename_input": "molecule",
        "pubchem_data": None,
        "uploaded_color_template": None,
        "uploaded_settings_template": None,
        "custom_color_templates": {},
        "custom_settings_templates": {},
        "template_applied_once": False,
        "structure_type": "3D",
        "manual_generate": False,
        "save_filename": "",
        "color_template_selector": "None",
        "settings_template_selector": "None",
        "config_manager_2d": None,
        "config_manager_3d": None,
    }

    defaults.update(get_2d_defaults())
    defaults.update(get_3d_defaults())

    return defaults


def initialize_session_state() -> None:
    defaults = get_session_defaults()

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    if "last_structure_type" not in st.session_state:
        st.session_state.last_structure_type = "3D"

    if "config_changed" not in st.session_state:
        st.session_state.config_changed = False

    logger.info(f"Session state initialized with {len(defaults)} keys")


def reset_to_defaults(dimension: str = "all") -> None:
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
        st.session_state.config_changed = True

    logger.info(f"Reset session state to defaults: {dimension}")


def get_config_for_rendering(dimension: Literal["2d", "3d"] = "2d") -> dict[str, Any]:
    if dimension == "2d":
        return {key: st.session_state.get(key) for key in get_2d_defaults().keys()}
    elif dimension == "3d":
        return {key: st.session_state.get(key) for key in get_3d_defaults().keys()}
    else:
        logger.warning(f"Unknown dimension: {dimension}")
        return {}
