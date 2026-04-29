"""
web/ui/components.py
==============================================================
"""

import json
import logging
from datetime import datetime

import streamlit as st
from template.utils import export_color_template, export_current_settings_as_template

from wikimolgen.configs import ConfigLoader

logger = logging.getLogger(__name__)

# ============================================================================
# CONFIG SAVING (On setting changes)
# ============================================================================

def save_config_to_session(dimension: str = "2d") -> None:
    """
    Mark config as changed and save to session.

    Call this AFTER user modifies any setting.

    Example:
        st.session_state.scale = new_value
        save_config_to_session("2d")

    Parameters
    ----------
    dimension : str
        "2d", "3d", or "protein"
    """
    st.session_state.config_changed = True
    st.session_state.last_changed_dimension = dimension

# ============================================================================
# ORIGINAL COMPONENTS (Unchanged)
# ============================================================================

def render_compound_input() -> str:
    """Render compound input field."""
    return st.text_input("Name/CID/SMILES", "", help="").strip()


def render_template_manager() -> None:
    """Render template management UI"""
    with st.expander("📁 Templates", expanded=False):
        st.markdown("**Manage Templates:**")
        tab1, tab2, tab3 = st.tabs(["Predefined", "Upload", "Save"])

        with tab1:
            template_list = ConfigLoader.list_templates()

            # Predefined + custom template combined
            all_color_templates = (
                ["None"] +
                template_list['color_templates'] +
                list(st.session_state.custom_color_templates.keys())
            )

            all_settings_templates = (
                ["None"] +
                template_list['settings_templates'] +
                list(st.session_state.custom_settings_templates.keys())
            )

            st.markdown("**Color Templates**")
            color_template_choice = st.selectbox(
                "Select Color Template:",
                all_color_templates,
                key="color_template_selector",
                label_visibility="collapsed"
            )

            st.markdown("**Settings Templates**")
            settings_template_choice = st.selectbox(
                "Select Settings Template:",
                all_settings_templates,
                key="settings_template_selector",
                label_visibility="collapsed"
            )

            # Remove custom template buttons
            if color_template_choice in st.session_state.custom_color_templates:
                if st.button(f"🗑️ Remove '{color_template_choice}'", key="remove_color"):
                    del st.session_state.custom_color_templates[color_template_choice]
                    st.rerun()

            if settings_template_choice in st.session_state.custom_settings_templates:
                if st.button(f"🗑️ Remove '{settings_template_choice}'", key="remove_settings"):
                    del st.session_state.custom_settings_templates[settings_template_choice]
                    st.rerun()

        with tab2:
            st.markdown("**Upload Color Template (JSON)**")
            uploaded_color = st.file_uploader(
                "Upload Color Template",
                type=['json'],
                key="color_uploader",
                label_visibility="collapsed"
            )

            if uploaded_color:
                try:
                    template_data = json.load(uploaded_color)
                    template_name = template_data.get('name', f'Custom_{datetime.now().strftime("%H%M%S")}')

                    # Store in session
                    st.session_state.custom_color_templates[template_name] = template_data
                    st.session_state.uploaded_color_template = template_data
                    save_config_to_session()  # Mark as changed

                    st.success(f"✓ Loaded & saved: {template_name}")
                    st.info("💡 Now available in 'Template list' tab dropdown")
                except Exception as e:
                    st.error(f"Error: {e}")

            st.markdown("**Upload Settings Template (JSON)**")
            uploaded_settings = st.file_uploader(
                "Upload Settings Template",
                type=['json'],
                key="settings_uploader",
                label_visibility="collapsed"
            )

            if uploaded_settings:
                try:
                    template_data = json.load(uploaded_settings)
                    template_name = template_data.get('name', f'Custom_{datetime.now().strftime("%H%M%S")}')

                    # Store in session
                    st.session_state.custom_settings_templates[template_name] = template_data
                    st.session_state.uploaded_settings_template = template_data

                    # Sync to sliders
                    for key, value in template_data.get("settings", {}).items():
                        if key in st.session_state:
                            st.session_state[key] = value

                    st.session_state.template_applied_once = True
                    save_config_to_session()  # Mark as changed

                    st.success(f"✓ Loaded & saved: {template_name}")
                    st.info("💡 Now available in 'Predefined' tab dropdown")
                except Exception as e:
                    st.error(f"Error: {e}")

            # Reset button
            if (
                st.session_state.get("uploaded_color_template") is not None or
                st.session_state.get("uploaded_settings_template") is not None
            ):
                st.divider()
                if st.button("Reset Loaded Template", use_container_width=True):
                    st.session_state.uploaded_color_template = None
                    st.session_state.uploaded_settings_template = None
                    st.session_state.template_applied_once = False

                    # Reset to defaults
                    defaults = {
                        "auto_orient_2d": True,
                        "scale": 30.0,
                        "margin": 0.8,
                        "bond_length": 50.0,
                        "min_font_size": 32,
                        "padding": 0.07,
                        "use_bw_palette": True,
                        "transparent_background": True,
                        "auto_orient_3d": True,
                        "stick_radius": 0.2,
                        "sphere_scale": 0.3,
                        "stick_ball_ratio": 1.8,
                        "ambient": 0.25,
                        "specular": 1.0,
                        "direct": 0.45,
                        "reflect": 0.45,
                        "shininess": 30,
                        "width": 1800,
                        "height": 1600,
                    }

                    for key, value in defaults.items():
                        st.session_state[key] = value

                    save_config_to_session()
                    st.success("✅ Reset to default style settings")

        with tab3:
            st.markdown("**Save Current Settings as Template**")
            gen_type = st.session_state.get("structure_type", "3D")

            # Custom filename input
            save_filename = st.text_input(
                "Template Filename",
                value=st.session_state.get("save_filename", f"{gen_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"),
                help="Enter desired filename (without .json extension)",
                key="save_filename"
            )

            col1, col2 = st.columns(2)
            template_dict = export_current_settings_as_template(gen_type)
            template_json = json.dumps(template_dict, indent=2)
            color_dict = export_color_template()
            color_json = json.dumps(color_dict, indent=2)

            with col1:
                st.download_button(
                    label="Download Settings Template",
                    data=template_json,
                    file_name=f"{save_filename}.json",
                    mime="application/json",
                    use_container_width=True,
                    key="dl_settings"
                )

            with col2:
                st.download_button(
                    label="Download Color Template",
                    data=color_json,
                    file_name=f"{save_filename}.json",
                    mime="application/json",
                    use_container_width=True,
                    key="dl_colors"
                )


