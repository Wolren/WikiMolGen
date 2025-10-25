"""
wikimolgen - Molecular Structure Generator for Wikipedia
===================================================
A Python package for generating 2D and 3D molecular visualizations for Wikipedia
from PubChem compounds or SMILES strings.

Features:
  - 2D SVG generation with customizable rotation and styling
  - 3D conformer generation with force field optimization
  - PyMOL-based high-quality 3D rendering
  - Support for PubChem CID, compound names, and direct SMILES input

Author: Wolren
Date: 2025-10-25
License: MIT
"""

__version__ = "1.0.0"
__all__ = ["MoleculeGenerator2D", "MoleculeGenerator3D", "fetch_compound"]

from .core import fetch_compound, validate_smiles
from .wikimol2d import MoleculeGenerator2D
from .wikimol3d import MoleculeGenerator3D
