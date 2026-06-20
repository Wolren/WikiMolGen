"""
web/ui/components.py
==============================================================
"""

import json
import logging
from datetime import datetime

import streamlit as st
from rendering.atom_colors import apply_scheme_to_session, get_scheme_choices
from template.utils import export_current_as_preset
from ui.icons import header

from wikimolgen.configs import Config3D, ConfigLoader


def _apply_settings_to_session(settings: dict) -> None:
    """Apply a settings dict to session state, handling prefixes and type conversions.

    Strips ``render_`` / ``conformer_`` prefixes and converts int→bool
    when the session stores a bool.
    """
    for key, value in settings.items():
        clean_key = key
        if clean_key.startswith("render_"):
            clean_key = clean_key[7:]
        elif clean_key.startswith("conformer_"):
            clean_key = clean_key[10:]

        if clean_key not in st.session_state:
            continue
        current = st.session_state[clean_key]
        if isinstance(current, bool) and isinstance(value, int):
            value = bool(value)
        st.session_state[clean_key] = value


# ============================================================================
# CALLBACKS (Rotation slider / number input sync)
# ============================================================================
def _sync_slider_to_config(key: str) -> None:
    st.session_state[key] = st.session_state[f"{key}_slider"]
    st.session_state.config_changed = True


def _sync_input_to_slider(key: str) -> None:
    st.session_state[f"{key}_slider"] = st.session_state[key]


def _sync_number_input(key: str) -> None:
    """Sync number_input (key_input) to config key and slider."""
    val = st.session_state[f"{key}_input"]
    st.session_state[key] = val
    st.session_state[f"{key}_slider"] = val
    save_config_to_session("3d")


# ============================================================================
# WIDGET FACTORY (Auto-save wrapper helpers)
# ============================================================================
def _s(dim: str, *a, **kw):
    v = st.slider(*a, **kw)
    save_config_to_session(dim)
    return v


def _cb(dim: str, *a, **kw):
    v = st.checkbox(*a, **kw)
    save_config_to_session(dim)
    return v


def _ni(dim: str, *a, **kw):
    v = st.number_input(*a, **kw)
    save_config_to_session(dim)
    return v


def _sb(dim: str, *a, **kw):
    v = st.selectbox(*a, **kw)
    save_config_to_session(dim)
    return v


# Shorter aliases for common dimensions
_s2 = lambda *a, **kw: _s("2d", *a, **kw)
_s3 = lambda *a, **kw: _s("3d", *a, **kw)
_cb2 = lambda *a, **kw: _cb("2d", *a, **kw)
_cb3 = lambda *a, **kw: _cb("3d", *a, **kw)
_ni3 = lambda *a, **kw: _ni("3d", *a, **kw)
_sb3 = lambda *a, **kw: _sb("3d", *a, **kw)


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
    return st.text_input(
        "Name/CID/SMILES",
        "",
        placeholder="e.g. aspirin, 2244, CC(=O)Oc1ccccc1C(=O)O",
    ).strip()


