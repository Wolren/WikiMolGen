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
    from wikimolgen.sources._client import make_headers, requests

    url = f"{DAILYMED_BASE}/spls.json?unii={unii}"
    resp = requests.get(
        url,
        headers=make_headers(description="dailymed fetcher"),
        timeout=timeout,
    )
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()
    spls = data.get("data", [])
    if spls and isinstance(spls, list):
        setid = spls[0].get("setid")
        if setid:
            return str(setid)
    return None
