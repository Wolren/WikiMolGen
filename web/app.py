"""
web/app.py
==========
Main Streamlit application for WikiMolGen web interface with ORIGINAL layout.
Matches the structure and feel of wiki_web_optimized.py exactly.

Usage:
    streamlit run web/app.py
"""

import streamlit as st
from pathlib import Path

# Import web components
from web.session_state import initialize_session_state
from web.ui_components import (
    render_compound_input,
    render_original_template_manager,
    render_mode_selector,
    render_original_2d_settings,
    render_original_3d_settings,
    render_original_canvas_settings,
    render_original_rendering_settings,
    render_original_lighting_settings,
    render_original_effects_settings,
    render_auto_generate_checkbox,
    render_generate_button,
)
from web.rendering import render_structure_dynamic
from web.wikipedia_boxes import render_wikipedia_metadata_section

# Optional theme support
try:
    from theme import apply_theme
    THEME_AVAILABLE = True
except ImportError:
    THEME_AVAILABLE = False


def configure_page() -> None:
    """Configure Streamlit page settings - ORIGINAL."""
    st.set_page_config(
        page_title="WikiMolGen",
        page_icon="media/wikimolgen_logo.png",
        layout="wide",
        initial_sidebar_state="expanded"
    )

    # Apply custom theme if available - ORIGINAL behavior
    if THEME_AVAILABLE:
        try:
            apply_theme()
        except:
            pass  # Silently fail like original


def render_header() -> None:
    """Render application header - ORIGINAL."""
    st.title("⌬ WikiMolGen")
    st.markdown("**Chemical structure generator for Wikipedia & Wikimedia Commons**")
    st.divider()


def render_original_sidebar() -> tuple:
    """
    Render complete sidebar with ORIGINAL layout and structure.

    Returns
    -------
    tuple
        (compound: str, structure_type: str, auto_generate: bool)
    """
    with st.sidebar:
        st.markdown("<div class='sidebar-main-header'>🛠️ Configuration</div>", unsafe_allow_html=True)
        st.divider()

        # Compound input - ORIGINAL
        compound = render_compound_input()
        st.divider()

        # Template management - ORIGINAL
        render_original_template_manager()
        st.divider()

        # Auto-generate toggle - ORIGINAL position
        auto_generate = render_auto_generate_checkbox()
        st.divider()

        # Mode selector (2D/3D) - ORIGINAL
        structure_type = render_mode_selector()
        st.divider()

        # Mode-specific settings - ORIGINAL structure
        if structure_type == "2D":
            render_original_2d_settings()
        else:  # 3D
            render_original_3d_settings()
            st.divider()

            # 3D specific sections - ORIGINAL order
            render_original_canvas_settings()
            render_original_rendering_settings()
            render_original_lighting_settings()
            render_original_effects_settings()

    return compound, structure_type, auto_generate


def render_main_content(compound: str, structure_type: str, auto_generate: bool) -> None:
    """
    Render main content area - ORIGINAL layout.

    Parameters
    ----------
    compound : str
        Compound identifier
    structure_type : str
        "2D" or "3D"
    auto_generate : bool
        Whether auto-generate is enabled
    """
    # Manual generate button - ORIGINAL position
    render_generate_button(auto_generate)

    # Interactive 3D info - ORIGINAL CSS (ready for future enhancements)
    if structure_type == "3D" and not st.session_state.get("auto_orient_3d", True):
        st.markdown("""
        <style>
        .structure-preview {
            cursor: grab;
            user-select: none;
        }
        .structure-preview:active {
            cursor: grabbing;
        }
        </style>
        """, unsafe_allow_html=True)

    # Preview area - ORIGINAL structure
    preview_placeholder = st.empty()

    # Check if we should render - ORIGINAL logic
    should_render = (
        auto_generate or
        st.session_state.get("manual_generate", False) or
        st.session_state.get("last_compound") != compound
    )

    if should_render and compound:
        # Clear manual trigger
        st.session_state.manual_generate = False

        # Render structure
        with st.spinner("🧬 Generating structure..."):
            image_html = render_structure_dynamic(compound, structure_type)

        if image_html:
            preview_placeholder.markdown(image_html, unsafe_allow_html=True)
    elif st.session_state.get("last_image_html"):
        # Show cached image - ORIGINAL behavior
        preview_placeholder.markdown(
            st.session_state.last_image_html,
            unsafe_allow_html=True
        )
    else:
        # ORIGINAL info message
        preview_placeholder.info("👆 Enter a compound and adjust settings, then click 'Generate Now' or enable auto-update.")

    st.divider()

    # Download section - ORIGINAL with fixed rendering
    render_download_section()


def render_download_section() -> None:
    """Render download buttons - ORIGINAL style with proper file handling."""
    # Only show download if we have file data in session
    if st.session_state.get("last_file_data"):
        file_data = st.session_state.last_file_data
        file_name = st.session_state.get("last_file_name", "structure.png")
        mime_type = st.session_state.get("last_file_mime", "image/png")

        # Determine file extension from name
        file_ext = Path(file_name).suffix.upper().replace(".", "")

        st.download_button(
            f"💾 Download {file_ext}",
            file_data,
            file_name=file_name,
            mime=mime_type,
            use_container_width=True
        )


def main() -> None:
    """Main application entry point - ORIGINAL flow."""
    # Initialize session state
    initialize_session_state()

    # Configure page
    configure_page()

    # Render header
    render_header()

    # Render sidebar and get settings - ORIGINAL
    compound, structure_type, auto_generate = render_original_sidebar()

    # Render main content - ORIGINAL
    render_main_content(compound, structure_type, auto_generate)

    # Wikipedia boxes section - ORIGINAL position and style
    if compound:
        render_wikipedia_metadata_section(compound, structure_type)

    # Footer - ORIGINAL
    st.divider()
    st.markdown("""
    <div style='text-align: center; color: #666; padding: 20px;'>
    <strong>WikiMolGen</strong> | Molecular rendering for Wikipedia<br>
    </div>
    """, unsafe_allow_html=True)


if __name__ == "__main__":
    main()
