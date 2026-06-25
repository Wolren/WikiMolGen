"""
web/app.py
==========
Main Streamlit application for WikiMolGen web interface with ORIGINAL layout.
Matches the structure and feel of wiki_web_optimized.py exactly.

Usage:
    streamlit run web/app.py
"""

import sys
import tempfile
import time
from pathlib import Path

import streamlit as st

# Ensure project root and web/ are on sys.path for both local and Streamlit Cloud
_THIS_DIR = Path(__file__).resolve().parent
_PROJECT_ROOT = _THIS_DIR.parent
for p in (_THIS_DIR, _PROJECT_ROOT):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
from rendering.base import encode_image_to_base64, render_structure_dynamic
from session.state import initialize_session_state
from ui.components import (
    render_2d_settings,
    render_canvas_settings,
    render_compound_input,
    render_conformer_settings,
    render_effects_settings,
    render_lighting_settings,
    render_mode_selector,
    render_preset_manager,
    render_rendering_settings,
    render_rotation_settings,
)
from ui.protein_web_component import render_protein_structure
from wikipedia.boxes import render_wikipedia_metadata_section
from template.theme import apply_theme


def configure_page() -> None:
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="WikiMolGen",
        page_icon="media/wikimolgen_logo.svg",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def _on_auto_change() -> None:
    st.query_params["auto"] = str(st.session_state.auto_generate).lower()


def _on_white_bg_change() -> None:
    """Trigger re-render in 2D mode so structure turns black on white background."""
    if st.session_state.get("structure_type", "3D") == "2D":
        st.session_state.config_changed = True
        st.session_state._last_render_ts = 0.0  # Bypass debounce


def render_sidebar() -> tuple:
    """
    Render complete sidebar with layout and structure.

    Returns
    -------
    tuple
        (compound: str, structure_type: str, auto_generate: bool, protein_inputs: tuple or None)
    """
    with st.sidebar:
        st.markdown("<div class='sidebar-main-header'>Configuration</div>", unsafe_allow_html=True)
        st.divider()

        # Mode selector + toggles on one line
        col_mode, col_auto, col_white = st.columns([3, 1, 1], gap="small")
        with col_mode:
            structure_type = render_mode_selector()
        with col_auto:
            st.toggle(
                " ",
                value=True,
                key="auto_generate",
                on_change=_on_auto_change,
                label_visibility="collapsed",
            )
            st.caption("Auto Update")
        with col_white:
            st.toggle(
                " ",
                value=False,
                key="preview_white_bg",
                label_visibility="collapsed",
                on_change=_on_white_bg_change,
            )
            st.caption("White background")
        st.divider()

        # Compound/protein input based on mode
        compound = ""
        pdb_id = ""
        if structure_type == "Protein":
            from ui.protein_web_component import render_protein_selector

            pdb_id = render_protein_selector()
        else:
            compound = render_compound_input()
        st.divider()

        # Reset settings — below compound input, resets all
        def _on_reset_all() -> None:
            from session.state import reset_to_defaults

            reset_to_defaults("2D")
            reset_to_defaults("3D")
            st.session_state.pop("last_compound_fetched", None)
            st.session_state.pop("pubchem_data", None)
            from ui.components import save_config_to_session

            save_config_to_session()
            st.toast("All settings reset to defaults", icon=":material/check_circle:")

        st.button(
            "Reset settings",
            use_container_width=True,
            key="reset_all_btn",
            icon=":material/restart_alt:",
            on_click=_on_reset_all,
        )
        st.divider()

        # Preset management
        render_preset_manager()
        st.divider()

        # auto_generate is now a toggle in main content; read from session state
        auto_generate = st.session_state.get("auto_generate", True)

        # Mode-specific settings + reset button
        protein_inputs = None
        if structure_type == "2D":
            st.checkbox(
                "ACS Mode (overrides custom settings)",
                value=True,
                key="acs_mode",
                help="Applies wikipedia compliant settings",
            )
            render_rotation_settings("2d")
            render_2d_settings()
        elif structure_type == "3D":
            render_rotation_settings("3d")
            with st.expander("3D Settings", expanded=False):
                render_canvas_settings()
                render_rendering_settings()
                render_lighting_settings()
                render_effects_settings()
                render_conformer_settings()
        elif structure_type == "Protein":
            from ui.protein_web_component import (
                render_protein_canvas_settings,
                render_protein_cartoon_settings,
                render_protein_effects_settings,
                render_protein_ligand_settings,
            )

            with st.expander("Rotation", expanded=True):
                auto_prot = st.checkbox("Auto-Orient", value=True, key="protein_auto_rot")
                if not auto_prot:
                    for axis, key in [("X", "prot_x"), ("Y", "prot_y"), ("Z", "prot_z")]:
                        col1, col2 = st.columns([3, 1], gap="small")
                        with col1:
                            st.slider(
                                f"{axis}",
                                -180.0,
                                180.0,
                                0.0,
                                5.0,
                                key=f"{key}_slider",
                                on_change=lambda k=key: (
                                    st.session_state.update(
                                        {
                                            k: st.session_state[f"{k}_slider"],
                                            f"{k}_input": st.session_state[f"{k}_slider"],
                                        }
                                    )
                                    and None
                                ),
                            )
                        with col2:
                            st.number_input(
                                "Set",
                                -180.0,
                                180.0,
                                0.0,
                                5.0,
                                key=f"{key}_input",
                                on_change=lambda k=key: (
                                    st.session_state.update(
                                        {
                                            k: st.session_state[f"{k}_input"],
                                            f"{k}_slider": st.session_state[f"{k}_input"],
                                        }
                                    )
                                    and None
                                ),
                            )
            with st.expander("Protein Settings", expanded=False):
                canvas_cfg = render_protein_canvas_settings()
                cartoon_cfg = render_protein_cartoon_settings()
                ligand_cfg = render_protein_ligand_settings()
                effects_cfg = render_protein_effects_settings()
                canvas_cfg.update(effects_cfg)
            protein_inputs = (pdb_id, cartoon_cfg, ligand_cfg, canvas_cfg)

    return compound, structure_type, auto_generate, protein_inputs


