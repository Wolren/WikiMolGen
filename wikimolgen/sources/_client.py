"""
wikimolgen.sources._client - Shared HTTP client
================================================

Centralises the ``requests`` import and common HTTP utilities so that
every source module does not repeat the same lazy-import boilerplate.
"""

from __future__ import annotations

try:
    import requests as _requests
except ImportError:
    raise ImportError(
        "The 'requests' library is required for external source lookups. "
        "Install with: pip install requests"
    )

USER_AGENT = "WikiMolGen/0.1 (chemical structure generator)"
PUG_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"

# Re-export for convenience
Session = _requests.Session


def get_session() -> _requests.Session:
    """Return a pre-configured ``requests.Session``."""
    session = _requests.Session()
    session.headers.update({"User-Agent": USER_AGENT})
    return session


def make_headers(*, description: str = "chemical structure generator") -> dict[str, str]:
    """Return request headers with a descriptive User-Agent."""
    return {"User-Agent": f"WikiMolGen/0.1 ({description})"}


# Re-export so source modules can write:
#   from wikimolgen.sources._client import requests
requests = _requests