def render_mode_selector() -> str:
    """Render 2D/3D mode selector."""
    structure_type = st.radio(
        "Mode",
        ["3D", "2D", "Protein"],
        horizontal=True,
        label_visibility="collapsed"
    )
    st.session_state.structure_type = structure_type
    return structure_type


def render_2d_settings() -> None:
    """Render 2D-specific settings controls."""
    st.markdown("#### **2D Display**", unsafe_allow_html=True)

    # Auto-orient checkbox
    auto_orient_2d = st.checkbox(
        "Auto orient",
        value=False,
        key="auto_orient_2d",
        help="Automatically find optimal viewing angle"
    )

    ACS_mode = st.checkbox(
        "ACS Mode (overrides custom settings)",
        value=True,
        key="acs_mode",
        help="Applies wikipedia compliant settings"
    )

    # Manual rotation (if not auto-orient)
    if not auto_orient_2d:
        angle_degrees = st.slider(
            "Rotation (°)",
            0, 360, 0, 5,
            key="angle_degrees",
        )
    else:
        angle_degrees = 180

    # Advanced 2D settings
    with st.expander("2D Settings", expanded=False):
        st.markdown("**Sizing & Spacing**")
        col1, col2 = st.columns(2)

        with col1:
            scale = st.slider(
                "Scale", 10.0, 40.0, 30.0, 1.0,
                key="scale",
                help="Pixels per coordinate unit"
            )
            save_config_to_session("2d")

            margin = st.slider(
                "Margin", 0.0, 5.0, 0.8, 0.1,
                key="margin",
                help="Canvas margin"
            )
            save_config_to_session("2d")

        with col2:
            bond_length = st.slider(
                "Bond Length", 10.0, 70.0, 50.0, 5.0,
                key="bond_length",
                help="Fixed bond length in pixels"
            )
            save_config_to_session("2d")

            padding = st.slider(
                "Padding", 0.00, 0.20, 0.07, 0.01,
                key="padding",
                help="Padding around drawing"
            )
            save_config_to_session("2d")

        st.markdown("**Typography & Colors**")
        col1, col2 = st.columns(2)

        with col1:
            min_font_size = st.slider(
                "Font Size", 10, 60, 32, 2,
                key="min_font_size",
            )
            save_config_to_session("2d")

            additional_atom_label_padding = st.slider(
                "Label padding", 0.0, 1.0, 0.1, 0.1,
                key="additional_atom_label_padding",
            )
            save_config_to_session("2d")

        with col2:
            use_bw_palette = st.checkbox(
                "B/W Palette", value=True,
                key="use_bw_palette",
            )
            save_config_to_session("2d")

            transparent_background = st.checkbox(
                "Transparent Background", value=True,
                key="transparent_background",
            )
            save_config_to_session("2d")

        # Amine orientation settings
        with st.expander("Amine Orientation", expanded=False):
            st.markdown("**Automatic amine group rotation for Wikipedia-style drawings**")
            auto_orient_amines = st.checkbox(
                "Auto-orient amines", value=True,
                key="auto_orient_amines",
                help="Automatically rotate amine groups for Wikipedia-style 2D drawings"
            )
            save_config_to_session("2d")

            if auto_orient_amines:
                amine_target_angle = st.slider(
                    "Amine target angle (°)", 0, 360, 0, 5,
                    key="amine_target_angle",
                    help="Target rotation angle for amine groups"
                )
                save_config_to_session("2d")

                phenethylamine_target = st.slider(
                    "Phenethylamine angle (°)", 0, 360, 90, 5,
                    key="phenethylamine_target",
                    help="Target rotation angle for phenethylamine sidechains"
                )
                save_config_to_session("2d")

        # Advanced RDKit drawing options
        with st.expander("Advanced Drawing", expanded=False):
            st.markdown("**RDKit Drawing Options**")
            col1, col2 = st.columns(2)
            with col1:
                bond_line_width = st.slider(
                    "Bond Line Width", 0.5, 5.0, 1.0, 0.5,
                    key="bond_line_width",
                    help="Thickness of bond lines in pixels"
                )
                save_config_to_session("2d")

                scaling_factor = st.slider(
                    "Font Scale", 0.5, 3.0, 1.0, 0.1,
                    key="scaling_factor",
                    help="Scaling factor for fonts and symbols"
                )
                save_config_to_session("2d")

                multiple_bond_offset = st.slider(
                    "Multi-bond offset", 0.0, 0.5, 0.15, 0.05,
                    key="multiple_bond_offset",
                    help="Spacing between lines in double/triple bonds"
                )
                save_config_to_session("2d")

            with col2:
                add_stereo_annotation = st.checkbox(
                    "Stereo labels (R/S)", value=False,
                    key="add_stereo_annotation",
                    help="Show stereocenter annotations (R/S labels)"
                )
                save_config_to_session("2d")

                include_radicals = st.checkbox(
                    "Show radicals", value=False,
                    key="include_radicals",
                    help="Show radical electrons as dots"
                )
                save_config_to_session("2d")

                include_chiral_flag = st.checkbox(
                    "Chiral flag", value=False,
                    key="include_chiral_flag",
                    help="Show chiral flag label on stereocenters"
                )
                save_config_to_session("2d")

            st.markdown("**Atom Labels**")
            col1, col2 = st.columns(2)
            with col1:
                no_atom_labels = st.checkbox(
                    "Hide all atom labels", value=False,
                    key="no_atom_labels",
                    help="Hide all atom symbols (clean structure only)"
                )
                save_config_to_session("2d")

                explicit_methyl = st.checkbox(
                    "Explicit methyl (CH3)", value=False,
                    key="explicit_methyl",
                    help="Show CH3 instead of Me abbreviation"
                )
                save_config_to_session("2d")

            with col2:
                include_atom_tags = st.checkbox(
                    "Atom map numbers", value=False,
                    key="include_atom_tags",
                    help="Include atom map/tag numbers (reaction mapping)"
                )
                save_config_to_session("2d")

            st.markdown("**Style**")
            col1, col2 = st.columns(2)
            with col1:
                comic_mode = st.checkbox(
                    "Comic style", value=False,
                    key="comic_mode",
                    help="Hand-drawn comic-style rendering"
                )
                save_config_to_session("2d")

            with col2:
                fixed_font_size = st.slider(
                    "Fixed font size (-1 = auto)", -1, 60, -1, 1,
                    key="fixed_font_size",
                    help="Lock font size to fixed value (-1 for automatic)"
                )
                save_config_to_session("2d")


