"""
wikimolgen.rendering.protein - Protein Structure Visualization
======================================================

Protein structure fetching and visualization using Biotite, PyMOL, and NGLView.
Supports PDB structures, protein-ligand complexes, and publication-quality rendering.
"""

from dataclasses import dataclass, field
from pathlib import Path
from typing import Optional, Dict, Tuple, List
import tempfile
from enum import Enum
import sys

# Try to import optional dependencies gracefully
HAS_BIOTITE = False
HAS_PYMOL = False
HAS_NGLVIEW = False
HAS_PIL = False

try:
    import biotite.database.rcsb as rcsb
    import biotite.structure.io.pdb as pdb
    HAS_BIOTITE = True
except ImportError:
    pass

try:
    from pymol import cmd as pymol_cmd
    from pymol import finish_launching
    HAS_PYMOL = True
except ImportError:
    try:
        import pymol2
        HAS_PYMOL = True
    except ImportError:
        pass

try:
    import nglview as nv
    HAS_NGLVIEW = True
except ImportError:
    pass

try:
    from PIL import Image, ImageEnhance
    HAS_PIL = True
except ImportError:
    pass


def hex_to_rgb(hex_color: str) -> Tuple[float, float, float]:
    """Convert hex color to normalized RGB tuple for PyMOL.

    Parameters
    ----------
    hex_color : str
        Hex color code (e.g., "#FF6B6B" or "FF6B6B")

    Returns
    -------
    Tuple[float, float, float]
        RGB values normalized to 0.0-1.0
    """
    hex_color = hex_color.lstrip("#")
    try:
        return tuple(int(hex_color[i:i+2], 16) / 255.0 for i in (0, 2, 4))
    except (ValueError, IndexError):
        # Fallback to white if parsing fails
        return (1.0, 1.0, 1.0)


def autocrop_image(image_path: Path, margin: int = 10, contrast_factor: float = 1.15) -> None:
    """Auto-crop PNG to protein bounds using alpha channel only.

    Keeps transparency untouched - best for transparent backgrounds.
    Same implementation as 3D molecular generator.

    Parameters
    ----------
    image_path : Path
        Path to PNG image
    margin : int
        Margin around protein in pixels (default: 10)
    contrast_factor : float
        Contrast enhancement factor (default: 1.15)
    """
    if not HAS_PIL:
        print("⚠ PIL not available - skipping autocrop")
        return

    if not image_path.exists():
        print(f"⚠ Image file not found: {image_path}")
        return

    img = Image.open(image_path).convert("RGBA")
    alpha = img.split()[-1]

    # Find bounding box of non-transparent pixels
    bbox = alpha.getbbox()
    if bbox is None:
        return  # Entire image is transparent

    left, top, right, bottom = bbox
    width, height = img.size

    # Add margin
    left = max(0, left - margin)
    top = max(0, top - margin)
    right = min(width, right + margin)
    bottom = min(height, bottom + margin)

    # Crop image
    img = img.crop((left, top, right, bottom))

    # Enhance contrast
    img = ImageEnhance.Contrast(img).enhance(contrast_factor)

    img.save(image_path)


def initialize_pymol() -> None:
    """Initialize PyMOL in headless mode (no GUI)."""
    try:
        from pymol import cmd
        # Check if already initialized
        cmd.reinitialize()
    except Exception:
        # Try pymol2 alternative
        try:
            import pymol2
            pymol2.PyMOL()
        except Exception:
            pass


class ProteinVisualizationError(Exception):
    """Raised when protein visualization fails."""
    pass


class ProteinFetchError(Exception):
    """Raised when protein structure cannot be fetched."""
    pass


class SecondaryStructureType(str, Enum):
    """Secondary structure representation types."""
    CARTOON = "cartoon"
    RIBBON = "ribbon"
    CARTOON_FANCY = "cartoon_fancy"
    TRACE = "trace"
    STICKS = "sticks"
    SPHERE = "sphere"


