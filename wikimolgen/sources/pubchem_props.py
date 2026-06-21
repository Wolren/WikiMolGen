"""
wikimolgen.sources.pubchem_props
================================

Client for `PubChem PUG REST <https://pubchem.ncbi.nlm.nih.gov/docs/pug-rest>`_
property endpoints.

Enriches compound data with computed physicochemical properties that
PubChemPy does not expose: logP, H-bond counts, exact mass, TPSA, etc.

Note: melting/boiling/flash points are **not** available via the PUG REST
property endpoint. PubChem only returns computed/predicted properties
here — experimental data requires a different endpoint.

No API key required — 5 requests/second recommended, free.
"""

from __future__ import annotations

import logging
from typing import Any

logger = logging.getLogger(__name__)

from wikimolgen.sources._client import PUG_BASE

# Properties we request from PubChem PUG REST
# Only computed/predicted properties are available here.
# Experimental data (melting/boiling points) requires a different endpoint.
_PROPERTY_NAMES = [
    "MolecularWeight",
    "XLogP",
    "ExactMass",
    "MonoisotopicMass",
    "TPSA",
    "Complexity",
    "Charge",
    "HBondDonorCount",
    "HBondAcceptorCount",
    "RotatableBondCount",
    "HeavyAtomCount",
]

# Map PubChem property names → our internal keys
_PROP_MAP: dict[str, str] = {
    "MolecularWeight": "molecular_weight",
    "XLogP": "xlogp",
    "ExactMass": "exact_mass",
    "MonoisotopicMass": "monoisotopic_mass",
    "TPSA": "tpsa",
    "Complexity": "complexity",
    "Charge": "charge",
    "HBondDonorCount": "h_bond_donors",
    "HBondAcceptorCount": "h_bond_acceptors",
    "RotatableBondCount": "rotatable_bonds",
    "HeavyAtomCount": "heavy_atoms",
}


def fetch_properties(pubchem_cid: int | str, timeout: float = 10) -> dict[str, Any]:
    """Fetch physicochemical properties from PubChem PUG REST.

    Parameters
    ----------
    pubchem_cid
        PubChem compound identifier (numeric).
    timeout
        HTTP request timeout in seconds.

    Returns
    -------
    dict
        Internal key → value mapping.  Only keys returned by PubChem
        are included (some compounds lack certain measurements).

    Raises
    ------
    ImportError
        If ``requests`` is not installed.
    requests.RequestException
        On network or API errors.
    """
    from wikimolgen.sources._client import make_headers, requests

    cid = str(int(pubchem_cid))
    prop_list = ",".join(_PROPERTY_NAMES)
    url = f"{PUG_BASE}/cid/{cid}/property/{prop_list}/JSON"

    resp = requests.get(
        url,
        headers=make_headers(description="chemical property fetcher"),
        timeout=timeout,
    )
    resp.raise_for_status()
    data = resp.json()

    result: dict[str, Any] = {}
    props = data.get("PropertyTable", {}).get("Properties", [])
    if not props:
        return result

    row = props[0]
    for pubchem_key, our_key in _PROP_MAP.items():
        val = row.get(pubchem_key)
        if val is not None:
            # Skip empty-string or zero-length values
            if isinstance(val, str) and not val.strip():
                continue
            result[our_key] = val

    return result
