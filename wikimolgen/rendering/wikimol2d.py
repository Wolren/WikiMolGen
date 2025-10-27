"""
wikimolgen.wikimol2d - 2D Molecular Structure Generation
=========================================================
Class-based 2D molecular visualization with SVG export and auto-orientation.
User-friendly angle specification in DEGREES.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Union
import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

from wikimolgen.core import fetch_compound, validate_smiles

try:
    from examples.optimization import find_optimal_2d_rotation

    HAS_OPTIMIZATION = True
except ImportError:
    HAS_OPTIMIZATION = False


@dataclass
class DrawingConfig:
    """Configuration for 2D molecular drawing."""

    auto_orient: bool = True
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
    Generate 2D molecular structure diagrams with optional auto-orientation.

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
    >>> # Using degrees (user-friendly)
    >>> gen = MoleculeGenerator2D("aspirin", angle_degrees=180)
    >>> gen.generate("aspirin.svg")

    >>> # Auto-orientation
    >>> gen = MoleculeGenerator2D("caffeine", auto_orient=True)
    >>> gen.generate("caffeine.svg")

    >>> # Custom angle
    >>> gen = MoleculeGenerator2D("glucose", angle_degrees=45)
    >>> gen.generate("glucose.svg")
    """

    def __init__(
            self,
            identifier: str,
            angle_degrees: Optional[float] = None,
            scale: float = 30.0,
            margin: float = 0.5,
            bond_length: float = 45.0,
            min_font_size: int = 36,
            padding: float = 0.03,
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
            Rotation angle in DEGREES (default: 180°, ignored if auto_orient=True)
            Examples: 0, 45, 90, 180, 270
        scale : float, optional
            Pixels per coordinate unit (default: 30.0)
        margin : float, optional
            Canvas margin in coordinate units (default: 1.2)
        bond_length : float, optional
            Fixed bond length in pixels (default: 50.0)
        min_font_size : int, optional
            Minimum font size for atom labels (default: 40)
        padding : float, optional
            Padding around drawing (default: 0.10)
        use_bw_palette : bool, optional
            Use black and white atom palette (default: True)
        transparent_background : bool, optional
            Use transparent background (default: True)
        auto_orient : bool, optional
            Automatically find optimal viewing angle (default: False)
        """
        self.identifier = identifier
        self.smiles, self.compound_name = fetch_compound(identifier)
        self.mol = validate_smiles(self.smiles)

        # Determine angle (convert degrees to radians internally)
        if auto_orient:
            if HAS_OPTIMIZATION:
                computed_angle = find_optimal_2d_rotation(self.mol)
                final_angle = computed_angle  # Already in radians
            else:
                print("Warning: optimization module not available, using default angle")
                if angle_degrees is not None:
                    final_angle = np.radians(angle_degrees)
                else:
                    final_angle = np.pi  # 180 degrees default
        else:
            if angle_degrees is not None:
                final_angle = np.radians(angle_degrees)  # Convert user input to radians
            else:
                final_angle = np.pi  # 180 degrees default

        self.config = DrawingConfig(
            angle=final_angle,  # Store in radians internally
            scale=scale,
            margin=margin,
            bond_length=bond_length,
            min_font_size=min_font_size,
            padding=padding,
            use_bw_palette=use_bw_palette,
            transparent_background=transparent_background,
            auto_orient=auto_orient,
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
        Calculate canvas dimensions with generous margins to prevent clipping.

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
        if self.config.auto_orient:
            print(f"  Auto-oriented: {np.degrees(self.config.angle):.1f}°")
        else:
            print(f"  Rotation: {np.degrees(self.config.angle):.1f}°")

        return output_path


    def load_color_template(self, template: Union[str, Path, 'ColorStyleTemplate']) -> None:
        """
        Apply a color style template to the generator.

        Parameters
        ----------
        template : ColorStyleTemplate, str, or Path
            Color template object, path to template file, or predefined template name

        Examples
        --------
        >>> gen = MoleculeGenerator2D("aspirin")
        >>> gen.load_color_template("minimal_bw")  # Predefined template
        >>> gen.load_color_template("my_template.json")  # From file
        """
        from wikimolgen.predefined_templates import TemplateLoader, ColorStyleTemplate, get_predefined_color_template, TemplateError

        # Load template if needed
        if isinstance(template, str):
            # Check if it's a predefined template name
            try:
                template = get_predefined_color_template(template)
            except TemplateError:
                # Try loading as file path
                template = TemplateLoader.load_from_file(template)
        elif isinstance(template, Path):
            template = TemplateLoader.load_from_file(template)

        if not isinstance(template, ColorStyleTemplate):
            raise ValueError("Invalid template type. Expected ColorStyleTemplate.")

        # Apply color settings to config
        self.config.use_bw_palette = template.use_bw_palette
        self.config.transparent_background = template.transparent_background

        print(f"✓ Applied color template: {template.name}")
        if template.description:
            print(f"  {template.description}")

    def load_settings_template(self, template: Union[str, Path, 'SettingsTemplate']) -> None:
        """
        Apply a settings template to the generator.

        Parameters
        ----------
        template : SettingsTemplate, str, or Path
            Settings template object, path to template file, or predefined template name

        Examples
        --------
        >>> gen = MoleculeGenerator2D("caffeine")
        >>> gen.load_settings_template("publication_2d")  # Predefined template
        >>> gen.load_settings_template("my_settings.json")  # From file
        """
        from wikimolgen.predefined_templates import TemplateLoader, SettingsTemplate, get_predefined_settings_template, TemplateError

        # Load template if needed
        if isinstance(template, str):
            # Check if it's a predefined template name
            try:
                template = get_predefined_settings_template(template)
            except TemplateError:
                # Try loading as file path
                template = TemplateLoader.load_from_file(template)
        elif isinstance(template, Path):
            template = TemplateLoader.load_from_file(template)

        if not isinstance(template, SettingsTemplate):
            raise ValueError("Invalid template type. Expected SettingsTemplate.")

        if template.dimension != '2D':
            raise ValueError(f"Template is for {template.dimension}, but this is a 2D generator.")

        # Apply settings to config
        settings = template.settings
        if 'scale' in settings:
            self.config.scale = settings['scale']
        if 'bond_length' in settings:
            self.config.bond_length = settings['bond_length']
        if 'min_font_size' in settings:
            self.config.min_font_size = settings['min_font_size']
        if 'padding' in settings:
            self.config.padding = settings['padding']
        if 'margin' in settings:
            self.config.margin = settings['margin']
        if 'auto_orient' in settings:
            self.config.auto_orient = settings['auto_orient']

        print(f"✓ Applied settings template: {template.name}")
        if template.description:
            print(f"  {template.description}")


    def __repr__(self) -> str:
        return (
            f"MoleculeGenerator2D(identifier='{self.identifier}', "
            f"compound='{self.compound_name}', atoms={self.mol.GetNumAtoms()})"
        )
