"""
wikimolgen.sources.wikipedia_infobox
======================================

Parser for `Wikipedia <https://en.wikipedia.org>`_ infobox data using the
`MediaWiki API <https://www.mediawiki.org/wiki/API:Main_page>`_.

Fetches the raw wikitext of a page and extracts structured data from
``Infobox drug`` and ``Infobox chemical`` templates — ATC codes, legal
status, routes of administration, pregnancy category, etc.

No API key required — free for reasonable use.
"""

from __future__ import annotations

import logging
import re
from typing import Any

logger = logging.getLogger(__name__)

API_ENDPOINT = "https://en.wikipedia.org/w/api.php"

# Fields to extract from {{Infobox drug}}
_DRUGINFOX_FIELDS: dict[str, str] = {
    # Clinical data
    "pronounce": "pronounce",
    "tradename": "tradename",
    "Drugs.com": "drugs_com",
    "MedlinePlus": "medlineplus",
    "pregnancy_AU": "pregnancy_au",
    "pregnancy_AU_comment": "pregnancy_au_comment",
    "pregnancy_category": "pregnancy_category",
    "routes_of_administration": "routes_of_administration",
    "class": "drug_class",
    # ATC codes
    "ATC_prefix": "atc_prefix",
    "ATC_suffix": "atc_suffix",
    "ATC_supplemental": "atc_supplemental",
    "ATCvet": "atc_vet",
    # Legal status
    "legal_status": "legal_status",
    "legal_AU": "legal_au",
    "legal_AU_comment": "legal_au_comment",
    "legal_BR": "legal_br",
    "legal_BR_comment": "legal_br_comment",
    "legal_CA": "legal_ca",
    "legal_CA_comment": "legal_ca_comment",
    "legal_DE": "legal_de",
    "legal_DE_comment": "legal_de_comment",
    "legal_NZ": "legal_nz",
    "legal_NZ_comment": "legal_nz_comment",
    "legal_UK": "legal_uk",
    "legal_UK_comment": "legal_uk_comment",
    "legal_US": "legal_us",
    "legal_US_comment": "legal_us_comment",
    "legal_UN": "legal_un",
    "legal_UN_comment": "legal_un_comment",
    # Licensing
    "licence_CA": "licence_ca",
    "licence_EU": "licence_eu",
    "licence_US": "licence_us",
    # Dependency / addiction
    "dependency_liability": "dependency_liability",
    "addiction_liability": "addiction_liability",
    # Pharmacokinetics
    "bioavailability": "bioavailability",
    "protein_bound": "protein_bound",
    "metabolism": "metabolism",
    "metabolites": "metabolites",
    "onset": "onset",
    "elimination_half-life": "elimination_half_life",
    "duration_of_action": "duration_of_action",
    "excretion": "excretion",
    # Additional identifiers
    "CAS_supplemental": "cas_supplemental",
    "IUPHAR_ligand": "iuphar_ligand",
    "PDB_ligand": "pdb_ligand",
    "NIAID_ChemDB": "niaid_chemdb",
    "PubChemSubstance": "pubchem_substance",
}


def _fetch_wikitext(page_title: str, timeout: float = 10) -> str | None:
    """Fetch raw wikitext of a Wikipedia page via the MediaWiki API."""
    from wikimolgen.sources._client import make_headers, requests

    params = {
        "action": "parse",
        "page": page_title,
        "prop": "wikitext",
        "format": "json",
    }
    resp = requests.get(
        API_ENDPOINT,
        params=params,
        headers=make_headers(description="infobox parser"),
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()

    parse = data.get("parse")
    if parse is None:
        return None
    wikitext = parse.get("wikitext", {}).get("*")
    return wikitext


def _extract_infobox(
    wikitext: str,
    template_name: str,
) -> dict[str, str] | None:
    """Extract a named infobox from wikitext and return its fields.

    Handles multi-line ``|key = value`` syntax using a balanced-brace
    approach to find the infobox boundaries.
    """
    # Find the infobox opening: {{Infobox drug  or  {{Infobox chemical
    escaped = re.escape(template_name)
    pattern = r"\{\{Infobox\s+" + escaped + r"\b"
    match = re.search(pattern, wikitext, re.IGNORECASE)
    if not match:
        return None

    start = match.start()
    # Walk forward finding the matching closing braces
    depth = 0
    end = start
    for i in range(start, len(wikitext)):
        if wikitext[i : i + 2] == "{{":
            depth += 1
            end = i + 2
        elif wikitext[i : i + 2] == "}}":
            depth -= 1
            end = i + 2
            if depth == 0:
                break
    else:
        return None

    infobox_text = wikitext[start:end]

    fields: dict[str, str] = {}
    # Match |key = value or |key=value lines within the infobox
    for line in infobox_text.split("\n"):
        line = line.strip()
        # Remove leading pipe
        if line.startswith("|"):
            line = line[1:]
        else:
            continue
        # Split on first =
        if "=" not in line:
            continue
        eq_idx = line.index("=")
        key = line[:eq_idx].strip()
        value = line[eq_idx + 1 :].strip()
        # Skip template-internal keys
        if key.startswith("#") or not key:
            continue
        # Remove trailing comments
        value = re.sub(r"<!--.*?-->", "", value).strip()
        # Remove wiki markup like <ref>...</ref>, [https://...], etc.
        value = re.sub(r"<ref[^>]*>.*?</ref>", "", value, flags=re.DOTALL).strip()
        value = re.sub(r"<br\s*/?>", ", ", value, flags=re.IGNORECASE).strip()
        fields[key.lower()] = value

    return fields if fields else None


def fetch_infobox(
    wikipedia_title: str,
    timeout: float = 10,
) -> dict[str, Any]:
    """Fetch and parse Wikipedia infobox data for a compound.

    Parameters
    ----------
    wikipedia_title
        The Wikipedia article title (e.g. ``"Aspirin"``).
    timeout
        HTTP request timeout in seconds.

    Returns
    -------
    dict
        Keys include ``atc_prefix``, ``atc_suffix``, ``legal_status``,
        ``pregnancy_category``, ``routes_of_administration``, etc.
        Returns an empty dict if the page has no relevant infobox or
        cannot be fetched.

    Raises
    ------
    ImportError
        If ``requests`` is not installed.
    """
    wikitext = _fetch_wikitext(wikipedia_title, timeout=timeout)
    if not wikitext:
        logger.info("No wikitext returned for '%s'", wikipedia_title)
        return {}

    result: dict[str, Any] = {}

    # Try Infobox drug first, then Infobox chemical
    infobox = _extract_infobox(wikitext, "drug")
    if infobox is None:
        infobox = _extract_infobox(wikitext, "chemical")

    if infobox is None:
        logger.info("No drug/chemical infobox found on '%s'", wikipedia_title)
        return {}

    for wiki_key, our_key in _DRUGINFOX_FIELDS.items():
        val = infobox.get(wiki_key.lower())
        if val and val not in ("", "None", "none", "?"):
            result[our_key] = val

    return result
