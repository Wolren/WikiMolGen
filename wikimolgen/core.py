"""
wikimolgen.core - Core Utilities
=================================
Shared utilities for molecular structure fetching and validation.
"""

import logging
import re
from concurrent.futures import ThreadPoolExecutor, as_completed

import pubchempy as pcp
from rdkit import Chem

from wikimolgen.sources import (
    fetch_dailymed_id,
    fetch_experimental_data,
    fetch_infobox,
    fetch_properties,
    fetch_substances,
    query_wikidata,
)

logger = logging.getLogger(__name__)


class CompoundFetchError(Exception):
    """Raised when compound data cannot be fetched from PubChem."""

    pass


class SMILESValidationError(Exception):
    """Raised when SMILES string is invalid."""

    pass


def fetch_compound(identifier: str) -> tuple[str, str]:
    """
    Fetch compound SMILES and name from PubChem or validate SMILES.

    Auto-detects input type in this order:
    1. PubChem CID (if numeric)
    2. PubChem compound name (if text lookup succeeds)
    3. Direct SMILES string (if valid chemical structure)

    Parameters
    ----------
    identifier : str
        PubChem CID (numeric), compound name, or SMILES string

    Returns
    -------
    tuple[str, str]
        (smiles, compound_name)

    Raises
    ------
    CompoundFetchError
        If identifier is not a valid CID, compound name, or SMILES
    """
    # Strategy 1: Try PubChem CID if identifier is numeric
    if identifier.isdigit():
        try:
            compound = pcp.Compound.from_cid(int(identifier))
            smiles = getattr(compound, "smiles", None) or compound.canonical_smiles
            return smiles, compound.iupac_name or f"CID_{identifier}"
        except Exception as e:
            raise CompoundFetchError(f"Failed to fetch PubChem CID {identifier}: {e}")

    # Strategy 2: Try PubChem compound name lookup
    try:
        compounds = pcp.get_compounds(identifier, "name")
        if compounds:
            compound = compounds[0]
            smiles = getattr(compound, "smiles", None) or compound.canonical_smiles
            return smiles, compound.iupac_name or identifier
    except Exception:
        pass  # Not a valid compound name, continue to SMILES check

    # Strategy 3: Try as direct SMILES string
    mol = Chem.MolFromSmiles(identifier)
    if mol is not None:
        return identifier, "custom_smiles"

    # All strategies failed
    raise CompoundFetchError(
        f"Could not interpret '{identifier}' as PubChem CID, compound name, or valid SMILES"
    )


def _parse_element_counts(formula: str) -> dict[str, int]:
    """Parse a molecular formula (e.g. ``"C9H8O4"``) into element counts.

    Keys are lower-cased element symbols suffixed with ``_count``, e.g.
    ``c_count=9``, ``h_count=8``, ``o_count=4``.
    """
    counts: dict[str, int] = {}
    for m in re.finditer(r"([A-Z][a-z]*)(\d*)", formula):
        elem = m.group(1)
        count = int(m.group(2)) if m.group(2) else 1
        counts[f"{elem.lower()}_count"] = count
    return counts


