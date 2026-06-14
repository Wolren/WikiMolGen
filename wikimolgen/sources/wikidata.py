"""
wikimolgen.sources.wikidata
============================

Client for the `Wikidata SPARQL Query Service
<https://query.wikidata.org/>`_.

Takes a PubChem CID and returns the Wikidata QID, English Wikipedia
article title, and other properties via SPARQL.

No API key required — free with a 60-second query timeout.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

SPARQL_ENDPOINT = "https://query.wikidata.org/sparql"

_WIKIDATA_QUERY = """\
SELECT ?compound ?qid ?wikipedia ?chembl_id ?chebi_id ?drugbank_id ?kegg_id ?cas_number WHERE {{
  ?compound wdt:P662 "{cid}" .
  BIND(STRAFTER(STR(?compound), "http://www.wikidata.org/entity/") AS ?qid)
  OPTIONAL {{
    ?wikipedia schema:about ?compound ;
              schema:isPartOf <https://en.wikipedia.org/> .
  }}
  OPTIONAL {{ ?compound wdt:P592 ?chembl_id . }}
  OPTIONAL {{ ?compound wdt:P683 ?chebi_id . }}
  OPTIONAL {{ ?compound wdt:P715 ?drugbank_id . }}
  OPTIONAL {{ ?compound wdt:P685 ?kegg_id . }}
  OPTIONAL {{ ?compound wdt:P231 ?cas_number . }}
}}
LIMIT 1
"""


def query_wikidata(pubchem_cid: int | str, timeout: float = 30) -> dict[str, Any]:
    """Query Wikidata for structured data about a PubChem compound.

    Parameters
    ----------
    pubchem_cid
        PubChem compound identifier (numeric).
    timeout
        SPARQL query timeout in seconds.

    Returns
    -------
    dict
        Keys: ``qid``, ``wikipedia_title``, ``chembl_id``,
        ``chebi_id``, ``drugbank_id``, ``kegg_id``, ``cas_number``.
        Each value is a string or ``None``.

    Raises
    ------
    ImportError
        If ``requests`` or ``SPARQLWrapper`` is not installed.
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
    query = _WIKIDATA_QUERY.format(cid=cid)

    resp = requests.get(
        SPARQL_ENDPOINT,
        params={"format": "json", "query": query},
        headers={"User-Agent": "WikiMolGen/0.1 (chemical structure generator)"},
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()

    result: dict[str, Any] = {}
    bindings = data.get("results", {}).get("bindings", [])
    if not bindings:
        return result

    row = bindings[0]
    field_map = {
        "qid": "wikidata_qid",
        "wikipedia": "wikipedia_title",
        "chembl_id": "chembl_id",
        "chebi_id": "chebi_id",
        "drugbank_id": "drugbank_id",
        "kegg_id": "kegg_id",
        "cas_number": "cas_number",
    }
    for sparq_key, dict_key in field_map.items():
        val = row.get(sparq_key, {}).get("value")
        if val:
            if sparq_key == "wikipedia":
                # Extract page title from full URL
                val = val.rsplit("/", 1)[-1]
            result[dict_key] = val

    return result
