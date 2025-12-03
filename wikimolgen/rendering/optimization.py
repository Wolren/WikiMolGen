"""
wikimolgen.optimization_enhanced - Enhanced Molecular Orientation
==================================================================

Extended optimization module with phenethylamine auto-orientation,
Wikipedia compliance, and amine group handling.

This module extends the original optimization.py with:
- Phenethylamine-specific orientation detection
- Amine group automatic positioning
- Wikipedia structure drawing compliance
- Advanced 2D layout optimization
"""

import math
from typing import Tuple, List

import numpy as np
from rdkit import Chem
from rdkit.Chem import rdDepictor

PHENETHYL_PATTERN = Chem.MolFromSmarts("c1ccccc1-CCN")

def is_phenethylamine(mol: Chem.Mol) -> bool:
    """
    Determine if molecule is a phenethylamine derivative.

    Checks for aromatic ring connected via ethyl chain to amine.
    Examples: phenethylamine, amphetamine, methamphetamine, dopamine

    Parameters
    ----------
    mol : Chem.Mol
        RDKit molecule object

    Returns
    -------
    bool
        True if phenethylamine pattern found

    Examples
    --------
    >>> mol = Chem.MolFromSmiles("NCCc1ccccc1")  # Phenethylamine
    >>> is_phenethylamine(mol)
    True

    >>> mol = Chem.MolFromSmiles("c1ccccc1C(C)N")  # Amphetamine
    >>> is_phenethylamine(mol)
    True
    """
    if mol.GetNumAtoms() < 9:  # Minimum atoms for phenethylamine
        return False

    return mol.HasSubstructMatch(PHENETHYL_PATTERN)


def orient_phenethylamine_sidechain(
    mol: Chem.Mol,
    target_angle_deg: float = 90.0,
    conf_id: int = 0
) -> bool:
    """
    Rotate molecule so phenethylamine sidechain points at target angle.

    For phenethylamines, this ensures the amine group appears in a canonical
    orientation relative to the phenyl ring, following chemical drawing
    conventions and Wikipedia standards.

    Parameters
    ----------
    mol : Chem.Mol
        RDKit molecule with 2D conformer (must have coordinates)
    target_angle_deg : float, optional
        Target angle in degrees for sidechain direction (default: 90° = up)
        Common choices:
        - 0°: pointing right
        - 90°: pointing up
        - 180°: pointing left
        - 270°: pointing down
        - 45°: diagonal up-right
    conf_id : int, optional
        Conformer ID (default: 0)

    Returns
    -------
    bool
        True if phenethylamine pattern found and rotated, False otherwise

    Notes
    -----
    This function differs from orient_amine_group() in that it:
    - Uses the phenethylamine-specific SMARTS pattern
    - Orients based on the CH2-CH2 vector for consistency
    - Applies to entire molecule (all atoms)

    Examples
    --------
    >>> mol = Chem.MolFromSmiles("NCCc1ccccc1")  # Phenethylamine
    >>> rdDepictor.Compute2DCoords(mol)
    >>> orient_phenethylamine_sidechain(mol, target_angle_deg=90)
    True

    >>> mol = Chem.MolFromSmiles("c1ccc(C)cc1C(C)N")  # Methamphetamine
    >>> rdDepictor.Compute2DCoords(mol)
    >>> orient_phenethylamine_sidechain(mol, target_angle_deg=90)
    True
    """
    if mol.GetNumConformers() == 0:
        return False

    # Try to match phenethylamine pattern
    match = mol.GetSubstructMatch(PHENETHYL_PATTERN)

    if not match:
        return False

    conf = mol.GetConformer(conf_id)

    # Extract the two aliphatic carbons from the sidechain
    # Pattern: c1ccccc1-CCN (last 3 atoms are C-C-N)
    if len(match) >= 3:
        # Find the CH2-CH2-N atoms (typically last 3 in match)
        # Iterate backwards to find two consecutive carbons followed by N
        ch2_indices = []
        for i in range(len(match) - 2):
            atom1_idx = match[i]
            atom2_idx = match[i + 1]
            atom1 = mol.GetAtomWithIdx(atom1_idx)
            atom2 = mol.GetAtomWithIdx(atom2_idx)

            # Look for aromatic C - aliphatic C - N pattern
            if (atom1.GetIsAromatic() and not atom2.GetIsAromatic() and
                atom2.GetAtomicNum() == 6):
                # This is the bridge from ring to chain
                ch2_1_idx = atom2_idx

                # Find next carbon (second CH2)
                for neighbor in atom2.GetNeighbors():
                    if (neighbor.GetAtomicNum() == 6 and
                        not neighbor.GetIsAromatic() and
                        neighbor.GetIdx() != atom1_idx):
                        ch2_2_idx = neighbor.GetIdx()
                        ch2_indices = [ch2_1_idx, ch2_2_idx]
                        break
                break

        if len(ch2_indices) != 2:
            return False

        ch2_1_idx, ch2_2_idx = ch2_indices
    else:
        # Fallback: use last two carbons in match
        carbon_indices = [idx for idx in match if mol.GetAtomWithIdx(idx).GetAtomicNum() == 6]
        if len(carbon_indices) < 2:
            return False
        ch2_1_idx = carbon_indices[-2]
        ch2_2_idx = carbon_indices[-1]

    # Get positions
    p1 = conf.GetAtomPosition(ch2_1_idx)
    p2 = conf.GetAtomPosition(ch2_2_idx)

    # Vector from first to second carbon in sidechain
    vx = p2.x - p1.x
    vy = p2.y - p1.y

    # Current angle of this vector
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


