"""
web/app.py
==========
Main Streamlit application for WikiMolGen web interface with ORIGINAL layout.
Matches the structure and feel of wiki_web_optimized.py exactly.

Usage:
    streamlit run web/app.py
"""

import json
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
from template.theme import apply_theme
from ui.components_shared import save_config_to_session
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


def configure_page() -> None:
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="WikiMolGen",
        page_icon="media/wikimolgen_logo.svg",
        layout="wide",
        initial_sidebar_state="expanded",
    )


def _on_auto_change() -> None:
    st.query_params["auto"] = str(st.session_state.get("auto_generate", True)).lower()


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

        # Mode selector with toggles below
        structure_type = render_mode_selector()

        col_auto, col_white = st.columns(2, gap="small")
        with col_auto:
            st.toggle(
                "Auto Update",
                value=st.session_state.get("auto_generate", structure_type != "Protein"),
                key="auto_generate",
                on_change=_on_auto_change,
            )
        with col_white:
            st.toggle(
                "White background",
                value=False,
                key="preview_white_bg",
                on_change=_on_white_bg_change,
            )
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
                on_change=lambda: save_config_to_session("2d"),
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
                                        },
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
                                        },
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

        # Reset all settings — at the bottom, away from inputs
        def _on_reset_all() -> None:
            from session.state import reset_to_defaults

            reset_to_defaults("2D")
            reset_to_defaults("3D")
            st.session_state.pop("last_compound_fetched", None)
            st.session_state.pop("pubchem_data", None)
            st.session_state.pop("preview_history", None)
            from ui.components import save_config_to_session

            save_config_to_session()
            st.toast("All settings reset to defaults", icon=":material/check_circle:")

        st.divider()
        st.button(
            "Reset settings",
            use_container_width=True,
            key="reset_all_btn",
            icon=":material/restart_alt:",
            on_click=_on_reset_all,
        )

    return compound, structure_type, auto_generate, protein_inputs


def _make_preview_container_class(structure_type: str) -> str:
    """Build the CSS class string for the preview container div."""
    classes = ["compound-preview-container"]
    if structure_type == "2D":
        classes.append("compound-preview-container-2d")
    if st.session_state.get("preview_white_bg", False):
        classes.append("white-bg")
    return " ".join(classes)


