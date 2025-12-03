"""
wikimolgen.wikimol2d - 2D Molecular Structure Generation
=========================================================
Config-driven 2D molecular visualization with SVG export and auto-orientation.
Uses ConfigLoader for centralized configuration management.
"""

from pathlib import Path
from typing import Optional, Union

import numpy as np
from rdkit import Chem
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

from wikimolgen.configs import ConfigLoader, Config2D
from wikimolgen.core import fetch_compound, validate_smiles
from wikimolgen.predefined_templates import (
    get_predefined_settings_template,
    get_predefined_color_template,
    TemplateLoader,
    SettingsTemplate,
    ColorStyleTemplate,
    TemplateError,
)
from wikimolgen.rendering.amine_canonicalization import (
    AmineCanonicalizer,
    orient_all_amines,
)
from wikimolgen.rendering.optimization import find_optimal_2d_rotation
from wikimolgen.rendering.optimization import (
    is_phenethylamine,
    orient_phenethylamine_sidechain,
)


class MoleculeGenerator2D:
    """
    Generate 2D molecular structure diagrams with config-driven rendering.

    Uses Config2D configuration objects for centralized settings management.
    Supports predefined templates and runtime configuration adjustments.

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
    config : Config2D
        Drawing configuration object

    Examples
    --------
    >>> # Using ConfigLoader defaults
    >>> config = ConfigLoader.get_2d_config()
    >>> gen = MoleculeGenerator2D("aspirin", config=config)
    >>> gen.draw("aspirin.svg")

    >>> # Using template
    >>> config = ConfigLoader.load_template("publication_2d")
    >>> gen = MoleculeGenerator2D("aspirin", config=config)
    >>> gen.draw("aspirin.svg")

    >>> # With custom overrides
    >>> config = ConfigLoader.get_2d_config(
    ...     overrides={"scale": 50.0, "margin": 0.8}
    ... )
    >>> gen = MoleculeGenerator2D("aspirin", config=config)
    >>> gen.draw("aspirin.svg")
    """

    def __init__(
            self,
            identifier: str,
            config: Optional[Config2D] = None,
            angle_degrees: Optional[float] = None,
            **kwargs
    ):
        """
        Initialize 2D molecule generator with config-driven setup.

        Parameters
        ----------
        identifier : str
            PubChem CID, compound name, or SMILES string
        config : Config2D, optional
            Configuration object. If None, uses ConfigLoader defaults.

        Raises
        ------
        ValueError
            If compound cannot be fetched or SMILES is invalid
        """
        self.identifier = identifier
        self.smiles, self.compound_name = fetch_compound(identifier)
        self.mol = validate_smiles(self.smiles)
        self.amine_canonicalizer = AmineCanonicalizer(self.mol)

        # Load configuration
        if config is None:
            # Build from parameters
            overrides = {}
            if angle_degrees is not None:
                overrides['angle_degrees'] = angle_degrees  # Degrees directly
            overrides.update(kwargs)

            if overrides:
                self.config = ConfigLoader.get_2d_config(overrides=overrides)
            else:
                self.config = ConfigLoader.get_2d_config()
        else:
            # Use provided config
            self.config = config

    def _rotate_coords(self, coords: np.ndarray) -> np.ndarray:
        """Rotate coordinates - convert degrees to radians here ONLY"""
        center = coords.mean(axis=0)
        centered = coords - center

        angle_rad = np.radians(self.config.angle_degrees)
        if self.config.auto_orient_2d:
            angle_rad = find_optimal_2d_rotation(self.mol)

        # Build rotation matrix
        rotation_matrix = np.array([
            [np.cos(angle_rad), -np.sin(angle_rad)],
            [np.sin(angle_rad), np.cos(angle_rad)]
        ])

        return centered @ rotation_matrix.T

    def _compute_canvas_size(
            self, coords: np.ndarray
    ) -> tuple[int, int, float, float]:
        """
        Calculate canvas dimensions with margins to prevent clipping.

        Parameters
        ----------
        coords : np.ndarray
            Nx2 array of coordinates

        Returns
        -------
        tuple[int, int, float, float]
            width, height, minx, miny
        """
        minx, miny = coords.min(axis=0)
        maxx, maxy = coords.max(axis=0)

        minx -= self.config.margin
        miny -= self.config.margin
        maxx += self.config.margin
        maxy += self.config.margin

        width = int((maxx - minx) * self.config.scale)
        height = int((maxy - miny) * self.config.scale)

        return width, height, minx, miny

    def draw(self, output: str = "molecule2d.svg") -> Path:
        """
        Generate 2D structure and save as SVG.

        Parameters
        ----------
        output : str, optional
            Output SVG filename (default: molecule2d.svg)

        Returns
        -------
        Path
            Path to saved SVG file
        """
        # Compute 2D coordinates
        if self.mol.GetNumConformers() == 0:  # ← Only compute if needed
            AllChem.Compute2DCoords(self.mol)

        # Apply amine orientation
        amine_orientation = self._apply_amine_orientation()

        # Extract coordinates
        conf = self.mol.GetConformer()
        coords = np.array(
            [
                (conf.GetAtomPosition(i).x, conf.GetAtomPosition(i).y)
                for i in range(self.mol.GetNumAtoms())
            ]
        )
        # Rotate coordinates
        rotated = self._rotate_coords(coords)

        # Compute canvas size
        width, height, minx, miny = self._compute_canvas_size(rotated)

        # Translate coordinates to canvas space
        for i, pos in enumerate(rotated):
            newx = pos[0] - minx
            newy = pos[1] - miny
            conf.SetAtomPosition(i, (newx, newy, 0.0))

        # Draw molecule
        drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
        opts = drawer.drawOptions()

        if self.config.use_bw_palette:
            opts.useBWAtomPalette()

        opts.fixedBondLength = self.config.bond_length
        opts.padding = self.config.padding
        opts.minFontSize = self.config.min_font_size
        opts.additionalAtomLabelPadding = self.config.additional_atom_label_padding

        if self.config.transparent_background:
            opts.setBackgroundColour((0, 0, 0, 0))

        rdMolDraw2D.PrepareAndDrawMolecule(drawer, self.mol)
        drawer.FinishDrawing()

        # Get SVG and process
        svg = drawer.GetDrawingText()
        if self.config.transparent_background:
            svg = svg.replace("fill:white", "fill:none")

        # Save file
        output_path = Path(output)
        output_path.write_text(svg)

        # Print summary
        self._print_generation_summary(width, height, amine_orientation)

        return output_path

    def apply_settings(self, **kwargs) -> None:
        """
        Apply settings adjustments at runtime.

        Parameters
        ----------
        **kwargs
            Configuration parameters to override
            (scale, margin, bond_length, min_font_size, padding, etc.)
        """
        for key, value in kwargs.items():
            if hasattr(self.config, key):
                setattr(self.config, key, value)
            else:
                raise ValueError(f"Unknown configuration parameter: {key}")

    def get_config_dict(self) -> dict:
        """
        Export current configuration as dictionary.

        Returns
        -------
        dict
            Configuration as dictionary (suitable for JSON serialization)
        """
        return {
            "scale": self.config.scale,
            "margin": self.config.margin,
            "bond_length": self.config.bond_length,
            "min_font_size": self.config.min_font_size,
            "padding": self.config.padding,
            "use_bw_palette": self.config.use_bw_palette,
            "transparent_background": self.config.transparent_background,
            "auto_orient_2d": self.config.auto_orient_2d,
            "auto_orient_amines": self.config.auto_orient_amines,
            "amine_target_angle": self.config.amine_target_angle,
            "phenethylamine_target": self.config.phenethylamine_target,
        }

    def load_color_template(
            self, template: Union[str, Path, ColorStyleTemplate]
    ) -> None:
        """
        Apply a color style template to the generator.

        Parameters
        ----------
        template : ColorStyleTemplate, str, or Path
            Color template object, predefined template name,
            or path to template file

        Examples
        --------
        >>> gen = MoleculeGenerator2D("aspirin")
        >>> gen.load_color_template("cpk_standard")
        >>> gen.draw("aspirin.svg")
        """
        if isinstance(template, str):
            try:
                template = get_predefined_color_template(template)
            except TemplateError:
                template = TemplateLoader.load_from_file(template)
        elif isinstance(template, Path):
            template = TemplateLoader.load_from_file(template)

        if not isinstance(template, ColorStyleTemplate):
            raise ValueError(
                "Invalid template type. Expected ColorStyleTemplate."
            )

        self.config.use_bw_palette = template.use_bw_palette
        self.config.transparent_background = template.transparent_background

        print(f"Applied color template: {template.name}")
        if template.description:
            print(f"  {template.description}")

    def load_settings_template(
            self, template: Union[str, Path, SettingsTemplate]
    ) -> None:
        """
        Apply a settings template to the generator.

        Parameters
        ----------
        template : SettingsTemplate, str, or Path
            Settings template object, predefined template name,
            or path to template file

        Examples
        --------
        >>> gen = MoleculeGenerator2D("caffeine")
        >>> gen.load_settings_template("publication_2d")
        >>> gen.draw("caffeine.svg")
        """
        if isinstance(template, str):
            try:
                template = get_predefined_settings_template(template)
            except TemplateError:
                template = TemplateLoader.load_from_file(template)
        elif isinstance(template, Path):
            template = TemplateLoader.load_from_file(template)

        if not isinstance(template, SettingsTemplate):
            raise ValueError(
                "Invalid template type. Expected SettingsTemplate."
            )

        if template.dimension != "2D":
            raise ValueError(
                f"Template is for {template.dimension}, but this is a 2D generator."
            )

        # Apply settings from template
        settings = template.settings
        if "scale" in settings:
            self.config.scale = settings["scale"]
        if "bond_length" in settings:
            self.config.bond_length = settings["bond_length"]
        if "min_font_size" in settings:
            self.config.min_font_size = settings["min_font_size"]
        if "padding" in settings:
            self.config.padding = settings["padding"]
        if "margin" in settings:
            self.config.margin = settings["margin"]
        if "auto_orient_2d" in settings:
            self.config.auto_orient_2d = settings["auto_orient_2d"]

        print(f"Applied settings template: {template.name}")
        if template.description:
            print(f"  {template.description}")

    def _apply_amine_orientation(self) -> dict:
        """
        Apply automatic amine orientation based on molecule type.

        Returns
        -------
        dict
            Orientation results with information about applied transformations
        """
        if not self.config.auto_orient_amines:
            return {}

        if is_phenethylamine(self.mol):
            success = orient_phenethylamine_sidechain(
                self.mol, target_angle_deg=self.config.phenethylamine_target
            )
            return {
                "type": "phenethylamine",
                "success": success,
                "target_angle": self.config.phenethylamine_target,
            }

        amine_count = orient_all_amines(
            self.mol, target_angle=self.config.amine_target_angle
        )
        if amine_count > 0:
            return {
                "type": "amines",
                "success": True,
                "count": amine_count,
                "target_angle": self.config.amine_target_angle,
            }

        return {}

    def _print_generation_summary(
            self, width: int, height: int, amine_orientation: dict
    ) -> None:
        """
        Print generation summary to console.

        Parameters
        ----------
        width : int
            Canvas width in pixels
        height : int
            Canvas height in pixels
        amine_orientation : dict
            Amine orientation results
        """
        print(f"2D structure saved")
        print(f"  Compound: {self.compound_name}")
        print(f"  Dimensions: {width}x{height} px")
        print(f"  Atoms: {self.mol.GetNumAtoms()}, Bonds: {self.mol.GetNumBonds()}")

        if self.config.auto_orient_2d:
            angle_deg = find_optimal_2d_rotation(self.mol)
            print(f"  Auto-oriented: {angle_deg:.1f}°")
        else:
            angle_deg = self.config.angle_degrees
            print(f"  Rotation: {angle_deg:.1f}°")

        if amine_orientation:
            if amine_orientation["type"] == "phenethylamine":
                print(
                    f"  Phenethylamine detected, sidechain: {amine_orientation['target_angle']}°"
                )
            elif amine_orientation["type"] == "amines":
                print(
                    f"  Amines oriented: {amine_orientation['count']} groups @ {amine_orientation['target_angle']}°"
                )

    def __repr__(self) -> str:
        return (
            f"MoleculeGenerator2D("
            f"identifier={self.identifier!r}, "
            f"compound={self.compound_name!r}, "
            f"atoms={self.mol.GetNumAtoms()})"
        )
