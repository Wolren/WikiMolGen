"""
wikimolgen.wikimol3d - 3D Molecular Structure Generation
=========================================================
Class-based 3D conformer generation with PyMOL rendering.
"""

from dataclasses import dataclass
from pathlib import Path
from typing import Optional, Literal

from rdkit import Chem
from rdkit.Chem import AllChem, rdmolfiles

from .core import fetch_compound, validate_smiles

ForceFieldType = Literal["MMFF94", "UFF"]


@dataclass
class RenderConfig:
    """Configuration for PyMOL 3D rendering."""
    
    width: int = 1320
    height: int = 990
    stick_radius: float = 0.2
    sphere_scale: float = 0.3
    sphere_quality: int = 4
    stick_ball_ratio: float = 1.8
    stick_quality: int = 30
    ambient: float = 0.25
    specular: float = 1.0
    shininess: int = 30
    antialias: int = 2
    zoom_buffer: float = 2.0
    x_rotation: float = 0.0
    y_rotation: float = 200.0
    z_rotation: float = 0.0
    bg_color: str = "white"
    
    # Element colors
    carbon_color: str = "gray25"
    nitrogen_color: str = "blue"
    oxygen_color: str = "red"
    hydrogen_color: str = "gray85"
    stick_color: str = "gray40"


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
    
    def _embed_conformer(self) -> None:
        """Generate 3D conformer using ETKDG."""
        params = AllChem.ETKDGv3()
        params.randomSeed = self.random_seed
        
        result = AllChem.EmbedMolecule(self.mol, params)
        if result == -1:
            raise ValueError("Failed to generate 3D conformer")
    
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
        if force_field == "MMFF94":
            result = AllChem.MMFFOptimizeMolecule(self.mol, maxIters=max_iterations)
            if result == 0:
                props = AllChem.MMFFGetMoleculeProperties(self.mol)
                ff = AllChem.MMFFGetMoleculeForceField(self.mol, props)
                self.energy = ff.CalcEnergy()
        elif force_field == "UFF":
            result = AllChem.UFFOptimizeMolecule(self.mol, maxIters=max_iterations)
            if result == 0:
                ff = AllChem.UFFGetMoleculeForceField(self.mol)
                self.energy = ff.CalcEnergy()
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
    
    def _render_pymol(self, sdf_path: Path, output: str) -> Path:
        """
        Render molecule using PyMOL.
        
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
            
            # Element colors
            cmd.color(cfg.carbon_color, "elem C")
            cmd.color(cfg.nitrogen_color, "elem N")
            cmd.color(cfg.oxygen_color, "elem O")
            cmd.color(cfg.hydrogen_color, "elem H")
            
            # Stick properties
            cmd.set("stick_radius", cfg.stick_radius)
            cmd.set("stick_color", cfg.stick_color)
            
            # Sphere properties
            cmd.set("sphere_scale", cfg.sphere_scale)
            cmd.set("sphere_quality", cfg.sphere_quality)
            
            # Stick ball properties
            cmd.set("stick_ball", "on")
            cmd.set("stick_ball_ratio", cfg.stick_ball_ratio)
            cmd.set("stick_quality", cfg.stick_quality)
            
            # Rendering properties
            cmd.set("ambient", cfg.ambient)
            cmd.set("specular", cfg.specular)
            cmd.set("shininess", cfg.shininess)
            cmd.set("ray_shadows", 0)
            cmd.set("antialias", cfg.antialias)
            cmd.set("ray_opaque_background", 0)
            cmd.set("depth_cue", 0)
            
            # Position and orientation
            cmd.zoom("all", buffer=cfg.zoom_buffer)
            cmd.orient("all")
            cmd.turn("x", cfg.x_rotation)
            cmd.turn("y", cfg.y_rotation)
            cmd.turn("z", cfg.z_rotation)
            
            # Render
            cmd.png(str(output_path), width=cfg.width, height=cfg.height)
        
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
        
        if optimize and self.energy is not None:
            print(f"  Energy: {self.energy:.2f} kcal/mol ({force_field})")
        
        # Render with PyMOL
        png_path = None
        if render:
            png_path = self._render_pymol(sdf_path, f"{output_base}.png")
            print(f"✓ Rendered image saved: {png_path}")
            print(f"  Dimensions: {self.render_config.width}×{self.render_config.height} px")
        
        return sdf_path, png_path
    
    def configure_rendering(
        self,
        width: Optional[int] = None,
        height: Optional[int] = None,
        y_rotation: Optional[float] = None,
        **kwargs,
    ) -> None:
        """
        Update rendering configuration.
        
        Parameters
        ----------
        width : int, optional
            Image width in pixels
        height : int, optional
            Image height in pixels
        y_rotation : float, optional
            Y-axis rotation in degrees
        **kwargs
            Additional RenderConfig parameters
        """
        if width is not None:
            self.render_config.width = width
        if height is not None:
            self.render_config.height = height
        if y_rotation is not None:
            self.render_config.y_rotation = y_rotation
        
        for key, value in kwargs.items():
            if hasattr(self.render_config, key):
                setattr(self.render_config, key, value)
    
    def __repr__(self) -> str:
        return (
            f"MoleculeGenerator3D(identifier='{self.identifier}', "
            f"compound='{self.compound_name}', atoms={self.mol.GetNumAtoms()})"
        )
