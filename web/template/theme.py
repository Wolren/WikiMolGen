"""
web/template/theme.py
====================
Inject WikiMolGen's custom CSS.

Theme switching is delegated to Streamlit's built-in Settings menu (top
right). When the user picks Dark / Light / Use system setting, Streamlit
writes its own theme variables (e.g. ``--background-color``,
``--text-color``, ``--primary-color``) directly on the ``.stApp`` element.
Our CSS re-themes every widget on top of those values.

Streamlit **does not** expose a stable class or data attribute that we
can hook for "light vs dark". So a tiny script watches the actual CSS
variable on ``.stApp`` and toggles a ``wiki-light`` class on the ``<html>``
element. Our CSS then reacts to ``html.wiki-light``.

Why this works in practice:
- The script runs once per re-render, sampling the current background
  luminance from ``.stApp``. If the background is light (luma > 0.5),
  ``html.wiki-light`` is added; otherwise removed.
- MutationObservers re-evaluate whenever Streamlit mutates the theme
  (e.g. user picks a different theme from the menu).
- The script is idempotent and cheap (one rAF, one luma calc).
"""

import logging
from pathlib import Path

logger = logging.getLogger(__name__)


# Re-evaluate the light/dark marker whenever Streamlit mutates the page
# (e.g. theme switch, rerun, navigation). The script samples the
# *computed* ``background-color`` of ``.stApp`` and toggles a
# ``wiki-light`` class on ``<html>``. This is the only reliable signal
# across Streamlit versions because the exact CSS variable names and
# data attributes are not part of any public API contract.
_THEME_DETECT_SCRIPT = """
<script>
(function () {
  if (window.__wikiThemeDetectInstalled) return;
  window.__wikiThemeDetectInstalled = true;

  function parseColor(str) {
    if (!str) return null;
    str = str.trim();
    var m = str.match(/#([0-9a-f]{6})/i) || str.match(/#([0-9a-f]{3})/i);
    if (m) {
      var hex = m[1];
      if (hex.length === 3) hex = hex.split("").map(function (c) { return c + c; }).join("");
      return [
        parseInt(hex.substr(0, 2), 16),
        parseInt(hex.substr(2, 2), 16),
        parseInt(hex.substr(4, 2), 16),
      ];
    }
    var rgb = str.match(/rgba?\\(\\s*(\\d+)\\s*,\\s*(\\d+)\\s*,\\s*(\\d+)/);
    if (rgb) return [+rgb[1], +rgb[2], +rgb[3]];
    return null;
  }

  function isLight() {
    var app = document.querySelector(".stApp");
    if (!app) return false;
    var rgb = parseColor(getComputedStyle(app).backgroundColor);
    if (!rgb) return false;
    var luma = 0.2126 * rgb[0] + 0.7152 * rgb[1] + 0.0722 * rgb[2];
    return luma > 128;
  }

  function apply() {
    var html = document.documentElement;
    if (isLight()) html.classList.add("wiki-light");
    else html.classList.remove("wiki-light");
  }

  apply();
  // Re-apply whenever the page mutates (rerun, theme switch, navigation).
  // The cost is one rAF + one luma calc; trivial.
  function loop() {
    apply();
    requestAnimationFrame(loop);
  }
  requestAnimationFrame(loop);
})();
</script>
"""


def _load_css() -> str:
    css_path = Path(__file__).parent / "wiki_theme.css"
    try:
        with open(css_path, encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("wiki_theme.css not found at %s", css_path)
        return _fallback_css()


def _fallback_css() -> str:
    """Inline CSS used when wiki_theme.css is missing from the install.

    Mirrors the structure of the real file so the app degrades gracefully.
    """
    return """:root {
    --bg-primary: #101418;
    --bg-secondary: #1c2024;
    --bg-tertiary: #272b2f;
    --text-primary: #eaecf0;
    --text-secondary: #a2a9b1;
    --text-muted: #72777d;
    --accent-blue: #6f8cff;
    --accent-blue-light: #8aa7ff;
    --accent-blue-bg: #1a2332;
    --border-color: #404348;
    --border-light: #333639;
    --link-color: #6f8cff;
    --link-hover: #8aa7ff;
    --success-bg: #0a2a1f;
    --success-border: #00af89;
    --info-bg: #1a2332;
    --info-border: #6f8cff;
    --warning-bg: #2a1f0a;
    --warning-border: #fc3;
    --error-bg: #2a0a0a;
    --error-border: #e33;
    --button-primary: #6f8cff;
    --button-primary-hover: #8aa7ff;
    --button-secondary: #272b2f;
    --button-secondary-border: #404348;
    --code-bg: #1c2024;
    --code-text: #eaecf0;
    --header-bg: #101418;
    --header-border: #404348;
}
html.wiki-light {
    --bg-primary: #ffffff;
    --bg-secondary: #f8f9fa;
    --bg-tertiary: #eaecf0;
    --text-primary: #202122;
    --text-secondary: #54595d;
    --text-muted: #72777d;
    --accent-blue: #3366cc;
    --accent-blue-light: #447ff5;
    --accent-blue-bg: #eaf3ff;
    --border-color: #c8ccd1;
    --border-light: #eaecf0;
    --link-color: #3366cc;
    --link-hover: #447ff5;
    --success-bg: #d5fdf4;
    --success-border: #00af89;
    --info-bg: #eaf3ff;
    --info-border: #3366cc;
    --warning-bg: #fef6e7;
    --warning-border: #fc3;
    --error-bg: #fee7e6;
    --error-border: #e33;
    --button-primary: #3366cc;
    --button-primary-hover: #447ff5;
    --button-secondary: #ffffff;
    --button-secondary-border: #a2a9b1;
    --code-bg: #f8f9fa;
    --code-text: #202122;
    --header-bg: #f8f9fa;
    --header-border: #c8ccd1;
}
.stApp { background-color: var(--bg-primary); }
[data-testid="stHeader"] { background-color: var(--header-bg) !important; }
"""


def apply_theme() -> None:
    """Inject the WikiMolGen custom stylesheet and theme-detection script.

    Must be called **after** :func:`streamlit.set_page_config`. The CSS
    defines semantic variables on ``:root`` (dark) and overrides them
    under ``html.wiki-light``. The detection script toggles
    ``html.wiki-light`` based on the active Streamlit theme, sampling
    ``.stApp``'s ``--background-color`` and computing its luminance.
    """
    import streamlit as st

    st.markdown(f"<style>\n{_load_css()}\n</style>", unsafe_allow_html=True)
    st.markdown(_THEME_DETECT_SCRIPT, unsafe_allow_html=True)
