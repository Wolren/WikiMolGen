"""
wikimolgen.cli - Command Line Interface
========================================
CLI for 2D and 3D molecular structure generation.
"""

import argparse
import sys
import numpy as np

from . import __version__
from .wikimol2d import MoleculeGenerator2D
from .wikimol3d import MoleculeGenerator3D


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser."""
    parser = argparse.ArgumentParser(
        prog="wikimolgen",
        description="Generate 2D and 3D molecular structures from PubChem or SMILES",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # 2D SVG generation
  wikimolgen 2d --compound 24802108 --output 4-MeO-DiPT.svg
  wikimolgen 2d --compound "psilocin" --angle 0 --scale 40
  
  # 3D structure with PyMOL rendering
  wikimolgen 3d --compound "DMT" --render --output-base dmt
  wikimolgen 3d --compound 5284583 --optimize --force-field MMFF94
  
  # Using SMILES directly
  wikimolgen 2d --compound "CC(C)N(CCC1=CNC2=C1C(=CC=C2)OC)C(C)C" --output test.svg
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )
    
    subparsers = parser.add_subparsers(dest="mode", help="Generation mode", required=True)
    
    # 2D subcommand
    parser_2d = subparsers.add_parser("2d", help="Generate 2D SVG structures")
    parser_2d.add_argument(
        "--compound",
        required=True,
        help="PubChem CID, compound name, or SMILES string"
    )
    parser_2d.add_argument(
        "--output",
        default="molecule_2d.svg",
        help="Output SVG filename (default: molecule_2d.svg)"
    )
    parser_2d.add_argument(
        "--angle",
        type=float,
        default=np.pi,
        help="Rotation angle in radians (default: π)"
    )
    parser_2d.add_argument(
        "--scale",
        type=float,
        default=30.0,
        help="Pixels per coordinate unit (default: 30.0)"
    )
    parser_2d.add_argument(
        "--margin",
        type=float,
        default=0.5,
        help="Canvas margin in coordinate units (default: 0.5)"
    )
    parser_2d.add_argument(
        "--bond-length",
        type=float,
        default=35.0,
        help="Fixed bond length in pixels (default: 35.0)"
    )
    parser_2d.add_argument(
        "--font-size",
        type=int,
        default=36,
        help="Minimum font size for atom labels (default: 36)"
    )
    parser_2d.add_argument(
        "--no-bw-palette",
        action="store_true",
        help="Use color palette instead of black and white"
    )
    parser_2d.add_argument(
        "--opaque-background",
        action="store_true",
        help="Use opaque white background instead of transparent"
    )
    
    # 3D subcommand
    parser_3d = subparsers.add_parser("3d", help="Generate 3D structures with optional PyMOL rendering")
    parser_3d.add_argument(
        "--compound",
        required=True,
        help="PubChem CID, compound name, or SMILES string"
    )
    parser_3d.add_argument(
        "--output-base",
        help="Base name for output files (default: compound name)"
    )
    parser_3d.add_argument(
        "--optimize",
        action="store_true",
        default=True,
        help="Optimize geometry with force field (default: True)"
    )
    parser_3d.add_argument(
        "--no-optimize",
        dest="optimize",
        action="store_false",
        help="Skip geometry optimization"
    )
    parser_3d.add_argument(
        "--force-field",
        choices=["MMFF94", "UFF"],
        default="MMFF94",
        help="Force field for optimization (default: MMFF94)"
    )
    parser_3d.add_argument(
        "--max-iterations",
        type=int,
        default=200,
        help="Maximum optimization iterations (default: 200)"
    )
    parser_3d.add_argument(
        "--seed",
        type=int,
        default=1,
        help="Random seed for conformer generation (default: 1)"
    )
    parser_3d.add_argument(
        "--render",
        action="store_true",
        help="Render molecule with PyMOL (generates PNG)"
    )
    parser_3d.add_argument(
        "--width",
        type=int,
        default=1320,
        help="Render width in pixels (default: 1320)"
    )
    parser_3d.add_argument(
        "--height",
        type=int,
        default=990,
        help="Render height in pixels (default: 990)"
    )
    parser_3d.add_argument(
        "--y-rotation",
        type=float,
        default=200.0,
        help="Y-axis rotation in degrees (default: 200.0)"
    )
    
    return parser


def run_2d(args: argparse.Namespace) -> None:
    """Execute 2D generation."""
    try:
        gen = MoleculeGenerator2D(
            identifier=args.compound,
            angle=args.angle,
            scale=args.scale,
            margin=args.margin,
            bond_length=args.bond_length,
            min_font_size=args.font_size,
            use_bw_palette=not args.no_bw_palette,
            transparent_background=not args.opaque_background,
        )
        gen.generate(output=args.output)
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_3d(args: argparse.Namespace) -> None:
    """Execute 3D generation."""
    try:
        gen = MoleculeGenerator3D(
            identifier=args.compound,
            random_seed=args.seed,
        )
        
        if args.render:
            gen.configure_rendering(
                width=args.width,
                height=args.height,
                y_rotation=args.y_rotation,
            )
        
        gen.generate(
            optimize=args.optimize,
            force_field=args.force_field,
            max_iterations=args.max_iterations,
            render=args.render,
            output_base=args.output_base,
        )
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Main entry point for CLI."""
    parser = create_parser()
    args = parser.parse_args()
    
    if args.mode == "2d":
        run_2d(args)
    elif args.mode == "3d":
        run_3d(args)


if __name__ == "__main__":
    main()
