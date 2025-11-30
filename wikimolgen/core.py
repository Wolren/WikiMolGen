"""
wikimolgen.core - Core Utilities
=================================
Shared utilities for molecular structure fetching and validation.
"""

import pubchempy as pcp
from rdkit import Chem
from rdkit import RDLogger
from rdkit.Chem import Descriptors

RDLogger.DisableLog('rdApp.*')


class CompoundFetchError(Exception):
    """Raised when compound data cannot be fetched from PubChem."""
    pass


class SMILESValidationError(Exception):
    """Raised when SMILES string is invalid."""
    pass


def fetch_compound(identifier: str) -> tuple[str, str]:
    """
    Fetch compound SMILES and primary name from PubChem.

    Returns the official compound name from PubChem's synonym list:
    - Primary name = synonyms[0] (the official one)
    - Falls back to IUPAC if no synonyms
    - Falls back to CID if nothing else

    Auto-detects input type:
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
        where compound_name is the PRIMARY name (synonyms[0])

    Raises
    ------
    CompoundFetchError
        If identifier is not a valid CID, compound name, or SMILES
    """

    # Helper function: Extract primary name from compound object
    def get_primary_name(compound, cid: int) -> str:
        """
        Get the primary/official compound name.

        Priority:
        1. synonyms[0] (the official/primary name)
        2. iupac_name (technical fallback)
        3. CID (last resort)
        """
        try:
            # Try to get synonyms
            if hasattr(compound, 'synonyms') and compound.synonyms:
                # synonyms[0] is the official primary name
                return compound.synonyms[0]
        except Exception:
            pass

        try:
            # Fallback to IUPAC name
            if hasattr(compound, 'iupac_name') and compound.iupac_name:
                return compound.iupac_name
        except Exception:
            pass

        # Last resort: CID
        return f"Compound {cid}"

    # Strategy 1: Try PubChem CID if identifier is numeric
    if identifier.isdigit():
        try:
            cid = int(identifier)
            compound = pcp.Compound.from_cid(cid)

            # Get SMILES
            smiles = getattr(compound, 'smiles', None) or compound.canonical_smiles

            # Get PRIMARY name (synonyms[0])
            compound_name = get_primary_name(compound, cid)

            return smiles, compound_name

        except Exception as e:
            raise CompoundFetchError(f"Failed to fetch PubChem CID {identifier}: {e}")

    # Strategy 2: Try PubChem compound name lookup
    try:
        compounds = pcp.get_compounds(identifier, 'name')
        if compounds:
            compound = compounds[0]

            # Get SMILES
            smiles = getattr(compound, 'smiles', None) or compound.canonical_smiles

            # Get PRIMARY name
            compound_name = get_primary_name(compound, compound.cid)

            return smiles, compound_name

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


def get_molecular_properties(mol: Chem.Mol) -> dict[str, float]:
    """
    Calculate basic molecular properties.

    Parameters
    ----------
    mol : Chem.Mol
        RDKit molecule object

    Returns
    -------
    dict[str, float]
        Dictionary containing molecular weight, logP, etc.
    """
    return {
        "molecular_weight": Descriptors.MolWt(mol),
        "logp": Descriptors.MolLogP(mol),
        "num_h_donors": Descriptors.NumHDonors(mol),
        "num_h_acceptors": Descriptors.NumHAcceptors(mol),
        "num_rotatable_bonds": Descriptors.NumRotatableBonds(mol),
        "tpsa": Descriptors.TPSA(mol),
    }
