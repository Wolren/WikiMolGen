"""
web/ui/components_2d.py
========================
2D-specific rendering settings for the WikiMolGen Streamlit UI.
"""

import logging

import streamlit as st
from ui.components_shared import (_s2, _cb2, save_config_to_session)

logger = logging.getLogger(__name__)


def render_2d_settings() -> None:
    """Render 2D-specific settings controls."""

    # Advanced 2D settings
    with st.expander("2D Settings", expanded=False):
        st.markdown("**Sizing & Spacing**")
        col1, col2 = st.columns(2)

        with col1:
            _s2("Scale", 10.0, 40.0, 30.0, 1.0, key="scale", help="Pixels per coordinate unit")
            _s2("Margin", 0.0, 5.0, 0.8, 0.1, key="margin")

        with col2:
            _s2("Bond Length", 10.0, 70.0, 50.0, 5.0, key="bond_length", help="Fixed bond length in pixels")
            _s2("Padding", 0.00, 0.20, 0.07, 0.01, key="padding", help="Padding around drawing")

        st.markdown("**Typography & Colors**")
        col1, col2 = st.columns(2)

        with col1:
            _s2("Font Size", 10, 60, 32, 2, key="min_font_size")
            _s2("Label padding", 0.0, 1.0, 0.1, 0.1, key="additional_atom_label_padding")

        with col2:
            _cb2("B/W Palette", value=True, key="use_bw_palette")
            _cb2("Transparent Background", value=True, key="transparent_background")

        # Amine orientation settings
        with st.expander("Amine Orientation", expanded=False):
            st.markdown("**Automatic amine group rotation for Wikipedia-style drawings**")
            auto_orient_amines = _cb2(
                "Auto-orient amines",
                value=True,
                key="auto_orient_amines",
                help="Automatically rotate amine groups for Wikipedia-style 2D drawings",
            )

            if auto_orient_amines:
                _s2("Amine target angle (\u00b0)", 0, 360, 0, 5, key="amine_target_angle",
                    help="Target rotation angle for amine groups")
                _s2("Phenethylamine angle (\u00b0)", 0, 360, 90, 5, key="phenethylamine_target",
                    help="Target rotation angle for phenethylamine sidechains")

        # Advanced RDKit drawing options
        with st.expander("Advanced Drawing", expanded=False):
            st.markdown("**RDKit Drawing Options**")
            col1, col2 = st.columns(2)
            with col1:
                _s2("Bond Line Width", 0.5, 5.0, 1.0, 0.5, key="bond_line_width")
                _s2("Font Scale", 0.5, 3.0, 1.0, 0.1, key="scaling_factor")
                _s2("Multi-bond offset", 0.0, 0.5, 0.15, 0.05, key="multiple_bond_offset")

            with col2:
                _cb2("Stereo labels (R/S)", value=False, key="add_stereo_annotation")
                _cb2("Show radicals", value=False, key="include_radicals")
                _cb2("Chiral flag", value=False, key="include_chiral_flag")

            st.markdown("**Atom Labels**")
            col1, col2 = st.columns(2)
            with col1:
                _cb2("Hide all atom labels", value=False, key="no_atom_labels")
                _cb2("Explicit methyl (CH3)", value=False, key="explicit_methyl")

            with col2:
                _cb2("Atom map numbers", value=False, key="include_atom_tags")

            st.markdown("**Style**")
            col1, col2 = st.columns(2)
            with col1:
                _cb2("Comic style", value=False, key="comic_mode")

            with col2:
                _s2("Fixed font size (-1 = auto)", -1, 60, -1, 1, key="fixed_font_size")

        with st.expander("Legend & Highlights", expanded=False):
            st.markdown("**Compound Legend**")
            legend_text = st.text_input(
                "Legend text (shown below structure)",
                value=st.session_state.get("legend", ""),
                max_chars=200,
                key="legend_input",
                placeholder="e.g. Compound name",
            )
            if legend_text != st.session_state.get("legend", ""):
                st.session_state.legend = legend_text
                save_config_to_session("2d")

            st.markdown("**Atom / Bond Highlighting**")
            col1, col2 = st.columns(2)
            with col1:
                highlight_atoms = st.text_input(
                    "Highlight atoms (comma-separated indices)",
                    value=st.session_state.get("highlight_atoms", ""),
                    max_chars=200,
                    key="highlight_atoms_input",
                    placeholder="e.g. 0,3,5,7",
                )
                if highlight_atoms != st.session_state.get("highlight_atoms", ""):
                    st.session_state.highlight_atoms = highlight_atoms
                    save_config_to_session("2d")

            with col2:
                highlight_bonds = st.text_input(
                    "Highlight bonds (comma-separated indices)",
                    value=st.session_state.get("highlight_bonds", ""),
                    max_chars=200,
                    key="highlight_bonds_input",
                    placeholder="e.g. 1,2",
                )
                if highlight_bonds != st.session_state.get("highlight_bonds", ""):
                    st.session_state.highlight_bonds = highlight_bonds
                    save_config_to_session("2d")

            highlight_color = st.color_picker(
                "Highlight color",
                value=st.session_state.get("highlight_color", "#FF8888"),
                key="highlight_color_picker",
            )
            if highlight_color != st.session_state.get("highlight_color", ""):
                st.session_state.highlight_color = highlight_color
                save_config_to_session("2d")