class ColorScheme(str, Enum):
    """Protein coloring schemes."""
    SECONDARY_STRUCTURE = "secondary_structure"
    RAINBOW = "rainbow"
    CHAIN = "chain"
    HYDROPHOBICITY = "hydrophobicity"
    ELEMENT = "element"
    BFACTOR = "bfactor"


@dataclass
class CartoonRenderConfig:
    """Configuration for cartoon-style protein rendering."""

    cartoon_style: str = "fancy_helices"
    cartoon_flat_sheets: bool = True
    cartoon_fancy_helices: int = 1
    cartoon_fancy_sheets: int = 1
    cartoon_transparency: float = 0.0

    helix_color: str = "#00FF00"
    sheet_color: str = "#00FFFF"
    loop_color: str = "#FFA500"

    ray_trace_mode: int = 0
    antialias: int = 4
    ambient: float = 0.4
    specular: int = 1
    shininess: int = 40
    ray_shadows: int = 0

    width: int = 1920
    height: int = 1080
    bg_color: str = "black"

    auto_orient: bool = True
    zoom_buffer: float = 2.0

    # Autocrop settings
    autocrop: bool = True
    crop_margin: int = 10


@dataclass
class LigandRenderConfig:
    """Configuration for ligand/peptide rendering in protein complex."""

    ligand_style: str = "sticks"
    ligand_transparency: float = 0.0
    ligand_color_scheme: str = "element"
    ligand_single_color: Optional[str] = "#FF6B6B"

    stick_radius: float = 0.25
    stick_quality: int = 64
    stick_ball_ratio: float = 1.5

    show_cartoon: bool = False
    show_bindsites: bool = True
    binding_site_radius: float = 5.0
    binding_site_color: str = "yellow"

    show_residue_labels: bool = False
    label_size: int = 14


@dataclass
class ProteinStructureMetadata:
    """Metadata about a protein structure."""

    pdb_id: str
    title: str = ""
    organism: str = ""
    resolution: Optional[float] = None
    chains: List[str] = field(default_factory=list)
    num_atoms: int = 0
    num_residues: int = 0
    has_ligand: bool = False
    has_water: bool = False
    experimental_method: str = ""


class BiotiteStructureProvider:
    """Fetch protein structures using Biotite/RCSB PDB."""

    def is_available(self) -> bool:
        """Check if Biotite is available."""
        return HAS_BIOTITE

    def fetch_structure(self, pdb_id: str) -> Tuple[Path, ProteinStructureMetadata]:
        """Fetch PDB structure from RCSB database.

        Parameters
        ----------
        pdb_id : str
            4-character PDB identifier

        Returns
        -------
        Tuple[Path, ProteinStructureMetadata]
            Path to PDB file and metadata

        Raises
        ------
        ProteinFetchError
            If Biotite not available or fetch fails
        """
        if not HAS_BIOTITE:
            raise ProteinFetchError(
                "Biotite not installed. Install with:\n"
                "  conda install -c conda-forge biotite\n"
                "  or: pip install biotite"
            )

        try:
            pdb_id = pdb_id.upper()

            # Create temporary directory for PDB file
            tmpdir = tempfile.mkdtemp()
            tmpdir_path = Path(tmpdir)

            # Download PDB file
            pdb_path = rcsb.fetch(pdb_id, "pdb", tmpdir)

            # Load structure using PDB parser
            structure = pdb.PDBFile.read(pdb_path).get_structure()

            metadata = ProteinStructureMetadata(
                pdb_id=pdb_id,
                num_atoms=len(structure),
                num_residues=len(set(structure.res_id)),
                chains=list(set(structure.chain_id)),
                has_ligand=self._has_hetatm(structure),
                has_water=self._has_water(structure),
            )

            return Path(pdb_path), metadata

        except Exception as e:
            raise ProteinFetchError(
                f"Failed to fetch PDB {pdb_id}: {type(e).__name__}: {e}"
            )

    @staticmethod
    def _has_hetatm(structure) -> bool:
        """Check if structure contains heteroatoms (ligands)."""
        standard_aa = {
            'ALA', 'ARG', 'ASN', 'ASP', 'CYS', 'GLU', 'GLN',
            'GLY', 'HIS', 'ILE', 'LEU', 'LYS', 'MET', 'PHE',
            'PRO', 'SER', 'THR', 'TRP', 'TYR', 'VAL'
        }
        try:
            return any(res_name not in standard_aa for res_name in set(structure.res_name))
        except:
            return False

    @staticmethod
    def _has_water(structure) -> bool:
        """Check if structure contains water molecules."""
        try:
            return 'HOH' in set(structure.res_name)
        except:
            return False