def apply_2d_styling_to_image(image_html: str) -> str:
    """
    Apply 2D-specific styling to SVG image by adding class to img tag.

    Parameters
    ----------
    image_html : str
        HTML string containing <img> tag

    Returns
    -------
    str
        HTML with compound-preview-image-2d class added to img tag
    """
    # Add the 2D-specific class to the img tag for color inversion
    return image_html.replace(
        'class="compound-preview-image"', 'class="compound-preview-image compound-preview-image-2d"'
    )


def render_protein_structure_dynamic(
    pdb_id: str, cartoon_cfg: dict, ligand_cfg: dict, canvas_cfg: dict
) -> str:
    """
    Render protein structure dynamically (same pattern as render_structure_dynamic for 2D/3D).

    Parameters
    ----------
    pdb_id : str
        PDB identifier
    cartoon_cfg : dict
        Cartoon configuration
    ligand_cfg : dict
        Ligand configuration
    canvas_cfg : dict
        Canvas configuration

    Returns
    -------
    str
        HTML string with embedded base64 image, or None on error
    """

    # Create output base in temp directory (like base_old.py does)

    with tempfile.TemporaryDirectory() as tmpdir:
        output_base = Path(tmpdir) / pdb_id

        # Render protein structure
        output_path = render_protein_structure(
            pdb_id,
            cartoon_cfg,
            ligand_cfg,
            canvas_cfg,
            output_base,
        )

        # Encode and create HTML (same as base_old.py)
        if output_path and output_path.exists():
            img_base64, mime_type = encode_image_to_base64(output_path)
            image_html = f'<img src="data:image/{mime_type};base64,{img_base64}" class="protein-preview-image" alt="Protein Structure">'

            # Read file data for download
            with open(output_path, "rb") as f:
                file_data = f.read()

            # Update session state (same pattern as base_old.py)
            st.session_state.last_protein_image_html = image_html
            st.session_state.last_protein_pdb = pdb_id
            st.session_state.last_protein_file_data = file_data
            st.session_state.last_protein_file_name = output_path.name

            return image_html
        else:
            st.error("Failed to generate protein structure image")
            return ""


