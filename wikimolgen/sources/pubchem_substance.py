"""
wikimolgen.sources.pubchem_substance
=====================================

Client for PubChem PUG REST SID endpoint.

Fetches PubChem Substance IDs (SIDs) associated with a PubChem Compound ID
(CID), for the ``PubChemSubstance`` field in Wikipedia's Infobox drug.

No API key required.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

from wikimolgen.sources._client import PUG_BASE


def fetch_substances(
    pubchem_cid: int | str,
    timeout: float = 10,
) -> dict[str, Any]:
    """Fetch PubChem Substance IDs (SIDs) for a compound.

    Parameters
    ----------
    pubchem_cid
        PubChem compound identifier (numeric).
    timeout
        HTTP request timeout in seconds.

    Returns
    -------
    dict
        Contains ``pubchem_substance`` (the first SID) and
        ``pubchem_substances`` (all SIDs), or an empty dict if none
        are found.

    Raises
    ------
    ImportError
        If ``requests`` is not installed.
    requests.RequestException
        On network or API errors.
    """
    from wikimolgen.sources._client import make_headers, requests

    cid = str(int(pubchem_cid))
    url = f"{PUG_BASE}/cid/{cid}/sids/JSON"

    resp = requests.get(
        url,
        headers=make_headers(description="substance fetcher"),
        timeout=timeout,
    )
    resp.raise_for_status()
    data: dict[str, Any] = resp.json()

    result: dict[str, Any] = {}
    id_list = data.get("IdentifierList", {})
    sids = id_list.get("SID", [])
    if sids:
        result["pubchem_substance"] = str(sids[0])
        result["pubchem_substances"] = [str(s) for s in sids]

    return result
