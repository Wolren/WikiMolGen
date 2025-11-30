"""
wikimolgen.amine_canonicalization - Amine Group Orientation & Formatting
========================================================================

Handles automatic amine group (NH2/NMe2/etc.) display with standard 
orientation and Wikipedia compliance.

Features:
- Automatic amine group detection
- Standard NH2 orientation (pointing up or right)
- Support for primary (NH2), secondary (NHR), tertiary (NR3) amines
- Wikipedia-compliant formatting (CH3 not Me)
- 2D coordinate manipulation for optimal display
"""

import math
from enum import Enum
from typing import Optional, Tuple, List, Dict

from rdkit import Chem
from rdkit.Chem import AllChem


class AmineType(Enum):
    """Classification of amine functional groups."""
    PRIMARY = "NH2"      # -NH2
    SECONDARY = "NHR"    # -NHR
    TERTIARY = "NR3"     # -NR3
    ANILINE = "ArNH2"    # -NH2 attached to aromatic ring
    AROMATIC = "ArNR2"   # Secondary/tertiary on aromatic
    UNKNOWN = "Unknown"


class AmineOrientation(Enum):
    """Standard orientations for amine display."""
    UP = 90.0           # Amine points upward
    DOWN = 270.0        # Amine points downward
    LEFT = 180.0        # Amine points left
    RIGHT = 0.0         # Amine points right
    AWAY = 45.0         # Diagonal up-right (away)
    TOWARD = 225.0      # Diagonal down-left (toward)


def detect_amine_groups(mol: Chem.Mol) -> List[Tuple[int, AmineType]]:
    """
    Detect all amine functional groups in molecule.
    
    Parameters
    ----------
    mol : Chem.Mol
        RDKit molecule object
    
    Returns
    -------
    List[Tuple[int, AmineType]]
        List of (nitrogen_atom_index, amine_type) tuples
    
    Examples
    --------
    >>> mol = Chem.MolFromSmiles("CCN")  # Ethylamine
    >>> amines = detect_amine_groups(mol)
    >>> # [(2, AmineType.PRIMARY)]
    
    >>> mol = Chem.MolFromSmiles("c1ccccc1N")  # Aniline
    >>> amines = detect_amine_groups(mol)
    >>> # [(6, AmineType.ANILINE)]
    
    >>> mol = Chem.MolFromSmiles("CCN(C)C")  # Trimethylamine
    >>> amines = detect_amine_groups(mol)
    >>> # [(2, AmineType.TERTIARY)]
    """
    amines = []
    
    for atom_idx, atom in enumerate(mol.GetAtoms()):
        if atom.GetAtomicNum() != 7:  # Not nitrogen
            continue
        
        # Skip amides (N bonded to C=O)
        if _is_amide(atom):
            continue
        
        # Count non-hydrogen neighbors
        carbon_neighbors = [
            nbr for nbr in atom.GetNeighbors() 
            if nbr.GetAtomicNum() == 6
        ]
        
        degree = len(carbon_neighbors)
        
        # Check if aromatic nitrogen
        is_aromatic = atom.GetIsAromatic()
        
        if degree == 0:  # NH3, NH2, or isolated
            if atom.GetTotalDegree() == 0:
                continue
            amines.append((atom_idx, AmineType.PRIMARY))
        
        elif degree == 1:  # RNH2 (primary) or ArNH2 (aniline)
            if is_aromatic:
                amines.append((atom_idx, AmineType.ANILINE))
            else:
                amines.append((atom_idx, AmineType.PRIMARY))
        
        elif degree == 2:  # R2NH (secondary)
            amines.append((atom_idx, AmineType.SECONDARY))
        
        elif degree == 3:  # R3N (tertiary)
            amines.append((atom_idx, AmineType.TERTIARY))
    
    return amines


def _is_amide(nitrogen_atom: Chem.Atom) -> bool:
    """Check if nitrogen is part of amide functional group (N-C=O)."""

    mol = nitrogen_atom.GetOwningMol()  # FIX: Get parent molecule

    for neighbor in nitrogen_atom.GetNeighbors():
        if neighbor.GetAtomicNum() == 6:  # Carbon
            for carbon_neighbor in neighbor.GetNeighbors():
                if carbon_neighbor.GetAtomicNum() == 8:  # Oxygen
                    # FIX: Use mol.GetBondBetweenAtoms(), not neighbor.GetBondBetweenAtoms()
                    bond = mol.GetBondBetweenAtoms(
                        neighbor.GetIdx(),
                        carbon_neighbor.GetIdx()
                    )

                    if bond and bond.GetBondType() == Chem.BondType.DOUBLE:
                        return True

