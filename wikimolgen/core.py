"""
wikimolgen.core - Core Utilities
=================================
Shared utilities for molecular structure fetching and validation.
"""

import pubchempy as pcp
from rdkit import Chem
from rdkit.Chem import Descriptors


class CompoundFetchError(Exception):
    """Raised when compound data cannot be fetched from PubChem."""
    pass


class SMILESValidationError(Exception):
    """Raised when SMILES string is invalid."""
    pass


def fetch_compound(identifier: str) -> tuple[str, str]:
    """
    Fetch compound SMILES and name from PubChem.
    
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
        If compound cannot be found or fetched from PubChem
    """
    # Try direct SMILES validation first
    mol = Chem.MolFromSmiles(identifier)
    if mol is not None:
        return identifier, "custom_smiles"
    
    # Try PubChem lookup
    try:
        if identifier.isdigit():
            compound = pcp.Compound.from_cid(int(identifier))
            return compound.canonical_smiles, compound.iupac_name or f"CID_{identifier}"
        else:
            compounds = pcp.get_compounds(identifier, 'name')
            if not compounds:
                raise CompoundFetchError(f"No compound found for name: {identifier}")
            compound = compounds[0]
            return compound.canonical_smiles, compound.iupac_name or identifier
    except Exception as e:
        raise CompoundFetchError(f"Failed to fetch compound '{identifier}': {e}")


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
