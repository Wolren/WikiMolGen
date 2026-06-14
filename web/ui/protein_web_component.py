"""
wikimolgen.web.protein_components - Streamlit Components for Protein Visualization
===================================================================================

Reusable Streamlit UI components for protein structure rendering.
"""

from pathlib import Path
from typing import Any

import streamlit as st

# Pymol and the rest of the rendering backend are imported lazily so the app
# can still boot (and the user can still use 2D/3D) when pymol's native
# libraries are not installed in the current environment.
try:
    from wikimolgen.rendering.protein import (
        ColorScheme,
        ProteinGenerator,
        ProteinVisualizationError,
    )

    _PROTEIN_BACKEND_AVAILABLE = True
except Exception as _protein_import_error:  # pragma: no cover - import-time guard
    ColorScheme = None  # type: ignore[assignment]
    ProteinGenerator = None  # type: ignore[assignment]
    ProteinVisualizationError = Exception  # type: ignore[assignment, misc]
    _PROTEIN_BACKEND_AVAILABLE = False
    _PROTEIN_IMPORT_ERROR: Exception = _protein_import_error


def render_protein_selector() -> str:
    """Render protein PDB ID selector."""
    pdb_id = (
        st.text_input(
            "PDB ID",
            value="8F7W",
            max_chars=4,
            placeholder="e.g. 8F7W (Dynorphin-KOR)",
            help="Enter 4-character PDB identifier (e.g., 8F7W for Dynorphin-KOR)",
        )
        .upper()
        .strip()
    )
    return pdb_id


