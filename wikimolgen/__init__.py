"""
WikiMolGen - Unified Molecular Structure Generator
===================================================
A Python package for generating 2D and 3D molecular visualizations
from PubChem compounds or SMILES strings. Originally built for Wikipedia.

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

__all__ = ["MoleculeGenerator2D", "MoleculeGenerator3D", "TemplateLoader", "ColorStyleTemplate", "SettingsTemplate",
           "list_predefined_templates", ]

from .core import fetch_compound, validate_smiles
from .templates import TemplateLoader, ColorStyleTemplate, SettingsTemplate, list_predefined_templates
from .wikimol2d import MoleculeGenerator2D
from .wikimol3d import MoleculeGenerator3D
