"""
Dark Forest Theme for WikiMolGen
================================
Streamlit CSS styling module for consistent theming across the application.
"""

DARK_FOREST_THEME_CSS = """
<style>
    /* Dark forest theme */
    :root {
        --primary-bg: #1a2421;
        --secondary-bg: #243029;
        --tertiary-bg: #2d3a32;
        --accent-green: #4a7c59;
        --accent-light: #6b9b7a;
        --text-primary: #e8f4ea;
        --text-secondary: #b8d4be;
        --border-color: #3d4f44;
    }

    /* Main background */
    .stApp {
        background-color: var(--primary-bg);
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background-color: var(--secondary-bg);
        border-right: 2px solid var(--border-color);
    }

    [data-testid="stSidebar"] * {
        color: var(--text-primary) !important;
    }

    /* Headers */
    h1, h2, h3 {
        color: var(--text-primary) !important;
        font-weight: 600 !important;
    }

    /* Compact sidebar styling */
    [data-testid="stSidebar"] .stMarkdown {
        padding: 0.15rem 0;
    }

    [data-testid="stSidebar"] h3, [data-testid="stSidebar"] h2 {
        font-size: 1.05rem !important;
        margin-bottom: 0.2rem !important;
        margin-top: 0.4rem !important;
        color: var(--accent-light) !important;
        font-weight: 700 !important;
    }

    /* Main config header */
    .sidebar-main-header {
        font-size: 1.45rem !important;
        font-weight: 700 !important;
        color: var(--text-primary) !important;
        margin-top: -1.2rem !important;
        margin-bottom: 0.55rem !important;
        padding-bottom: 0 !important;
        padding-top: 0 !important;
        letter-spacing: 0.03em;
        line-height: 1.16 !important;
    }

    /* Sidebar container padding */
    [data-testid="stSidebar"] .block-container {
        padding-top: 0.4rem !important;
    }

    /* Make "Compound:" label bigger */
    [data-testid="stSidebar"] label[data-baseweb="label"]:first-of-type {
        font-size: 1.12rem !important;
        font-weight: 700 !important;
        color: var(--accent-light) !important;
        margin-bottom: 0.3rem !important;
    }

    /* Input fields */
    .stTextInput input, .stNumberInput input {
        background-color: var(--tertiary-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--border-color) !important;
    }

    /* Sliders - more compact */
    .stSlider {
        padding: 0.3rem 0 !important;
    }

    /* Radio buttons - more compact */
    [data-testid="stSidebar"] .stRadio {
        margin-top: 0.3rem !important;
        margin-bottom: -0.6rem !important;
        padding: 0 !important;
    }

    /* Checkboxes - more compact */
    .stCheckbox {
        margin-top: 0.7rem !important;
        margin-bottom: -0.3rem !important;
    }

    /* Dividers - thinner and more compact */
    [data-testid="stSidebar"] hr {
        margin-top: 0.5rem !important;
        margin-bottom: 0.5rem !important;
        border-color: var(--border-color) !important;
        opacity: 0.4;
    }

    /* Buttons */
    .stButton>button {
        background-color: var(--accent-green) !important;
        color: var(--text-primary) !important;
        border: none !important;
        font-weight: 600 !important;
        border-radius: 6px !important;
        padding: 0.6rem 1rem !important;
    }

    .stButton>button:hover {
        background-color: var(--accent-light) !important;
    }

    /* Download buttons */
    .stDownloadButton>button {
        background-color: var(--tertiary-bg) !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--accent-green) !important;
    }

    /* Expanders */
    .streamlit-expanderHeader {
        background-color: var(--tertiary-bg) !important;
        color: var(--text-secondary) !important;
        border-radius: 4px !important;
        font-size: 0.88rem !important;
        padding: 0.35rem 0.7rem !important;
    }

    /* Success/Info boxes */
    .stSuccess {
        background-color: #2d4a35 !important;
        color: var(--text-primary) !important;
        border: 1px solid var(--accent-green) !important;
    }

    .stInfo {
        background-color: var(--tertiary-bg) !important;
        color: var(--text-secondary) !important;
        border: 1px solid var(--border-color) !important;
    }

    /* Code blocks */
    code {
        background-color: var(--tertiary-bg) !important;
        color: #8fd4a0 !important;
    }

    /* Dividers */
    hr {
        border-color: var(--border-color) !important;
    }

    /* Select boxes */
    .stSelectbox>div>div {
        background-color: var(--tertiary-bg) !important;
        color: var(--text-primary) !important;
    }

    .sidebar-section-header {
        font-size: 1.32rem !important;
        font-weight: 800 !important;
        color: var(--accent-light) !important;
        margin-bottom: 0.5rem !important;
        line-height: 1.16 !important;
    }

</style>
"""


def apply_theme(theme_name: str = DARK_FOREST_THEME_CSS):
    """Apply the dark forest theme to the Streamlit app."""
    import streamlit as st
    st.markdown(theme_name, unsafe_allow_html=True)