def render_protein_structure_dynamic(
    pdb_id: str, cartoon_cfg: dict, ligand_cfg: dict, canvas_cfg: dict,
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
        st.error("Failed to generate protein structure image")
        return ""


def _clean_svg_white_bg(image_html: str) -> str:
    """Remove white background <rect> from SVG data URLs in the image HTML.

    Works on any SVG <rect> with fill:white, fill:#FFFFFF, fill="#FFFFFF",
    or fill="white" — both attribute and style-attribute variants.
    Does NOT touch the rendering pipeline; this is a post-processing step
    applied to the already-generated SVG string.
    """
    import re as _re
    import base64 as _b64

    def _clean_one(m):
        prefix = m.group(1)
        b64_data = m.group(2)
        try:
            svg_text = _b64.b64decode(b64_data).decode("utf-8", errors="replace")
        except Exception:
            return m.group(0)  # can't decode, leave untouched

        # Remove <rect> elements whose sole purpose is a white background fill
        # Style-attribute variant: <rect style="...fill:white/##FFFFFF..."
        svg_text = _re.sub(
            r'<rect\s+style\s*=\s*["\'][^"\']*?'
            r'fill\s*:\s*(?:white|#FFFFFF|#ffffff)'
            r'[^"\']*?["\']\s*[^>]*>\s*</rect>',
            "",
            svg_text,
        )
        # Style-attribute variant, self-closing or space-closed
        svg_text = _re.sub(
            r'<rect\s+style\s*=\s*["\'][^"\']*?'
            r'fill\s*:\s*(?:white|#FFFFFF|#ffffff)'
            r'[^"\']*?["\']\s*/?\s*>',
            "",
            svg_text,
        )
        # Attribute variant: <rect fill="white" ...> or fill="#FFFFFF"
        svg_text = _re.sub(
            r'<rect\s+[^>]*?fill\s*=\s*["\'](?:white|#FFFFFF|#ffffff)["\'][^>]*>\s*</rect>',
            "",
            svg_text,
        )
        svg_text = _re.sub(
            r'<rect\s+[^>]*?fill\s*=\s*["\'](?:white|#FFFFFF|#ffffff)["\'][^>]*/>',
            "",
            svg_text,
        )

        try:
            new_b64 = _b64.b64encode(svg_text.encode("utf-8")).decode("ascii")
        except Exception:
            return m.group(0)
        return f'{prefix}{new_b64}"'

    return _re.sub(
        r'(src="data:image/svg\+xml;base64,)([A-Za-z0-9+/=]+)"',
        _clean_one,
        image_html,
    )


def _debounce_pass() -> bool:
    """Return True if 500ms have elapsed since last auto-render."""
    now = time.time()
    last = st.session_state.get("_last_render_ts", 0.0)
    return now - last >= 0.5


def _add_to_preview_history() -> None:
    """Store the latest rendered preview in history (max 8 entries)."""
    history: list = st.session_state.get("preview_history", [])
    entry = {
        "image_html": st.session_state.get("last_image_html", ""),
        "compound": st.session_state.get("last_compound", ""),
        "structure_type": st.session_state.get("structure_type", ""),
        "timestamp": time.time(),
    }
    # Don't duplicate identical compound+type
    if history and history[0].get("compound") == entry["compound"] \
       and history[0].get("structure_type") == entry["structure_type"]:
        return
    history.insert(0, entry)
    st.session_state.preview_history = history[:10]


def _render_history_strip() -> None:
    """Render the preview history as a horizontal scrollable strip."""
    history: list = st.session_state.get("preview_history", [])
    if not history:
        return

    active_compound = st.session_state.get("last_compound", "")
    active_type = st.session_state.get("structure_type", "")

    items_html = ""
    for i, item in enumerate(history):
        img_html = item.get("image_html", "")
        compound = item.get("compound", "")
        stype = item.get("structure_type", "")
        is_active = (compound == active_compound and stype == active_type)
        active_cls = " active" if is_active else ""
        # Wrap img in a constrained thumbnail container
        img_html = img_html.replace(
            'class="compound-preview-image"',
            'class="compound-preview-image preview-history-thumb"',
        )
        items_html += (
            f'<div class="preview-history-item{active_cls}" onclick="navigate_history({i})">'
            f'{img_html}'
            f'<div class="preview-history-label">{compound[:18]}</div>'
            f"</div>"
        )

    # JavaScript to restore a history item via session state
    history_json = json.dumps([
        {
            "image_html": h.get("image_html", ""),
            "compound": h.get("compound", ""),
            "structure_type": h.get("structure_type", ""),
        }
        for h in history
    ]).replace("</", "<\\/")
    st.markdown(
        f"""
        <div class="preview-history">
            {items_html}
        </div>
        <script>
        const historyData = {history_json};
        function navigate_history(idx) {{
            if (idx < historyData.length) {{
                const params = new URLSearchParams(window.location.search);
                params.set('hist_idx', idx);
                window.history.replaceState({{}}, '', '?' + params.toString());
                window.location.reload();
            }}
        }}
        </script>
        """,
        unsafe_allow_html=True,
    )

    # Check if a history item was selected via query param
    hist_idx = st.query_params.get("hist_idx")
    if hist_idx is not None and hist_idx.isdigit():
        idx = int(hist_idx)
        if 0 <= idx < len(history):
            item = history[idx]
            st.session_state.last_image_html = item["image_html"]
            st.session_state.last_compound = item["compound"]
            st.session_state.structure_type = item["structure_type"]
            st.session_state.rendered_structure = True
            st.query_params.clear()  # Don't re-trigger
            st.rerun()


def _render_small_molecule_content(compound: str, structure_type: str) -> None:
    """Render the 2D/3D structure preview with auto-update, caching, full-width toggle, and history."""

    # Full-width toggle via query param (client-side button triggers this)
    if st.query_params.get("fw") == "1":
        st.session_state.full_width_preview = not st.session_state.get("full_width_preview", False)
        st.query_params.clear()
        # No rerun needed -- page already reloaded from the button click

    # Generate button
    if st.button(
        "Generate Now",
        type="primary",
        use_container_width=True,
        disabled=st.session_state.get("auto_generate", True),
        key="generate_now_btn",
    ):
        st.session_state.manual_generate = True

    auto_generate = st.session_state.get("auto_generate", True)

    preview_placeholder = st.empty()

    # Build overlay fullscreen button — use addEventListener to avoid React error #231
    fw_active = st.session_state.get("full_width_preview", False)
    fw_icon = "✕" if fw_active else "⛶"
    fw_title = "Exit full-width" if fw_active else "Full-width preview"
    fs_id = "fs-btn-" + str(id(st.session_state))[-4:]
    fw_btn = (
        f'<button id="{fs_id}" class="fullscreen-btn" title="{fw_title}">{fw_icon}</button>'
    )
    fw_script = (
        f'<script>'
        f'document.getElementById("{fs_id}").addEventListener("click",function(){{'
        f'var p=new URLSearchParams(window.location.search);p.set("fw","1");'
        f'window.location.search=p.toString()}});'
        f'</script>'
    )

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
            # Clean white background from SVG (only when white-bg is OFF)
            if not st.session_state.get("preview_white_bg", False):
                image_html = _clean_svg_white_bg(image_html)
            # Overwrite session state so history thumbnails use clean SVGs too
            st.session_state.last_image_html = image_html
            st.session_state.last_compound = compound
            _add_to_preview_history()
            container_class = _make_preview_container_class(structure_type)
            with preview_placeholder.container():
                st.markdown(
                    f'<div id="preview-wrap" class="{container_class}">{fw_btn}{image_html}{fw_script}</div>',
                    unsafe_allow_html=True,
                )
        else:
            # Render failed — clear cached image so placeholder shows instead
            # of silently displaying stale data under the error message
            for key in ("last_image_html", "last_file_data", "last_file_name", "last_file_mime"):
                st.session_state.pop(key, None)
            st.session_state.rendered_structure = False
            with preview_placeholder.container():
                st.markdown(
                    '<div id="preview-wrap" class="compound-preview-placeholder">'
                    '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
                    '<circle cx="12" cy="12" r="1"/><path d="M20.2 20.2c2.04-2.03.02-7.36-4.5-11.9-4.54-4.52-9.87-6.54-11.9-4.5-2.04 2.03-.02 7.36 4.5 11.9 4.54 4.52 9.87 6.54 11.9 4.5Z"/>'
                    '<path d="M15.7 15.7c4.52-4.54 6.54-9.87 4.5-11.9-2.03-2.04-7.36-.02-11.9 4.5-4.52 4.54-6.54 9.87-4.5 11.9 2.03 2.04 7.36.02 11.9-4.5Z"/>'
                    "</svg>"
                    "<span>Rendering failed</span>"
                    '<span class="hint">Check the compound name or try a different format.</span>'
                    "</div>",
                    unsafe_allow_html=True,
                )
    elif not has_pending_config and st.session_state.get("last_image_html"):
        container_class = _make_preview_container_class(
            st.session_state.get("structure_type", structure_type)
        )
        with preview_placeholder.container():
            st.markdown(
                f'<div id="preview-wrap" class="{container_class}">'
                f'{fw_btn}{st.session_state.last_image_html}{fw_script}</div>',
                unsafe_allow_html=True,
            )
    else:
        with preview_placeholder.container():
            st.markdown(
                '<div id="preview-wrap" class="compound-preview-placeholder">'
                '<svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5" stroke-linecap="round" stroke-linejoin="round">'
                '<circle cx="12" cy="12" r="1"/><path d="M20.2 20.2c2.04-2.03.02-7.36-4.5-11.9-4.54-4.52-9.87-6.54-11.9-4.5-2.04 2.03-.02 7.36 4.5 11.9 4.54 4.52 9.87 6.54 11.9 4.5Z"/>'
                '<path d="M15.7 15.7c4.52-4.54 6.54-9.87 4.5-11.9-2.03-2.04-7.36-.02-11.9 4.5-4.52 4.54-6.54 9.87-4.5 11.9 2.03 2.04 7.36.02 11.9-4.5Z"/>'
                "</svg>"
                "<span>Enter a compound in the sidebar</span>"
                '<span class="hint">e.g. aspirin, 2244, or CC(=O)Oc1ccccc1C(=O)O</span>'
                "</div>",
                unsafe_allow_html=True,
            )


def _render_protein_content(protein_inputs: tuple | None) -> None:
    """Render the Protein structure preview with auto-update."""
    if not protein_inputs:
        st.info("Configure protein settings in the sidebar to render a structure.")
        return

    pdb_id, cartoon_cfg, ligand_cfg, canvas_cfg = protein_inputs
    if not pdb_id:
        return

    auto_generate = st.session_state.get("auto_generate", True)

    # Determine if we need to re-render
    has_pending = st.session_state.get("config_changed", False)
    last_pdb = st.session_state.get("last_protein_pdb", "")
    prev_cfg = st.session_state.get("_last_protein_cfg", {})
    cfg_changed = (
        cartoon_cfg != prev_cfg.get("cartoon")
        or ligand_cfg != prev_cfg.get("ligand")
        or canvas_cfg != prev_cfg.get("canvas")
    )
    needs_render = (auto_generate and (has_pending or pdb_id != last_pdb or cfg_changed))

    if needs_render:
        st.session_state.config_changed = False
        st.session_state._last_protein_cfg = {
            "cartoon": cartoon_cfg, "ligand": ligand_cfg, "canvas": canvas_cfg,
        }
        with st.spinner("Generating protein structure..."):
            image_html = render_protein_structure_dynamic(pdb_id, cartoon_cfg, ligand_cfg, canvas_cfg)
        if image_html:
            st.session_state.rendered_structure = True

    if st.button(
        "Generate Protein Structure",
        use_container_width=True,
        key="protein_gen_btn",
        disabled=auto_generate,
    ):
        st.session_state.config_changed = True
        st.rerun()

    # Show protein preview if available
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


def render_main_content(
    compound: str, structure_type: str, protein_inputs: tuple | None = None,
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

    # Preview history — after download, not inline with preview
    if structure_type != "Protein" and st.session_state.get("preview_history"):
        _render_history_strip()

    # Inject full-width CSS inline (avoids body-class issue)
    if st.session_state.get("full_width_preview", False):
        st.markdown(
            """<style>
            [data-testid="stSidebar"] { display: none !important; }
            .main > .block-container {
                max-width: 100% !important;
                padding-left: 2rem !important;
                padding-right: 2rem !important;
            }
            </style>""",
            unsafe_allow_html=True,
        )


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
                "Reset", use_container_width=True, key="reset_filename_btn", on_click=on_reset,
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
    # Hide when config is pending (mode switch with auto-update OFF)
    if compound and structure_type != "Protein" and not st.session_state.get("config_changed", False):
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
