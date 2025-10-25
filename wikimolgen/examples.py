"""
Example Usage Scripts for wikimolgen
=====================================
Demonstrates various use cases for the wikimolgen package.
"""

import numpy as np
from wikimolgen import MoleculeGenerator2D, MoleculeGenerator3D, fetch_compound


def example_2d_basic():
    """Basic 2D structure generation."""
    print("=" * 60)
    print("Example 1: Basic 2D Structure Generation")
    print("=" * 60)
    
    # From PubChem CID
    gen = MoleculeGenerator2D("24802108")
    gen.generate("examples/4-MeO-DiPT_2d.svg")
    print()


def example_2d_custom():
    """2D structure with custom styling."""
    print("=" * 60)
    print("Example 2: Custom 2D Styling")
    print("=" * 60)
    
    # Custom rotation and scaling
    gen = MoleculeGenerator2D(
        "psilocin",
        angle=0,  # No rotation
        scale=40,  # Larger scale
        margin=1.0,  # More margin
        bond_length=40.0,
        min_font_size=42,
    )
    gen.generate("examples/psilocin_custom.svg")
    print()


def example_2d_smiles():
    """2D structure from SMILES string."""
    print("=" * 60)
    print("Example 3: 2D from SMILES")
    print("=" * 60)
    
    smiles = "CC(C)N(CCC1=CNC2=C1C(=CC=C2)OC)C(C)C"
    gen = MoleculeGenerator2D(smiles, angle=np.pi/2)
    gen.generate("examples/smiles_2d.svg")
    print()


def example_3d_basic():
    """Basic 3D structure generation."""
    print("=" * 60)
    print("Example 4: Basic 3D Structure Generation")
    print("=" * 60)
    
    gen = MoleculeGenerator3D("24802108", random_seed=42)
    sdf_path, _ = gen.generate(
        optimize=True,
        force_field="MMFF94",
        output_base="examples/4-MeO-DiPT_3d"
    )
    print()


def example_3d_render():
    """3D structure with PyMOL rendering."""
    print("=" * 60)
    print("Example 5: 3D with PyMOL Rendering")
    print("=" * 60)
    
    gen = MoleculeGenerator3D("DMT", random_seed=1)
    gen.configure_rendering(
        width=1920,
        height=1080,
        y_rotation=180,
        sphere_scale=0.35,
    )
    sdf_path, png_path = gen.generate(
        render=True,
        output_base="examples/dmt_3d_rendered"
    )
    print()


def example_3d_custom_render():
    """3D structure with custom PyMOL styling."""
    print("=" * 60)
    print("Example 6: Custom 3D Rendering")
    print("=" * 60)
    
    gen = MoleculeGenerator3D("5284583")  # Mescaline
    gen.configure_rendering(
        width=2560,
        height=1440,
        stick_radius=0.25,
        sphere_scale=0.32,
        stick_ball_ratio=2.0,
        y_rotation=220,
        bg_color="white",
        carbon_color="gray20",
    )
    sdf_path, png_path = gen.generate(
        optimize=True,
        force_field="MMFF94",
        render=True,
        output_base="examples/mescaline_custom"
    )
    print()


def example_batch_processing():
    """Batch processing multiple compounds."""
    print("=" * 60)
    print("Example 7: Batch Processing")
    print("=" * 60)
    
    compounds = {
        "psilocin": "520-52-5",
        "DMT": "6089",
        "5-MeO-DMT": "1832",
        "mescaline": "5284583",
    }
    
    for name, cid in compounds.items():
        print(f"\nProcessing {name}...")
        
        # 2D structure
        gen_2d = MoleculeGenerator2D(cid)
        gen_2d.generate(f"examples/batch/{name}_2d.svg")
        
        # 3D structure (SDF only for batch)
        gen_3d = MoleculeGenerator3D(cid, random_seed=42)
        gen_3d.generate(
            optimize=True,
            output_base=f"examples/batch/{name}_3d"
        )
    print()


def example_fetch_compound():
    """Demonstrate compound fetching utility."""
    print("=" * 60)
    print("Example 8: Compound Fetching")
    print("=" * 60)
    
    # Fetch by name
    smiles, name = fetch_compound("psilocin")
    print(f"Name: {name}")
    print(f"SMILES: {smiles}")
    print()
    
    # Fetch by CID
    smiles, name = fetch_compound("24802108")
    print(f"CID 24802108:")
    print(f"Name: {name}")
    print(f"SMILES: {smiles}")
    print()


def example_comparison():
    """Generate structures for comparison."""
    print("=" * 60)
    print("Example 9: Structural Comparison")
    print("=" * 60)
    
    compounds = ["psilocin", "psilocybin", "4-HO-MET", "4-AcO-DMT"]
    
    for compound in compounds:
        try:
            gen = MoleculeGenerator2D(
                compound,
                angle=np.pi,
                scale=35,
                margin=0.8,
            )
            gen.generate(f"examples/comparison/{compound}.svg")
        except Exception as e:
            print(f"Error processing {compound}: {e}")
    print()


def main():
    """Run all examples."""
    import os
    
    # Create output directories
    os.makedirs("examples", exist_ok=True)
    os.makedirs("examples/batch", exist_ok=True)
    os.makedirs("examples/comparison", exist_ok=True)
    
    # Run examples
    example_2d_basic()
    example_2d_custom()
    example_2d_smiles()
    example_3d_basic()
    
    # Uncomment if PyMOL is installed
    # example_3d_render()
    # example_3d_custom_render()
    
    example_batch_processing()
    example_fetch_compound()
    example_comparison()
    
    print("=" * 60)
    print("All examples completed!")
    print("=" * 60)


if __name__ == "__main__":
    main()
