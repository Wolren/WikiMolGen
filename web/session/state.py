"""
web/session/state.py
====================
Session state initialization and default values for the WikiMolGen Streamlit app.
"""

import logging
from typing import Any

import streamlit as st

logger = logging.getLogger(__name__)


def get_2d_defaults() -> dict[str, Any]:
    return {
        "scale": 30.0,
        "bond_length": 50.0,
        "margin": 0.8,
        "padding": 0.07,
        "min_font_size": 32,
        "additional_atom_label_padding": 0.1,
        "fixed_font_size": -1,
        "use_bw_palette": True,
        "transparent_background": True,
        "auto_orient_2d": True,
        "angle_degrees": 0.0,
        "bond_line_width": 1.0,
        "scaling_factor": 1.0,
        "multiple_bond_offset": 0.15,
        "add_stereo_annotation": False,
        "include_radicals": False,
        "include_chiral_flag": False,
        "no_atom_labels": False,
        "explicit_methyl": False,
        "include_atom_tags": False,
        "comic_mode": False,
        "legend": "",
        "highlight_atoms": "",
        "highlight_bonds": "",
        "highlight_color": "#FF8888",
        "auto_orient_amines": True,
        "amine_target_angle": 90,
        "phenethylamine_target": 90,
    }


def get_3d_defaults() -> dict[str, Any]:
    return {
        "width": 1800,
        "height": 1600,
        "crop_margin": 10,
        "auto_crop": True,
        "representation": "sticks+spheres",
        "ray_trace_mode": 0,
        "ray_shadows": False,
        "antialias": 4,
        "stick_radius": 0.2,
        "sphere_scale": 0.3,
        "stick_ball_ratio": 1.8,
        "stick_quality": 64,
        "sphere_quality": 6,
        "stick_ball": True,
        "opaque_background": False,
        "two_sided_lighting": True,
        "transparency_mode": 1,
        "bg_color": "white",
        "atom_color_choice": "None",
        "stick_color": "gray50",
        "ambient": 0.25,
        "specular": 1.0,
        "shininess": 30,
        "direct": 0.45,
        "reflect": 0.45,
        "stick_transparency": 0.0,
        "sphere_transparency": 0.0,
        "valence": 0.0,
        "depth_cue": False,
        "fog_start": 1.0,
        "ambient_occlusion": False,
        "ambient_occlusion_scale": 20.0,
        "ray_trace_fog": 0.0,
        "zoom_buffer": 2.0,
        "auto_orient_3d": True,
        "x_rotation": 0.0,
        "y_rotation": 0.0,
        "z_rotation": 0.0,
        "num_conformers": 50,
        "max_iterations": 500,
        "prune_rms_thresh": 0.1,
        "use_random_coords": False,
        "use_basic_knowledge": True,
        "enforce_chirality": True,
        "use_small_ring_torsions": True,
        "use_macrocycle_torsions": False,
        "use_exp_torsion_prefs": True,
    }


def get_protein_defaults() -> dict[str, Any]:
    return {
        "protein_cartoon": True,
        "protein_color_scheme": "chain",
        "protein_water": False,
        "protein_ligand": True,
        "pdb_path": "",
    }


def get_mode_keys(mode: str) -> list[str]:
    if mode == "2D":
        return list(get_2d_defaults().keys()) + ["mode_selector", "structure_type"]
    if mode == "3D":
        return list(get_3d_defaults().keys()) + ["mode_selector", "structure_type"]
    return list(get_protein_defaults().keys()) + ["mode_selector", "structure_type"]


def initialize_session_state() -> None:
    """Ensure all required session state defaults are set."""
    defaults: dict[str, Any] = {
        **get_2d_defaults(),
        **get_3d_defaults(),
        **get_protein_defaults(),
        "smiles": "",
        "cid": "",
        "compound_name": "",
        "last_search_query": "",
        "last_changed_dimension": "2d",
        "config_changed": False,
        "manual_generate": False,
        "mode_selector": "3D",
        "structure_type": "3D",
        "_last_active_mode": "3D",
    }
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def reset_to_defaults(dimension: str = "all") -> None:
    """Reset settings for a given dimension to factory defaults."""
    if dimension in {"2D", "all"}:
        for key in get_2d_defaults():
            st.session_state.pop(key, None)

    if dimension in {"3D", "all"}:
        for key in get_3d_defaults():
            st.session_state.pop(key, None)

    if dimension in {"Protein", "all"}:
        for key in get_protein_defaults():
            st.session_state.pop(key, None)

    initialize_session_state()