def render_3d_settings() -> None:
    """Render 3D-specific settings controls."""
    # Auto-orient checkbox
    auto_orient_3d = st.checkbox(
        "Auto-Orient",
        value=False,
        key="auto_orient_3d",
        help="Automatically optimize 3D orientation"
    )

    # Manual rotation sliders (if not auto-orient)
    if not auto_orient_3d:
        x_rot = st.slider(
            "X Rotation", 0.0, 360.0, 0.0, 5.0,
            key="x_rot_slider",
        )
        save_config_to_session("3d")

        y_rot = st.slider(
            "Y Rotation", 0.0, 360.0, 0.0, 5.0,
            key="y_rot_slider",
        )
        save_config_to_session("3d")

        z_rot = st.slider(
            "Z Rotation", 0.0, 360.0, 0.0, 5.0,
            key="z_rot_slider",
        )
        save_config_to_session("3d")
    else:
        x_rot, y_rot, z_rot = 0.0, 0.0, 0.0


def render_canvas_settings() -> None:
    """Render canvas/dimension settings."""
    with st.expander("📐 Canvas", expanded=False):
        st.markdown("**Image Dimensions**")
        col1, col2 = st.columns(2)

        with col1:
            width = st.number_input("Width (pixels)", 800, 4000, 1800, 100, key="width")
            save_config_to_session("3d")

            height = st.number_input("Height (pixels)", 600, 3000, 1600, 100, key="height")
            save_config_to_session("3d")

        with col2:
            crop_margin = st.slider("Crop Margin", 5, 50, 10, 5, key="crop_margin")
            auto_crop = st.checkbox("Auto Crop", value=True, key="auto_crop")
            save_config_to_session("3d")


