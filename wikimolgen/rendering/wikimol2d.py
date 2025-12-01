"""
wikimolgen.wikimol2d - 2D Molecular Structure Generation

=========================================================

Class-based 2D molecular visualization with SVG export and auto-orientation.

User-friendly angle specification in DEGREES.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional

import numpy as np
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

from wikimolgen.core import fetch_compound, validate_smiles
from wikimolgen.rendering.optimization import (
    is_phenethylamine, orient_molecule, find_optimal_2d_rotation
)


@dataclass
class DrawingConfig:
    """Configuration for 2D molecular drawing."""
    auto_orient: bool = True
    angle: float = 0.0
    scale: float = 30.0
    margin: float = 0.8
    bond_length: float = 50.0
    min_font_size: int = 36
    padding: float = 0.07
    use_bw_palette: bool = True
    transparent_background: bool = True


class MoleculeGenerator2D:
    """
    Generate 2D molecular structure diagrams with optional auto-orientation.

    Special handling for phenethylamines:
    - Automatically orients sidechain pointing RIGHT (0°)
    - NH2 amine group points UP (90°) within the sidechain
    - Br and other substituents positioned on LEFT of ring
    - User can optionally apply additional rotation
    - Non-phenethylamines use standard rotation
    """

    def __init__(
        self,
        identifier: str,
        angle_degrees: Optional[float] = None,
        scale: float = 30.0,
        margin: float = 0.8,
        bond_length: float = 50.0,
        min_font_size: int = 36,
        padding: float = 0.07,
        use_bw_palette: bool = True,
        transparent_background: bool = True,
        auto_orient: bool = False,
    ):
        """
        Initialize 2D molecule generator.

        Parameters
        ----------
        identifier : str
            PubChem CID, compound name, or SMILES string
        angle_degrees : float, optional
            Rotation angle in DEGREES (applied after phenethylamine orientation)
            Default: None (0° for standard rendering)
        scale : float, optional
            Pixels per coordinate unit (default: 30.0)
        margin : float, optional
            Canvas margin in coordinate units (default: 0.5)
        bond_length : float, optional
            Fixed bond length in pixels (default: 45.0)
        min_font_size : int, optional
            Minimum font size for atom labels (default: 36)
        padding : float, optional
            Padding around drawing (default: 0.03)
        use_bw_palette : bool, optional
            Use black and white atom palette (default: True)
        transparent_background : bool, optional
            Use transparent background (default: True)
        auto_orient : bool, optional
            Automatically find optimal viewing angle (default: False)
        auto_orient_amines : bool, optional
            Automatically orient amine groups (default: True)
        phenethylamine_sidechain_angle : float, optional
            Target angle for phenethylamine sidechain in degrees (default: 0° = RIGHT)
        amine_target_angle : float, optional
            Target angle for amine NH/N groups in degrees (default: 90° = UP)
        skip_rotation_for_phenethylamines : bool, optional
            Skip additional rotation for phenethylamines (default: False)
        """
        self.identifier = identifier
        self.smiles, self.compound_name = fetch_compound(identifier)
        self.mol = validate_smiles(self.smiles)

        # Determine angle (convert degrees to radians internally)
        if auto_orient:
            computed_angle = find_optimal_2d_rotation(self.mol)
            final_angle = computed_angle
        else:
            if angle_degrees is not None:
                final_angle = np.radians(angle_degrees)
            else:
                final_angle = 0.0

        self.config = DrawingConfig(
            angle=final_angle,
            scale=scale,
            margin=margin,
            bond_length=bond_length,
            min_font_size=min_font_size,
            padding=padding,
            use_bw_palette=use_bw_palette,
            transparent_background=transparent_background,
            auto_orient=auto_orient,
        )

        # Store user's explicit angle_degrees for later use
        self.user_angle_degrees = angle_degrees

    def _rotate_coords(self, coords: np.ndarray) -> np.ndarray:
        """Rotate 2D coordinates around the center."""
        center = coords.mean(axis=0)
        centered = coords - center
        angle = self.config.angle

        rotation_matrix = np.array([
            [np.cos(angle), -np.sin(angle)],
            [np.sin(angle), np.cos(angle)]
        ])

        return centered @ rotation_matrix.T + center

    def _compute_canvas_size(self, coords: np.ndarray) -> tuple:
        """Calculate canvas dimensions with margins."""
        min_x, min_y = coords.min(axis=0)
        max_x, max_y = coords.max(axis=0)

        min_x -= self.config.margin
        min_y -= self.config.margin
        max_x += self.config.margin
        max_y += self.config.margin

        width = int((max_x - min_x) * self.config.scale)
        height = int((max_y - min_y) * self.config.scale)

        return width, height, min_x, min_y

    def _apply_amine_orientation(self) -> dict:
        """
        Apply automatic amine orientation based on molecule type.

        Returns
        -------
        dict
            Orientation results with type, success, count/target_angle info
        """

        AllChem.Compute2DCoords(self.mol)

        # Check if phenethylamine
        if is_phenethylamine(self.mol):
            # Orient sidechain to point RIGHT (0°), with NH2 group pointing UP (90°)
            orient_molecule(self.mol)

        return {}

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

        # Apply amine orientation (phenethylamines get sidechain pointing right, NH2 up)
        amine_orientation = self._apply_amine_orientation()

        conf = self.mol.GetConformer()

        # Extract coordinates
        coords = np.array([
            [conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y]
            for i in range(self.mol.GetNumAtoms())
        ])

        # Decide on rotation strategy
        is_phenethylamine_mol = amine_orientation.get('type') == 'phenethylamine'

        if is_phenethylamine_mol:
            # Phenethylamine already oriented with sidechain RIGHT, NH2 UP
            if self.user_angle_degrees is not None:
                # User explicitly requested additional rotation
                rotated = self._rotate_coords(coords)
            else:
                # Apply configured rotation (default 0° = no rotation)
                rotated = self._rotate_coords(coords)
        else:
            # Non-phenethylamine: apply normal rotation
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

        # Print status
        print(f"✓ 2D structure saved: {output_path}")
        print(f" Compound: {self.compound_name}")
        print(f" Dimensions: {width}×{height} px")
        print(f" Atoms: {self.mol.GetNumAtoms()}, Bonds: {self.mol.GetNumBonds()}")

        if is_phenethylamine_mol:
            print(f" ★ Phenethylamine: Sidechain RIGHT (0°) + NH2 UP (90°)")
            if self.user_angle_degrees is not None:
                print(f"   + Additional rotation: {self.user_angle_degrees}°")
        elif self.config.auto_orient:
            print(f" Auto-oriented: {np.degrees(self.config.angle):.1f}°")
        else:
            print(f" Rotation: {np.degrees(self.config.angle):.1f}°")

        if amine_orientation:
            if amine_orientation['type'] == 'phenethylamine':
                pass  # Already printed above
            elif amine_orientation['type'] == 'amines':
                print(f" Amines oriented: {amine_orientation['count']} groups → {amine_orientation['target_angle']}°")

        return output_path

    def __repr__(self) -> str:
        return (
            f"MoleculeGenerator2D(identifier='{self.identifier}', "
            f"compound='{self.compound_name}', atoms={self.mol.GetNumAtoms()})"
        )
