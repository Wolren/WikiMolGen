"""
wikimolgen.optimization - Molecular Orientation Optimization
============================================================
Intelligent angle detection for optimal 2D/3D molecular visualization.
"""

from typing import Tuple

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem


def calculate_principal_axes(mol: Chem.Mol, conf_id: int = 0) -> Tuple[np.ndarray, np.ndarray]:
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
        AllChem.Compute2DCoords(mol)

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


def find_optimal_3d_orientation(mol: Chem.Mol, conf_id: int = 0) -> Tuple[float, float, float]:
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
    y_rot = np.arctan2(-v1[2], np.sqrt(v1[0] ** 2 + v1[1] ** 2))

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
