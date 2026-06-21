"""
wikimolgen.wikimol2d - 2D Molecular Structure Generation
=========================================================
Config-driven 2D molecular visualization with SVG export and auto-orientation.
Uses ConfigLoader for centralized configuration management.
"""

import re
import dataclasses
from pathlib import Path

import numpy as np
from rdkit.Chem import AllChem
from rdkit.Chem.Draw import rdMolDraw2D

from wikimolgen.configs import ColorConfig, Config2D, ConfigLoader
from wikimolgen.core import fetch_compound, validate_smiles
from wikimolgen.rendering.amine_canonicalization import (
    AmineCanonicalizer,
    orient_all_amines,
)
from wikimolgen.rendering.optimization import (
    _separate_heavy_substituents,
    find_optimal_2d_rotation,
    is_phenethylamine,
    orient_phenethylamine_sidechain,
)
from wikimolgen.rendering.utils import load_color_config, resolve_settings_template


def _parse_indices(raw: str) -> list[int] | None:
    """Parse comma-separated indices string into int list."""
    if not raw or not raw.strip():
        return None
    try:
        return [int(x.strip()) for x in raw.split(",") if x.strip()]
    except ValueError:
        return None


def _make_highlight_colors(config: Config2D) -> dict[int, tuple[float, float, float]] | None:
    """Build highlightAtomColors dict from config."""
    atoms = _parse_indices(config.highlight_atoms)
    if not atoms or not config.highlight_color:
        return None
    raw = config.highlight_color.lstrip("#")
    if len(raw) != 6:
        return None
    try:
        rgb = tuple(int(raw[i : i + 2], 16) / 255.0 for i in (0, 2, 4))
    except ValueError:
        return None
    return {a: rgb for a in atoms}


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
    >>> config = ConfigLoader.load_template("wikipedia_2d")
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
        config: Config2D | None = None,
        angle_degrees: float | None = None,
        **kwargs,
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
        self._amines_oriented: bool = False

        # Load configuration
        if config is None:
            # Build from parameters
            overrides = {}
            if angle_degrees is not None:
                overrides["angle_degrees"] = angle_degrees  # Degrees directly
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

        if self.config.auto_orient_2d and not self._amines_oriented:
            self._rotation_angle = find_optimal_2d_rotation(self.mol)
        else:
            self._rotation_angle = self.config.angle_degrees
        angle_rad = np.radians(self._rotation_angle)

        # Build rotation matrix
        rotation_matrix = np.array(
            [[np.cos(angle_rad), -np.sin(angle_rad)], [np.sin(angle_rad), np.cos(angle_rad)]]
        )

        return centered @ rotation_matrix.T

    def _compute_canvas_size(self, coords: np.ndarray) -> tuple[int, int, float, float]:
        minx, miny = coords.min(axis=0)
        maxx, maxy = coords.max(axis=0)

        margin = max(self.config.margin, self.config.max_font_size * 2 / self.config.scale)
        minx -= margin
        miny -= margin
        maxx += margin
        maxy += margin

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
        if self.mol.GetNumConformers() == 0:
            if self.config.use_coord_gen:
                from rdkit.Chem import rdDepictor

                rdDepictor.SetPreferCoordGen(True)
                AllChem.Compute2DCoords(self.mol)
            else:
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
        # Rotate coordinates (stores angle in self._rotation_angle)
        rotated = self._rotate_coords(coords)

        # Compute canvas size
        width, height, minx, miny = self._compute_canvas_size(rotated)

        # Translate coordinates to canvas space
        for i, pos in enumerate(rotated):
            newx = pos[0] - minx
            newy = pos[1] - miny
            conf.SetAtomPosition(i, (newx, newy, 0.0))

        # ACS mode uses auto-size drawer + post-generation scaling to target
        # dimensions, with SetACS1996Mode handling all styling internally.
        # Non-ACS mode draws directly at the calculated canvas size with
        # user-configurable options.
        if self.config.acs_mode:
            drawer = rdMolDraw2D.MolDraw2DSVG(-1, -1)
            opts = drawer.drawOptions()
            mean_bl = rdMolDraw2D.MeanBondLength(self.mol)
            if mean_bl <= 0.0:
                AllChem.Compute2DCoords(self.mol)
                mean_bl = rdMolDraw2D.MeanBondLength(self.mol)
            if mean_bl <= 0.0:
                mean_bl = 1.0
            rdMolDraw2D.SetACS1996Mode(opts, mean_bl)
            if self.config.transparent_background:
                opts.setBackgroundColour((0, 0, 0, 0))
        else:
            drawer = rdMolDraw2D.MolDraw2DSVG(width, height)
            opts = drawer.drawOptions()
            opts.fixedBondLength = self.config.bond_length
            opts.padding = self.config.padding
            opts.minFontSize = self.config.min_font_size
            opts.additionalAtomLabelPadding = self.config.additional_atom_label_padding
            opts.legendFontSize = self.config.legend_font_size
            opts.maxFontSize = self.config.max_font_size
            if hasattr(opts, "annotationFontScale"):
                opts.annotationFontScale = self.config.font_size_scale
            elif hasattr(opts, "fontSizeScale"):
                opts.fontSizeScale = self.config.font_size_scale
            if hasattr(opts, "setDotsPerAngstrom"):
                opts.setDotsPerAngstrom(self.config.dots_per_angstrom)
            if self.config.use_bw_palette:
                opts.useBWAtomPalette()
            if self.config.transparent_background:
                opts.setBackgroundColour((0, 0, 0, 0))
            opts.bondLineWidth = self.config.bond_line_width
            opts.addStereoAnnotation = self.config.add_stereo_annotation
            opts.includeRadicals = self.config.include_radicals
            opts.scalingFactor = self.config.scaling_factor
            opts.explicitMethyl = self.config.explicit_methyl
            opts.noAtomLabels = self.config.no_atom_labels
            opts.multipleBondOffset = self.config.multiple_bond_offset
            opts.includeAtomTags = self.config.include_atom_tags
            opts.includeChiralFlagLabel = self.config.include_chiral_flag
            opts.comicMode = self.config.comic_mode
            if self.config.fixed_font_size > 0:
                opts.fixedFontSize = self.config.fixed_font_size

        rdMolDraw2D.PrepareAndDrawMolecule(
            drawer,
            self.mol,
            legend=self.config.legend if self.config.legend else "",
            highlightAtoms=_parse_indices(self.config.highlight_atoms) or None,
            highlightBonds=_parse_indices(self.config.highlight_bonds) or None,
            highlightAtomColors=_make_highlight_colors(self.config),
        )
        drawer.FinishDrawing()

        svg = drawer.GetDrawingText()
        if self.config.transparent_background:
            svg = svg.replace("fill:white", "fill:none")

        # Scale auto-sized ACS SVGs to a minimum display size
        if self.config.acs_mode:
            svg = self._scale_svg(svg, self.config.svg_min_display_size)

        if self.config.strip_annotation_markers:
            svg = re.sub(
                r"<path class=\'atom-\d+\'[^>]*stroke:#FF0000[^>]*/>\s*",
                "",
                svg,
            )

        svg = self._clean_svg_for_wikipedia(svg)

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
        return {f.name: getattr(self.config, f.name) for f in dataclasses.fields(Config2D)}

    def load_color_template(self, template: str | Path | ColorConfig | dict) -> None:
        if isinstance(template, dict):
            self.config.use_bw_palette = template.get("use_bw_palette", False)
            self.config.transparent_background = template.get("transparent_background", False)
            return
        color_cfg = load_color_config(template)
        self.config.use_bw_palette = False
        self.config.transparent_background = color_cfg.bg_color == "white"

    def load_settings_template(self, template: str | Path | Config2D | dict) -> None:
        if isinstance(template, dict):
            self.config.update(**template)
            return
        if isinstance(template, Config2D):
            self.config = template
            return
        cfg = resolve_settings_template(template)
        if isinstance(cfg, Config2D):
            self.config = cfg

    def _apply_amine_orientation(self) -> dict:
        """
        Apply automatic amine orientation based on molecule type.

        When active, sets self._amines_oriented so that PCA auto-rotation
        in _rotate_coords is skipped — otherwise PCA would undo the
        deliberate amine orientation.

        Returns
        -------
        dict
            Orientation results with information about applied transformations
        """
        self._amines_oriented = False

        if not self.config.auto_orient_amines:
            return {}

        if is_phenethylamine(self.mol):
            success = orient_phenethylamine_sidechain(
                self.mol, target_angle_deg=self.config.phenethylamine_target
            )
            if success:
                _separate_heavy_substituents(self.mol)
                self._amines_oriented = True
            return {
                "type": "phenethylamine",
                "success": success,
                "target_angle": self.config.phenethylamine_target,
            }

        amine_count = orient_all_amines(self.mol, target_angle=self.config.amine_target_angle)
        if amine_count > 0:
            self._amines_oriented = True
            return {
                "type": "amines",
                "success": True,
                "count": amine_count,
                "target_angle": self.config.amine_target_angle,
            }

        return {}

    def _print_generation_summary(self, width: int, height: int, amine_orientation: dict) -> None:
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
        print("2D structure saved")
        print(f"  Compound: {self.compound_name}")
        print(f"  Dimensions: {width}x{height} px")
        print(f"  Atoms: {self.mol.GetNumAtoms()}, Bonds: {self.mol.GetNumBonds()}")

        angle_deg = getattr(self, "_rotation_angle", self.config.angle_degrees)
        if self.config.auto_orient_2d:
            print(f"  Auto-oriented: {angle_deg:.1f}°")
        else:
            print(f"  Rotation: {angle_deg:.1f}°")

        if amine_orientation:
            if amine_orientation["type"] == "phenethylamine":
                print(f"  Phenethylamine detected, sidechain: {amine_orientation['target_angle']}°")
            elif amine_orientation["type"] == "amines":
                print(
                    f"  Amines oriented: {amine_orientation['count']} groups @ {amine_orientation['target_angle']}°"
                )

    @staticmethod
    def _clean_svg_for_wikipedia(svg_text: str) -> str:
        svg_text = re.sub(r"\s+xmlns:rdkit='[^']*'", "", svg_text)
        svg_text = re.sub(r"<!-- END OF HEADER -->\s*", "", svg_text)
        svg_text = re.sub(r"\s+class='[^']*'", "", svg_text)
        return svg_text

    @staticmethod
    def _scale_svg(m_svg: str, min_size: int = 600) -> str:
        # Parse width/height from SVG (handles both quote styles and "px" suffix)
        dims = re.findall(r"""(?:width|height)=["'](\d+)""", m_svg)
        if len(dims) < 2:
            return m_svg
        ow, oh = int(dims[0]), int(dims[1])

        s = max(1, min_size // ow, min_size // oh)
        if s == 1:
            return m_svg

        # Scale width/height dimensions only. Keep original viewBox so the
        # browser naturally scales all strokes, fonts, and paths proportionally.
        m_svg = re.sub(
            r"""(width|height)=["'](\d+)(?:px)?["']""",
            lambda mm: f'{mm.group(1)}="{int(mm.group(2)) * s}"',
            m_svg,
        )
        return m_svg

    def __repr__(self) -> str:
        return (
            f"MoleculeGenerator2D("
            f"identifier={self.identifier!r}, "
            f"compound={self.compound_name!r}, "
            f"atoms={self.mol.GetNumAtoms()})"
        )
