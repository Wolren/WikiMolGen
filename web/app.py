"""
web/app.py
==========
Main Streamlit application for WikiMolGen web interface with ORIGINAL layout.
Matches the structure and feel of wiki_web_optimized.py exactly.

Usage:
    streamlit run web/app.py
"""

import base64
import tempfile
from pathlib import Path

import streamlit as st

from rendering.base import render_structure_dynamic
from session.state import initialize_session_state
from ui.components import (
    render_compound_input,
    render_template_manager,
    render_mode_selector,
    render_2d_settings,
    render_3d_settings,
    render_canvas_settings,
    render_rendering_settings,
    render_lighting_settings,
    render_effects_settings,
    render_auto_generate_checkbox,
    render_generate_button,
)
from ui.protein_web_component import render_protein_structure
from wikipedia.boxes import render_wikipedia_metadata_section


def configure_page() -> None:
    """Configure Streamlit page settings"""
    st.set_page_config(
        page_title="WikiMolGen",
        page_icon="media/wikimolgen_logo.png",
        layout="wide",
        initial_sidebar_state="expanded"
    )

# Apply theme
from template.theme import apply_theme

apply_theme()

st.markdown("""
       <style>
       .compound-preview-container {
           padding: 8px;
           background-color: rgba(255, 255, 255, 0);
           display: flex;
           align-items: center;
           justify-content: center;
       }

       .compound-preview-image-2d {
            filter: invert(1);
       }

       .compound-preview-image[data-type="2D"] {
            max-width: 100%;
       }

       .compound-preview-image[data-type="3D"] {
            width: auto;
            height: auto;
            max-width: 800px;
       }

       .compound-preview-image {
            max-width: 100%;
            height: auto;
            display: block;
            border: 3px dashed rgba(100, 150, 200, 1);
            border-radius: 4px;
       }

       .compound-preview-image {
           max-width: 100%;
           height: auto;
           display: block;
       }

       .protein-preview-container {
           display: flex;
           align-items: center;
           justify-content: center;
           max-width: 800px;
           margin: 0 auto;
       }

       .protein-preview-image {
           max-width: 800px;
           width: 100%;
           height: auto;
           display: block;
           border: 3px dashed rgba(100, 150, 200, 1);
           border-radius: 4px;
       }
       </style>
   """, unsafe_allow_html=True)


def encode_image_to_base64(image_path: Path) -> tuple:
    """
    Encode image file to base64 string (same as base_old.py).

    Parameters
    ----------
    image_path : Path
        Path to image file

    Returns
    -------
    tuple
        (base64_string, mime_type)
    """
    with open(image_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode()
        mime_type = "png"
    return img_base64, mime_type


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

        # Compound input
        compound = render_compound_input()
        st.divider()

        # Template management
        render_template_manager()
        st.divider()

        # Auto-generate toggle
        auto_generate = render_auto_generate_checkbox()
        st.divider()

        # Mode selector (2D/3D/Protein)
        structure_type = render_mode_selector()
        st.divider()

        # Mode-specific settings
        protein_inputs = None
        if structure_type == "2D":
            render_2d_settings()
        elif structure_type == "3D":
            render_3d_settings()
            render_canvas_settings()
            render_rendering_settings()
            render_lighting_settings()
            render_effects_settings()
        elif structure_type == "Protein":
            # Protein-specific settings
            from ui.protein_web_component import (
                render_protein_selector,
                render_protein_cartoon_settings,
                render_protein_ligand_settings,
                render_protein_canvas_settings,
            )
            st.markdown("#### Protein Rendering Settings")
            pdb_id = render_protein_selector()
            cartoon_cfg = render_protein_cartoon_settings()
            ligand_cfg = render_protein_ligand_settings()
            canvas_cfg = render_protein_canvas_settings()
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
        'class="compound-preview-image"',
        'class="compound-preview-image compound-preview-image-2d"'
    )


def render_protein_structure_dynamic(pdb_id: str, cartoon_cfg: dict, ligand_cfg: dict, canvas_cfg: dict) -> str:
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
        if output_path.exists():
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
            return None