class ProteinGenerator:
    """Generate high-quality protein structure visualizations."""

    def __init__(
        self,
        pdb_id: str,
        provider: Optional[BiotiteStructureProvider] = None,
        random_seed: int = 42,
    ):
        """Initialize protein structure generator.

        Parameters
        ----------
        pdb_id : str
            4-character PDB identifier (e.g., "8F7W")
        provider : BiotiteStructureProvider, optional
            Structure data provider (default: BiotiteStructureProvider)
        random_seed : int
            Random seed for reproducibility

        Raises
        ------
        ProteinFetchError
            If structure cannot be fetched
        """
        self.pdb_id = pdb_id.upper()
        self.provider = provider or BiotiteStructureProvider()
        self.random_seed = random_seed

        self.pdb_path: Optional[Path] = None
        self.metadata: Optional[ProteinStructureMetadata] = None

        self.cartoon_config = CartoonRenderConfig()
        self.ligand_config = LigandRenderConfig()

        self._fetch_structure()

    def _fetch_structure(self) -> None:
        """Fetch protein structure from provider.

        Raises
        ------
        ProteinFetchError
            If provider not available or fetch fails
        """
        if not self.provider.is_available():
            raise ProteinFetchError(
                "Biotite provider not available. Install with:\n"
                "  conda install -c conda-forge biotite\n"
                "  or: pip install biotite"
            )

        self.pdb_path, self.metadata = self.provider.fetch_structure(self.pdb_id)
        print(f"✓ Fetched {self.pdb_id}")
        print(f"  Chains: {', '.join(self.metadata.chains)}")
        print(f"  Atoms: {self.metadata.num_atoms} | Residues: {self.metadata.num_residues}")
        if self.metadata.has_ligand:
            print(f"  Has ligand/heteroatoms")
        if self.metadata.has_water:
            print(f"  Contains water molecules")

    def generate(
        self,
        output: str,
        color_scheme: ColorScheme = ColorScheme.SECONDARY_STRUCTURE,
        show_ligand: bool = True,
        show_water: bool = False,
    ) -> Path:
        """Generate protein structure visualization.

        Parameters
        ----------
        output : str
            Output PNG filename
        color_scheme : ColorScheme
            Coloring scheme for protein
        show_ligand : bool
            Show ligand/heteroatoms
        show_water : bool
            Show water molecules

        Returns
        -------
        Path
            Path to rendered PNG file

        Raises
        ------
        ProteinVisualizationError
            If PyMOL not available or rendering fails
        """
        if not HAS_PYMOL:
            raise ProteinVisualizationError(
                "PyMOL not installed. Install with:\n"
                "  conda install -c conda-forge pymol-open-source\n"
                "  or: pip install pymol-open-source"
            )

        output_path = Path(output)

        try:
            # Initialize PyMOL (headless mode, no GUI)
            from pymol import cmd
            initialize_pymol()

            # Load structure
            cmd.load(str(self.pdb_path), "protein")
            cmd.hide("everything")
            cmd.show("cartoon", "polymer.protein")

            # Color by scheme
            if color_scheme == ColorScheme.SECONDARY_STRUCTURE:
                # Convert hex colors to RGB tuples for PyMOL
                helix_rgb = hex_to_rgb(self.cartoon_config.helix_color)
                sheet_rgb = hex_to_rgb(self.cartoon_config.sheet_color)
                loop_rgb = hex_to_rgb(self.cartoon_config.loop_color)

                cmd.set_color("custom_helix", helix_rgb)
                cmd.set_color("custom_sheet", sheet_rgb)
                cmd.set_color("custom_loop", loop_rgb)

                cmd.color("custom_helix", "ss h")
                cmd.color("custom_sheet", "ss s")
                cmd.color("custom_loop", "ss l+''")
            elif color_scheme == ColorScheme.RAINBOW:
                cmd.spectrum("count", "rainbow", selection="polymer.protein")
            elif color_scheme == ColorScheme.CHAIN:
                cmd.util.cbc()

            # Cartoon settings
            cmd.set("cartoon_fancy_helices", 1)
            cmd.set("cartoon_flat_sheets", 1)
            cmd.set("cartoon_transparency", self.cartoon_config.cartoon_transparency)

            # Rendering settings
            cmd.set("antialias", self.cartoon_config.antialias)
            cmd.set("ambient", self.cartoon_config.ambient)
            cmd.set("specular", self.cartoon_config.specular)
            cmd.set("shininess", self.cartoon_config.shininess)
            cmd.set("ray_shadows", self.cartoon_config.ray_shadows)
            cmd.bg_color(self.cartoon_config.bg_color)

            # Show ligand
            if show_ligand and self.metadata.has_ligand:
                cmd.show(self.ligand_config.ligand_style, "organic")
                if self.ligand_config.ligand_color_scheme == "element":
                    cmd.util.cbaw("organic")
                elif self.ligand_config.ligand_color_scheme == "single":
                    ligand_rgb = hex_to_rgb(self.ligand_config.ligand_single_color or "#FF6B6B")
                    cmd.set_color("custom_ligand", ligand_rgb)
                    cmd.color("custom_ligand", "organic")

            # Show water
            if show_water and self.metadata.has_water:
                cmd.show("spheres", "resn HOH")
                cmd.color("cyan", "resn HOH")
                cmd.set("sphere_scale", 0.4)

            # Orient and zoom
            if self.cartoon_config.auto_orient:
                cmd.orient("all")
                cmd.zoom("all", buffer=self.cartoon_config.zoom_buffer)

            # Ray trace and render
            if self.cartoon_config.ray_trace_mode > 0:
                cmd.ray(
                    width=self.cartoon_config.width,
                    height=self.cartoon_config.height
                )

            cmd.png(
                str(output_path),
                width=self.cartoon_config.width,
                height=self.cartoon_config.height,
            )

            # Autocrop if enabled (same as 3D generator)
            if self.cartoon_config.autocrop:
                autocrop_image(
                    output_path,
                    margin=self.cartoon_config.crop_margin,
                    contrast_factor=1.15
                )
                print(f"✓ Auto-cropped with {self.cartoon_config.crop_margin}px margin")

            print(f"✓ Rendered: {output_path}")
            return output_path

        except Exception as e:
            raise ProteinVisualizationError(
                f"Failed to render: {type(e).__name__}: {e}"
            )

    def configure_cartoon(self, **kwargs) -> None:
        """Update cartoon rendering configuration.

        Parameters
        ----------
        **kwargs
            Any CartoonRenderConfig attribute and value
        """
        for key, value in kwargs.items():
            if hasattr(self.cartoon_config, key):
                setattr(self.cartoon_config, key, value)

    def configure_ligand(self, **kwargs) -> None:
        """Update ligand rendering configuration.

        Parameters
        ----------
        **kwargs
            Any LigandRenderConfig attribute and value
        """
        for key, value in kwargs.items():
            if hasattr(self.ligand_config, key):
                setattr(self.ligand_config, key, value)


