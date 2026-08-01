"""
web/ui/components_3d.py
========================
3D-specific rendering settings for the WikiMolGen Streamlit UI:
canvas, rendering (quality + style + colors), lighting, effects, conformer.
"""

import json
import logging
from datetime import datetime

import streamlit as st
from rendering.atom_colors import apply_scheme_to_session, export_scheme_from_session, get_scheme_choices
from template.utils import MAX_UPLOAD_SIZE
from ui.icons import header
from ui.components_shared import (_s3, _cb3, _ni3, _sb3, _validate_atom_scheme, save_config_to_session)

logger = logging.getLogger(__name__)


# ============================================================================
# CANVAS SETTINGS
# ============================================================================


def render_canvas_settings() -> None:
    """Render canvas/dimension settings."""
    with st.expander("Canvas", expanded=False):
        st.markdown(header("ruler", "Image Dimensions"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            _ni3("Width (pixels)", 800, 4000, 1800, 100, key="width")
            _ni3("Height (pixels)", 600, 3000, 1600, 100, key="height")

        with col2:
            _s3("Crop Margin", 5, 50, 10, 5, key="crop_margin")
            _cb3("Auto Crop", value=True, key="auto_crop")


# ============================================================================
# RENDERING SETTINGS (quality, style, colors)
# ============================================================================


def render_rendering_settings() -> None:
    """Render rendering quality settings."""
    with st.expander("Rendering", expanded=False):
        st.markdown(header("atom", "Molecular Representation"), unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)

        with col1:
            _s3("Stick Radius", 0.1, 0.5, 0.2, 0.05, key="stick_radius")

        with col2:
            _s3("Atom Size", 0.15, 0.5, 0.3, 0.05, key="sphere_scale")

        with col3:
            _s3("Ball Ratio", 1.2, 3.0, 1.8, 0.1, key="stick_ball_ratio")

        st.markdown(header("settings-2", "Quality Settings"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            _sb3("Ray Tracing", [0, 1, 2, 3], index=0, key="ray_trace_mode",
                 help="0=Off, 1=Ray trace, 2=Realtime, 3=Realtime strip")
            _cb3("Shadows", value=False, key="ray_shadows",
                 help="Enable shadows (slower, requires ray tracing)")

        with col2:
            _sb3("Antialiasing", [0, 1, 2, 3, 4], 4, key="antialias",
                 help="0=Off, 1=On, 2-4=Multisample levels")

        st.markdown("**Render Quality**")
        col1, col2 = st.columns(2)
        with col1:
            _s3("Stick Quality", 16, 128, 64, 8, key="stick_quality")
        with col2:
            _s3("Sphere Quality", 2, 12, 6, 1, key="sphere_quality")

        st.markdown("**Representation**")
        _sb3("Style", ["sticks+spheres", "sticks", "spheres", "lines"], key="representation")

        render_color_palette()

        st.markdown("**Lighting Mode**")
        col1, col2 = st.columns(2)
        with col1:
            _cb3("Two-sided lighting", value=True, key="two_sided_lighting")
        with col2:
            _sb3("Transparency Mode", [0, 1, 2], index=1, key="transparency_mode",
                 help="0=Off, 1=Additive, 2=Weighted average")

        st.markdown("**Miscellaneous**")
        col1, col2 = st.columns(2)
        with col1:
            _cb3("Stick-ball style", value=True, key="stick_ball")
        with col2:
            _cb3("Opaque background", value=False, key="opaque_background")


def render_color_palette() -> None:
    """Render color palette with Predefined/Upload/Save tabs (like presets)."""
    st.markdown(header("palette", "Colors"), unsafe_allow_html=True)

    _sb3("Background", ["white", "black", "gray"], key="bg_color",
         help="Set the background color behind the molecule render")

    tab1, tab2, tab3 = st.tabs(["Predefined", "Upload", "Save"])

    with tab1:
        atom_choices = get_scheme_choices()
        current_atom = st.session_state.get("atom_color_choice", "None")
        atom_idx = atom_choices.index(current_atom) if current_atom in atom_choices else 0
        new_atom = st.selectbox("Atom Color Scheme", atom_choices, index=atom_idx, key="atom_color_sel")
        if new_atom != current_atom:
            apply_scheme_to_session(new_atom)

        current_choice = st.session_state.get("atom_color_choice", "None")
        if current_choice in st.session_state.get("custom_atom_schemes", {}) and st.button(
            f"Remove '{current_choice}'",
            key="remove_atom_scheme",
            icon=":material/delete:",
        ):
            del st.session_state.custom_atom_schemes[current_choice]
            st.rerun()

        st.markdown("**Manual Overrides**")
        st.text_input(
            "Stick Color",
            value="gray50",
            max_chars=20,
            key="stick_color",
            on_change=lambda: save_config_to_session("3d"),
        )

    with tab2:
        st.markdown("**Upload Atom Color Scheme (JSON)**")
        upload_key = f"atom_scheme_uploader_{st.session_state.get('_atom_scheme_upload_counter', 0)}"
        uploaded = st.file_uploader("Upload Scheme", type=["json"], key=upload_key, label_visibility="collapsed")
        if uploaded:
            try:
                raw = uploaded.read()
                if len(raw) > MAX_UPLOAD_SIZE:
                    st.error(f"File too large ({len(raw) / 1024:.0f} KB). Maximum: 1 MB.")
                else:
                    data = json.loads(raw)
                    err = _validate_atom_scheme(data)
                    if err:
                        st.error(f"Invalid scheme: {err}")
                    else:
                        name = data.get("name", f"Custom_{datetime.now().strftime('%H%M%S')}")
                        if "custom_atom_schemes" not in st.session_state:
                            st.session_state.custom_atom_schemes = {}
                        st.session_state.custom_atom_schemes[name] = data
                        apply_scheme_to_session(name)
                        st.session_state._atom_scheme_upload_counter = (
                            st.session_state.get("_atom_scheme_upload_counter", 0) + 1
                        )
                        st.success(f"Applied: {name}", icon=":material/check_circle:")
            except Exception as e:
                st.error(f"Invalid JSON: {e}")

    with tab3:
        st.markdown("**Save Current Colors as Scheme**")
        scheme_name = st.text_input(
            "Scheme Name",
            value=f"Scheme_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            max_chars=100,
            key="save_scheme_name",
        )
        scheme_dict = export_scheme_from_session()
        scheme_dict["name"] = scheme_name
        scheme_json = json.dumps(scheme_dict, indent=2)

        st.download_button(
            label="Download Scheme",
            data=scheme_json,
            file_name=f"{scheme_name}.json",
            mime="application/json",
            use_container_width=True,
            key="dl_scheme",
        )


# ============================================================================
# LIGHTING SETTINGS
# ============================================================================


def render_lighting_settings() -> None:
    """Render lighting control settings."""
    with st.expander("Lighting", expanded=False):
        st.markdown(header("lightbulb", "Light Intensity & Quality"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            _s3("Ambient", 0.0, 1.0, 0.25, 0.05, key="ambient")
            _s3("Specular", 0.0, 2.0, 1.0, 0.1, key="specular")

        with col2:
            _s3("Direct Light", 0.0, 1.0, 0.45, 0.05, key="direct")
            _s3("Reflection", 0.0, 1.0, 0.45, 0.05, key="reflect")

        _s3("Shininess", 10, 100, 30, 5, key="shininess")


# ============================================================================
# EFFECTS SETTINGS
# ============================================================================


def render_effects_settings() -> None:
    """Render special effects settings."""
    with st.expander("Effects", expanded=False):
        st.markdown(header("cloud-fog", "Transparency & Special Effects"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            _s3("Stick Transparency", 0.0, 1.0, 0.0, 0.1, key="stick_transparency")
            _s3("Sphere Transparency", 0.0, 1.0, 0.0, 0.1, key="sphere_transparency")

        with col2:
            _s3("Valence Visibility", 0.0, 0.3, 0.0, 0.05, key="valence",
                help="Show valence bonds (0=off)")
            _cb3("Depth Cueing", value=False, key="depth_cue",
                 help="Enable fog effect for depth perception")

        if st.session_state.get("depth_cue", False):
            _s3("Fog Start", 0.0, 10.0, 1.0, 0.5, key="fog_start",
                help="Distance at which fog effect begins")

        st.markdown("**Ambient Occlusion**")
        col1, col2 = st.columns(2)
        with col1:
            _cb3("Ambient Occlusion", value=False, key="ambient_occlusion",
                 help="Enable ambient occlusion for depth shading")
        with col2:
            if st.session_state.get("ambient_occlusion", False):
                _s3("AO Scale", 5.0, 50.0, 20.0, 5.0, key="ambient_occlusion_scale",
                    help="Ambient occlusion radius scale")

        st.markdown("**Ray Tracing Fog**")
        _s3("RT Fog", 0.0, 1.0, 0.0, 0.05, key="ray_trace_fog",
            help="Ray tracing fog density (0=off)")

        st.markdown("**Zoom**")
        _s3("Zoom Buffer", 0.5, 5.0, 2.0, 0.1, key="zoom_buffer")


# ============================================================================
# CONFORMER SETTINGS
# ============================================================================


def render_conformer_settings() -> None:
    """Render conformer generation settings."""
    with st.expander("Conformer Generation", expanded=False):
        st.markdown(header("settings-2", "RDKit ETKDG Conformer Engine"), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            _ni3("Conformers", 1, 200, 50, key="num_conformers",
                 help="Number of 3D conformers to generate")
            _s3("Max Iterations", 100, 5000, 500, 100, key="max_iterations",
                help="Force field optimization iterations")
            _s3("Prune RMSD", 0.05, 2.0, 0.1, 0.05, key="prune_rms_thresh",
                help="RMSD threshold to prune similar conformers")

        with col2:
            _cb3("Random coords", value=False, key="use_random_coords",
                 help="Use random starting coordinates (instead of ETKDG)")
            _cb3("Basic knowledge", value=True, key="use_basic_knowledge",
                 help="Use ETKDG basic knowledge terms")
            _cb3("Chirality", value=True, key="enforce_chirality",
                 help="Enforce stereochemistry during embedding")
            _cb3("Small ring torsions", value=True, key="use_small_ring_torsions",
                 help="Use small ring torsion knowledge")
            _cb3("Macrocycle torsions", value=False, key="use_macrocycle_torsions",
                 help="Use macrocycle torsion knowledge (for large rings)")
            _cb3("Exp. torsion prefs", value=True, key="use_exp_torsion_prefs",
                 help="Use experimental torsion angle preferences")
