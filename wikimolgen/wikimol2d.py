"""
wikimolgen.wikimol2d - 2D Molecular Structure Generation
=========================================================
Class-based 2D molecular visualization with SVG export.
"""

from dataclasses import dataclass
from pathlib import Path

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

from .core import fetch_compound, validate_smiles


@dataclass
class DrawingConfig:
    """Configuration for 2D molecular drawing."""
    
    angle: float = np.pi
    scale: float = 30.0
    margin: float = 0.5
    bond_length: float = 35.0
    min_font_size: int = 36
    padding: float = 0.01
    use_bw_palette: bool = True
    transparent_background: bool = True


class MoleculeGenerator2D:
    """
    Generate 2D molecular structure diagrams.
    
    Attributes
    ----------
    identifier : str
        PubChem CID, compound name, or SMILES string
    smiles : str
        Canonical SMILES representation
    compound_name : str
        Name of the compound
    mol : Chem.Mol
        RDKit molecule object
    config : DrawingConfig
        Drawing configuration parameters
        
    Examples
    --------
    >>> gen = MoleculeGenerator2D("24802108")
    >>> gen.generate("4-MeO-DiPT.svg")
    
    >>> gen = MoleculeGenerator2D("psilocin", angle=0, scale=40)
    >>> gen.generate("psilocin.svg")
    """
    
    def __init__(
        self,
        identifier: str,
        angle: float = np.pi,
        scale: float = 30.0,
        margin: float = 0.5,
        bond_length: float = 35.0,
        min_font_size: int = 36,
        padding: float = 0.01,
        use_bw_palette: bool = True,
        transparent_background: bool = True,
    ):
        """
        Initialize 2D molecule generator.
        
        Parameters
        ----------
        identifier : str
            PubChem CID, compound name, or SMILES string
        angle : float, optional
            Rotation angle in radians (default: π)
        scale : float, optional
            Pixels per coordinate unit (default: 30.0)
        margin : float, optional
            Canvas margin in coordinate units (default: 0.5)
        bond_length : float, optional
            Fixed bond length in pixels (default: 35.0)
        min_font_size : int, optional
            Minimum font size for atom labels (default: 36)
        padding : float, optional
            Padding around drawing (default: 0.01)
        use_bw_palette : bool, optional
            Use black and white atom palette (default: True)
        transparent_background : bool, optional
            Use transparent background (default: True)
        """
        self.identifier = identifier
        self.smiles, self.compound_name = fetch_compound(identifier)
        self.mol = validate_smiles(self.smiles)
        
        self.config = DrawingConfig(
            angle=angle,
            scale=scale,
            margin=margin,
            bond_length=bond_length,
            min_font_size=min_font_size,
            padding=padding,
            use_bw_palette=use_bw_palette,
            transparent_background=transparent_background,
        )
    
    def _rotate_coords(self, coords: np.ndarray) -> np.ndarray:
        """
        Rotate 2D coordinates around the center.
        
        Parameters
        ----------
        coords : np.ndarray
            Nx2 array of coordinates
            
        Returns
        -------
        np.ndarray
            Rotated coordinates
        """
        center = coords.mean(axis=0)
        centered = coords - center
        
        angle = self.config.angle
        rotation_matrix = np.array([
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)]
        ])
        
        return centered @ rotation_matrix.T
    
    def _compute_canvas_size(self, coords: np.ndarray) -> tuple[int, int, float, float]:
        """
        Calculate canvas dimensions.
        
        Parameters
        ----------
        coords : np.ndarray
            Nx2 array of coordinates
            
        Returns
        -------
        tuple[int, int, float, float]
            (width, height, min_x, min_y)
        """
        min_x, min_y = coords.min(axis=0)
        max_x, max_y = coords.max(axis=0)
        
        min_x -= self.config.margin
        min_y -= self.config.margin
        max_x += self.config.margin
        max_y += self.config.margin
        
        width = int((max_x - min_x) * self.config.scale)
        height = int((max_y - min_y) * self.config.scale)
        
        return width, height, min_x, min_y
    
    def generate(self, output: str = "molecule_2d.svg") -> Path:
        """
        Generate 2D structure and save as SVG.
        
        Parameters
        ----------
        output : str, optional
            Output SVG filename (default: "molecule_2d.svg")
            
        Returns
        -------
        Path
            Path to saved SVG file
        """
        # Compute 2D coordinates
        AllChem.Compute2DCoords(self.mol)
        conf = self.mol.GetConformer()
        
        # Extract and rotate coordinates
        coords = np.array([
            [conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y]
            for i in range(self.mol.GetNumAtoms())
        ])
        rotated = self._rotate_coords(coords)
        
        # Compute canvas dimensions
        width, height, min_x, min_y = self._compute_canvas_size(rotated)
        
        # Translate coordinates to canvas space
        for i, pos in enumerate(rotated):
            new_x = pos[0] - min_x
            new_y = pos[1] - min_y
            conf.SetAtomPosition(i, (new_x, new_y, 0.0))
        
        # Configure drawer
        drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        opts = drawer.drawOptions()
        
        if self.config.use_bw_palette:
            opts.useBWAtomPalette()
        
        opts.fixedBondLength = self.config.bond_length
        opts.padding = self.config.padding
        opts.minFontSize = self.config.min_font_size
        
        if self.config.transparent_background:
            opts.setBackgroundColour((0, 0, 0, 0))
        
        # Draw molecule
        rdMolDraw2D.PrepareAndDrawMolecule(drawer, self.mol)
        drawer.FinishDrawing()
        
        # Process and save SVG
        svg = drawer.GetDrawingText()
        if self.config.transparent_background:
            svg = svg.replace('fill:white', 'fill:none')
        
        output_path = Path(output)
        output_path.write_text(svg)
        
        print(f"✓ 2D structure saved: {output_path}")
        print(f"  Compound: {self.compound_name}")
        print(f"  Dimensions: {width}×{height} px")
        print(f"  Atoms: {self.mol.GetNumAtoms()}, Bonds: {self.mol.GetNumBonds()}")
        
        return output_path
    
    def __repr__(self) -> str:
        return (
            f"MoleculeGenerator2D(identifier='{self.identifier}', "
            f"compound='{self.compound_name}', atoms={self.mol.GetNumAtoms()})"
        )