def _debounce_pass() -> bool:
    """Return True if 500ms have elapsed since last auto-render."""
    now = time.time()
    last = st.session_state.get("_last_render_ts", 0.0)
    return now - last >= 0.5


def _render_small_molecule_content(compound: str, structure_type: str) -> None:
    """Render the 2D/3D structure preview with auto-update and caching."""
    if st.button(
        "Generate Now",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.get("auto_generate", True),
        key="generate_now_btn",
    ):
        st.session_state.manual_generate = True

    auto_generate = st.session_state.get("auto_generate", True)
    wb = " white-bg" if st.session_state.get("preview_white_bg", False) else ""

    preview_placeholder = st.empty()

    has_pending_config = st.session_state.get("config_changed", False)
    never_rendered = not st.session_state.get("rendered_structure", False)
    should_render = (
        (auto_generate and _debounce_pass() and (has_pending_config or never_rendered))
        or st.session_state.get("manual_generate", False)
        or st.session_state.get("last_compound") != compound
    )

    if should_render and compound:
        st.session_state._last_render_ts = time.time()
        st.session_state.config_changed = False
        st.session_state.manual_generate = False

        with st.spinner("Generating structure..."):
            image_html = render_structure_dynamic(compound, structure_type)

        if image_html:
            if structure_type == "2D":
                image_html = apply_2d_styling_to_image(image_html)

            with preview_placeholder.container():
                st.markdown(
                    f'<div id="preview-wrap" class="compound-preview-container{wb}">{image_html}</div>',
                    unsafe_allow_html=True,
                )
        elif st.session_state.get("last_image_html"):
            cached_html = st.session_state.last_image_html
            if st.session_state.get("structure_type") == "2D":
                cached_html = apply_2d_styling_to_image(cached_html)
            with preview_placeholder.container():
                st.markdown(
                    f'<div id="preview-wrap" class="compound-preview-container{wb}">{cached_html}</div>',
                    unsafe_allow_html=True,
                )
        else:
            with preview_placeholder.container():
                st.markdown(
                    f'<div id="preview-wrap" class="compound-preview-container{wb}" style="min-height:200px;">'
                    '<span style="color:var(--text-secondary);font-size:0.9rem;">'
                    "Enter a compound and adjust settings, then click 'Generate Now' or enable auto-update."
                    "</span></div>",
                    unsafe_allow_html=True,
                )
    elif st.session_state.get("last_image_html"):
        cached_html = st.session_state.last_image_html
        if st.session_state.get("structure_type") == "2D":
            cached_html = apply_2d_styling_to_image(cached_html)

        with preview_placeholder.container():
            st.markdown(
                f'<div id="preview-wrap" class="compound-preview-container{wb}">{cached_html}</div>',
                unsafe_allow_html=True,
            )
    else:
        with preview_placeholder.container():
            st.markdown(
                f'<div id="preview-wrap" class="compound-preview-container{wb}" style="min-height:200px;">'
                '<span style="color:var(--text-secondary);font-size:0.9rem;">'
                "Enter a compound and adjust settings, then click 'Generate Now' or enable auto-update."
                "</span></div>",
                unsafe_allow_html=True,
            )


def _render_protein_content(protein_inputs: tuple | None) -> None:
    """Render the Protein structure preview."""
    if protein_inputs:
        pdb_id, cartoon_cfg, ligand_cfg, canvas_cfg = protein_inputs

        if st.button("Generate Protein Structure", use_container_width=True, key="protein_gen_btn"):
            render_protein_structure_dynamic(pdb_id, cartoon_cfg, ligand_cfg, canvas_cfg)

        if st.session_state.get("last_protein_image_html"):
            col1, col2, col3, col4 = st.columns(4)
            if st.session_state.get("last_protein_metadata"):
                metadata = st.session_state.last_protein_metadata
                with col1:
                    st.metric("Chains", len(metadata.get("chains", [])))
                with col2:
                    st.metric("Atoms", metadata.get("num_atoms", 0))
                with col3:
                    st.metric("Residues", metadata.get("num_residues", 0))
                with col4:
                    st.metric("Has Ligand", "✓" if metadata.get("has_ligand", False) else "✗")

            st.markdown(
                f'<div class="protein-preview-container">{st.session_state.last_protein_image_html}</div>',
                unsafe_allow_html=True,
            )
    else:
        st.info("Configure protein settings in the sidebar to render a structure.")


