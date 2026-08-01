"""
wikimolgen.sources.dailymed
============================

Client for the `DailyMed <https://dailymed.nlm.nih.gov/>`_ REST API.

Retrieves the SPL ``setid`` for a drug product by UNII code — this maps
directly to the ``DailyMedID`` field in Wikipedia's Infobox drug template.

No API key required.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

DAILYMED_BASE = "https://dailymed.nlm.nih.gov/dailymed/services/v2"


def fetch_dailymed_id(
    unii: str,
    timeout: float = 10,
) -> str | None:
    """Look up the DailyMed SPL *setid* (DailyMedID) for a given UNII code.

    Parameters
    ----------
    unii
        The UNII (Unique Ingredient Identifier) code, e.g. ``"R16CO5Y76E"``.
    timeout
        HTTP request timeout in seconds.

    Returns
    -------
    str or None
        The SPL ``setid`` (a UUID string), or ``None`` if no match is found.

    Raises
    ------
    ImportError
        If ``requests`` is not installed.
    requests.RequestException
        On network or API errors.
    """
    from wikimolgen.sources._client import get_with_retry, make_headers
    from wikimolgen.validation import is_valid_setid, is_valid_unii

    # Format-check the UNII before hitting the API: a malformed code is a
    # caller error, not a lookup miss.
    if not is_valid_unii(unii):
        logger.warning("Skipping DailyMed lookup: invalid UNII format %r", unii)
        return None

    url = f"{DAILYMED_BASE}/spls.json?unii={unii}"
    resp = get_with_retry(
        url,
        headers=make_headers(description="dailymed fetcher"),
        timeout=timeout,
    )
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    spls = data.get("data", [])
    if spls and isinstance(spls, list):
        setid = spls[0].get("setid")
        # The search is scoped server-side by UNII, but the returned setid
        # must still be a well-formed UUID before we propagate it.
        if setid and is_valid_setid(str(setid)):
            return str(setid)
        logger.warning("DailyMed returned malformed setid for UNII %s: %r", unii, setid)
    return None
