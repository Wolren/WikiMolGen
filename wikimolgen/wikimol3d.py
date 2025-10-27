"""
wikimolgen.wikimol3d - 3D Molecular Structure Generation
=========================================================
Class-based 3D conformer generation with PyMOL rendering and auto-cropping.
Extended element colors and RDKit configuration options.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Literal, Dict, Union
import numpy as np
from PIL import ImageEnhance
from rdkit import Chem
from rdkit.Chem import AllChem, rdmolfiles

from .core import fetch_compound, validate_smiles

try:
    from .optimization import find_optimal_3d_orientation, optimize_zoom_buffer
    HAS_OPTIMIZATION = True
except ImportError:
    HAS_OPTIMIZATION = False


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



@dataclass
class RenderConfig:
    """
    Configuration for PyMOL 3D rendering with comprehensive element colors.

    Element colors follow standard CPK coloring scheme adapted for clarity.
    """

    # Auto orientation
    auto_orient: bool = True  # Enable automatic 3D orientation

    # Canvas settings
    width: int = 1320
    height: int = 990
    auto_crop: bool = True
    crop_margin: int = 10

    # Molecular representation
    stick_radius: float = 0.2
    stick_ball_ratio: float = 1.8
    stick_quality: int = 64
    sphere_scale: float = 0.3
    sphere_quality: int = 6
    stick_transparency: float = 0.0  # 0.0=opaque, 1.0=fully transparent
    sphere_transparency: float = 0.0  # 0.0=opaque, 1.0=fully transparent
    valence: float = 0.0  # Show valence (0=off, 0.05-0.2 typical)

    # Ray tracing options
    ray_trace_mode: int = 0
    ray_trace_gain: float = 0.0  # Brightness boost for ray tracing
    ray_trace_color: str = "black"  # Background for ray tracing (black/white/grey)
    ray_transparency_contrast: float = 1.0  # Transparency contrast (0.5-2.0)
    ray_transparency_oblique: float = 0.0  # Oblique transparency (0.0-1.0)

    # Lighting and rendering
    ambient: float = 0.25
    specular: int = 1
    shininess: int = 30
    ray_shadows: int = 0  # 0=off, 1=on (slower but more realistic)
    antialias: int = 4  # 0=off, 1=on, 2=2x, 3=3x, 4=4x
    depth_cue: int = 0  # Depth cueing (fog effect)
    fog_start: float = 1.0  # Where fog starts (0.0-1.0)
    direct: float = 0.5  # Direct lighting intensity (0.0-1.0)
    reflect: float = 0.5  # Reflection intensity (0.0-1.0)

    # Camera and orientation
    zoom_buffer: float = 2.0
    x_rotation: float = 0.0
    y_rotation: float = 0.0
    z_rotation: float = 0.0
    bg_color: str = "white"

    # Comprehensive element colors (CPK-based with adjustments for clarity)
    element_colors: Dict[str, str] = field(default_factory=lambda: {
        # Common organic elements
        "C": "gray25",          # Carbon - dark gray
        "H": "gray85",          # Hydrogen - light gray
        "N": "blue",            # Nitrogen - blue
        "O": "red",             # Oxygen - red
        "S": "yellow",          # Sulfur - yellow
        "P": "orange",          # Phosphorus - orange

        # Halogens
        "F": "palegreen",       # Fluorine - pale green
        "Cl": "green",          # Chlorine - green
        "Br": "firebrick",      # Bromine - dark red/brown
        "I": "purple",          # Iodine - purple

        # Metals (alkali & alkaline earth)
        "Li": "violet",         # Lithium
        "Na": "slate",          # Sodium
        "K": "violet",          # Potassium
        "Mg": "forest",         # Magnesium
        "Ca": "forest",         # Calcium

        # Transition metals (common in organometallics)
        "Fe": "darkorange",     # Iron
        "Cu": "chocolate",      # Copper
        "Zn": "brown",          # Zinc
        "Ni": "forest",         # Nickel
        "Co": "salmon",         # Cobalt
        "Mn": "violet",         # Manganese
        "Cr": "gray50",         # Chromium
        "Pd": "forest",         # Palladium
        "Pt": "gray50",         # Platinum
        "Au": "gold",           # Gold
        "Ag": "gray70",         # Silver

        # Other common elements
        "B": "salmon",          # Boron
        "Si": "goldenrod",      # Silicon
        "Se": "orange",         # Selenium
        "As": "violet",         # Arsenic

        "He": "cyan",
        "Ne": "cyan",
        "Ar": "cyan",
        "Kr": "cyan",
        "Xe": "cyan",
    })

    # Stick coloring (default uses element colors, or set to specific color)
    stick_color: Optional[str] = "gray40"  # None = use element colors


@dataclass
class ConformerConfig:
    """Configuration for RDKit conformer generation and optimization."""

    # ETKDG parameters
    use_random_coords: bool = False
    clear_confs: bool = True
    use_macrocycle_torsions: bool = False
    use_basic_knowledge: bool = True
    enforce_chirality: bool = True
    use_small_ring_torsions: bool = False

    # Optimization parameters
    max_iterations: int = 200
    vdw_thresh: float = 10.0
    conf_energy_threshold: float = 10.0  # kcal/mol for multi-conformer

    # Multi-conformer settings
    num_conformers: int = 1
    prune_rms_thresh: float = 0.5  # RMS threshold for conformer pruning


class MoleculeGenerator3D:
    """
    Generate 3D molecular structures with conformer optimization and rendering.

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
    render_config : RenderConfig
        PyMOL rendering configuration
    conformer_config : ConformerConfig
        RDKit conformer generation configuration

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
        random_seed: int = 1,
    ):
        """
        Initialize 3D molecule generator.

        Parameters
        ----------
        identifier : str
            PubChem CID, compound name, or SMILES string
        random_seed : int, optional
            Random seed for conformer generation (default: 1)
        """
        self.identifier = identifier
        self.smiles, self.compound_name = fetch_compound(identifier)
        self.mol = validate_smiles(self.smiles)
        self.mol = Chem.AddHs(self.mol)
        self.random_seed = random_seed
        self.energy: Optional[float] = None
        self.render_config = RenderConfig()
        self.conformer_config = ConformerConfig()

    def _embed_conformer(self) -> None:
        """Generate 3D conformer using ETKDG with configurable parameters."""
        params = AllChem.ETKDGv3()
        params.randomSeed = self.random_seed
        params.useRandomCoords = self.conformer_config.use_random_coords
        params.clearConfs = self.conformer_config.clear_confs
        params.useBasicKnowledge = self.conformer_config.use_basic_knowledge
        params.enforceChirality = self.conformer_config.enforce_chirality
        params.useSmallRingTorsions = self.conformer_config.use_small_ring_torsions

        if self.conformer_config.num_conformers == 1:
            result = AllChem.EmbedMolecule(self.mol, params)
            if result == -1:
                raise ValueError("Failed to generate 3D conformer")
        else:
            # Multi-conformer generation
            result = AllChem.EmbedMultipleConfs(
                self.mol,
                numConfs=self.conformer_config.num_conformers,
                params=params,
                pruneRmsThresh=self.conformer_config.prune_rms_thresh
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
        max_iters = max_iterations or self.conformer_config.max_iterations

        if force_field == "MMFF94":
            if self.conformer_config.num_conformers == 1:
                result = AllChem.MMFFOptimizeMolecule(self.mol, maxIters=max_iters)
                if result == 0:
                    props = AllChem.MMFFGetMoleculeProperties(self.mol)
                    ff = AllChem.MMFFGetMoleculeForceField(self.mol, props)
                    self.energy = ff.CalcEnergy()
            else:
                results = AllChem.MMFFOptimizeMoleculeConfs(self.mol, maxIters=max_iters)
                energies = [r[1] for r in results]
                self.energy = min(energies)

        elif force_field == "UFF":
            if self.conformer_config.num_conformers == 1:
                result = AllChem.UFFOptimizeMolecule(self.mol, maxIters=max_iters)
                if result == 0:
                    ff = AllChem.UFFGetMoleculeForceField(self.mol)
                    self.energy = ff.CalcEnergy()
            else:
                results = AllChem.UFFOptimizeMoleculeConfs(self.mol, maxIters=max_iters)
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
            ImageEnhance.Contrast(img).enhance(contrast_factor)
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

        cfg = self.render_config
        output_path = Path(output)

        with pymol2.PyMOL() as pymol:
            cmd = pymol.cmd

            # Load molecule
            cmd.load(str(sdf_path))
            cmd.hide("everything")
            cmd.show("sticks", "all")
            cmd.show("spheres", "all")
            cmd.bg_color(cfg.bg_color)

            # Apply element colors
            for element, color_name in cfg.element_colors.items():
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
            if cfg.auto_orient and HAS_OPTIMIZATION:
                x_opt, y_opt, z_opt = find_optimal_3d_orientation(self.mol)
                zoom_opt = optimize_zoom_buffer(self.mol)
                cmd.zoom("all", buffer=zoom_opt)
                cmd.orient("all")
                cmd.turn("x", x_opt)
                cmd.turn("y", y_opt)
                cmd.turn("z", z_opt)
                print(f"  Auto-oriented: x={x_opt:.1f}°, y={y_opt:.1f}°, z={z_opt:.1f}°")
                print(f"  Auto-zoom: {zoom_opt:.2f}")
            else:
                cmd.zoom("all", buffer=cfg.zoom_buffer)
                cmd.orient("all")
                cmd.turn("x", cfg.x_rotation)
                cmd.turn("y", cfg.y_rotation)
                cmd.turn("z", cfg.z_rotation)

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
            output_base = self.compound_name.replace(" ", "_") if self.compound_name != "custom_smiles" else "molecule_3d"

        # Generate conformer
        self._embed_conformer()

        # Optimize geometry
        if optimize:
            self._optimize_geometry(force_field, max_iterations)

        # Save SDF
        sdf_path = self._save_sdf(f"{output_base}.sdf")
        print(f"✓ 3D structure saved: {sdf_path}")
        print(f"  Compound: {self.compound_name}")
        print(f"  Atoms: {self.mol.GetNumAtoms()}, Bonds: {self.mol.GetNumBonds()}")

        if self.conformer_config.num_conformers > 1:
            print(f"  Conformers: {self.mol.GetNumConformers()}")

        if optimize and self.energy is not None:
            print(f"  Energy: {self.energy:.2f} kcal/mol ({force_field})")

        # Render with PyMOL
        png_path = None
        if render:
            png_path = self._render_pymol(sdf_path, f"{output_base}.png")
            print(f"✓ Rendered image saved: {png_path}")
            if self.render_config.auto_crop:
                print(f"  Auto-cropped with {self.render_config.crop_margin}px margin")
            else:
                print(f"  Dimensions: {self.render_config.width}×{self.render_config.height} px")

        return sdf_path, png_path

    def configure_rendering(
            self,
            width: Optional[int] = None,
            height: Optional[int] = None,
            y_rotation: Optional[float] = None,
            x_rotation: Optional[float] = None,
            z_rotation: Optional[float] = None,
            auto_crop: Optional[bool] = None,
            crop_margin: Optional[int] = None,
            auto_orient: Optional[bool] = None,
            stick_radius: Optional[float] = None,
            sphere_scale: Optional[float] = None,
            stick_ball_ratio: Optional[float] = None,
            ray_trace_mode: Optional[int] = None,
            ray_shadows: Optional[int] = None,
            stick_transparency: Optional[float] = None,
            sphere_transparency: Optional[float] = None,
            valence: Optional[float] = None,
            antialias: Optional[int] = None,
            ambient: Optional[float] = None,
            specular: Optional[float] = None,
            direct: Optional[float] = None,
            reflect: Optional[float] = None,
            shininess: Optional[int] = None,
            depth_cue: Optional[int] = None,
            bg_color: Optional[str] = None,
            **kwargs,
    ) -> None:
        """
        Update rendering configuration.

        Parameters
        ----------
        width : int, optional
            Image width in pixels (before cropping)
        height : int, optional
            Image height in pixels (before cropping)
        x_rotation : float, optional
            X-axis rotation in degrees
        y_rotation : float, optional
            Y-axis rotation in degrees
        z_rotation : float, optional
            Z-axis rotation in degrees
        auto_crop : bool, optional
            Enable automatic cropping to molecule bounds
        crop_margin : int, optional
            Margin around molecule in pixels (default: 10)
        auto_orient : bool, optional
            Automatically orient molecule
        stick_radius : float, optional
            Thickness of bond sticks
        sphere_scale : float, optional
            Scale factor for atom spheres
        stick_ball_ratio : float, optional
            Ratio of stick to ball size
        ray_trace_mode : int, optional
            Enable ray tracing (0=off, 1=on)
        ray_shadows : int, optional
            Enable ray tracing shadows (0=off, 1=on)
        stick_transparency : float, optional
            Transparency of sticks (0.0-1.0)
        sphere_transparency : float, optional
            Transparency of spheres (0.0-1.0)
        valence : float, optional
            Valence bond visibility
        antialias : int, optional
            Antialiasing level (0-4)
        ambient : float, optional
            Ambient light intensity (0.0-1.0)
        specular : float, optional
            Specular reflection intensity
        direct : float, optional
            Direct light intensity (0.0-1.0)
        reflect : float, optional
            Environmental reflection intensity (0.0-1.0)
        shininess : int, optional
            Surface shininess (10-100)
        depth_cue : int, optional
            Enable depth cueing/fog (0=off, 1=on)
        bg_color : str, optional
            Background color ('white', 'black', 'gray')
        **kwargs
            Additional RenderConfig parameters
        """
        if width is not None:
            self.render_config.width = width
        if height is not None:
            self.render_config.height = height
        if x_rotation is not None:
            self.render_config.x_rotation = x_rotation
        if y_rotation is not None:
            self.render_config.y_rotation = y_rotation
        if z_rotation is not None:
            self.render_config.z_rotation = z_rotation
        if auto_crop is not None:
            self.render_config.auto_crop = auto_crop
        if crop_margin is not None:
            self.render_config.crop_margin = crop_margin
        if auto_orient is not None:
            self.render_config.auto_orient = auto_orient
        if stick_radius is not None:
            self.render_config.stick_radius = stick_radius
        if sphere_scale is not None:
            self.render_config.sphere_scale = sphere_scale
        if stick_ball_ratio is not None:
            self.render_config.stick_ball_ratio = stick_ball_ratio
        if ray_trace_mode is not None:
            self.render_config.ray_trace_mode = ray_trace_mode
        if ray_shadows is not None:
            self.render_config.ray_shadows = ray_shadows
        if stick_transparency is not None:
            self.render_config.stick_transparency = stick_transparency
        if sphere_transparency is not None:
            self.render_config.sphere_transparency = sphere_transparency
        if valence is not None:
            self.render_config.valence = valence
        if antialias is not None:
            self.render_config.antialias = antialias
        if ambient is not None:
            self.render_config.ambient = ambient
        if specular is not None:
            self.render_config.specular = specular
        if direct is not None:
            self.render_config.direct = direct
        if reflect is not None:
            self.render_config.reflect = reflect
        if shininess is not None:
            self.render_config.shininess = shininess
        if depth_cue is not None:
            self.render_config.depth_cue = depth_cue
        if bg_color is not None:
            self.render_config.bg_color = bg_color

        # Handle any remaining kwargs
        for key, value in kwargs.items():
            if hasattr(self.render_config, key):
                setattr(self.render_config, key, value)

    def configure_conformer(
        self,
        num_conformers: Optional[int] = None,
        max_iterations: Optional[int] = None,
        enforce_chirality: Optional[bool] = None,
        **kwargs,
    ) -> None:
        """
        Update conformer generation configuration.

        Parameters
        ----------
        num_conformers : int, optional
            Number of conformers to generate
        max_iterations : int, optional
            Maximum optimization iterations
        enforce_chirality : bool, optional
            Enforce chirality during embedding
        **kwargs
            Additional ConformerConfig parameters
        """
        if num_conformers is not None:
            self.conformer_config.num_conformers = num_conformers
        if max_iterations is not None:
            self.conformer_config.max_iterations = max_iterations
        if enforce_chirality is not None:
            self.conformer_config.enforce_chirality = enforce_chirality

        for key, value in kwargs.items():
            if hasattr(self.conformer_config, key):
                setattr(self.conformer_config, key, value)


    def load_color_template(self, template: Union[str, Path, 'ColorStyleTemplate']) -> None:
        """
        Apply a color style template to the 3D generator.

        Parameters
        ----------
        template : ColorStyleTemplate, str, or Path
            Color template object, path to template file, or predefined template name

        Examples
        --------
        >>> gen = MoleculeGenerator3D("caffeine")
        >>> gen.load_color_template("cpk_standard")  # Predefined template
        >>> gen.load_color_template("my_colors.json")  # From file
        """
        from .templates import TemplateLoader, ColorStyleTemplate, get_predefined_color_template, TemplateError

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
        if template.element_colors:
            self.render_config.element_colors.update(template.element_colors)

        if template.stick_color is not None:
            self.render_config.stick_color = template.stick_color

        self.render_config.bg_color = template.bg_color

        print(f"✓ Applied color template: {template.name}")
        if template.description:
            print(f"  {template.description}")

    def load_settings_template(self, template: Union[str, Path, 'SettingsTemplate']) -> None:
        """
        Apply a settings template to the 3D generator.

        Parameters
        ----------
        template : SettingsTemplate, str, or Path
            Settings template object, path to template file, or predefined template name

        Examples
        --------
        >>> gen = MoleculeGenerator3D("dopamine")
        >>> gen.load_settings_template("high_quality_3d")  # Predefined template
        >>> gen.load_settings_template("my_settings.json")  # From file
        """
        from .templates import TemplateLoader, SettingsTemplate, get_predefined_settings_template, TemplateError

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

        if template.dimension != '3D':
            raise ValueError(f"Template is for {template.dimension}, but this is a 3D generator.")

        # Apply settings to render config
        settings = template.settings
        for key, value in settings.items():
            if hasattr(self.render_config, key):
                setattr(self.render_config, key, value)

        print(f"✓ Applied settings template: {template.name}")
        if template.description:
            print(f"  {template.description}")


    def __repr__(self) -> str:
        return (
            f"MoleculeGenerator3D(identifier='{self.identifier}', "
            f"compound='{self.compound_name}', atoms={self.mol.GetNumAtoms()})"
        )
