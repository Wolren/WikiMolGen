import logging
from dataclasses import asdict
from typing import Any

import streamlit as st

from wikimolgen.configs.loader import ConfigLoader, ProteinConfig

logger = logging.getLogger(__name__)


def get_2d_defaults() -> dict[str, Any]:
    cfg = ConfigLoader.get_2d_config()
    return cfg.to_dict()


def get_3d_defaults() -> dict[str, Any]:
    cfg = ConfigLoader.get_3d_config()
    d = asdict(cfg.render) if hasattr(cfg, "render") else {}
    conf = asdict(cfg.conformer) if hasattr(cfg, "conformer") else {}
    d.update(conf)
    d["ray_shadows"] = bool(getattr(cfg.render, "ray_shadows", 0))
    d["depth_cue"] = bool(getattr(cfg.render, "depth_cue", 0))
    d["ambient_occlusion"] = bool(getattr(cfg.render, "ambient_occlusion", False))
    return d


def get_protein_defaults() -> dict[str, Any]:
    return asdict(ProteinConfig())


def get_session_defaults() -> dict[str, Any]:
    defaults: dict[str, Any] = {
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
        "custom_atom_schemes": {},
        "custom_presets": {},
        "atom_color_choice": "None",
        "structure_type": "3D",
        "manual_generate": False,
        "auto_generate": True,
        "save_filename": "",
        "preset_selector": "None",
        "config_manager_2d": None,
        "config_manager_3d": None,
        "sdf_content": None,
    }

    defaults.update(get_2d_defaults())
    defaults.update(get_3d_defaults())
    defaults.update(get_protein_defaults())

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
        for key in get_2d_defaults():
            st.session_state.pop(key, None)

    if dimension == "3D" or dimension == "all":
        for key in get_3d_defaults():
            st.session_state.pop(key, None)

    if dimension == "Protein" or dimension == "all":
        for key in get_protein_defaults():
            st.session_state.pop(key, None)

    if dimension == "all":
        st.session_state.pop("atom_color_choice", None)
        st.session_state.pop("custom_atom_schemes", None)
        st.session_state.pop("custom_presets", None)
        st.session_state.config_changed = True

    logger.info(f"Reset session state to defaults: {dimension}")


def get_mode_keys(mode: str) -> set[str]:
    """Return the set of setting keys that belong to a given mode."""
    if mode == "2D":
        return set(get_2d_defaults().keys())
    elif mode == "3D":
        return set(get_3d_defaults().keys())
    elif mode == "Protein":
        return set(get_protein_defaults().keys())
    return set()
