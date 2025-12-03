"""
wikimolgen.cli - Command Line Interface with Complete Settings Support
======================================================================

Enhanced CLI with full template support and comprehensive parameter options.
"""

import argparse
import sys

from wikimolgen import __version__
from wikimolgen.rendering.wikimol2d import MoleculeGenerator2D
from wikimolgen.rendering.wikimol3d import MoleculeGenerator3D


def create_parser() -> argparse.ArgumentParser:
    """Create and configure argument parser with comprehensive settings support."""

    parser = argparse.ArgumentParser(
        prog="wikimolgen",
        description="Generate 2D and 3D molecular structures from PubChem or SMILES",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:

# 2D SVG generation
  wikimolgen 2d --compound aspirin --output aspirin.svg
  wikimolgen 2d --compound 24802108 --template publication_2d

# 3D structure with PyMOL rendering
  wikimolgen 3d --compound DMT --render --template high_quality_3d
  wikimolgen 3d --compound 5284583 --color-template cpk_standard

# Using custom template
  wikimolgen 2d --compound glucose --template my_settings.json
  wikimolgen 3d --compound caffeine --color-template my_colors.json --render

# 3D with custom rotations (sliders in web interface)
  wikimolgen 3d --compound aspirin --render --x-rotation 10 --y-rotation 200 --z-rotation 0
"""
    )

    parser.add_argument(
        "--version",
        action="version",
        version=f"%(prog)s {__version__}"
    )

    subparsers = parser.add_subparsers(dest="mode", help="Generation mode", required=True)

    # ===== 2D SUBCOMMAND =====
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
        "--template",
        help="Settings template (predefined name or JSON file path)"
    )
    parser_2d.add_argument(
        "--color-template",
        help="Color template (predefined name or JSON file path)"
    )

    # 2D Display Settings
    parser_2d.add_argument(
        "--angle",
        type=float,
        default=180,
        help="Rotation angle in degrees (default: 180)"
    )
    parser_2d.add_argument(
        "--auto-orient",
        action="store_true",
        help="Automatically optimize viewing angle using PCA"
    )

    # 2D Advanced Settings
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
        default=45.0,
        help="Fixed bond length in pixels (default: 45.0)"
    )
    parser_2d.add_argument(
        "--min-font-size",
        type=int,
        default=36,
        help="Minimum font size for atom labels (default: 36)"
    )
    parser_2d.add_argument(
        "--padding",
        type=float,
        default=0.03,
        help="Padding around drawing (default: 0.03)"
    )
    parser_2d.add_argument(
        "--use-bw",
        action="store_true",
        help="Use black and white atom palette"
    )
    parser_2d.add_argument(
        "--transparent-bg",
        action="store_true",
        help="Use transparent background"
    )

    # ===== 3D SUBCOMMAND =====
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
        "--template",
        help="Settings template (predefined name or JSON file path)"
    )
    parser_3d.add_argument(
        "--color-template",
        help="Color template (predefined name or JSON file path)"
    )

    # 3D Generation Options
    parser_3d.add_argument(
        "--optimize",
        action="store_true",
        default=True,
        help="Optimize geometry with force field (default: True)"
    )
    parser_3d.add_argument(
        "--force-field",
        choices=["MMFF94", "UFF"],
        default="MMFF94",
        help="Force field for optimization (default: MMFF94)"
    )
    parser_3d.add_argument(
        "--render",
        action="store_true",
        help="Render molecule with PyMOL (generates PNG)"
    )

    # 3D Display - Orientation (as sliders in CLI context)
    parser_3d.add_argument(
        "--auto-orient",
        action="store_true",
        help="Automatically optimize 3D orientation"
    )
    parser_3d.add_argument(
        "--x-rotation",
        type=float,
        default=0.0,
        help="X-axis rotation in degrees (0-360, default: 0)"
    )
    parser_3d.add_argument(
        "--y-rotation",
        type=float,
        default=200.0,
        help="Y-axis rotation in degrees (0-360, default: 200)"
    )
    parser_3d.add_argument(
        "--z-rotation",
        type=float,
        default=0.0,
        help="Z-axis rotation in degrees (0-360, default: 0)"
    )

    # 3D Rendering Settings
    parser_3d.add_argument(
        "--stick-radius",
        type=float,
        default=0.2,
        help="Stick radius (0.1-0.5, default: 0.2)"
    )
    parser_3d.add_argument(
        "--sphere-scale",
        type=float,
        default=0.3,
        help="Sphere scale factor (0.15-0.5, default: 0.3)"
    )
    parser_3d.add_argument(
        "--stick-ball-ratio",
        type=float,
        default=1.8,
        help="Stick-to-ball ratio (1.2-3.0, default: 1.8)"
    )
    parser_3d.add_argument(
        "--ray-trace",
        action="store_true",
        help="Enable ray tracing mode"
    )
    parser_3d.add_argument(
        "--ray-shadows",
        action="store_true",
        help="Enable ray tracing shadows (slower)"
    )
    parser_3d.add_argument(
        "--antialias",
        type=int,
        choices=[0, 1, 2, 3, 4],
        default=2,
        help="Antialiasing level (0=off, 1=on, 2-4=multisample, default: 2)"
    )

    # 3D Lighting Settings
    parser_3d.add_argument(
        "--ambient",
        type=float,
        default=0.25,
        help="Ambient lighting (0.0-1.0, default: 0.25)"
    )
    parser_3d.add_argument(
        "--specular",
        type=float,
        default=1.0,
        help="Specular lighting (0.0-2.0, default: 1.0)"
    )
    parser_3d.add_argument(
        "--direct",
        type=float,
        default=0.45,
        help="Direct lighting intensity (0.0-1.0, default: 0.45)"
    )
    parser_3d.add_argument(
        "--reflect",
        type=float,
        default=0.45,
        help="Reflection intensity (0.0-1.0, default: 0.45)"
    )
    parser_3d.add_argument(
        "--shininess",
        type=int,
        default=30,
        help="Surface shininess (10-100, default: 30)"
    )

    # 3D Effects Settings
    parser_3d.add_argument(
        "--stick-transparency",
        type=float,
        default=0.0,
        help="Stick transparency (0.0-1.0, default: 0.0)"
    )
    parser_3d.add_argument(
        "--sphere-transparency",
        type=float,
        default=0.0,
        help="Sphere transparency (0.0-1.0, default: 0.0)"
    )
    parser_3d.add_argument(
        "--valence",
        type=float,
        default=0.0,
        help="Valence visibility (0.0-0.3, default: 0.0)"
    )
    parser_3d.add_argument(
        "--depth-cue",
        action="store_true",
        help="Enable depth cueing (fog effect)"
    )

    # 3D Canvas Settings
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
        "--bg-color",
        choices=["white", "black", "gray"],
        default="white",
        help="Background color (default: white)"
    )
    parser_3d.add_argument(
        "--crop-margin",
        type=int,
        default=10,
        help="Auto-crop margin in pixels (default: 10)"
    )

    return parser


def run_2d(args: argparse.Namespace) -> None:
    """Execute 2D generation with comprehensive template support."""

    try:
        # Create generator with settings
        gen = MoleculeGenerator2D(
            identifier=args.compound,
            angle_degrees=args.angle if not args.auto_orient else None,
            scale=args.scale,
            margin=args.margin,
            bond_length=args.bond_length,
            min_font_size=args.min_font_size,
            padding=args.padding,
            use_bw_palette=args.use_bw,
            transparent_background=args.transparent_bg,
            auto_orient=args.auto_orient,
        )

        # Apply template if provided
        if args.template:
            print(f"Loading settings template: {args.template}")
            gen.load_settings_template(args.template)

        if args.color_template:
            print(f"Loading color template: {args.color_template}")
            gen.load_color_template(args.color_template)

        # Generate output
        gen.generate(output=args.output)

    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        sys.exit(1)


def run_3d(args: argparse.Namespace) -> None:
    """Execute 3D generation with comprehensive settings and template support."""

    try:
        # Create generator
        gen = MoleculeGenerator3D(identifier=args.compound)

        # Configure rendering with all settings
        gen.configure_rendering(
            auto_orient=args.auto_orient,
            x_rotation=args.x_rotation if not args.auto_orient else 0.0,
            y_rotation=args.y_rotation if not args.auto_orient else 200.0,
            z_rotation=args.z_rotation if not args.auto_orient else 0.0,
            stick_radius=args.stick_radius,
            sphere_scale=args.sphere_scale,
            stick_ball_ratio=args.stick_ball_ratio,
            ray_trace_mode=1 if args.ray_trace else 0,
            ray_shadows=1 if args.ray_shadows else 0,
            stick_transparency=args.stick_transparency,
            sphere_transparency=args.sphere_transparency,
            valence=args.valence,
            antialias=args.antialias,
            ambient=args.ambient,
            specular=args.specular,
            direct=args.direct,
            reflect=args.reflect,
            shininess=args.shininess,
            depth_cue=1 if args.depth_cue else 0,
            width=args.width,
            height=args.height,
            bg_color=args.bg_color,
            auto_crop=True,
            crop_margin=args.crop_margin,
        )

        # Apply template if provided
        if args.template:
            print(f"Loading settings template: {args.template}")
            gen.load_settings_template(args.template)

        if args.color_template:
            print(f"Loading color template: {args.color_template}")
            gen.load_color_template(args.color_template)

        # Generate output
        gen.generate(
            optimize=args.optimize,
            force_field=args.force_field,
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
