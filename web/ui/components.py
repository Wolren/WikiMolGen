"""
web/ui/components.py
==============================================================
"""

import json
import logging
from datetime import datetime

import streamlit as st

from template.utils import (
    export_current_settings_as_template,
    export_color_template
)
from wikimolgen.predefined_templates import list_predefined_templates

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
            template_list = list_predefined_templates()

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
            ray_trace = st.checkbox(
                "Ray Tracing", value=False,
                key="ray_trace",
                help="Enable ray tracing for photorealistic rendering"
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