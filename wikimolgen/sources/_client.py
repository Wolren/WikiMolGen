"""wikimolgen.sources._client - Shared HTTP client
================================================

Centralises the ``requests`` import and common HTTP utilities so that
every source module does not repeat the same lazy-import boilerplate.
"""

from __future__ import annotations

import time
from typing import Any

try:
    import requests as _requests
except ImportError as e:
    raise ImportError(
        "The 'requests' library is required for external source lookups. "
        "Install with: pip install requests",
    ) from e

USER_AGENT = "WikiMolGen/0.1 (chemical structure generator)"
PUG_BASE = "https://pubchem.ncbi.nlm.nih.gov/rest/pug/compound"

# HTTP statuses that are transient and worth retrying: rate limiting (429)
# and server-side errors (5xx).  404/400 are definitive and never retried.
RETRYABLE_STATUS: frozenset[int] = frozenset({429, 500, 502, 503, 504})

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


def get_with_retry(
    url: str,
    *,
    params: dict[str, Any] | None = None,
    headers: dict[str, Any] | None = None,
    timeout: float = 10,
    attempts: int = 3,
    backoff: float = 0.5,
) -> _requests.Response:
    """GET with retry on transient failures.

    Retries on retryable HTTP statuses (``429``, ``5xx``) and on network
    exceptions, sleeping ``backoff * 2**attempt`` seconds between tries.
    Returns the first non-retryable response (e.g. ``404``) immediately;
    raises the last exception when attempts are exhausted.

    Parameters
    ----------
    attempts
        Maximum number of GET attempts (default 3).
    backoff
        Base sleep in seconds before the first retry (doubles per attempt).
    """
    last_exc: Exception | None = None
    for attempt in range(attempts):
        try:
            resp = _requests.get(url, params=params, headers=headers, timeout=timeout)
            if resp.status_code in RETRYABLE_STATUS and attempt < attempts - 1:
                time.sleep(backoff * (2**attempt))
                continue
            return resp
        except _requests.RequestException as e:
            last_exc = e
            if attempt < attempts - 1:
                time.sleep(backoff * (2**attempt))
                continue
    assert last_exc is not None
    raise last_exc


requests = _requests
