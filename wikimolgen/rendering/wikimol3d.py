"""
wikimolgen.wikimol3d - 3D Molecular Structure Generation
=========================================================
Class-based 3D conformer generation with PyMOL rendering and auto-cropping.
Extended element colors and RDKit configuration options.

Uses split Config3D structure (render + conformer) from ConfigLoader.
"""

from pathlib import Path
from typing import Optional, Literal, Union

from rdkit import Chem
from rdkit.Chem import AllChem, rdmolfiles, rdForceFieldHelpers

from wikimolgen.configs import ConfigLoader, Config3D
from wikimolgen.core import fetch_compound, validate_smiles
from wikimolgen.rendering.optimization import (
    find_optimal_3d_orientation,
    optimize_zoom_buffer,
)

ForceFieldType = Literal["MMFF94", "UFF"]


def color_name_to_rgb(color_name: str) -> tuple:
    """Convert color name to RGB tuple for PyMOL."""
    color_map = {
        # Grays
        "gray10": (0.10, 0.10, 0.10), "gray20": (0.20, 0.20, 0.20),
        "gray25": (0.25, 0.25, 0.25), "gray30": (0.30, 0.30, 0.30),
        "gray40": (0.40, 0.40, 0.40), "gray50": (0.50, 0.50, 0.50),
        "gray60": (0.60, 0.60, 0.60), "gray70": (0.70, 0.70, 0.70),
        "gray80": (0.80, 0.80, 0.80), "gray85": (0.85, 0.85, 0.85),
        "gray90": (0.90, 0.90, 0.90),
        # Extended colors
        "palegreen": (0.596, 0.984, 0.596), "firebrick": (0.698, 0.133, 0.133),
        "darkorange": (1.0, 0.549, 0.0), "chocolate": (0.824, 0.412, 0.118),
        "goldenrod": (0.855, 0.647, 0.125), "gold": (1.0, 0.843, 0.0),
        # PyMOL native (fallback)
        "white": (1.0, 1.0, 1.0), "black": (0.0, 0.0, 0.0),
        "red": (1.0, 0.0, 0.0), "green": (0.0, 1.0, 0.0),
        "blue": (0.0, 0.0, 1.0), "yellow": (1.0, 1.0, 0.0),
        "cyan": (0.0, 1.0, 1.0), "magenta": (1.0, 0.0, 1.0),
        "orange": (1.0, 0.647, 0.0), "purple": (0.627, 0.125, 0.941),
        "pink": (1.0, 0.753, 0.796), "brown": (0.647, 0.165, 0.165),
        "gray": (0.502, 0.502, 0.502), "slate": (0.439, 0.502, 0.565),
        "salmon": (0.980, 0.502, 0.447), "violet": (0.933, 0.510, 0.933),
        "forest": (0.133, 0.545, 0.133),
    }
    return color_map.get(color_name.lower(), (0.5, 0.5, 0.5))


