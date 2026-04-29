import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_LIGHT_OVERRIDE = """
<style>
:root {
    --bg-primary: #ffffff !important;
    --bg-secondary: #f8f9fa !important;
    --bg-tertiary: #eaecf0 !important;
    --text-primary: #202122 !important;
    --text-secondary: #54595d !important;
    --text-muted: #72777d !important;
    --accent-blue: #3366cc !important;
    --accent-blue-light: #447ff5 !important;
    --accent-blue-bg: #eaf3ff !important;
    --border-color: #c8ccd1 !important;
    --border-light: #eaecf0 !important;
    --link-color: #3366cc !important;
    --link-hover: #447ff5 !important;
    --success-bg: #d5fdf4 !important;
    --success-border: #00af89 !important;
    --info-bg: #eaf3ff !important;
    --info-border: #3366cc !important;
    --warning-bg: #fef6e7 !important;
    --warning-border: #fc3 !important;
    --error-bg: #fee7e6 !important;
    --error-border: #e33 !important;
    --button-primary: #3366cc !important;
    --button-primary-hover: #447ff5 !important;
    --button-secondary: #ffffff !important;
    --button-secondary-border: #a2a9b1 !important;
    --code-bg: #f8f9fa !important;
    --code-text: #202122 !important;
    --header-bg: #f8f9fa !important;
    --header-border: #c8ccd1 !important;
}
.compound-preview-image[data-type="2D"] { filter: none !important; }
</style>
"""


def _load_css() -> str:
    css_path = Path(__file__).parent / "wiki_theme.css"
    try:
        with open(css_path, encoding="utf-8") as f:
            return f"<style>\n{f.read()}\n</style>"
    except FileNotFoundError:
        logger.warning("wiki_theme.css not found at %s", css_path)
        return _fallback_css()


def _fallback_css() -> str:
    return """<style>
:root {
    --bg-primary: #101418; --bg-secondary: #1c2024; --bg-tertiary: #272b2f;
    --text-primary: #eaecf0; --text-secondary: #a2a9b1; --text-muted: #72777d;
    --accent-blue: #6f8cff; --accent-blue-light: #8aa7ff;
    --border-color: #404348; --border-light: #333639;
    --button-primary: #6f8cff; --button-primary-hover: #8aa7ff;
    --code-bg: #1c2024; --code-text: #eaecf0;
    --header-bg: #101418; --header-border: #404348;
}
.stApp { background-color: var(--bg-primary); }
header, [data-testid="stHeader"] { background-color: var(--header-bg) !important; border-bottom: 1px solid var(--header-border) !important; }
[data-testid="stToolbar"], [data-testid="stDecoration"] { background-color: var(--header-bg) !important; }
[data-testid="stToolbar"] button { color: var(--text-primary) !important; }
[data-testid="stSidebar"] { background-color: var(--bg-secondary); border-right: 1px solid var(--border-color); }
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
h1, h2, h3 { color: var(--text-primary) !important; font-weight: 600 !important; }
.stButton>button { background-color: var(--button-primary) !important; border: none !important; font-weight: 600 !important; border-radius: 4px !important; color: #ffffff !important; }
.stButton>button:hover { background-color: var(--button-primary-hover) !important; }
.streamlit-expanderHeader { background-color: var(--bg-secondary) !important; border: 1px solid var(--border-color) !important; border-radius: 4px !important; }
.stSelectbox>div>div { background-color: var(--bg-primary) !important; border: 1px solid var(--border-color) !important; }
.compound-preview-image[data-type="2D"] { max-width: 100%; filter: invert(1) hue-rotate(180deg); }
.compound-preview-image[data-type="3D"] { filter: none; }
a { color: var(--link-color) !important; }
</style>"""


def apply_theme() -> None:
    import streamlit as st
    st.markdown(_load_css(), unsafe_allow_html=True)
    if st.session_state.get("wiki_theme") == "Light":
        st.markdown(_LIGHT_OVERRIDE, unsafe_allow_html=True)