def render_rendering_settings() -> None:
    """Render rendering quality settings."""
    with st.expander("🎨 Rendering", expanded=True):
        st.markdown("**Molecular Representation**")
        col1, col2, col3 = st.columns(3)

        with col1:
            stick_radius = st.slider(
                "Stick Radius", 0.1, 0.5, 0.2, 0.05,
                key="stick_radius",
                help="Thickness of bond sticks"
            )
            save_config_to_session("3d")

        with col2:
            sphere_scale = st.slider(
                "Atom Size", 0.15, 0.5, 0.3, 0.05,
                key="sphere_scale",
                help="Sphere scale factor for atoms"
            )
            save_config_to_session("3d")

        with col3:
            stick_ball_ratio = st.slider(
                "Ball Ratio", 1.2, 3.0, 1.8, 0.1,
                key="stick_ball_ratio",
                help="Stick-to-ball proportion"
            )
            save_config_to_session("3d")

        st.markdown("**Quality Settings**")
        col1, col2 = st.columns(2)

        with col1:
            ray_trace_mode = st.selectbox(
                "Ray Tracing", [0, 1, 2, 3],
                index=0,
                key="ray_trace_mode",
                help="0=Off, 1=Ray trace, 2=Realtime, 3=Realtime strip"
            )
            save_config_to_session("3d")

            ray_shadows = st.checkbox(
                "Shadows", value=False,
                key="ray_shadows",
                help="Enable shadows (slower, requires ray tracing)"
            )
            save_config_to_session("3d")

        with col2:
            antialias = st.selectbox(
                "Antialiasing", [0, 1, 2, 3, 4], 2,
                key="antialias",
                help="0=Off, 1=On, 2-4=Multisample levels"
            )
            save_config_to_session("3d")

        st.markdown("**Render Quality**")
        col1, col2 = st.columns(2)
        with col1:
            stick_quality = st.slider(
                "Stick Quality", 16, 128, 64, 8,
                key="stick_quality",
                help="Stick rendering smoothness (higher = smoother)"
            )
            save_config_to_session("3d")
        with col2:
            sphere_quality = st.slider(
                "Sphere Quality", 2, 12, 6, 1,
                key="sphere_quality",
                help="Sphere rendering quality (higher = smoother)"
            )
            save_config_to_session("3d")

        st.markdown("**Representation**")
        representation = st.selectbox(
            "Style",
            ["sticks+spheres", "sticks", "spheres", "lines"],
            key="representation",
            help="Molecular representation style"
        )
        save_config_to_session("3d")

        st.markdown("**Colors**")
        col1, col2 = st.columns(2)
        with col1:
            bg_color = st.selectbox(
                "Background", ["white", "black", "gray", "transparent"],
                key="bg_color",
                help="Canvas background color"
            )
            save_config_to_session("3d")
        with col2:
            stick_color = st.text_input(
                "Stick Color", value="gray40",
                key="stick_color",
                help="PyMOL color name for bonds (e.g. gray40, black, custom)"
            )
            save_config_to_session("3d")

        st.markdown("**Lighting Mode**")
        col1, col2 = st.columns(2)
        with col1:
            two_sided_lighting = st.checkbox(
                "Two-sided lighting", value=True,
                key="two_sided_lighting",
                help="Enable two-sided polygon lighting"
            )
            save_config_to_session("3d")
        with col2:
            transparency_mode = st.selectbox(
                "Transparency Mode", [0, 1, 2],
                index=1,
                key="transparency_mode",
                help="0=Off, 1=Additive, 2=Weighted average"
            )
            save_config_to_session("3d")

        st.markdown("**Miscellaneous**")
        col1, col2 = st.columns(2)
        with col1:
            stick_ball = st.checkbox(
                "Stick-ball style", value=True,
                key="stick_ball",
                help="Use ball-shaped stick joins"
            )
            save_config_to_session("3d")
        with col2:
            opaque_background = st.checkbox(
                "Opaque background", value=False,
                key="opaque_background",
                help="Use solid background (instead of transparent)"
            )
            save_config_to_session("3d")


