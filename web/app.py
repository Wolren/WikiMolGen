"""
web/app.py
==========
Main Streamlit application for WikiMolGen web interface with ORIGINAL layout.
Matches the structure and feel of wiki_web_optimized.py exactly.

Usage:
    streamlit run web/app.py
"""

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
from template.themes_css import apply_theme

apply_theme()


# Render header of the main section
def render_header() -> None:
    """Render application header"""
    st.title("⌬ WikiMolGen")
    st.markdown("**Chemical structure generator for Wikipedia & Wikimedia Commons**")
    st.divider()


def render_sidebar() -> tuple:
    """
    Render complete sidebar with layout and structure.

    Returns
    -------
    tuple
        (compound: str, structure_type: str, auto_generate: bool)
    """
    with st.sidebar:
        st.markdown("<div class='sidebar-main-header'>🛠️ Configuration</div>", unsafe_allow_html=True)
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

        # Mode selector (2D/3D)
        structure_type = render_mode_selector()
        st.divider()

        # Mode-specific settings
        if structure_type == "2D":
            render_2d_settings()
        else:
            render_3d_settings()
            st.divider()

            render_canvas_settings()
            render_rendering_settings()
            render_lighting_settings()
            render_effects_settings()

    return compound, structure_type, auto_generate


def render_main_content(compound: str, structure_type: str, auto_generate: bool) -> None:
    """
    Render main content area.

    Parameters
    ----------
    compound : str
        Compound identifier
    structure_type : str
        "2D" or "3D"
    auto_generate : bool
        Whether auto-generate is enabled
    """
    # Manual generation button
    render_generate_button(auto_generate)

    # Placeholder for the structure image
    preview_placeholder = st.empty()

    # Check if image should be rendered at the momement
    should_render = (
            auto_generate or
            st.session_state.get("manual_generate", False) or
            st.session_state.get("last_compound") != compound
    )

    if should_render and compound:
        # Clear manual trigger
        st.session_state.manual_generate = False

        # Render structure
        with st.spinner("Generating structure..."):
            image_html = render_structure_dynamic(compound, structure_type)

        if image_html:
            preview_placeholder.markdown(image_html, unsafe_allow_html=True)
    elif st.session_state.get("last_image_html"):
        # Show cached image
        preview_placeholder.markdown(
            st.session_state.last_image_html,
            unsafe_allow_html=True
        )
    else:
        preview_placeholder.info(
            "Enter a compound and adjust settings, then click 'Generate Now' or enable auto-update.")

    st.divider()

    render_download_section()


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
            """Reset both filename and input to original values"""
            st.session_state.last_file_name = file_name
            st.session_state.download_filename_input = base_name

        # Create three columns: download button | filename input | reset button
        col_download, col_rename, col_reset = st.columns([2, 1, 0.6], gap="small")

        with col_reset:
            st.button("Reset", use_container_width=True, key="reset_filename_btn", on_click=on_reset)

        with col_rename:
            custom_base_name = st.text_input(
                "File name",
                value=st.session_state.download_filename_input,
                label_visibility="collapsed",
                placeholder="Enter filename...",
                key="download_filename_input"
            )

            clean_base = Path(custom_base_name).stem
            full_filename = f"{clean_base}{file_ext}"
            st.session_state.last_file_name = full_filename

        with col_download:
            st.download_button(
                f"💾 Download {file_ext.upper().replace('.', '')}",
                file_data,
                file_name=st.session_state.last_file_name,
                mime=mime_type,
                use_container_width=True
            )


def main() -> None:
    """Main application entry point"""
    # Initialize session state
    initialize_session_state()

    # Configure page
    configure_page()

    # Render header
    render_header()

    # Render sidebar and get settings
    compound, structure_type, auto_generate = render_sidebar()

    # Render main content
    render_main_content(compound, structure_type, auto_generate)

    # Wikipedia boxes section
    if compound:
        render_wikipedia_metadata_section(compound, structure_type)

    # Footer
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
    <strong>WikiMolGen</strong> | Wolren<br>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
