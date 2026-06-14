import time
from pathlib import Path

import streamlit as st

_JS_DETECT = (
    '<img src="x?%d" onerror="'
    "var d=document,b=d.body;"
    "requestAnimationFrame(function(){"
    "var c=getComputedStyle(b).backgroundColor,m=c.match(/\\d+/g);"
    "if(m&&m.length>=3){"
    "var l=(0.299*m[0]+0.587*m[1]+0.114*m[2])/255;"
    "b.classList.toggle('wiki-light',l>0.455);"
    "}"
    "});"
    '" style="display:none">'
)


def apply_theme() -> None:
    """Inject custom CSS and theme-detection JS.

    Must be called **after** :func:`streamlit.set_page_config`.
    ``wiki_theme.css`` contains all ``:root`` (dark) and
    ``body.wiki-light`` (light) CSS variable definitions, plus
    structural rules for custom elements (sidebar, file uploader,
    previews, icons, footer).

    The ``<img onerror>`` snippet triggers a JavaScript theme
    check each rerun.  It reads the computed ``body`` background-
    color, calculates luminance, and toggles ``body.wiki-light``.
    The timestamp in the ``src`` forces React to replace the DOM
    node so the event fires on every rerun.
    """
    css_path = Path(__file__).parent / "wiki_theme.css"
    try:
        with open(css_path, encoding="utf-8") as f:
            css = f.read()
    except FileNotFoundError:
        css = ""

    ts = int(time.time() * 1000)
    st.markdown(
        f"<style>{css}</style>{_JS_DETECT % ts}",
        unsafe_allow_html=True,
    )