class ProteinNGLViewRenderer:
    """Interactive protein visualization using NGLView for Jupyter notebooks."""

    def __init__(self, pdb_id: str):
        """Initialize NGLView renderer.

        Parameters
        ----------
        pdb_id : str
            PDB identifier

        Raises
        ------
        ImportError
            If NGLView not available
        """
        if not HAS_NGLVIEW:
            raise ImportError(
                "NGLView not installed. Install with: pip install nglview"
            )

        self.pdb_id = pdb_id.upper()
        self.view = None

    def create_view(
        self,
        background: str = "black",
        width: int = 600,
        height: int = 400,
    ):
        """Create interactive NGLView.

        Parameters
        ----------
        background : str
            Background color
        width : int
            View width in pixels
        height : int
            View height in pixels

        Returns
        -------
        nglview.NGLWidget
            Interactive view widget
        """
        pdb_file = f"rcsb://{self.pdb_id}.pdb"
        self.view = nv.show_structure_file(pdb_file, gui=True)
        self.view._set_size(width, height)
        return self.view

    def add_cartoon(self, color_scheme: str = "chainindex", transparency: float = 0.0):
        """Add cartoon representation.

        Parameters
        ----------
        color_scheme : str
            Color scheme for cartoon
        transparency : float
            Transparency level (0-1)

        Returns
        -------
        ProteinNGLViewRenderer
            Self for method chaining
        """
        if self.view is None:
            raise ValueError("Call create_view() first")
        self.view.add_cartoon(colorScheme=color_scheme)
        return self

    def add_ligand_sticks(self, color_by: str = "element"):
        """Add ligand as sticks representation.

        Parameters
        ----------
        color_by : str
            Coloring scheme

        Returns
        -------
        ProteinNGLViewRenderer
            Self for method chaining
        """
        if self.view is None:
            raise ValueError("Call create_view() first")
        self.view.add_ball_and_stick("organic", colorScheme=color_by)
        return self

    def add_surface(self, opacity: float = 0.7, surface_type: str = "av"):
        """Add molecular surface.

        Parameters
        ----------
        opacity : float
            Surface opacity (0-1)
        surface_type : str
            Surface type (av, vdw, etc)

        Returns
        -------
        ProteinNGLViewRenderer
            Self for method chaining
        """
        if self.view is None:
            raise ValueError("Call create_view() first")
        self.view.add_surface(opacity=opacity, surfaceType=surface_type)
        return self