def enrich_compound_data(compound_data: dict | None) -> dict | None:
    """Enrich PubChem data with cross-references, properties, and metadata.

    Calls Wikidata (cross-references + Wikipedia title), PubChem PUG REST
    (computed physicochemical properties), PubChem full record (experimental
    physical properties), and Wikipedia API (infobox pharmacology data)
    **in parallel** for lower latency.

    Added keys:
        Cross-references — ``wikidata_qid``, ``wikipedia_title``,
        ``chembl_id``, ``chebi_id``, ``drugbank_id``, ``kegg_id``,
        ``cas_number``, ``chemspider_id``, ``unii``.
        Computed properties — ``xlogp``, ``exact_mass``,
        ``monoisotopic_mass``, ``tpsa``, ``complexity``, ``charge``,
        ``h_bond_donors``, ``h_bond_acceptors``, ``rotatable_bonds``,
        ``heavy_atoms``.
        Experimental properties — ``melting_point``, ``boiling_point``,
        ``flash_point``, ``solubility``, ``density``, ``appearance``.
        Pharmacology — ``atc_prefix``, ``atc_suffix``, ``legal_status``,
        ``pregnancy_category``, ``routes_of_administration``, ``drug_class``.

    Parameters
    ----------
    compound_data
        Data dict from ``fetch_pubchem_data()`` (must contain ``cid``).

    Returns
    -------
    dict or None
        The enriched dict, or ``None`` if input was ``None``.
    """
    if not compound_data or not compound_data.get("cid"):
        return compound_data

    cid = compound_data["cid"]

    def _wikidata():
        try:
            return query_wikidata(cid)
        except Exception as e:
            logger.warning("Wikidata query failed for CID %s: %s", cid, e)
            return {}

    def _props():
        try:
            return fetch_properties(cid)
        except Exception as e:
            logger.warning("PubChem properties failed for CID %s: %s", cid, e)
            return {}

    def _experimental():
        try:
            return fetch_experimental_data(cid)
        except Exception as e:
            logger.warning("PubChem experimental data failed for CID %s: %s", cid, e)
            return {}

    def _substances():
        try:
            return fetch_substances(cid)
        except Exception as e:
            logger.warning("PubChem substance lookup failed for CID %s: %s", cid, e)
            return {}

    sources = {
        "substances": _substances,
        "experimental": _experimental,
        "wikidata": _wikidata,
        "props": _props,
    }

    # Phase 1: Fetch all parallel sources, collect results
    raw: dict[str, dict] = {}
    with ThreadPoolExecutor(max_workers=4) as pool:
        submitted = {pool.submit(fn): name for name, fn in sources.items()}
        for fut in as_completed(submitted):
            name = submitted[fut]
            try:
                raw[name] = fut.result()
            except Exception as e:
                logger.warning("%s enrichment failed for CID %s: %s", name, cid, e)
                raw[name] = {}

    # Merge results in priority order (ascending — highest priority overwrites lower).
    # Priority: substances < experimental < wikidata < props < base
    result: dict = {}
    for name in ["substances", "experimental", "wikidata", "props"]:
        result.update(raw.get(name, {}))
    result.update(compound_data)  # base data = highest priority

    # Phase 2: Wikipedia infobox — lowest priority, NEVER overwrites existing keys
    wikipedia_title = result.get("wikipedia_title")
    if wikipedia_title:
        try:
            for k, v in (fetch_infobox(wikipedia_title) or {}).items():
                if k not in result:
                    result[k] = v
        except Exception as e:
            logger.warning("Wikipedia infobox lookup failed for CID %s: %s", cid, e)

    # Phase 3: Element counts from molecular formula
    formula = result.get("molecular_formula", "")
    if formula:
        try:
            result.update(_parse_element_counts(formula))
        except Exception as e:
            logger.warning("Element count parsing failed for formula '%s': %s", formula, e)

    # Phase 4: DailyMed ID (depends on UNII from Wikidata)
    unii = result.get("unii")
    if unii:
        try:
            dailymed_id = fetch_dailymed_id(unii)
            if dailymed_id:
                result["dailymed_id"] = dailymed_id
        except Exception as e:
            logger.warning("DailyMed lookup failed for UNII %s: %s", unii, e)

    return result


def validate_smiles(smiles: str) -> Chem.Mol:
    """
    Validate and parse a SMILES string.

    Parameters
    ----------
    smiles : str
        SMILES representation of molecule

    Returns
    -------
    Chem.Mol
        RDKit molecule object

    Raises
    ------
    SMILESValidationError
        If SMILES string is invalid
    """
    mol = Chem.MolFromSmiles(smiles)
    if mol is None:
        raise SMILESValidationError(f"Invalid SMILES string: {smiles}")
    return mol
