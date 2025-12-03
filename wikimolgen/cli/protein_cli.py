"""
wikimolgen.rendering.protein_cli - Protein Structure CLI Commands
=========================================================

Command-line interface for protein structure generation and rendering.
"""

import click
from pathlib import Path
from typing import Optional
from wikimolgen.rendering.protein import (
    ProteinGenerator,
    ColorScheme,
    ProteinNGLViewRenderer,
    get_optimal_dynorphin_kor_view
)


@click.group()
def protein():
    """Protein structure visualization tools."""
    pass


@protein.command()
@click.argument("pdb_id")
@click.option("--output", "-o", default=None, help="Output PNG filename")
@click.option("--color-scheme",
              type=click.Choice(["secondary_structure", "rainbow", "chain", "hydrophobicity"]),
              default="secondary_structure",
              help="Color scheme for protein")
@click.option("--show-ligand/--no-ligand", default=True, help="Show ligand/heteroatoms")
@click.option("--show-water/--no-water", default=False, help="Show water molecules")
@click.option("--width", type=int, default=1920, help="Image width")
@click.option("--height", type=int, default=1080, help="Image height")
@click.option("--ray-trace/--no-ray-trace", default=False, help="Enable ray tracing")
def render(pdb_id, output, color_scheme, show_ligand, show_water, width, height, ray_trace):
    """Render protein structure."""

    if output is None:
        output = f"{pdb_id.lower()}_protein.png"

    gen = ProteinGenerator(pdb_id)

    gen.configure_cartoon(
        width=width,
        height=height,
        ray_trace_mode=1 if ray_trace else 0,
    )

    gen.generate(
        output,
        color_scheme=ColorScheme(color_scheme),
        show_ligand=show_ligand,
        show_water=show_water,
    )

    click.echo(f"✓ Rendered: {output}")


@protein.command()
@click.argument("pdb_id")
def info(pdb_id):
    """Display protein structure information."""

    gen = ProteinGenerator(pdb_id)
    meta = gen.metadata

    click.echo(f"\nPDB ID: {meta.pdb_id}")
    click.echo(f"Chains: {', '.join(meta.chains)}")
    click.echo(f"Atoms: {meta.num_atoms}")
    click.echo(f"Residues: {meta.num_residues}")
    click.echo(f"Has Ligand: {meta.has_ligand}")
    click.echo(f"Has Water: {meta.has_water}")
    if meta.title:
        click.echo(f"Title: {meta.title}")
    if meta.resolution:
        click.echo(f"Resolution: {meta.resolution} Å")


@protein.command()
@click.argument("pdb_id")
@click.option("--output", "-o", default="protein_view.html", help="Output HTML file")
def interactive(pdb_id, output):
    """Create interactive NGLView visualization (for Jupyter)."""

    try:
        renderer = ProteinNGLViewRenderer(pdb_id)
        view = renderer.create_view()
        view.add_cartoon("spectrum")
        view.add_ligand_sticks()

        click.echo(f"✓ Created interactive view")

    except ImportError as e:
        click.echo(f"Error: {e}")


@protein.command()
@click.option("--output", "-o", default="dynorphin_kor.png", help="Output PNG filename")
def dynorphin_kor(output):
    """Render Dynorphin-KOR complex (8F7W) with optimized settings."""

    click.echo("Rendering Dynorphin-KOR complex (PDB: 8F7W)...")

    config = get_optimal_dynorphin_kor_view()

    gen = ProteinGenerator("8F7W")
    gen.configure_cartoon(**config["cartoon"])
    gen.configure_ligand(**config["ligand"])

    gen.cartoon_config.width = config["render"]["width"]
    gen.cartoon_config.height = config["render"]["height"]
    gen.cartoon_config.bg_color = config["render"]["bg_color"]
    gen.cartoon_config.antialias = config["render"]["antialias"]
    gen.cartoon_config.auto_orient = config["render"]["auto_orient"]

    gen.generate(output, color_scheme=ColorScheme.SECONDARY_STRUCTURE)

    click.echo(f"✓ Saved: {output}")


if __name__ == "__main__":
    protein()