def render_preset_manager() -> None:
    """Render preset management UI (full config snapshots per mode)."""
    st.markdown(header("folder", "Presets"), unsafe_allow_html=True)
    with st.expander("Presets", expanded=False):
        tab1, tab2, tab3 = st.tabs(["Predefined", "Upload", "Save"])

        with tab1:
            template_list = ConfigLoader.list_templates()

            all_presets = (
                ["None"]
                + template_list["settings_templates"]
                + list(st.session_state.get("custom_presets", {}).keys())
            )

            st.markdown("**Presets**")
            # Deferred preset selection from upload (set before widget renders)
            if "_pending_preset_name" in st.session_state:
                st.session_state.preset_selector = st.session_state.pop("_pending_preset_name")

            prev_selection = st.session_state.get("_prev_preset_sel", "None")
            preset_choice = st.selectbox(
                "Select Preset:",
                all_presets,
                key="preset_selector",
                label_visibility="collapsed",
            )
            if preset_choice != prev_selection:
                if preset_choice != "None":
                    st.toast(f"Preset: {preset_choice}", icon=":material/tune:")
                    _apply_preset_now(preset_choice)
                st.session_state._prev_preset_sel = preset_choice

            if preset_choice in st.session_state.get("custom_presets", {}):
                if st.button(
                    f"Remove '{preset_choice}'",
                    key="remove_preset",
                    icon=":material/delete:",
                ):
                    del st.session_state.custom_presets[preset_choice]
                    st.rerun()

        with tab2:
            st.markdown("**Upload Preset (JSON)**")
            upload_key = f"preset_uploader_{st.session_state.get('_upload_counter', 0)}"
            uploaded = st.file_uploader(
                "Upload Preset",
                type=["json"],
                key=upload_key,
                label_visibility="collapsed",
            )

            if uploaded:
                try:
                    data = json.load(uploaded)
                    name = data.get("name", f"Custom_{datetime.now().strftime('%H%M%S')}")

                    if "custom_presets" not in st.session_state:
                        st.session_state.custom_presets = {}
                    st.session_state.custom_presets[name] = data

                    _apply_settings_to_session(data.get("settings", data))

                    st.session_state._pending_preset_name = name
                    st.session_state._upload_counter = (
                        st.session_state.get("_upload_counter", 0) + 1
                    )
                    save_config_to_session()
                    st.toast(f"Loaded: {name}", icon=":material/tune:")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error: {e}")

        with tab3:
            st.markdown("**Save Current Settings as Preset**")
            gen_type = st.session_state.get("structure_type", "3D")

            save_filename = st.text_input(
                "Preset Filename",
                value=st.session_state.get(
                    "save_filename", f"{gen_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                ),
                help="Enter desired filename (without .json extension)",
                key="save_filename",
            )

            preset_name = st.session_state.get("save_filename", f"Custom_{gen_type}")
            preset_dict = export_current_as_preset(gen_type, name=preset_name)
            preset_json = json.dumps(preset_dict, indent=2)

            st.download_button(
                label="Download Preset",
                data=preset_json,
                file_name=f"{save_filename}.json",
                mime="application/json",
                use_container_width=True,
                key="dl_preset",
            )


def _apply_preset_now(choice: str) -> None:
    """Apply a preset (built-in or custom) to session state immediately."""
    if choice in st.session_state.get("custom_presets", {}):
        data = st.session_state.custom_presets[choice]
        settings = data.get("settings", data)
    else:
        try:
            config = ConfigLoader.load_template(choice)
            if isinstance(config, Config3D):
                settings = {}
                settings.update(config.render.__dict__)
                settings.update(config.conformer.__dict__)
            else:
                settings = config.to_dict() if hasattr(config, "to_dict") else {}
        except Exception:
            return
    _apply_settings_to_session(settings)


def _on_mode_change() -> None:
    """Snapshot old mode's settings and restore new mode's settings on switch."""
    new_mode = st.session_state.mode_selector
    old_mode = st.session_state.get("_last_active_mode", new_mode)
    if new_mode == old_mode:
        return

    from session.state import get_mode_keys

    # Snapshot old mode
    old_keys = get_mode_keys(old_mode)
    st.session_state[f"_snap_{old_mode}"] = {
        k: v for k, v in st.session_state.items() if k in old_keys
    }

    # Restore new mode
    new_keys = get_mode_keys(new_mode)
    snap = st.session_state.get(f"_snap_{new_mode}", {})
    for k, v in snap.items():
        st.session_state[k] = v

    st.session_state._last_active_mode = new_mode
    st.query_params["mode"] = new_mode


def render_mode_selector() -> str:
    """Render 2D/3D/Protein mode selector as styled segmented control."""
    st.markdown(header("atom", "Mode"), unsafe_allow_html=True)
    structure_type = st.segmented_control(
        "Mode",
        options=["3D", "2D", "Protein"],
        default="3D",
        label_visibility="collapsed",
        key="mode_selector",
        on_change=_on_mode_change,
    )
    if "_last_active_mode" not in st.session_state:
        st.session_state._last_active_mode = structure_type
    st.session_state.structure_type = structure_type
    return structure_type


def render_rotation_settings(dim: str) -> None:
    """Render unified rotation section inside an auto-expanded expander."""
    with st.expander("Rotation", expanded=True):
        if dim == "2d":
            st.checkbox("Auto orient", value=False, key="auto_orient_2d")
            if not st.session_state.get("auto_orient_2d", False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.slider(
                        "Rotation (°)",
                        0.0,
                        360.0,
                        st.session_state.get("angle_degrees", 0.0),
                        5.0,
                        key="angle_degrees_slider",
                        on_change=_sync_slider_to_config,
                        args=("angle_degrees",),
                    )
                with col2:
                    st.number_input(
                        "Set",
                        0.0,
                        360.0,
                        st.session_state.get("angle_degrees", 0.0),
                        5.0,
                        key="angle_degrees",
                        on_change=_sync_input_to_slider,
                        args=("angle_degrees",),
                    )
        else:
            st.checkbox(
                "Auto-Orient",
                key="auto_orient_3d",
                help="Automatically orient the molecule (disables manual rotation)",
            )
            if not st.session_state.get("auto_orient_3d", False):
                for axis, key in [("X", "x_rotation"), ("Y", "y_rotation"), ("Z", "z_rotation")]:
                    col1, col2 = st.columns([3, 1], gap="small")
                    with col1:
                        st.slider(
                            f"{axis}",
                            -180.0,
                            180.0,
                            st.session_state.get(key, 0.0),
                            5.0,
                            key=f"{key}_slider",
                            on_change=_sync_slider_to_config,
                            args=(key,),
                        )
                    with col2:
                        st.number_input(
                            "Set",
                            -180.0,
                            180.0,
                            st.session_state.get(key, 0.0),
                            5.0,
                            key=f"{key}_input",
                            on_change=lambda k=key: _sync_number_input(k),
                        )


def render_2d_settings() -> None:
    """Render 2D-specific settings controls."""

    # Advanced 2D settings
    with st.expander("2D Settings", expanded=False):
        st.markdown("**Sizing & Spacing**")
        col1, col2 = st.columns(2)

        with col1:
            scale = _s2(
                "Scale", 10.0, 40.0, 30.0, 1.0, key="scale", help="Pixels per coordinate unit"
            )
            margin = _s2("Margin", 0.0, 5.0, 0.8, 0.1, key="margin")

        with col2:
            bond_length = _s2(
                "Bond Length",
                10.0,
                70.0,
                50.0,
                5.0,
                key="bond_length",
                help="Fixed bond length in pixels",
            )
            padding = _s2(
                "Padding", 0.00, 0.20, 0.07, 0.01, key="padding", help="Padding around drawing"
            )

        st.markdown("**Typography & Colors**")
        col1, col2 = st.columns(2)

        with col1:
            min_font_size = _s2("Font Size", 10, 60, 32, 2, key="min_font_size")
            additional_atom_label_padding = _s2(
                "Label padding", 0.0, 1.0, 0.1, 0.1, key="additional_atom_label_padding"
            )

        with col2:
            use_bw_palette = _cb2("B/W Palette", value=True, key="use_bw_palette")
            transparent_background = _cb2(
                "Transparent Background", value=True, key="transparent_background"
            )

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
                amine_target_angle = _s2(
                    "Amine target angle (°)",
                    0,
                    360,
                    0,
                    5,
                    key="amine_target_angle",
                    help="Target rotation angle for amine groups",
                )
                phenethylamine_target = _s2(
                    "Phenethylamine angle (°)",
                    0,
                    360,
                    90,
                    5,
                    key="phenethylamine_target",
                    help="Target rotation angle for phenethylamine sidechains",
                )

        # Advanced RDKit drawing options
        with st.expander("Advanced Drawing", expanded=False):
            st.markdown("**RDKit Drawing Options**")
            col1, col2 = st.columns(2)
            with col1:
                bond_line_width = _s2("Bond Line Width", 0.5, 5.0, 1.0, 0.5, key="bond_line_width")
                scaling_factor = _s2("Font Scale", 0.5, 3.0, 1.0, 0.1, key="scaling_factor")
                multiple_bond_offset = _s2(
                    "Multi-bond offset", 0.0, 0.5, 0.15, 0.05, key="multiple_bond_offset"
                )

            with col2:
                add_stereo_annotation = _cb2(
                    "Stereo labels (R/S)", value=False, key="add_stereo_annotation"
                )
                include_radicals = _cb2("Show radicals", value=False, key="include_radicals")
                include_chiral_flag = _cb2("Chiral flag", value=False, key="include_chiral_flag")

            st.markdown("**Atom Labels**")
            col1, col2 = st.columns(2)
            with col1:
                no_atom_labels = _cb2("Hide all atom labels", value=False, key="no_atom_labels")
                explicit_methyl = _cb2("Explicit methyl (CH3)", value=False, key="explicit_methyl")

            with col2:
                include_atom_tags = _cb2("Atom map numbers", value=False, key="include_atom_tags")

            st.markdown("**Style**")
            col1, col2 = st.columns(2)
            with col1:
                comic_mode = _cb2("Comic style", value=False, key="comic_mode")

            with col2:
                fixed_font_size = _s2(
                    "Fixed font size (-1 = auto)", -1, 60, -1, 1, key="fixed_font_size"
                )

        with st.expander("Legend & Highlights", expanded=False):
            st.markdown("**Compound Legend**")
            legend_text = st.text_input(
                "Legend text (shown below structure)",
                value=st.session_state.get("legend", ""),
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


def render_canvas_settings() -> None:
    """Render canvas/dimension settings."""
    with st.expander("Canvas", expanded=False):
        st.markdown(header("ruler", "Image Dimensions"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            width = _ni3("Width (pixels)", 800, 4000, 1800, 100, key="width")
            height = _ni3("Height (pixels)", 600, 3000, 1600, 100, key="height")

        with col2:
            crop_margin = _s3("Crop Margin", 5, 50, 10, 5, key="crop_margin")
            auto_crop = _cb3("Auto Crop", value=True, key="auto_crop")


def render_rendering_settings() -> None:
    """Render rendering quality settings."""
    with st.expander("Rendering", expanded=False):
        st.markdown(header("atom", "Molecular Representation"), unsafe_allow_html=True)
        col1, col2, col3 = st.columns(3)

        with col1:
            stick_radius = _s3("Stick Radius", 0.1, 0.5, 0.2, 0.05, key="stick_radius")

        with col2:
            sphere_scale = _s3("Atom Size", 0.15, 0.5, 0.3, 0.05, key="sphere_scale")

        with col3:
            stick_ball_ratio = _s3("Ball Ratio", 1.2, 3.0, 1.8, 0.1, key="stick_ball_ratio")

        st.markdown(header("settings-2", "Quality Settings"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            ray_trace_mode = _sb3(
                "Ray Tracing",
                [0, 1, 2, 3],
                index=0,
                key="ray_trace_mode",
                help="0=Off, 1=Ray trace, 2=Realtime, 3=Realtime strip",
            )
            ray_shadows = _cb3(
                "Shadows",
                value=False,
                key="ray_shadows",
                help="Enable shadows (slower, requires ray tracing)",
            )

        with col2:
            antialias = _sb3(
                "Antialiasing",
                [0, 1, 2, 3, 4],
                4,
                key="antialias",
                help="0=Off, 1=On, 2-4=Multisample levels",
            )

        st.markdown("**Render Quality**")
        col1, col2 = st.columns(2)
        with col1:
            stick_quality = _s3("Stick Quality", 16, 128, 64, 8, key="stick_quality")
        with col2:
            sphere_quality = _s3("Sphere Quality", 2, 12, 6, 1, key="sphere_quality")

        st.markdown("**Representation**")
        representation = _sb3(
            "Style", ["sticks+spheres", "sticks", "spheres", "lines"], key="representation"
        )

        st.markdown(header("palette", "Colors"), unsafe_allow_html=True)

        bg_color = _sb3(
            "Background",
            ["white", "black", "gray", "transparent"],
            key="bg_color",
            help="Set the background color behind the molecule render",
        )

        atom_choices = get_scheme_choices()
        current_atom = st.session_state.get("atom_color_choice", "None")
        atom_idx = atom_choices.index(current_atom) if current_atom in atom_choices else 0
        new_atom = st.selectbox(
            "Atom Color Scheme",
            atom_choices,
            index=atom_idx,
            key="atom_color_sel",
        )
        if new_atom != current_atom:
            apply_scheme_to_session(new_atom)

        with st.expander("Upload Custom Scheme", expanded=False):
            uploaded = st.file_uploader(
                "Atom Color Scheme JSON",
                type=["json"],
                key="atom_scheme_uploader",
                label_visibility="collapsed",
            )
            if uploaded:
                try:
                    data = json.load(uploaded)
                    name = data.get("name", f"Custom_{datetime.now().strftime('%H%M%S')}")
                    if "custom_atom_schemes" not in st.session_state:
                        st.session_state.custom_atom_schemes = {}
                    st.session_state.custom_atom_schemes[name] = data
                    apply_scheme_to_session(name)
                    st.success(f"Applied custom scheme: {name}", icon=":material/check_circle:")
                except Exception as e:
                    st.error(f"Error: {e}")

        st.markdown("**Manual Overrides**")
        stick_color = st.text_input("Stick Color", value="gray50", key="stick_color")
        save_config_to_session("3d")

        st.markdown("**Lighting Mode**")
        col1, col2 = st.columns(2)
        with col1:
            two_sided_lighting = _cb3("Two-sided lighting", value=True, key="two_sided_lighting")
        with col2:
            transparency_mode = _sb3(
                "Transparency Mode",
                [0, 1, 2],
                index=1,
                key="transparency_mode",
                help="0=Off, 1=Additive, 2=Weighted average",
            )

        st.markdown("**Miscellaneous**")
        col1, col2 = st.columns(2)
        with col1:
            stick_ball = _cb3("Stick-ball style", value=True, key="stick_ball")
        with col2:
            opaque_background = _cb3("Opaque background", value=False, key="opaque_background")


def render_lighting_settings() -> None:
    """Render lighting control settings."""
    with st.expander("Lighting", expanded=False):
        st.markdown(header("lightbulb", "Light Intensity & Quality"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            ambient = _s3("Ambient", 0.0, 1.0, 0.25, 0.05, key="ambient")
            specular = _s3("Specular", 0.0, 2.0, 1.0, 0.1, key="specular")

        with col2:
            direct = _s3("Direct Light", 0.0, 1.0, 0.45, 0.05, key="direct")
            reflect = _s3("Reflection", 0.0, 1.0, 0.45, 0.05, key="reflect")

        shininess = _s3("Shininess", 10, 100, 30, 5, key="shininess")


def render_effects_settings() -> None:
    """Render special effects settings."""
    with st.expander("Effects", expanded=False):
        st.markdown(header("cloud-fog", "Transparency & Special Effects"), unsafe_allow_html=True)
        col1, col2 = st.columns(2)

        with col1:
            stick_transparency = _s3(
                "Stick Transparency", 0.0, 1.0, 0.0, 0.1, key="stick_transparency"
            )
            sphere_transparency = _s3(
                "Sphere Transparency", 0.0, 1.0, 0.0, 0.1, key="sphere_transparency"
            )

        with col2:
            valence = _s3(
                "Valence Visibility",
                0.0,
                0.3,
                0.0,
                0.05,
                key="valence",
                help="Show valence bonds (0=off)",
            )
            depth_cue = _cb3(
                "Depth Cueing",
                value=False,
                key="depth_cue",
                help="Enable fog effect for depth perception",
            )

        if st.session_state.get("depth_cue", False):
            fog_start = _s3(
                "Fog Start",
                0.0,
                10.0,
                1.0,
                0.5,
                key="fog_start",
                help="Distance at which fog effect begins",
            )

        st.markdown("**Ambient Occlusion**")
        col1, col2 = st.columns(2)
        with col1:
            ambient_occlusion = _cb3(
                "Ambient Occlusion",
                value=False,
                key="ambient_occlusion",
                help="Enable ambient occlusion for depth shading",
            )
        with col2:
            if st.session_state.get("ambient_occlusion", False):
                ambient_occlusion_scale = _s3(
                    "AO Scale",
                    5.0,
                    50.0,
                    20.0,
                    5.0,
                    key="ambient_occlusion_scale",
                    help="Ambient occlusion radius scale",
                )

        st.markdown("**Ray Tracing Fog**")
        ray_trace_fog = _s3(
            "RT Fog",
            0.0,
            1.0,
            0.0,
            0.05,
            key="ray_trace_fog",
            help="Ray tracing fog density (0=off)",
        )

        st.markdown("**Zoom**")
        zoom_buffer = _s3("Zoom Buffer", 0.5, 5.0, 2.0, 0.1, key="zoom_buffer")


def render_conformer_settings() -> None:
    """Render conformer generation settings."""
    with st.expander("Conformer Generation", expanded=False):
        st.markdown(header("settings-2", "RDKit ETKDG Conformer Engine"), unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        with col1:
            num_conformers = _ni3(
                "Conformers",
                1,
                200,
                50,
                key="num_conformers",
                help="Number of 3D conformers to generate",
            )
            max_iterations = _s3(
                "Max Iterations",
                100,
                5000,
                500,
                100,
                key="max_iterations",
                help="Force field optimization iterations",
            )
            prune_rms_thresh = _s3(
                "Prune RMSD",
                0.05,
                2.0,
                0.1,
                0.05,
                key="prune_rms_thresh",
                help="RMSD threshold to prune similar conformers",
            )

        with col2:
            use_random_coords = _cb3(
                "Random coords",
                value=False,
                key="use_random_coords",
                help="Use random starting coordinates (instead of ETKDG)",
            )
            use_basic_knowledge = _cb3(
                "Basic knowledge",
                value=True,
                key="use_basic_knowledge",
                help="Use ETKDG basic knowledge terms",
            )
            enforce_chirality = _cb3(
                "Chirality",
                value=True,
                key="enforce_chirality",
                help="Enforce stereochemistry during embedding",
            )
            use_small_ring_torsions = _cb3(
                "Small ring torsions",
                value=True,
                key="use_small_ring_torsions",
                help="Use small ring torsion knowledge",
            )
            use_macrocycle_torsions = _cb3(
                "Macrocycle torsions",
                value=False,
                key="use_macrocycle_torsions",
                help="Use macrocycle torsion knowledge (for large rings)",
            )
            use_exp_torsion_prefs = _cb3(
                "Exp. torsion prefs",
                value=True,
                key="use_exp_torsion_prefs",
                help="Use experimental torsion angle preferences",
            )


def render_generate_button(auto_generate: bool) -> bool:
    """Render manual generate button."""
    generate_btn_enabled = not auto_generate
    clicked = st.button(
        "Generate Now", type="primary", use_container_width=True, disabled=not generate_btn_enabled
    )

    if clicked:
        st.session_state.manual_generate = True

    return clicked


def render_3d_preview(compound: str = "") -> None:
    """Interactive 3Dmol.js preview — drag to orbit, scroll to zoom."""
    sdf_content = st.session_state.get("sdf_content")
    if not sdf_content:
        if not compound:
            compound = st.session_state.get("last_compound", "")
        if compound:
            _cache_3d_preview_sdf(compound)
            sdf_content = st.session_state.get("sdf_content")

    if not sdf_content:
        st.caption("Enter a compound and click Generate to preview")
        return

    bg_color = st.session_state.get("bg_color", "white")
    representation = st.session_state.get("representation", "sticks+spheres")
    stick_radius = st.session_state.get("stick_radius", 0.2)
    sphere_scale = st.session_state.get("sphere_scale", 0.3)
    stick_color = st.session_state.get("stick_color", None)
    apply_element_colors = st.session_state.get("apply_element_colors", True)
    stick_transparency = st.session_state.get("stick_transparency", 0.0)
    sphere_transparency = st.session_state.get("sphere_transparency", 0.0)

    style: dict = {}
    if representation in ("sticks+spheres", "sticks"):
        stick: dict = {"radius": stick_radius}
        if stick_transparency > 0:
            stick["opacity"] = 1.0 - stick_transparency
        style["stick"] = stick
    if representation in ("sticks+spheres", "spheres"):
        sphere: dict = {"radius": sphere_scale}
        if sphere_transparency > 0:
            sphere["opacity"] = 1.0 - sphere_transparency
        style["sphere"] = sphere
    if representation == "lines":
        style["line"] = {}
    if not apply_element_colors and stick_color:
        c = stick_color.strip().lower()
        for spec in style.values():
            if isinstance(spec, dict):
                spec["color"] = c

    style_json = json.dumps(style)
    sdf_escaped = sdf_content.replace("\\", "\\\\").replace("`", "\\`").replace("${", "\\${")

    transparent_bg = bg_color == "transparent"

    html = f"""<!DOCTYPE html>
<html><head><meta charset="utf-8"><style>
  * {{ margin:0; padding:0; box-sizing:border-box; }}
  body, #mol-container {{ background:transparent !important; }}
  #mol-container {{ width:100%; height:340px; }}
</style></head><body>
<div id="mol-container"></div>

<script src="https://cdn.jsdelivr.net/npm/3dmol@2.5.5/build/3Dmol-min.js"></script>
<script>
var viewer=$3Dmol.createViewer(document.getElementById("mol-container"),{{backgroundColor:"white"}});
{"viewer.setBackgroundColor(0xffffff,0);" if transparent_bg else ""}
viewer.addModel(`{sdf_escaped}`,"sdf");
viewer.setStyle({style_json});
viewer.zoomTo();
viewer.render();
(function(){{
  var c=document.getElementById("mol-container");
  c.addEventListener("wheel",function(e){{
    e.preventDefault();
    e.stopImmediatePropagation();
    var d=e.deltaY>0?0.92:1.08;
    viewer.zoom(d);
  }},{{passive:false,capture:true}});
}})();

</script></body></html>"""

    st.components.v1.html(html, height=400)


def _cache_3d_preview_sdf(compound: str) -> None:
    """Generate 3D SDF for preview and cache in session state."""
    try:
        from rdkit import Chem
        from rdkit.Chem import AllChem

        from wikimolgen.core import fetch_compound, validate_smiles

        smiles, _name = fetch_compound(compound)
        mol = validate_smiles(smiles)
        mol = Chem.AddHs(mol)
        AllChem.EmbedMolecule(mol, AllChem.ETKDGv3())
        sdf_block = Chem.MolToMolBlock(mol)
        st.session_state.sdf_content = sdf_block
    except Exception as exc:
        logger.warning("Could not generate 3D preview SDF for %s: %s", compound, exc)