def orient_amine_group(
    mol: Chem.Mol,
    amine_n_idx: int,
    target_angle_deg: float = 90.0,
    conf_id: int = 0
) -> bool:
    """
    Rotate molecule so amine group points in target direction.
    
    For phenethylamines and other compounds, ensures amine is displayed
    in a canonical orientation for clarity and Wikipedia compliance.
    
    Parameters
    ----------
    mol : Chem.Mol
        RDKit molecule with 2D coordinates
    amine_n_idx : int
        Atom index of amine nitrogen
    target_angle_deg : float, optional
        Target angle in degrees for amine orientation (default: 90° = up)
        - 0°: pointing right
        - 90°: pointing up
        - 180°: pointing left
        - 270°: pointing down
    conf_id : int, optional
        Conformer ID (default: 0)
    
    Returns
    -------
    bool
        True if successful, False if no conformer
    
    Examples
    --------
    >>> mol = Chem.MolFromSmiles("CCN")
    >>> AllChem.Compute2DCoords(mol)
    >>> orient_amine_group(mol, 2, 90.0)  # Amine points up
    True
    """
    if mol.GetNumConformers() == 0:
        return False
    
    conf = mol.GetConformer(conf_id)
    n_atom = mol.GetAtomWithIdx(amine_n_idx)
    
    # Find the "outward" direction: N's neighbor that's not aromatic
    # For primary amines, use the C-N bond direction
    neighbors = n_atom.GetNeighbors()
    if not neighbors:
        return False
    
    # Prefer non-aromatic neighbors for angle calculation
    reference_neighbor = None
    for neighbor in neighbors:
        if not neighbor.GetIsAromatic():
            reference_neighbor = neighbor
            break
    
    if reference_neighbor is None:
        reference_neighbor = neighbors[0]
    
    # Get positions
    n_pos = conf.GetAtomPosition(amine_n_idx)
    ref_pos = conf.GetAtomPosition(reference_neighbor.GetIdx())
    
    # Vector from reference to nitrogen
    vx = n_pos.x - ref_pos.x
    vy = n_pos.y - ref_pos.y
    
    # Current angle
    current_angle = math.atan2(vy, vx)
    target_angle_rad = math.radians(target_angle_deg)
    
    # Rotation needed
    delta = target_angle_rad - current_angle
    cos_d = math.cos(delta)
    sin_d = math.sin(delta)
    
    # Rotate all atoms around molecule center
    center_x = sum(conf.GetAtomPosition(i).x for i in range(mol.GetNumAtoms())) / mol.GetNumAtoms()
    center_y = sum(conf.GetAtomPosition(i).y for i in range(mol.GetNumAtoms())) / mol.GetNumAtoms()
    
    for i in range(mol.GetNumAtoms()):
        p = conf.GetAtomPosition(i)
        
        # Translate to origin
        x = p.x - center_x
        y = p.y - center_y
        
        # Rotate
        x_new = x * cos_d - y * sin_d
        y_new = x * sin_d + y * cos_d
        
        # Translate back
        conf.SetAtomPosition(i, (x_new + center_x, y_new + center_y, 0.0))
    
    return True


def get_amine_display_name(amine_type: AmineType, methyl_on_heteroatom: bool = False) -> str:
    """
    Get Wikipedia-compliant display name for amine type.
    
    Parameters
    ----------
    amine_type : AmineType
        Type of amine group
    methyl_on_heteroatom : bool, optional
        If True, use "NMe2" format for secondary/tertiary on heteroatom
        (default: False, use "NHR" format)
    
    Returns
    -------
    str
        Display name following Wikipedia conventions
    
    Examples
    --------
    >>> get_amine_display_name(AmineType.PRIMARY)
    'NH2'
    
    >>> get_amine_display_name(AmineType.TERTIARY)
    'NR3'
    
    >>> get_amine_display_name(AmineType.SECONDARY, methyl_on_heteroatom=True)
    'NMe2'
    """
    if amine_type == AmineType.PRIMARY:
        return "NH2"
    elif amine_type == AmineType.SECONDARY:
        return "NMe2" if methyl_on_heteroatom else "NHR"
    elif amine_type == AmineType.TERTIARY:
        return "NMe3" if methyl_on_heteroatom else "NR3"
    elif amine_type == AmineType.ANILINE:
        return "NH2"
    elif amine_type == AmineType.AROMATIC:
        return "NMe2" if methyl_on_heteroatom else "NR2"
    else:
        return "N"


