import logging
from pathlib import Path

logger = logging.getLogger(__name__)

_FALLBACK_CSS = """
<style>
:root {
    --bg-primary: #101418; --bg-secondary: #1c2024; --bg-tertiary: #272b2f;
    --text-primary: #eaecf0; --text-secondary: #a2a9b1; --text-muted: #72777d;
    --accent-blue: #6f8cff; --accent-blue-light: #8aa7ff;
    --border-color: #404348; --border-light: #333639;
    --link-color: #6f8cff; --link-hover: #8aa7ff;
    --button-primary: #6f8cff; --button-primary-hover: #8aa7ff;
    --code-bg: #1c2024; --code-text: #eaecf0;
}
@media (prefers-color-scheme: light) {
    :root {
        --bg-primary: #ffffff; --bg-secondary: #f8f9fa; --bg-tertiary: #eaecf0;
        --text-primary: #202122; --text-secondary: #54595d; --text-muted: #72777d;
        --accent-blue: #3366cc; --accent-blue-light: #447ff5;
        --border-color: #c8ccd1; --border-light: #eaecf0;
        --link-color: #3366cc; --link-hover: #447ff5;
        --button-primary: #3366cc; --button-primary-hover: #447ff5;
        --code-bg: #f8f9fa; --code-text: #202122;
    }
}
* { color-scheme: dark; }
@media (prefers-color-scheme: light) { * { color-scheme: light; } }
.stApp { background-color: var(--bg-primary); }
[data-testid="stSidebar"] { background-color: var(--bg-secondary); border-right: 1px solid var(--border-color); }
[data-testid="stSidebar"] * { color: var(--text-primary) !important; }
h1, h2, h3 { color: var(--text-primary) !important; font-weight: 600 !important; }
[data-testid="stSidebar"] h3, [data-testid="stSidebar"] h2 { color: var(--accent-blue) !important; font-weight: 700 !important; }
.stButton>button { background-color: var(--button-primary) !important; border: none !important; font-weight: 600 !important; border-radius: 4px !important; }
.stButton>button:hover { background-color: var(--button-primary-hover) !important; }
.streamlit-expanderHeader { background-color: var(--bg-secondary) !important; border: 1px solid var(--border-color) !important; border-radius: 4px !important; }
.stSelectbox>div>div { background-color: var(--bg-primary) !important; border: 1px solid var(--border-color) !important; }
.compound-preview-image[data-type="2D"] { max-width: 100%; filter: invert(1) hue-rotate(180deg); }
@media (prefers-color-scheme: light) { .compound-preview-image[data-type="2D"] { filter: none; } }
.compound-preview-image[data-type="3D"] { filter: none; }
a { color: var(--link-color) !important; }
a:hover { color: var(--link-hover) !important; }
</style>
"""


def _load_css() -> str:
    css_path = Path(__file__).parent / "wiki_theme.css"
    try:
        with open(css_path, encoding="utf-8") as f:
            css = f.read()
        return f"<style>\n{css}\n</style>"
    except FileNotFoundError:
        logger.warning("wiki_theme.css not found at %s, using fallback", css_path)
        return _FALLBACK_CSS


def apply_theme() -> None:
    import streamlit as st
    st.markdown(_load_css(), unsafe_allow_html=True)