def render_main_content(compound: str, structure_type: str, auto_generate: bool, protein_inputs: tuple = None) -> None:
    """
    Render main content area.

    Parameters
    ----------
    compound : str
        Compound identifier
    structure_type : str
        "2D", "3D", or "Protein"
    auto_generate : bool
        Whether auto-generate is enabled
    protein_inputs : tuple or None
        Protein configuration (pdb_id, cartoon_cfg, ligand_cfg, canvas_cfg)
    """
    # Only render compound inputs/button for 2D and 3D
    if structure_type != "Protein":
        render_generate_button(auto_generate)

        # Placeholder for the structure image in a fixed container
        preview_placeholder = st.empty()

        # Check if image should be rendered at the moment
        should_render = (
                auto_generate
                or st.session_state.get("manual_generate", False)
                or st.session_state.get("last_compound") != compound
        )

        if should_render and compound:
            # Clear manual trigger
            st.session_state.manual_generate = False

            # Render structure
            with st.spinner("Generating structure..."):
                image_html = render_structure_dynamic(compound, structure_type)

            if image_html:
                # Apply 2D-specific styling (color inversion) only for 2D renders
                if structure_type == "2D":
                    image_html = apply_2d_styling_to_image(image_html)

                # Render in fixed container with border and transparent background
                with preview_placeholder.container():
                    st.markdown(
                        f'<div class="compound-preview-container">{image_html}</div>',
                        unsafe_allow_html=True
                    )
                # finalize_and_save_config(structure_type.lower())

            elif st.session_state.get("last_image_html"):
                # Show cached image in the same container
                cached_html = st.session_state.last_image_html
                # Apply 2D styling if this was a 2D render
                if st.session_state.get("structure_type") == "2D":
                    cached_html = apply_2d_styling_to_image(cached_html)

                with preview_placeholder.container():
                    st.markdown(
                        f'<div class="compound-preview-container">{cached_html}</div>',
                        unsafe_allow_html=True
                    )
            else:
                with preview_placeholder.container():
                    st.info(
                        "Enter a compound and adjust settings, then click 'Generate Now' or enable auto-update."
                    )
        elif st.session_state.get("last_image_html"):
            # Show cached image
            cached_html = st.session_state.last_image_html
            # Apply 2D styling if this was a 2D render
            if st.session_state.get("structure_type") == "2D":
                cached_html = apply_2d_styling_to_image(cached_html)

            with preview_placeholder.container():
                st.markdown(
                    f'<div class="compound-preview-container">{cached_html}</div>',
                    unsafe_allow_html=True
                )

    else:  # structure_type == "Protein"
        # Protein rendering section
        if protein_inputs:
            pdb_id, cartoon_cfg, ligand_cfg, canvas_cfg = protein_inputs

            # Generate button always visible at top
            if st.button("Generate Protein Structure", use_container_width=True, key="protein_gen_btn"):
                image_html = render_protein_structure_dynamic(pdb_id, cartoon_cfg, ligand_cfg, canvas_cfg)

            # Show success message and metrics if rendered
            if st.session_state.get("last_protein_image_html"):
                st.success(f"✓ Fetched {pdb_id}")

                # Display metrics (data above image)
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
                        st.metric("Has Ligand", "âœ“" if metadata.get("has_ligand", False) else "âœ—")

                # Display protein image
                st.markdown(
                    f'<div class="protein-preview-container">{st.session_state.last_protein_image_html}</div>',
                    unsafe_allow_html=True
                )
        else:
            st.info("Configure protein settings in the sidebar to render a structure.")

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
        file_ext = Path(file_name).suffix
        base_name = Path(file_name).stem

        # Initialize the input key if not present
        if "download_filename_input" not in st.session_state:
            st.session_state.download_filename_input = base_name

        def on_reset():
            """Reset to original compound-based filename with structure type"""
            # Get compound name and structure type
            compound = st.session_state.get("last_compound", "structure")
            structure_type = st.session_state.get("structure_type", "2D")

            # Construct original filename: "compound_name 2D" or "compound_name 3D"
            original_base = f"{compound} {structure_type}"

            # Reconstruct original filename
            original_filename = f"{original_base}{file_ext}"
            st.session_state.last_file_name = original_filename
            st.session_state.download_filename_input = original_base

        # Create three columns: download button | filename input | reset button
        col_download, col_rename, col_reset = st.columns([2, 1, 0.6], gap="small")

        with col_reset:
            st.button(
                "Reset",
                use_container_width=True,
                key="reset_filename_btn",
                on_click=on_reset
            )

        with col_rename:
            custom_base_name = st.text_input(
                "File name",
                value=st.session_state.download_filename_input,
                label_visibility="collapsed",
                placeholder="Enter filename...",
                key="download_filename_input"
            )
            clean_base = Path(custom_base_name).stem
            st.session_state.last_file_name = clean_base

        with col_download:
            st.download_button(
                f"Download {file_ext.upper().replace('.', '')}",
                file_data,
                file_name=st.session_state.last_file_name,
                mime=mime_type,
                use_container_width=True
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
            key="protein_download_btn"
        )


def main() -> None:
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()

    # Configure page
    configure_page()

    # Render sidebar and get settings
    compound, structure_type, auto_generate, protein_inputs = render_sidebar()

    if st.session_state.get("last_structure_type") != structure_type:
        st.session_state.last_structure_type = structure_type

    # Render main content
    render_main_content(compound, structure_type, auto_generate, protein_inputs)

    # Wikipedia boxes section (only for 2D/3D, not for Protein)
    if compound and structure_type != "Protein":
        render_wikipedia_metadata_section(compound, structure_type)

    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
    <strong>WikiMolGen</strong>, a chemical structure generator for Wikipedia & Wikimedia Commons | Wolren<br>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