def render_main_content(
    compound: str, structure_type: str, protein_inputs: tuple | None = None
) -> None:
    """Render main content area."""
    if structure_type != "Protein":
        _render_small_molecule_content(compound, structure_type)
    else:
        _render_protein_content(protein_inputs)

    st.divider()
    if structure_type != "Protein":
        render_download_section()
    else:
        render_protein_download_section()


@st.fragment
def render_download_section() -> None:
    """Render download button with filename customization and reset"""
    if st.session_state.get("last_file_data"):
        file_data = st.session_state.last_file_data
        file_name = st.session_state.get("last_file_name", "structure.png")
        mime_type = st.session_state.get("last_file_mime", "image/png")
        # Derive extension from mime type if filename lacks it
        if "." not in file_name:
            file_ext = ".svg" if "svg" in mime_type else ".png"
            file_name += file_ext

        file_ext = Path(file_name).suffix
        base_name = Path(file_name).stem

        # Initialize the input key if not present
        if "download_filename_input" not in st.session_state:
            st.session_state.download_filename_input = base_name

        def on_reset() -> None:
            """Reset to original compound-based filename with structure type"""
            compound = st.session_state.get("last_compound", "structure")
            structure_type = st.session_state.get("structure_type", "2D")
            original_base = f"{compound} {structure_type}"
            st.session_state.last_file_name = f"{original_base}{file_ext}"
            st.session_state.download_filename_input = original_base

        # Filename input above
        custom_base_name = st.text_input(
            "File name",
            value=st.session_state.download_filename_input,
            placeholder="Enter filename...",
            max_chars=200,
            key="download_filename_input",
        )
        clean_base = Path(custom_base_name).stem
        st.session_state.last_file_name = f"{clean_base}{file_ext}"

        # Download + Reset side by side
        col_download, col_reset = st.columns([3, 1], gap="small")
        with col_download:
            st.download_button(
                f"Download {file_ext.upper().replace('.', '')}",
                file_data,
                file_name=st.session_state.last_file_name,
                mime=mime_type,
                use_container_width=True,
            )
        with col_reset:
            st.button(
                "Reset", use_container_width=True, key="reset_filename_btn", on_click=on_reset
            )


@st.fragment
def render_protein_download_section() -> None:
    """Render protein download button (same pattern as 2D/3D via base_old.py)"""
    if st.session_state.get("last_protein_file_data"):
        file_data = st.session_state.last_protein_file_data
        file_name = st.session_state.get("last_protein_file_name", "protein.png")
        mime_type = "image/png"

        st.download_button(
            "Download PNG",
            data=file_data,
            file_name=file_name,
            mime=mime_type,
            use_container_width=True,
            key="protein_download_btn",
        )


def main() -> None:
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()

    # Restore last-used mode from URL query params
    mode_param = st.query_params.get("mode")
    if mode_param in ("2D", "3D", "Protein"):
        st.session_state.mode_selector = mode_param
        st.session_state.structure_type = mode_param
        st.session_state._last_active_mode = mode_param

    # Restore auto-update from URL query params
    auto_param = st.query_params.get("auto")
    if auto_param is not None:
        st.session_state.auto_generate = auto_param.lower() == "true"

    # Configure page
    configure_page()

    # Apply custom theme CSS (after set_page_config, before any widgets)
    apply_theme()

    # Render sidebar and get settings
    compound, structure_type, auto_generate, protein_inputs = render_sidebar()

    # Render main content
    render_main_content(compound, structure_type, protein_inputs)

    # Wikipedia boxes section (only for 2D/3D, not for Protein)
    if compound and structure_type != "Protein":
        render_wikipedia_metadata_section(compound, structure_type)

    # Footer
    st.divider()
    st.markdown(
        """
    <div class='footer-text'>
    <strong>WikiMolGen</strong>, a chemical structure generator for Wikipedia &amp; Wikimedia Commons | Wolren<br>
    </div>
    """,
        unsafe_allow_html=True,
    )


if __name__ == "__main__":
    main()
