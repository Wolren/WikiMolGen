"""
wikimolgen.sources.unichem
==========================

Client for the `UniChem REST API <https://www.ebi.ac.uk/unichem/api/docs>`_.

Takes a PubChem CID and returns cross-references to other chemical
databases (ChEMBL, ChEBI, DrugBank, KEGG, ChemSpider, UNII, etc.)
in a single request.

No API key required — free for reasonable use.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

BASE_URL = "https://www.ebi.ac.uk/unichem/api/v1"

# UniChem source IDs → our internal key names
_SOURCE_MAP: dict[int, str] = {
    1: "chembl_id",
    2: "chebi_id",
    3: "drugbank_id",
    4: "kegg_id",
    5: "chemspider_id",
    21: "wikidata_qid",
    22: "unii",
}


def resolve_unichem(pubchem_cid: int | str, timeout: float = 10) -> dict[str, Any]:
    """Resolve a PubChem CID against UniChem to get cross-reference IDs.

    Parameters
    ----------
    pubchem_cid
        PubChem compound identifier (numeric).
    timeout
        HTTP request timeout in seconds.

    Returns
    -------
    dict
        Mapping of internal key names to identifier values.
        Only keys that were successfully resolved are included.

    Raises
    ------
    ImportError
        If ``requests`` is not installed.
    requests.RequestException
        On network or API errors.
    """
    try:
        import requests
    except ImportError:
        raise ImportError(
            "The 'requests' library is required for external source lookups. "
            "Install with: pip install requests"
        )

    cid = str(int(pubchem_cid))
    url = f"{BASE_URL}/compound/{cid}/sources/1,2,3,4,5,21,22"

    resp = requests.get(
        url,
        headers={"User-Agent": "WikiMolGen/0.1 (chemical structure resolver)"},
        timeout=timeout,
    )

    if resp.status_code == 404:
        logger.info("PubChem CID %s not found in UniChem", cid)
        return {}

    resp.raise_for_status()
    data = resp.json()

    result: dict[str, Any] = {}
    for entry in data.get("compound", {}).get("unichem", []):
        src_id = entry.get("source_id")
        src_compound_id = entry.get("source_compound_id")
        if src_id and src_compound_id:
            key = _SOURCE_MAP.get(src_id)
            if key:
                result[key] = src_compound_id

    return result
