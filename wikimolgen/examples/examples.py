"""
wikimolgen Examples - Comprehensive Demonstration
==================================================
Examples using common pharmaceutical and biochemical compounds.
Demonstrates both manual and auto-orientation for 2D and 3D structures.
"""

import os
from wikimolgen.rendering.wikimol2d import MoleculeGenerator2D
from wikimolgen.rendering.wikimol3d import MoleculeGenerator3D

os.makedirs("examples/2D", exist_ok=True)
os.makedirs("examples/3D", exist_ok=True)
os.makedirs("examples/batch", exist_ok=True)


def example_2d_manual():
    """Example 1: 2D structure with manual orientation."""
    print("=" * 70)
    print("Example 1: 2D Structure (Manual Orientation)")
    print("=" * 70)

    # Aspirin (acetylsalicylic acid)
    gen = MoleculeGenerator2D("2244", angle_degrees=180)
    gen.generate("examples/2D/aspirin_manual.svg")
    print()



def example_2d_auto():
    """Example 2: 2D structure with auto-orientation."""
    print("=" * 70)
    print("Example 2: 2D Structure (Auto-Orientation)")
    print("=" * 70)

    gen = MoleculeGenerator2D("2244", auto_orient=True)
    gen.generate("examples/2D/aspirin_auto.svg")

    gen = MoleculeGenerator2D("1832", auto_orient=True, padding=0.1)
    gen.generate("examples/2D/5-MeO-DMT.svg")

    gen = MoleculeGenerator2D("24802108", auto_orient=True)
    gen.generate("examples/2D/4-MeO-DiPT.svg")
    print()


def example_3d_manual():
    """Example 3: 3D structure with manual orientation."""
    print("=" * 70)
    print("Example 3: 3D Structure (Manual Orientation)")
    print("=" * 70)

    # Caffeine
    gen = MoleculeGenerator3D("2519")
    gen.generate(
        optimize=True,
        force_field="MMFF94",
        render=True,
        output_base="examples/3D/caffeine_manual"
    )
    print()


def example_3d_auto():
    """Example 4: 3D structure with auto-orientation."""
    print("=" * 70)
    print("Example 4: 3D Structure (Auto-Orientation)")
    print("=" * 70)

    # Caffeine with automatic orientation
    gen = MoleculeGenerator3D("2519")
    gen.configure_rendering(auto_orient=True)
    gen.generate(
        optimize=True,
        force_field="MMFF94",
        render=True,
        output_base="examples/3D/caffeine_auto"
    )
    print()


def example_batch_processing():
    """Example 5: Batch processing of multiple compounds."""
    print("=" * 70)
    print("Example 5: Batch Processing (Auto-Orientation)")
    print("=" * 70)

    # Common pharmaceutical and biochemical compounds
    compounds = {
        "aspirin": "2244",  # Acetylsalicylic acid (NSAID)
        "caffeine": "2519",  # Stimulant (contains N)
        "glucose": "5793",  # Simple sugar (contains O)
        "ibuprofen": "3672",  # NSAID (common medication)
        "vitamin_c": "54670067",  # Ascorbic acid (antioxidant)
        "penicillin": "5904",  # Antibiotic (contains S)
        "dopamine": "681",  # Neurotransmitter
        "serotonin": "5202",  # Neurotransmitter
    }

    for name, cid in compounds.items():
        print(f"\nProcessing: {name} (CID: {cid})")

        try:
            # 2D with auto-orientation
            print(f"  Generating 2D structure...")
            gen_2d = MoleculeGenerator2D(cid, auto_orient=True)
            gen_2d.generate(f"examples/batch/{name}_2d.svg")

            # 3D with auto-orientation (SDF only for batch efficiency)
            print(f"  Generating 3D structure...")
            gen_3d = MoleculeGenerator3D(cid)
            gen_3d.generate(
                optimize=True,
                force_field="MMFF94",
                render=False,  # Skip rendering for faster batch processing
                output_base=f"examples/batch/{name}_3d"
            )

        except Exception as e:
            print(f"  Error: {e}")

    print()


def example_element_colors():
    """Example 6: Demonstrating different element colors."""
    print("=" * 70)
    print("Example 6: Demonstrating different element colors")
    print("=" * 70)

    # Compounds chosen to showcase different elements
    showcase = {
        "glucose": "5793",  # C, H, O (oxygen-rich)
        "dopamine": "681",  # C, H, O, N (nitrogen)
        "penicillin": "5904",  # C, H, O, N, S (sulfur)
        "chloroquine": "2719",  # C, H, N, Cl (chlorine)
        "levothyroxine": "853",  # C, H, O, N, I (iodine)
    }

    for name, cid in showcase.items():
        print(f"\nGenerating: {name}")

        try:
            gen = MoleculeGenerator3D(cid)
            gen.configure_rendering(auto_orient=True)
            gen.generate(
                optimize=True,
                render=True,
                output_base=f"examples/3D/{name}_colors",
            )
        except Exception as e:
            print(f"  Error: {e}")

    print()


def example_4_MeO_DiPT():
    """Example 7: 4-MeO-DiPT"""
    print("=" * 70)
    print("Example 7: 4-MeO-DiPT")
    print("=" * 70)

    gen = MoleculeGenerator3D("24802108")
    gen.configure_rendering(
        auto_crop=True,
        auto_orient=False,
        y_rotation=200,
    )
    gen.generate(
        optimize=True,
        render=True,
        force_field="MMFF94",
        output_base="examples/3D/4-Meo-DiPT"
    )
    print()


def example_minimal():
    """Example 8: Minimal/Clean Style"""
    print("=" * 70)
    print("Example 8: Minimal/Clean Style")
    print("=" * 70)

    gen = MoleculeGenerator3D("5202")

    gen.configure_rendering(
        stick_radius=0.15,           # Thin sticks
        sphere_scale=0.20,           # Small spheres
        stick_ball_ratio=1.5,        # Subtle balls
        ambient=0.3,                 # Bright ambient
        specular=0.5,                # Less specular
        bg_color="white",
    )

    gen.generate(optimize=True, render=True, output_base="examples/3D/serotonin_minimal")


def example_dramatic_lighting():
    """Example 9: Dramatic Lighting"""
    print("=" * 70)
    print("Example 9: Dramatic Lighting")
    print("=" * 70)

    gen = MoleculeGenerator3D("chloroquine")

    gen.configure_rendering(
        ambient=0.1,                 # Low ambient (darker)
        specular=1.5,                # High specular (shiny)
        shininess=50,                # Very shiny
        direct=0.7,                  # Strong direct light
        reflect=0.3,                 # Some reflection
        bg_color="black",            # Dark background
    )

    gen.generate(optimize=True, render=True, output_base="examples/3D/chloroquine_dramatic")

def main():
    """Run all examples."""
    print("\n" + "=" * 70)
    print("WIKIMOLGEN EXAMPLES - PHARMACEUTICAL & BIOCHEMICAL COMPOUNDS")
    print("=" * 70 + "\n")

    # Run examples
    example_2d_manual()
    example_2d_auto()
    example_3d_manual()
    example_3d_auto()
    example_batch_processing()
    example_element_colors()
    example_4_MeO_DiPT()
    example_minimal()
    example_dramatic_lighting()

    print("=" * 70)
    print("All examples completed successfully!")
    print("=" * 70)
    print("\nOutput locations:")
    print("  - 2D structures: examples/2D/")
    print("  - 3D structures: examples/3D/")
    print("  - Batch processing: examples/batch/")
    print()


if __name__ == "__main__":
    main()