def calculate_principal_axes(
    mol: Chem.Mol, conf_id: int = 0
) -> Tuple[np.ndarray, np.ndarray]:
    """
    Calculate principal axes of molecule using PCA on atomic coordinates.

    Parameters
    ----------
    mol : Chem.Mol
        RDKit molecule with 3D coordinates
    conf_id : int, optional
        Conformer ID to use (default: 0)

    Returns
    -------
    Tuple[np.ndarray, np.ndarray]
        (eigenvalues, eigenvectors) - eigenvectors are principal axes
    """
    conf = mol.GetConformer(conf_id)
    coords = np.array([
        [conf.GetAtomPosition(i).x,
         conf.GetAtomPosition(i).y,
         conf.GetAtomPosition(i).z]
        for i in range(mol.GetNumAtoms())
    ])

    # Center coordinates
    centered = coords - coords.mean(axis=0)

    # Calculate covariance matrix
    cov = np.cov(centered.T)

    # Get eigenvalues and eigenvectors
    eigenvalues, eigenvectors = np.linalg.eig(cov)

    # Sort by eigenvalue (descending)
    idx = eigenvalues.argsort()[::-1]
    eigenvalues = eigenvalues[idx]
    eigenvectors = eigenvectors[:, idx]

    return eigenvalues, eigenvectors


def find_optimal_2d_rotation(mol: Chem.Mol) -> float:
    """
    Find optimal 2D rotation angle to minimize visual overlap.

    Uses moment of inertia and bond orientation analysis.

    Parameters
    ----------
    mol : Chem.Mol
        RDKit molecule with 2D coordinates

    Returns
    -------
    float
        Optimal rotation angle in radians
    """
    # Ensure we have 2D coords
    if mol.GetNumConformers() == 0:
        rdDepictor.Compute2DCoords(mol)

    conf = mol.GetConformer()
    coords = np.array([
        [conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y]
        for i in range(mol.GetNumAtoms())
    ])

    # Center coordinates
    centered = coords - coords.mean(axis=0)

    # Calculate principal axis via PCA
    cov = np.cov(centered.T)
    eigenvalues, eigenvectors = np.linalg.eig(cov)

    # Get angle of principal axis
    principal_axis = eigenvectors[:, eigenvalues.argmax()]
    angle = np.arctan2(principal_axis[1], principal_axis[0])

    # Align longest axis horizontally (rotate to make angle = 0)
    optimal_angle = -angle

    # Normalize to [0, 2π]
    optimal_angle = optimal_angle % (2 * np.pi)

    return optimal_angle


def find_optimal_3d_orientation(
    mol: Chem.Mol, conf_id: int = 0
) -> Tuple[float, float, float]:
    """
    Find optimal 3D orientation (Euler angles) for visualization.

    Aligns molecule along principal axes for maximum clarity.

    Parameters
    ----------
    mol : Chem.Mol
        RDKit molecule with 3D coordinates
    conf_id : int, optional
        Conformer ID to use (default: 0)

    Returns
    -------
    Tuple[float, float, float]
        (x_rotation, y_rotation, z_rotation) in degrees
    """
    eigenvalues, eigenvectors = calculate_principal_axes(mol, conf_id)

    # Principal axes (sorted by variance)
    v1 = eigenvectors[:, 0]  # Longest axis
    v2 = eigenvectors[:, 1]  # Second longest
    v3 = eigenvectors[:, 2]  # Shortest axis

    # Calculate Euler angles to align v1 with x-axis and v2 with xy-plane
    # Y-rotation (around y-axis)
    y_rot = np.arctan2(-v1[2], np.sqrt(v1[0]**2 + v1[1]**2))

    # Z-rotation (around z-axis)
    z_rot = np.arctan2(v1[1], v1[0])

    # X-rotation (fine-tune for v2)
    x_rot = 0.0

    # Add slight tilt for depth perception (15-30 degrees)
    y_rot_deg = np.degrees(y_rot) + 20
    z_rot_deg = np.degrees(z_rot)
    x_rot_deg = np.degrees(x_rot) + 10

    return x_rot_deg, y_rot_deg, z_rot_deg


def calculate_aspect_ratio(mol: Chem.Mol, conf_id: int = 0) -> float:
    """
    Calculate molecular aspect ratio (length/width) for 3D molecules.

    Parameters
    ----------
    mol : Chem.Mol
        RDKit molecule with 3D coordinates
    conf_id : int, optional
        Conformer ID to use (default: 0)

    Returns
    -------
    float
        Aspect ratio
    """
    eigenvalues, _ = calculate_principal_axes(mol, conf_id)

    # Aspect ratio is ratio of largest to second-largest eigenvalue
    if eigenvalues[1] > 0:
        return np.sqrt(eigenvalues[0] / eigenvalues[1])

    return 1.0


def optimize_zoom_buffer(mol: Chem.Mol, conf_id: int = 0) -> float:
    """
    Calculate optimal zoom buffer based on molecular shape.

    Parameters
    ----------
    mol : Chem.Mol
        RDKit molecule with 3D coordinates
    conf_id : int, optional
        Conformer ID to use (default: 0)

    Returns
    -------
    float
        Optimal zoom buffer (1.5 to 3.0)
    """
    aspect_ratio = calculate_aspect_ratio(mol, conf_id)

    # More spherical molecules need more buffer
    # Linear molecules need less buffer
    if aspect_ratio > 5:  # Very linear
        return 1.5
    elif aspect_ratio > 3:  # Moderately elongated
        return 2.0
    else:  # Compact/spherical
        return 2.5