class MoleculeGenerator3D:
    """
    Generate 3D molecular structures with conformer optimization and rendering.

    Uses split Config3D configuration with render and conformer configs.
    Supports comprehensive element coloring, auto-cropping, and multi-conformer generation.

    Attributes
    ----------
    identifier : str
        PubChem CID, compound name, or SMILES string
    smiles : str
        Canonical SMILES representation
    compound_name : str
        Name of the compound
    mol : Chem.Mol
        RDKit molecule object with hydrogens
    energy : Optional[float]
        Final optimized energy in kcal/mol
    config : Config3D
        Configuration object with split render and conformer configs

    Examples
    --------
    >>> gen = MoleculeGenerator3D("24802108")
    >>> gen.generate(optimize=True, render=True, output_base="4-MeO-DiPT")

    >>> gen = MoleculeGenerator3D("CC(C)N(CCC1=CNC2=C1C(=CC=C2)OC)C(C)C")
    >>> sdf_path, png_path = gen.generate(force_field="MMFF94", render=True)
    """

    def __init__(
        self,
        identifier: str,
        config: Optional[Config3D] = None,
        random_seed: int = 1,
        **kwargs
    ):
        """
        Initialize 3D molecule generator with config-driven setup.

        Parameters
        ----------
        identifier : str
            PubChem CID, compound name, or SMILES string
        config : Config3D, optional
            Configuration object. If None, build from kwargs
        random_seed : int, optional
            Random seed for conformer generation (default: 1)
        **kwargs
            Additional configuration parameters
        """
        self.identifier = identifier
        self.smiles, self.compound_name = fetch_compound(identifier)
        self.mol = validate_smiles(self.smiles)
        self.mol = Chem.AddHs(self.mol)

        self.random_seed = random_seed
        self.energy: Optional[float] = None

        # Load configuration
        if config is None:
            if kwargs:
                self.config = ConfigLoader.get_3d_config(overrides=kwargs)
            else:
                self.config = ConfigLoader.get_3d_config()
        else:
            self.config = config

    def _embed_conformer(self) -> None:
        """Generate 3D conformer using ETKDG with configurable parameters."""
        params = AllChem.ETKDGv3()
        params.randomSeed = self.random_seed
        params.useRandomCoords = self.config.conformer.use_random_coords
        params.clearConfs = self.config.conformer.clear_confs
        params.useBasicKnowledge = self.config.conformer.use_basic_knowledge
        params.enforceChirality = self.config.conformer.enforce_chirality
        params.useSmallRingTorsions = self.config.conformer.use_small_ring_torsions

        if self.config.conformer.num_conformers == 1:
            result = AllChem.EmbedMolecule(self.mol, params)
            if result == -1:
                raise ValueError("Failed to generate 3D conformer")
        else:
            # Multi-conformer generation
            result = AllChem.EmbedMultipleConfs(
                self.mol,
                numConfs=self.config.conformer.num_conformers,
                params=params,
                pruneRmsThresh=self.config.conformer.prune_rms_thresh
            )
            if len(result) == 0:
                raise ValueError("Failed to generate 3D conformers")

    def _optimize_geometry(self, force_field: ForceFieldType, max_iterations: int = 200) -> None:
        """
        Optimize molecular geometry using force field.

        Parameters
        ----------
        force_field : ForceFieldType
            "MMFF94" or "UFF"
        max_iterations : int, optional
            Maximum optimization iterations (default: 200)
        """
        max_iters = max_iterations or self.config.conformer.max_iterations

        if force_field == "MMFF94":
            if self.config.conformer.num_conformers == 1:
                result = rdForceFieldHelpers.MMFFOptimizeMolecule(self.mol, maxIters=max_iters)
                if result == 0:
                    props = rdForceFieldHelpers.MMFFGetMoleculeProperties(self.mol)
                    ff = rdForceFieldHelpers.MMFFGetMoleculeForceField(self.mol, props)
                    self.energy = ff.CalcEnergy()
            else:
                results = rdForceFieldHelpers.MMFFOptimizeMoleculeConfs(self.mol, maxIters=max_iters)
                energies = [r[1] for r in results]
                self.energy = min(energies)

        elif force_field == "UFF":
            if self.config.conformer.num_conformers == 1:
                result = rdForceFieldHelpers.UFFOptimizeMolecule(self.mol, maxIters=max_iters)
                if result == 0:
                    ff = rdForceFieldHelpers.UFFGetMoleculeForceField(self.mol)
                    self.energy = ff.CalcEnergy()
            else:
                results = rdForceFieldHelpers.UFFOptimizeMoleculeConfs(self.mol, maxIters=max_iters)
                energies = [r[1] for r in results]
                self.energy = min(energies)
        else:
            raise ValueError(f"Unknown force field: {force_field}")

    def _save_sdf(self, output: str) -> Path:
        """
        Save molecule as SDF file.

        Parameters
        ----------
        output : str
            Output SDF filename

        Returns
        -------
        Path
            Path to saved SDF file
        """
        output_path = Path(output)
        rdmolfiles.MolToMolFile(self.mol, str(output_path))
        return output_path

    def _auto_crop_image(self, image_path: Path, margin: int = 10, contrast_factor: float = 1.15) -> None:
        """
        Auto-crop PNG to molecule bounds using alpha channel only (no white compositing).

        Keeps transparency untouched—best for Discord/transparent backgrounds.

        Parameters
        ----------
        image_path : Path
            Path to PNG image
        margin : int
            Margin around molecule in pixels (default: 10)
        contrast_factor : float
            Contrast enhancement factor (default: 1.15)
        """
        from PIL import Image

        img = Image.open(image_path).convert("RGBA")
        alpha = img.split()[-1]

        # Find the bounding box of non-transparent pixels
        bbox = alpha.getbbox()

        if bbox:
            left, top, right, bottom = bbox
            width, height = img.size

            left = max(0, left - margin)
            top = max(0, top - margin)
            right = min(width, right + margin)
            bottom = min(height, bottom + margin)

            img = img.crop((left, top, right, bottom))
            img.save(image_path)
        else:
            img.save(image_path)

    def _render_pymol(self, sdf_path: Path, output: str) -> Path:
        """
        Render molecule using PyMOL with auto-cropping.

        Parameters
        ----------
        sdf_path : Path
            Path to SDF file
        output : str
            Output PNG filename

        Returns
        -------
        Path
            Path to saved PNG file
        """
        try:
            import pymol2
        except ImportError:
            raise ImportError(
                "pymol2 not installed. Install with: conda install -c conda-forge pymol-open-source"
            )

        cfg = self.config.render
        output_path = Path(output)

        with pymol2.PyMOL() as pymol:
            cmd = pymol.cmd

            # Load molecule
            cmd.load(str(sdf_path))
            cmd.hide("everything")
            cmd.show("sticks", "all")
            cmd.show("spheres", "all")
            cmd.bg_color(cfg.bg_color)

            element_colors = {
                # Common organic elements
                "C": "gray25",  # Carbon - dark gray
                "H": "gray85",  # Hydrogen - light gray
                "N": "blue",  # Nitrogen - blue
                "O": "red",  # Oxygen - red
                "S": "yellow",  # Sulfur - yellow
                "P": "orange",  # Phosphorus - orange

                # Halogens
                "F": "palegreen",  # Fluorine - pale green
                "Cl": "green",  # Chlorine - green
                "Br": "firebrick",  # Bromine - dark red/brown
                "I": "purple",  # Iodine - purple

                # Metals (alkali & alkaline earth)
                "Li": "violet",  # Lithium
                "Na": "slate",  # Sodium
                "K": "violet",  # Potassium
                "Mg": "forest",  # Magnesium
                "Ca": "forest",  # Calcium

                # Transition metals (common in organometallics)
                "Fe": "darkorange",  # Iron
                "Cu": "chocolate",  # Copper
                "Zn": "brown",  # Zinc
                "Ni": "forest",  # Nickel
                "Co": "salmon",  # Cobalt
                "Mn": "violet",  # Manganese
                "Cr": "gray50",  # Chromium
                "Pd": "forest",  # Palladium
                "Pt": "gray50",  # Platinum
                "Au": "gold",  # Gold
                "Ag": "gray70",  # Silver

                # Other common elements
                "B": "salmon",  # Boron
                "Si": "goldenrod",  # Silicon
                "Se": "orange",  # Selenium
                "As": "violet",  # Arsenic

                "He": "cyan",
                "Ne": "cyan",
                "Ar": "cyan",
                "Kr": "cyan",
                "Xe": "cyan",
            }

            for element, color_name in element_colors.items():
                rgb = color_name_to_rgb(color_name)
                custom_color = f"custom_{color_name}"
                cmd.set_color(custom_color, list(rgb))
                cmd.color(custom_color, f"elem {element}")

            # Stick properties
            cmd.set("stick_radius", cfg.stick_radius)
            cmd.set("stick_quality", cfg.stick_quality)
            cmd.set("stick_transparency", cfg.stick_transparency)

            if cfg.stick_color:
                stick_rgb = color_name_to_rgb(cfg.stick_color)
                cmd.set_color("custom_stick", list(stick_rgb))
                cmd.set("stick_color", "custom_stick")

            # Sphere properties
            cmd.set("sphere_scale", cfg.sphere_scale)
            cmd.set("sphere_quality", cfg.sphere_quality)
            cmd.set("sphere_transparency", cfg.sphere_transparency)

            # Stick ball properties
            cmd.set("stick_ball", "on")
            cmd.set("stick_ball_ratio", cfg.stick_ball_ratio)

            # Valence display
            if cfg.valence > 0:
                cmd.set("valence", cfg.valence)

            # Rendering properties
            cmd.set("ambient", cfg.ambient)
            cmd.set("specular", cfg.specular)
            cmd.set("shininess", cfg.shininess)
            cmd.set("ray_shadows", cfg.ray_shadows)
            cmd.set("antialias", cfg.antialias)
            cmd.set("ray_opaque_background", 0)
            cmd.set("depth_cue", cfg.depth_cue)

            if cfg.depth_cue:
                cmd.set("fog_start", cfg.fog_start)

            # Direct lighting control
            cmd.set("direct", cfg.direct)
            cmd.set("reflect", cfg.reflect)

            # Ray tracing parameters
            cmd.set("ray_trace_mode", cfg.ray_trace_mode)
            cmd.set("ray_trace_gain", cfg.ray_trace_gain)
            cmd.set("ray_trace_color", cfg.ray_trace_color)
            cmd.set("ray_transparency_contrast", cfg.ray_transparency_contrast)
            cmd.set("ray_transparency_oblique", cfg.ray_transparency_oblique)

            # Position and orientation
            if cfg.auto_orient_3d:
                x_opt, y_opt, z_opt = find_optimal_3d_orientation(self.mol)
                zoom_opt = optimize_zoom_buffer(self.mol)
                cmd.orient("all")
                cmd.turn("x", x_opt)
                cmd.turn("y", y_opt)
                cmd.turn("z", z_opt)
                cmd.zoom("all", buffer=zoom_opt)
                print(f" Auto-oriented: x={x_opt:.1f}°, y={y_opt:.1f}°, z={z_opt:.1f}°")
                print(f" Auto-zoom: {zoom_opt:.2f}")
            else:
                cmd.orient("all")
                cmd.turn("x", cfg.x_rotation)
                cmd.turn("y", cfg.y_rotation)
                cmd.turn("z", cfg.z_rotation)
                cmd.zoom("all", buffer=cfg.zoom_buffer)

            # Render
            if cfg.ray_trace_mode > 0:
                cmd.ray(width=cfg.width, height=cfg.height)
                cmd.png(str(output_path))
            else:
                cmd.png(str(output_path), width=cfg.width, height=cfg.height)

            # Auto-crop if enabled
            if cfg.auto_crop:
                self._auto_crop_image(output_path, margin=cfg.crop_margin)

            return output_path

    def generate(
        self,
        optimize: bool = True,
        force_field: ForceFieldType = "MMFF94",
        max_iterations: int = 200,
        render: bool = False,
        output_base: Optional[str] = None,
    ) -> tuple[Path, Optional[Path]]:
        """
        Generate 3D structure with optional rendering.

        Parameters
        ----------
        optimize : bool, optional
            Apply force field optimization (default: True)
        force_field : ForceFieldType, optional
            "MMFF94" or "UFF" (default: "MMFF94")
        max_iterations : int, optional
            Maximum optimization iterations (default: 200)
        render : bool, optional
            Render with PyMOL (default: False)
        output_base : str, optional
            Base name for output files (default: compound name or "molecule_3d")

        Returns
        -------
        tuple[Path, Optional[Path]]
            (sdf_path, png_path) - PNG path is None if render=False
        """
        if output_base is None:
            output_base = (
                self.compound_name.replace(" ", "_")
                if self.compound_name != "custom_smiles"
                else "molecule_3d"
            )

        # Generate conformer
        self._embed_conformer()

        # Optimize geometry
        if optimize:
            self._optimize_geometry(force_field, max_iterations)

        # Save SDF
        sdf_path = self._save_sdf(f"{output_base}.sdf")
        print(f"✓ 3D structure saved: {sdf_path}")
        print(f" Compound: {self.compound_name}")
        print(f" Atoms: {self.mol.GetNumAtoms()}, Bonds: {self.mol.GetNumBonds()}")

        if self.config.conformer.num_conformers > 1:
            print(f" Conformers: {self.mol.GetNumConformers()}")

        if optimize and self.energy is not None:
            print(f" Energy: {self.energy:.2f} kcal/mol ({force_field})")

        # Render with PyMOL
        png_path = None
        if render:
            png_path = self._render_pymol(sdf_path, f"{output_base}.png")
            print(f"✓ Rendered image saved: {png_path}")
            if self.config.render.auto_crop:
                print(f" Auto-cropped with {self.config.render.crop_margin}px margin")
            else:
                print(f" Dimensions: {self.config.render.width}×{self.config.render.height} px")

        return sdf_path, png_path

    def configure_rendering(self, **kwargs) -> None:
        """
        Update rendering configuration at runtime.

        Parameters
        ----------
        **kwargs
            Rendering parameters to override (50+ parameters supported)
            width, height, stick_radius, sphere_scale, antialias, auto_orient, etc.

        Raises
        ------
        ValueError
            If an unknown rendering parameter is provided
        """
        valid_render_params = {
            attr for attr in dir(self.config.render)
            if not attr.startswith('_') and not callable(getattr(self.config.render, attr))
        }

        for key, value in kwargs.items():
            if key in valid_render_params:
                setattr(self.config.render, key, value)
            else:
                raise ValueError(
                    f"Unknown rendering parameter: {key}\n"
                    f"Valid parameters: {', '.join(sorted(valid_render_params))}"
                )

    def configure_conformer(self, **kwargs) -> None:
        """
        Update conformer generation configuration.

        Parameters
        ----------
        **kwargs
            Conformer parameters to override
            (num_conformers, max_iterations, enforce_chirality, etc.)

        Raises
        ------
        ValueError
            If an unknown conformer parameter is provided
        """
        valid_conformer_params = {
            attr for attr in dir(self.config.conformer)
            if not attr.startswith('_') and not callable(getattr(self.config.conformer, attr))
        }

        for key, value in kwargs.items():
            if key in valid_conformer_params:
                setattr(self.config.conformer, key, value)
            else:
                raise ValueError(
                    f"Unknown conformer parameter: {key}\n"
                    f"Valid parameters: {', '.join(sorted(valid_conformer_params))}"
                )

    def load_color_template(
        self, template: Union[str, Path, "ColorStyleTemplate"]
    ) -> None:
        """
        Apply a color style template to the 3D generator.

        Parameters
        ----------
        template : ColorStyleTemplate, str, or Path
            Color template object, path to template file, or predefined template name

        Examples
        --------
        >>> gen = MoleculeGenerator3D("caffeine")
        >>> gen.load_color_template("cpk_standard") # Predefined template
        >>> gen.load_color_template("my_colors.json") # From file
        """
        from wikimolgen.predefined_templates import (
            TemplateLoader,
            ColorStyleTemplate,
            get_predefined_color_template,
            TemplateError,
        )

        # Load template if needed
        if isinstance(template, str):
            try:
                template = get_predefined_color_template(template)
            except TemplateError:
                template = TemplateLoader.load_from_file(template)
        elif isinstance(template, Path):
            template = TemplateLoader.load_from_file(template)

        if not isinstance(template, ColorStyleTemplate):
            raise ValueError("Invalid template type. Expected ColorStyleTemplate.")

        # Apply color settings to render config
        if hasattr(template, "element_colors") and template.element_colors:
            # Note: element_colors are applied dynamically in _render_pymol
            pass

        if hasattr(template, "stick_color") and template.stick_color:
            self.config.render.stick_color = template.stick_color

        if hasattr(template, "bg_color") and template.bg_color:
            self.config.render.bg_color = template.bg_color

        print(f"✓ Applied color template: {template.name}")
        if hasattr(template, "description") and template.description:
            print(f" {template.description}")

    def load_settings_template(
        self, template: Union[str, Path, "SettingsTemplate"]
    ) -> None:
        """
        Apply a settings template to the 3D generator.

        Parameters
        ----------
        template : SettingsTemplate, str, or Path
            Settings template object, path to template file, or predefined template name

        Examples
        --------
        >>> gen = MoleculeGenerator3D("dopamine")
        >>> gen.load_settings_template("high_quality_3d") # Predefined template
        >>> gen.load_settings_template("my_settings.json") # From file
        """
        from wikimolgen.predefined_templates import (
            TemplateLoader,
            SettingsTemplate,
            get_predefined_settings_template,
            TemplateError,
        )

        # Load template if needed
        if isinstance(template, str):
            try:
                template = get_predefined_settings_template(template)
            except TemplateError:
                template = TemplateLoader.load_from_file(template)
        elif isinstance(template, Path):
            template = TemplateLoader.load_from_file(template)

        if not isinstance(template, SettingsTemplate):
            raise ValueError("Invalid template type. Expected SettingsTemplate.")

        if template.dimension != "3D":
            raise ValueError(
                f"Template is for {template.dimension}, but this is a 3D generator."
            )

        # Apply settings to appropriate nested config
        if hasattr(template, "settings"):
            settings = template.settings
            for key, value in settings.items():
                if hasattr(self.config.render, key):
                    setattr(self.config.render, key, value)
                elif hasattr(self.config.conformer, key):
                    setattr(self.config.conformer, key, value)

        print(f"✓ Applied settings template: {template.name}")
        if hasattr(template, "description") and template.description:
            print(f" {template.description}")

    def get_config_dict(self) -> dict:
        """
        Export current configuration as dictionary.

        Returns
        -------
        dict
            Configuration as nested dictionary (JSON-serializable)
        """
        return self.config.to_dict()

    def __repr__(self) -> str:
        return (
            f"MoleculeGenerator3D(identifier='{self.identifier}', "
            f"compound='{self.compound_name}', atoms={self.mol.GetNumAtoms()})"
        )