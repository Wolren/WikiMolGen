import argparse


def run_protein_render(args: argparse.Namespace) -> None:
    from wikimolgen.rendering.protein import ColorScheme, ProteinGenerator

    output = args.output or f"{args.pdb_id.lower()}_protein.png"

    gen = ProteinGenerator(args.pdb_id)
    gen.configure_cartoon(
        width=args.width,
        height=args.height,
        ray_trace_mode=1 if args.ray_trace else 0,
    )
    gen.generate(
        output,
        color_scheme=ColorScheme(args.color_scheme),
        show_ligand=args.show_ligand,
        show_water=args.show_water,
    )

    print(f"Rendered: {output}")