def render_protein_cartoon_settings() -> dict[str, Any]:
    """Render protein cartoon rendering controls."""

    config = {}

    with st.expander("Cartoon", expanded=False):
        color_scheme = st.selectbox(
            "Color Scheme",
            [
                "Secondary Structure",
                "Rainbow",
                "Chain",
                "Hydrophobicity",
                "Element",
                "B Factor",
                "Occupancy",
                "B Factor (Temperature)",
                "Per-Chain Rainbow",
            ],
            key="protein_color_scheme",
            help="How to color the protein structure",
        )

        config["color_scheme"] = {
            "Secondary Structure": "secondary_structure",
            "Rainbow": "rainbow",
            "Chain": "chain",
            "Hydrophobicity": "hydrophobicity",
            "Element": "element",
            "B Factor": "bfactor",
            "Occupancy": "occupancy",
            "B Factor (Temperature)": "b_factor_temperature",
            "Per-Chain Rainbow": "chain_rainbow",
        }[color_scheme]

        if color_scheme == "Secondary Structure":
            with st.expander("Secondary Structure Colors", expanded=False):
                col1, col2, col3 = st.columns(3)
                with col1:
                    config["helix_color"] = st.color_picker("α-Helix", "#3399FF", key="helix_color")
                with col2:
                    config["sheet_color"] = st.color_picker("β-Sheet", "#FFCC00", key="sheet_color")
                with col3:
                    config["loop_color"] = st.color_picker("Coil/Loop", "#99AABB", key="loop_color")

        with st.expander("Cartoon Settings", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                config["cartoon_transparency"] = st.slider(
                    "Transparency", 0.0, 1.0, 0.0, 0.1, key="cartoon_transparency"
                )
                config["cartoon_fancy_helices"] = st.checkbox(
                    "Fancy Helices", value=True, key="cartoon_fancy"
                )

            with col2:
                config["cartoon_flat_sheets"] = st.checkbox(
                    "Flat Sheets", value=True, key="cartoon_sheets"
                )

        return config


def render_protein_ligand_settings() -> dict[str, Any]:
    """Render ligand/heteroatom rendering controls."""

    config = {}

    with st.expander("Ligand & Heteroatoms", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            config["show_ligand"] = st.checkbox(
                "Show Ligand",
                value=False,
                key="show_ligand",
                help="Display organic molecules (ligands) in the structure",
            )

        with col2:
            config["show_water"] = st.checkbox(
                "Show Water", value=False, key="show_water", help="Display water molecules"
            )

        if config["show_ligand"]:
            with st.expander("Ligand Display", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    config["ligand_style"] = st.selectbox(
                        "Representation",
                        ["sticks", "spheres", "lines", "ball_and_stick"],
                        key="ligand_style",
                    )
                with col2:
                    config["ligand_transparency"] = st.slider(
                        "Transparency", 0.0, 1.0, 0.0, 0.05, key="ligand_transparency"
                    )

                col1, col2 = st.columns(2)
                with col1:
                    config["ligand_color"] = st.selectbox(
                        "Coloring", ["element", "single", "chain"], key="ligand_color"
                    )
                with col2:
                    config["stick_radius"] = st.slider(
                        "Stick Radius", 0.1, 1.0, 0.25, 0.05, key="ligand_stick_radius"
                    )

                if config["ligand_color"] == "single":
                    config["ligand_single_color"] = st.color_picker(
                        "Ligand Color", "#FF6B6B", key="ligand_single_color"
                    )

        return config


def render_protein_canvas_settings() -> dict[str, Any]:
    """Render canvas and rendering quality controls."""

    config = {}

    with st.expander("Rendering", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            config["width"] = st.slider("Width (px)", 800, 3840, 1920, 100, key="protein_width")

        with col2:
            config["height"] = st.slider("Height (px)", 600, 2160, 1080, 100, key="protein_height")

        with st.expander("Quality Settings", expanded=False):
            col1, col2 = st.columns(2)

            with col1:
                config["antialias"] = st.slider(
                    "Antialiasing",
                    0,
                    4,
                    2,
                    key="protein_antialias",
                    help="0=off, 1=2x, 2=3x, 3=4x, 4=8x",
                )

                config["specular"] = st.slider(
                    "Specular",
                    0,
                    5,
                    1,
                    key="protein_specular",
                    help="Specular reflection intensity",
                )

            with col2:
                config["ambient"] = st.slider(
                    "Ambient Light", 0.0, 1.0, 0.40, 0.05, key="protein_ambient"
                )

                config["bg_color"] = st.selectbox(
                    "Background", ["black", "white", "gray"], key="protein_bg"
                )

                config["shininess"] = st.slider(
                    "Shininess",
                    0,
                    100,
                    10,
                    key="protein_shininess",
                    help="Surface shininess (higher = more glossy)",
                )

            config["ray_shadows"] = st.checkbox(
                "Ray Shadows",
                value=True,
                key="protein_ray_shadows",
                help="Cast shadows during ray tracing (slower but more depth)",
            )

            config["ray_trace"] = st.checkbox(
                "Ray Tracing",
                value=True,
                key="protein_ray_trace",
                help="Ray-traced rendering (slower but higher quality)",
            )

        col1, col2 = st.columns(2)

        with col1:
            config["auto_orient"] = st.checkbox(
                "Auto-Orient Protein", value=True, key="protein_auto_orient"
            )

        with col2:
            config["autocrop"] = st.checkbox(
                "Auto-Crop Image",
                value=True,
                key="protein_autocrop",
                help="Same as 3D generation - crops to protein bounds",
            )

        if config["autocrop"]:
            config["crop_margin"] = st.slider(
                "Crop Margin (px)", 0, 50, 10, 1, key="protein_crop_margin"
            )

        return config


def render_protein_structure(
    pdb_id: str,
    cartoon_config: dict[str, Any],
    ligand_config: dict[str, Any],
    canvas_config: dict[str, Any],
    output_base: Path,
) -> Path:
    """Render protein structure and save to file.

    Follows the same pattern as MoleculeGenerator2D/3D:
    - Accepts output_base parameter (required)
    - Returns Path to the generated .png file
    - Consistent with 2D/3D rendering workflow
    - Includes autocropping support

    Parameters
    ----------
    pdb_id : str
        PDB identifier (e.g., "8F7W")
    cartoon_config : Dict[str, Any]
        Cartoon rendering configuration
    ligand_config : Dict[str, Any]
        Ligand rendering configuration
    canvas_config : Dict[str, Any]
        Canvas/rendering quality configuration
    output_base : Path
        Base output path (without extension)

    Returns
    -------
    Path
        Path to rendered PNG file (.png extension added)

    Raises
    ------
    ProteinVisualizationError
        If protein rendering fails
    """
    if not _PROTEIN_BACKEND_AVAILABLE:
        st.error(
            "Protein rendering is unavailable: the pymol backend failed to "
            f"import ({type(_PROTEIN_IMPORT_ERROR).__name__}: "
            f"{_PROTEIN_IMPORT_ERROR}). Install pymol-open-source to enable it."
        )
        raise RuntimeError("pymol backend not available") from _PROTEIN_IMPORT_ERROR

    # Create output path with .png extension (same as 3D generator)
    output_path = output_base.with_suffix(".png")

    try:
        with st.spinner(f"Fetching PDB structure {pdb_id}..."):
            gen = ProteinGenerator(pdb_id)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Chains", len(gen.metadata.chains))
        with col2:
            st.metric("Atoms", gen.metadata.num_atoms)
        with col3:
            st.metric("Residues", gen.metadata.num_residues)
        with col4:
            st.metric("Has Ligand", "Yes" if gen.metadata.has_ligand else "No")

        # Configure cartoon rendering (same pattern as 3D generator)
        gen.configure_cartoon(
            helix_color=cartoon_config.get("helix_color", "#3399FF"),
            sheet_color=cartoon_config.get("sheet_color", "#FFCC00"),
            loop_color=cartoon_config.get("loop_color", "#99AABB"),
            width=canvas_config["width"],
            height=canvas_config["height"],
            bg_color=canvas_config["bg_color"],
            ambient=canvas_config.get("ambient", 0.40),
            specular=canvas_config.get("specular", 1),
            shininess=canvas_config.get("shininess", 10),
            antialias=canvas_config.get("antialias", 2),
            ray_trace_mode=1 if canvas_config.get("ray_trace", False) else 0,
            ray_shadows=1 if canvas_config.get("ray_shadows", True) else 0,
            auto_orient=canvas_config.get("auto_orient", True),
            autocrop=canvas_config.get("autocrop", True),
            crop_margin=canvas_config.get("crop_margin", 10),
        )

        gen.configure_ligand(
            ligand_style=ligand_config.get("ligand_style", "sticks"),
            ligand_transparency=ligand_config.get("ligand_transparency", 0.0),
            ligand_color_scheme=ligand_config.get("ligand_color", "element"),
            ligand_single_color=ligand_config.get("ligand_single_color", "#FF6B6B"),
            stick_radius=ligand_config.get("stick_radius", 0.25),
        )

        # Generate and save protein structure (same as 3D generator)
        with st.spinner("Rendering protein structure..."):
            gen.generate(
                str(output_path),
                color_scheme=ColorScheme(cartoon_config["color_scheme"]),
                show_ligand=ligand_config.get("show_ligand", True),
                show_water=ligand_config.get("show_water", False),
            )

        print(f"[ok] Rendered to {output_path}")
        return output_path

    except ProteinVisualizationError as e:
        st.error(f"Visualization Error: {e}")
        return None
    except Exception as e:
        st.error(f"Error: {type(e).__name__}: {e}")
        return None


def display_protein_image(image_path: Path, title: str = "Protein Structure") -> None:
    """Display rendered protein image with download button.

    Parameters
    ----------
    image_path : Path
        Path to the rendered PNG image
    title : str
        Title for the image display
    """
    if image_path.exists():
        st.image(str(image_path), caption=title, use_column_width=True)

        with open(image_path, "rb") as f:
            st.download_button(
                label="Download PNG",
                data=f.read(),
                file_name=image_path.name,
                mime="image/png",
                use_container_width=True,
            )
    else:
        st.error(f"Image file not found: {image_path}")
