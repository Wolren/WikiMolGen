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
SELECT ?compound ?qid ?wikipedia ?chembl_id ?chebi_id ?drugbank_id ?kegg_id ?cas_number ?chemspider_id ?unii ?medlineplus ?iuphar_ligand ?pdb_ligand ?niaid_chemdb ?mesh_id ?inn WHERE {{
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
  OPTIONAL {{ ?compound wdt:P661 ?chemspider_id . }}
  OPTIONAL {{ ?compound wdt:P652 ?unii . }}
  OPTIONAL {{ ?compound wdt:P604 ?medlineplus . }}
  OPTIONAL {{ ?compound wdt:P595 ?iuphar_ligand . }}
  OPTIONAL {{ ?compound wdt:P638 ?pdb_ligand . }}
  OPTIONAL {{ ?compound wdt:P2036 ?niaid_chemdb . }}
  OPTIONAL {{ ?compound wdt:P486 ?mesh_id . }}
  OPTIONAL {{ ?compound wdt:P2768 ?inn . }}
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
        ``chebi_id``, ``drugbank_id``, ``kegg_id``, ``cas_number``,
        ``chemspider_id``, ``unii``, ``medlineplus``,
        ``iuphar_ligand``, ``pdb_ligand``, ``niaid_chemdb``,
        ``mesh_id``, ``inn``.
        Each value is a string or ``None``.

    Raises
    ------
    ImportError
        If ``requests`` or ``SPARQLWrapper`` is not installed.
    requests.RequestException
        On network or API errors.
    """
    from wikimolgen.sources._client import make_headers, requests

    cid = int(pubchem_cid)
    if cid < 1 or cid > 999_999_999:
        raise ValueError(f"PubChem CID out of valid range (1-999999999): {cid}")
    query = _WIKIDATA_QUERY.replace("{cid}", str(cid))

    resp = requests.get(
        SPARQL_ENDPOINT,
        params={"format": "json", "query": query},
        headers=make_headers(),
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
        "chemspider_id": "chemspider_id",
        "unii": "unii",
        "medlineplus": "medlineplus",
        "iuphar_ligand": "iuphar_ligand",
        "pdb_ligand": "pdb_ligand",
        "niaid_chemdb": "niaid_chemdb",
        "mesh_id": "mesh_id",
        "inn": "inn",
    }
    for sparq_key, dict_key in field_map.items():
        val = row.get(sparq_key, {}).get("value")
        if val:
            if sparq_key == "wikipedia":
                # Extract page title from full URL
                val = val.rsplit("/", 1)[-1]
            result[dict_key] = val

    return result
