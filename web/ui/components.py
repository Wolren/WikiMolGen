"""
web/ui/components.py
==============================================================
"""

import json
import logging
from datetime import datetime
from typing import Any

import streamlit as st
from rendering.atom_colors import (
    apply_scheme_to_session,
    export_scheme_from_session,
    get_scheme_choices,
)
from template.utils import MAX_UPLOAD_SIZE, apply_preset_to_session, export_current_as_preset

from ui.icons import header

from wikimolgen.configs import Config3D, ConfigLoader


def _validate_atom_scheme(data: dict) -> str | None:
    """Validate uploaded scheme data, return error message or ``None`` on success."""
    ec = data.get("element_colors")
    if ec is not None:
        if not isinstance(ec, dict):
            return "element_colors must be an object (dict)"
        for k, v in ec.items():
            if not isinstance(k, str) or not k.isascii() or len(k) > 2:
                return f"Invalid element symbol: {k!r}"
            if not isinstance(v, str):
                return f"Color for element {k!r} must be a string"
    name = data.get("name")
    if name is not None and (not isinstance(name, str) or len(name) > 100):
        return "Scheme name must be a string under 100 characters"
    return None


# ============================================================================
# CALLBACKS (Rotation slider / number input sync)
# ============================================================================
def _sync_slider_to_config(key: str) -> None:
    st.session_state[key] = st.session_state[f"{key}_slider"]
    st.session_state.config_changed = True


def _sync_input_to_slider(key: str) -> None:
    st.session_state[f"{key}_slider"] = st.session_state[key]
    st.session_state.config_changed = True


def _sync_number_input(key: str) -> None:
    """Sync number_input (key_input) to config key and slider."""
    val = st.session_state[f"{key}_input"]
    st.session_state[key] = val
    st.session_state[f"{key}_slider"] = val
    save_config_to_session("3d")


# ============================================================================
# WIDGET FACTORY (Auto-save wrapper helpers)
# ============================================================================
def _s(dim: str, *a: Any, **kw: Any) -> Any:
    return st.slider(*a, on_change=lambda: save_config_to_session(dim), **kw)


def _cb(dim: str, *a: Any, **kw: Any) -> Any:
    kw.pop("on_change", None)
    return st.checkbox(*a, on_change=lambda: save_config_to_session(dim), **kw)  # type: ignore[call-overload,misc]


def _ni(dim: str, *a: Any, **kw: Any) -> Any:
    return st.number_input(*a, on_change=lambda: save_config_to_session(dim), **kw)


def _sb(dim: str, *a: Any, **kw: Any) -> Any:
    kw.pop("on_change", None)
    return st.selectbox(*a, on_change=lambda: save_config_to_session(dim), **kw)  # type: ignore[call-overload,misc]


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
    raw = st.text_input(
        "Name/CID/SMILES",
        "",
        max_chars=1000,
        placeholder="e.g. aspirin, 2244, CC(=O)Oc1ccccc1C(=O)O",
    )
    return "".join(c for c in raw if c.isprintable()).strip()


def render_preset_manager() -> None:
    """Render preset management UI (full config snapshots per mode)."""
    st.markdown(header("folder", "Presets"), unsafe_allow_html=True)
    with st.expander("Presets", expanded=False):
        tab1, tab2, tab3 = st.tabs(["Predefined", "Upload", "Save"])

        with tab1:
            template_list = ConfigLoader.list_templates()

            all_presets = (
                ["Default"]
                + template_list["settings_templates"]
                + list(st.session_state.get("custom_presets", {}).keys())
            )

            st.markdown("**Presets**")
            if "_pending_preset_name" in st.session_state:
                st.session_state.preset_selector = st.session_state.pop("_pending_preset_name")

            prev_selection = st.session_state.get("_prev_preset_sel", "Default")
            preset_choice = st.selectbox(
                "Select Preset:",
                all_presets,
                key="preset_selector",
                label_visibility="collapsed",
            )
            if preset_choice != prev_selection:
                if preset_choice != "Default":
                    st.toast(f"Preset: {preset_choice}", icon=":material/tune:")
                    _apply_preset_now(preset_choice)
                st.session_state._prev_preset_sel = preset_choice

            if preset_choice in st.session_state.get("custom_presets", {}) and st.button(
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
                    raw = uploaded.read()
                    if len(raw) > MAX_UPLOAD_SIZE:
                        st.error(f"File too large ({len(raw) / 1024:.0f} KB). Maximum: 1 MB.")
                        st.stop()
                    data = json.loads(raw)
                    name = data.get("name", f"Custom_{datetime.now().strftime('%H%M%S')}")

                    if "custom_presets" not in st.session_state:
                        st.session_state.custom_presets = {}
                    st.session_state.custom_presets[name] = data

                    apply_preset_to_session(data.get("settings", data))

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
                max_chars=200,
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
    apply_preset_to_session(settings)
    save_config_to_session()


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
    st.session_state.config_changed = True


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
    assert structure_type is not None
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

        render_color_palette()

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


def render_color_palette() -> None:
    """Render color palette with Predefined/Upload/Save tabs (like presets)."""
    st.markdown(header("palette", "Colors"), unsafe_allow_html=True)

    bg_color = _sb3(
        "Background",
        ["white", "black", "gray", "transparent"],
        key="bg_color",
        help="Set the background color behind the molecule render",
    )

    tab1, tab2, tab3 = st.tabs(["Predefined", "Upload", "Save"])

    with tab1:
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
        upload_key = (
            f"atom_scheme_uploader_{st.session_state.get('_atom_scheme_upload_counter', 0)}"
        )
        uploaded = st.file_uploader(
            "Upload Scheme",
            type=["json"],
            key=upload_key,
            label_visibility="collapsed",
        )
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
