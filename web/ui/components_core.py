"""
web/ui/components_core.py
==========================
Core UI components shared across rendering modes:
compound input, preset manager, mode selector, rotation settings.
"""

import json
import logging
from datetime import datetime

import streamlit as st
from template.utils import MAX_UPLOAD_SIZE, apply_preset_to_session, export_current_as_preset
from ui.icons import header
from ui.components_shared import save_config_to_session

from wikimolgen.configs import Config3D, ConfigLoader

from ui.components_shared import save_config_to_session, _sync_slider_to_config, _sync_input_to_slider, _sync_number_input

logger = logging.getLogger(__name__)


# ============================================================================
# COMPOUND INPUT
# ============================================================================


def render_compound_input() -> str:
    """Render compound input field with resolved-name feedback."""
    raw = st.text_input(
        "Name/CID/SMILES",
        "",
        max_chars=1000,
        placeholder="e.g. aspirin, 2244, CC(=O)Oc1ccccc1C(=O)O",
    )
    compound = "".join(c for c in raw if c.isprintable()).strip()

    # Show resolved name feedback when a compound has been fetched successfully
    fetched = st.session_state.get("last_compound_fetched", "")
    if fetched and compound and compound == st.session_state.get("last_search_query", ""):
        pubchem_data = st.session_state.get("pubchem_data", {})
        if pubchem_data and pubchem_data.get("title"):
            st.markdown(
                f'<div class="compound-feedback">'
                f'<span class="resolved">\u2713 {pubchem_data["title"]}</span>'
                f"</div>",
                unsafe_allow_html=True,
            )
    return compound


# ============================================================================
# PRESET MANAGER
# ============================================================================


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
                    "save_filename", f"{gen_type}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
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


# ============================================================================
# MODE SELECTOR
# ============================================================================


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


# ============================================================================
# ROTATION SETTINGS (shared by 2D and 3D)
# ============================================================================


def render_rotation_settings(dim: str) -> None:
    """Render unified rotation section inside an auto-expanded expander."""
    with st.expander("Rotation", expanded=True):
        if dim == "2d":
            st.checkbox(
                "Auto orient", value=False, key="auto_orient_2d",
                on_change=lambda: save_config_to_session("2d"),
            )
            if not st.session_state.get("auto_orient_2d", False):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.slider(
                        "Rotation (\u00b0)",
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
                on_change=lambda: save_config_to_session("3d"),
                help="Automatically orient the molecule (disables manual rotation)",
            )
            if not st.session_state.get("auto_orient_3d", False):
                axis_colors = {"X": "#e74c3c", "Y": "#2ecc71", "Z": "#3498db"}
                for axis, key in [("X", "x_rotation"), ("Y", "y_rotation"), ("Z", "z_rotation")]:
                    color = axis_colors[axis]
                    st.markdown(
                        f'<span style="color:{color};font-weight:600;font-size:0.85rem">{axis} Axis</span>',
                        unsafe_allow_html=True,
                    )
                    col1, col2 = st.columns([3, 1], gap="small")
                    with col1:
                        st.slider(
                            " ",
                            -180.0,
                            180.0,
                            st.session_state.get(key, 0.0),
                            5.0,
                            key=f"{key}_slider",
                            label_visibility="collapsed",
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


# ============================================================================
# GENERATE BUTTON
# ============================================================================


def render_generate_button(auto_generate: bool) -> bool:
    """Render manual generate button."""
    generate_btn_enabled = not auto_generate
    clicked = st.button(
        "Generate Now", type="primary", use_container_width=True, disabled=not generate_btn_enabled,
    )

    if clicked:
        st.session_state.manual_generate = True

    return clicked