def find_phenethylamine_amine_index(mol: Chem.Mol) -> Optional[int]:
    """
    Find the amine nitrogen in phenethylamine-like compounds.
    
    Looks for pattern: aromatic ring - CH2 - CH2 - NH2
    
    Parameters
    ----------
    mol : Chem.Mol
        RDKit molecule object
    
    Returns
    -------
    Optional[int]
        Index of amine nitrogen, or None if not found
    
    Examples
    --------
    >>> mol = Chem.MolFromSmiles("c1ccccc1CCN")  # Phenethylamine
    >>> idx = find_phenethylamine_amine_index(mol)
    >>> idx  # Index of N atom
    8
    """
    pattern = Chem.MolFromSmarts("c1ccccc1CCN")
    match = mol.GetSubstructMatch(pattern)
    
    if match:
        return match[-1]  # Last atom in pattern is N
    
    return None


class AmineCanonicalizer:
    """
    Comprehensive amine group formatter for Wikipedia compliance.
    
    Handles:
    - Automatic amine detection and orientation
    - CH3 vs Me nomenclature rules
    - Phenethylamine standard positioning
    - SVG coordinate manipulation
    """
    
    def __init__(self, mol: Chem.Mol, conf_id: int = 0):
        """
        Initialize canonicalizer for a molecule.
        
        Parameters
        ----------
        mol : Chem.Mol
            RDKit molecule object
        conf_id : int, optional
            Conformer ID (default: 0)
        """
        self.mol = mol
        self.conf_id = conf_id
        self.amines = detect_amine_groups(mol)
    
    def auto_orient_amines(
        self,
        phenethylamine_target: float = 90.0,
        general_target: float = 90.0
    ) -> Dict[int, bool]:
        """
        Automatically orient all amine groups.
        
        Parameters
        ----------
        phenethylamine_target : float, optional
            Target angle for phenethylamine amine (default: 90° = up)
        general_target : float, optional
            Target angle for other amines (default: 90° = up)
        
        Returns
        -------
        Dict[int, bool]
            {amine_n_idx: success} for each amine
        """
        results = {}
        
        # Check if this is a phenethylamine
        pea_n_idx = find_phenethylamine_amine_index(self.mol)
        
        for n_idx, amine_type in self.amines:
            if n_idx == pea_n_idx:
                success = orient_amine_group(
                    self.mol, n_idx,
                    phenethylamine_target,
                    self.conf_id
                )
            else:
                success = orient_amine_group(
                    self.mol, n_idx,
                    general_target,
                    self.conf_id
                )
            results[n_idx] = success
        
        return results
    
    def get_amine_info(self) -> List[Dict]:
        """
        Get comprehensive information about all amines.
        
        Returns
        -------
        List[Dict]
            List of dicts with amine info (index, type, display_name)
        """
        info = []
        for n_idx, amine_type in self.amines:
            info.append({
                'atom_index': n_idx,
                'type': amine_type,
                'display_name': get_amine_display_name(amine_type),
                'is_phenethylamine': n_idx == find_phenethylamine_amine_index(self.mol)
            })
        return info
    
    def has_amines(self) -> bool:
        """Check if molecule contains any amine groups."""
        return len(self.amines) > 0
    
    def amine_count(self) -> int:
        """Get total number of amine groups."""
        return len(self.amines)


# Convenience functions for common use cases

def orient_all_amines(mol: Chem.Mol, target_angle: float = 90.0) -> int:
    """
    Orient all amine groups in molecule.
    
    Parameters
    ----------
    mol : Chem.Mol
        RDKit molecule with 2D coordinates
    target_angle : float, optional
        Target angle in degrees (default: 90° = up)
    
    Returns
    -------
    int
        Number of amines oriented
    """
    canonicalizer = AmineCanonicalizer(mol)
    results = canonicalizer.auto_orient_amines(
        phenethylamine_target=target_angle,
        general_target=target_angle
    )
    return sum(1 for success in results.values() if success)


def has_amine_groups(mol: Chem.Mol) -> bool:
    """Quick check for presence of amine groups."""
    return len(detect_amine_groups(mol)) > 0


def get_amines_info(mol: Chem.Mol) -> List[Dict]:
    """Get all amine information for a molecule."""
    canonicalizer = AmineCanonicalizer(mol)
    return canonicalizer.get_amine_info()