def render_lighting_settings() -> None:
    """Render lighting control settings."""
    with st.expander("💡 Lighting", expanded=True):
        st.markdown("**Light Intensity & Quality**")
        col1, col2 = st.columns(2)

        with col1:
            ambient = st.slider(
                "Ambient", 0.0, 1.0, 0.25, 0.05,
                key="ambient",
                help="Ambient light intensity (global brightness)"
            )
            save_config_to_session("3d")

            specular = st.slider(
                "Specular", 0.0, 2.0, 1.0, 0.1,
                key="specular",
                help="Specular reflection intensity (shininess)"
            )
            save_config_to_session("3d")

        with col2:
            direct = st.slider(
                "Direct Light", 0.0, 1.0, 0.45, 0.05,
                key="direct",
                help="Direct light source intensity"
            )
            save_config_to_session("3d")

            reflect = st.slider(
                "Reflection", 0.0, 1.0, 0.45, 0.05,
                key="reflect",
                help="Environmental reflection intensity"
            )
            save_config_to_session("3d")

        shininess = st.slider(
            "Shininess", 10, 100, 30, 5,
            key="shininess",
            help="Surface shininess level (higher = more glossy)"
        )
        save_config_to_session("3d")


def render_effects_settings() -> None:
    """Render special effects settings."""
    with st.expander("🌫️ Effects", expanded=False):
        st.markdown("**Transparency & Special Effects**")
        col1, col2 = st.columns(2)

        with col1:
            stick_transparency = st.slider(
                "Stick Transparency", 0.0, 1.0, 0.0, 0.1,
                key="stick_transparency",
                help="Bond transparency level"
            )
            save_config_to_session("3d")

            sphere_transparency = st.slider(
                "Sphere Transparency", 0.0, 1.0, 0.0, 0.1,
                key="sphere_transparency",
                help="Atom transparency level"
            )
            save_config_to_session("3d")

        with col2:
            valence = st.slider(
                "Valence Visibility", 0.0, 0.3, 0.0, 0.05,
                key="valence",
                help="Show valence bonds (0=off)"
            )
            save_config_to_session("3d")

            depth_cue = st.checkbox(
                "Depth Cueing", value=False,
                key="depth_cue",
                help="Enable fog effect for depth perception"
            )
            save_config_to_session("3d")

        if st.session_state.get("depth_cue", False):
            fog_start = st.slider(
                "Fog Start", 0.0, 10.0, 1.0, 0.5,
                key="fog_start",
                help="Distance at which fog effect begins"
            )
            save_config_to_session("3d")

        st.markdown("**Ambient Occlusion**")
        col1, col2 = st.columns(2)
        with col1:
            ambient_occlusion = st.checkbox(
                "Ambient Occlusion", value=False,
                key="ambient_occlusion",
                help="Enable ambient occlusion for depth shading"
            )
            save_config_to_session("3d")
        with col2:
            if st.session_state.get("ambient_occlusion", False):
                ambient_occlusion_scale = st.slider(
                    "AO Scale", 5.0, 50.0, 20.0, 5.0,
                    key="ambient_occlusion_scale",
                    help="Ambient occlusion radius scale"
                )
                save_config_to_session("3d")

        st.markdown("**Ray Tracing Fog**")
        ray_trace_fog = st.slider(
            "RT Fog", 0.0, 1.0, 0.0, 0.05,
            key="ray_trace_fog",
            help="Ray tracing fog density (0=off)"
        )
        save_config_to_session("3d")

        st.markdown("**Zoom**")
        zoom_buffer = st.slider(
            "Zoom Buffer", 0.5, 5.0, 2.0, 0.1,
            key="zoom_buffer",
            help="Padding around molecule (lower = zoomed in)"
        )
        save_config_to_session("3d")


