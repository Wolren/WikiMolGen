"""
wikimolgen.core - Core Utilities
=================================
Shared utilities for molecular structure fetching and validation.
"""

import pubchempy as pcp
from rdkit import Chem


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
            smiles = getattr(compound, 'smiles', None) or compound.canonical_smiles
            return smiles, compound.iupac_name or f"CID_{identifier}"
        except Exception as e:
            raise CompoundFetchError(f"Failed to fetch PubChem CID {identifier}: {e}")

    # Strategy 2: Try PubChem compound name lookup
    try:
        compounds = pcp.get_compounds(identifier, 'name')
        if compounds:
            compound = compounds[0]
            smiles = getattr(compound, 'smiles', None) or compound.canonical_smiles
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