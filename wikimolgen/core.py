"""
wikimolgen.core - Core Utilities
=================================
Shared utilities for molecular structure fetching and validation.
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

import pubchempy as pcp
from rdkit import Chem

from wikimolgen.sources import fetch_properties, resolve_unichem, query_wikidata

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


def enrich_compound_data(compound_data: dict | None) -> dict | None:
    """Enrich PubChem data with cross-references and physicochemical properties.

    Calls UniChem (identifier resolution), Wikidata (QID / Wikipedia title),
    and PubChem PUG REST (physicochemical properties) **in parallel** for
    lower latency.

    Added keys:
        ``chembl_id``, ``chebi_id``, ``drugbank_id``, ``kegg_id``,
        ``chemspider_id``, ``unii``, ``wikidata_qid``, ``wikipedia_title``,
        ``cas_number``, ``xlogp``, ``exact_mass``, ``monoisotopic_mass``,
        ``tpsa``, ``complexity``, ``charge``, ``h_bond_donors``,
        ``h_bond_acceptors``, ``rotatable_bonds``, ``heavy_atoms``.
        Melting/boiling/flash points are not available via PUG REST.

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

    def _unichem():
        try:
            return resolve_unichem(cid)
        except Exception as e:
            logger.warning("UniChem lookup failed for CID %s: %s", cid, e)
            return {}

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

    futures = {"unichem": _unichem, "wikidata": _wikidata, "props": _props}

    with ThreadPoolExecutor(max_workers=3) as pool:
        submitted = {pool.submit(fn): name for name, fn in futures.items()}
        for fut in as_completed(submitted):
            name = submitted[fut]
            try:
                result = fut.result()
                compound_data.update(result)
            except Exception as e:
                logger.warning("%s enrichment failed for CID %s: %s", name, cid, e)

    return compound_data


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