def get_optimal_dynorphin_kor_view() -> Dict:
    """Get optimized rendering settings for Dynorphin-KOR complex (8F7W).

    This is the kappa opioid receptor bound to dynorphin A.
    Optimized for visualizing receptor-ligand interactions.

    Returns
    -------
    Dict
        Recommended configuration for this specific complex
    """
    return {
        "cartoon": {
            "cartoon_style": "fancy_helices",
            "helix_color": "#00FF00",
            "sheet_color": "#00FFFF",
            "loop_color": "#FFA500",
        },
        "ligand": {
            "ligand_style": "sticks",
            "show_cartoon": True,
            "show_bindsites": True,
            "binding_site_radius": 6.0,
        },
        "render": {
            "width": 1920,
            "height": 1080,
            "bg_color": "black",
            "antialias": 4,
            "auto_orient": True,
        }
    }


if __name__ == "__main__":
    print("WikiMolGen Protein Visualization Module")
    print("=" * 50)

    print(f"\nDependency Status:")
    print(f"  Biotite: {'✓ Available' if HAS_BIOTITE else '✗ Not available'}")
    print(f"  PyMOL: {'✓ Available' if HAS_PYMOL else '✗ Not available'}")
    print(f"  NGLView: {'✓ Available' if HAS_NGLVIEW else '✗ Not available'}")
    print(f"  PIL: {'✓ Available' if HAS_PIL else '✗ Not available'}")

    if not HAS_BIOTITE or not HAS_PYMOL:
        print("\n⚠️  Required dependencies not installed.")
        print("\nInstall with:")
        print("  conda install -c conda-forge biotite pymol-open-source")
        print("  pip install nglview pillow")
    else:
        print("\n✓ All dependencies available!")
        print("\nExample usage:")
        print("  gen = ProteinGenerator('8F7W')")