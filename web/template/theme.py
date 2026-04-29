from pathlib import Path


def _load_css() -> str:
    css_path = Path(__file__).parent / "wiki_theme.css"
    with open(css_path) as f:
        css = f.read()
    return f"<style>\n{css}\n</style>"


def apply_theme() -> None:
    import streamlit as st
    st.markdown(_load_css(), unsafe_allow_html=True)