def render_conformer_settings() -> None:
    """Render conformer generation settings."""
    with st.expander("⚙️ Conformer Generation", expanded=False):
        st.markdown("**RDKit ETKDG Conformer Engine**")

        col1, col2 = st.columns(2)
        with col1:
            num_conformers = st.number_input(
                "Conformers", 1, 100, 1,
                key="num_conformers",
                help="Number of 3D conformers to generate"
            )
            save_config_to_session("3d")

            max_iterations = st.slider(
                "Max Iterations", 50, 1000, 200, 50,
                key="max_iterations",
                help="Force field optimization iterations"
            )
            save_config_to_session("3d")

            prune_rms_thresh = st.slider(
                "Prune RMSD", 0.1, 2.0, 0.5, 0.1,
                key="prune_rms_thresh",
                help="RMSD threshold to prune similar conformers"
            )
            save_config_to_session("3d")

        with col2:
            use_random_coords = st.checkbox(
                "Random coords", value=False,
                key="use_random_coords",
                help="Use random starting coordinates (instead of ETKDG)"
            )
            save_config_to_session("3d")

            use_basic_knowledge = st.checkbox(
                "Basic knowledge", value=True,
                key="use_basic_knowledge",
                help="Use ETKDG basic knowledge terms"
            )
            save_config_to_session("3d")

            enforce_chirality = st.checkbox(
                "Chirality", value=True,
                key="enforce_chirality",
                help="Enforce stereochemistry during embedding"
            )
            save_config_to_session("3d")

            use_small_ring_torsions = st.checkbox(
                "Small ring torsions", value=False,
                key="use_small_ring_torsions",
                help="Use small ring torsion knowledge"
            )
            save_config_to_session("3d")

            use_macrocycle_torsions = st.checkbox(
                "Macrocycle torsions", value=False,
                key="use_macrocycle_torsions",
                help="Use macrocycle torsion knowledge (for large rings)"
            )
            save_config_to_session("3d")

            use_exp_torsion_prefs = st.checkbox(
                "Exp. torsion prefs", value=False,
                key="use_exp_torsion_prefs",
                help="Use experimental torsion angle preferences"
            )
            save_config_to_session("3d")


def render_auto_generate_checkbox() -> bool:
    """Render auto-generate checkbox."""
    return st.checkbox(
        "Auto-update",
        value=True,
    )


def render_generate_button(auto_generate: bool) -> bool:
    """Render manual generate button."""
    generate_btn_enabled = not auto_generate
    clicked = st.button(
        "Generate Now",
        type="primary",
        use_container_width=True,
        disabled=not generate_btn_enabled
    )

    if clicked:
        st.session_state.manual_generate = True

    return clicked


def render_theme_toggle() -> None:
    st.markdown("---")
    current = st.session_state.get("wiki_theme", "Dark")
    choice = st.selectbox(
        "Theme",
        ["Dark", "Light"],
        index=0 if current == "Dark" else 1,
        key="wiki_theme",
        help="Switch between dark and light appearance",
    )



