"""
wikimolgen.web.protein_components - Streamlit Components for Protein Visualization
===================================================================================

Reusable Streamlit UI components for protein structure rendering.
"""

import streamlit as st
from pathlib import Path
from typing import Optional, Dict, Any

from wikimolgen.rendering.protein import (
    ProteinGenerator,
    ColorScheme,
    ProteinVisualizationError,
)


def render_protein_selector() -> str:
    """Render protein PDB ID selector."""

    col1, col2 = st.columns([3, 1])

    with col1:
        pdb_id = st.text_input(
            "PDB ID",
            value="8F7W",
            max_chars=4,
            help="Enter 4-character PDB identifier (e.g., 8F7W for Dynorphin-KOR)"
        ).upper().strip()

    with col2:
        preset = st.selectbox(
            "Preset",
            ["Custom", "8F7W (Dynorphin-KOR)", "3V2O (GPCR)", "1A8O (Protein-Ligand)"],
            label_visibility="collapsed"
        )

        if "8F7W" in preset:
            pdb_id = "8F7W"
        elif "3V2O" in preset:
            pdb_id = "3V2O"
        elif "1A8O" in preset:
            pdb_id = "1A8O"

    return pdb_id


def render_protein_cartoon_settings() -> Dict[str, Any]:
    """Render protein cartoon rendering controls."""

    config = {}

    st.markdown("#### **Protein Cartoon**")

    color_scheme = st.selectbox(
        "Color Scheme",
        ["Secondary Structure", "Rainbow", "Chain"],
        key="protein_color_scheme",
        help="How to color the protein structure"
    )

    config["color_scheme"] = {
        "Secondary Structure": "secondary_structure",
        "Rainbow": "rainbow",
        "Chain": "chain",
    }[color_scheme]

    with st.expander("Structure Colors", expanded=False):
        col1, col2, col3 = st.columns(3)

        if color_scheme == "Secondary Structure":
            # Standard secondary structure colors
            with col1:
                config["helix_color"] = st.color_picker(
                    "α-Helix",
                    "#00FF00",
                    key="helix_color"
                )

            with col2:
                config["sheet_color"] = st.color_picker(
                    "β-Sheet",
                    "#00FFFF",
                    key="sheet_color"
                )

            with col3:
                config["loop_color"] = st.color_picker(
                    "Coil/Loop",
                    "#FFA500",
                    key="loop_color"
                )

    with st.expander("Cartoon Settings", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            config["cartoon_transparency"] = st.slider(
                "Transparency",
                0.0, 1.0, 0.0, 0.1,
                key="cartoon_transparency"
            )
            config["cartoon_fancy_helices"] = st.checkbox(
                "Fancy Helices",
                value=True,
                key="cartoon_fancy"
            )

        with col2:
            config["cartoon_flat_sheets"] = st.checkbox(
                "Flat Sheets",
                value=True,
                key="cartoon_sheets"
            )

    return config


def render_protein_ligand_settings() -> Dict[str, Any]:
    """Render ligand/heteroatom rendering controls."""

    config = {}

    st.markdown("#### **Ligand & Heteroatoms**")

    col1, col2 = st.columns(2)

    with col1:
        config["show_ligand"] = st.checkbox(
            "Show Ligand",
            value=True,
            key="show_ligand",
            help="Display organic molecules (ligands) in the structure"
        )

    with col2:
        config["show_water"] = st.checkbox(
            "Show Water",
            value=False,
            key="show_water",
            help="Display water molecules"
        )

    if config["show_ligand"]:
        with st.expander("Ligand Display", expanded=False):
            config["ligand_style"] = st.selectbox(
                "Ligand Representation",
                ["sticks", "spheres", "lines", "ball_and_stick"],
                key="ligand_style"
            )

            config["ligand_color"] = st.selectbox(
                "Ligand Coloring",
                ["element", "single_color", "chain"],
                key="ligand_color"
            )

            if config["ligand_color"] == "single_color":
                config["ligand_single_color"] = st.color_picker(
                    "Ligand Color",
                    "#FF6B6B",
                    key="ligand_single_color"
                )

    return config


def render_protein_canvas_settings() -> Dict[str, Any]:
    """Render canvas and rendering quality controls."""

    config = {}

    st.markdown("#### **Rendering**")

    col1, col2 = st.columns(2)

    with col1:
        config["width"] = st.slider(
            "Width (px)",
            800, 3840, 1920, 100,
            key="protein_width"
        )

    with col2:
        config["height"] = st.slider(
            "Height (px)",
            600, 2160, 1080, 100,
            key="protein_height"
        )

    with st.expander("Quality Settings", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            config["antialias"] = st.slider(
                "Antialiasing",
                0, 4, 2,
                key="protein_antialias",
                help="0=off, 1=2x, 2=3x, 3=4x, 4=8x"
            )

            config["ray_trace"] = st.checkbox(
                "Ray Tracing",
                value=False,
                key="protein_ray_trace"
            )

        with col2:
            config["ambient"] = st.slider(
                "Ambient Light",
                0.0, 1.0, 0.4, 0.05,
                key="protein_ambient"
            )

            config["bg_color"] = st.selectbox(
                "Background",
                ["black", "white", "gray"],
                key="protein_bg"
            )

    col1, col2 = st.columns(2)

    with col1:
        config["auto_orient"] = st.checkbox(
            "Auto-Orient Protein",
            value=True,
            key="protein_auto_orient"
        )

    with col2:
        config["autocrop"] = st.checkbox(
            "Auto-Crop Image",
            value=True,
            key="protein_autocrop",
            help="Same as 3D generation - crops to protein bounds"
        )

    if config["autocrop"]:
        config["crop_margin"] = st.slider(
            "Crop Margin (px)",
            0, 50, 10, 1,
            key="protein_crop_margin"
        )

    return config


def render_protein_structure(
    pdb_id: str,
    cartoon_config: Dict[str, Any],
    ligand_config: Dict[str, Any],
    canvas_config: Dict[str, Any],
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

    # Create output path with .png extension (same as 3D generator)
    output_path = output_base.with_suffix(".png")

    try:
        with st.spinner(f"Fetching PDB structure {pdb_id}..."):
            gen = ProteinGenerator(pdb_id)

        st.success(f"✓ Fetched {pdb_id}")

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Chains", len(gen.metadata.chains))
        with col2:
            st.metric("Atoms", gen.metadata.num_atoms)
        with col3:
            st.metric("Residues", gen.metadata.num_residues)
        with col4:
            st.metric("Has Ligand", "✓" if gen.metadata.has_ligand else "✗")

        # Configure cartoon rendering (same pattern as 3D generator)
        gen.configure_cartoon(
            helix_color=cartoon_config.get("helix_color", "#00FF00"),
            sheet_color=cartoon_config.get("sheet_color", "#00FFFF"),
            loop_color=cartoon_config.get("loop_color", "#FFA500"),
            transgender_pink=cartoon_config.get("transgender_pink", "#FF1493"),
            transgender_white=cartoon_config.get("transgender_white", "#FFFFFF"),
            transgender_blue=cartoon_config.get("transgender_blue", "#1493FF"),
            width=canvas_config["width"],
            height=canvas_config["height"],
            bg_color=canvas_config["bg_color"],
            ambient=canvas_config["ambient"],
            antialias=canvas_config["antialias"],
            ray_trace_mode=1 if canvas_config.get("ray_trace", False) else 0,
            auto_orient=canvas_config["auto_orient"],
            autocrop=canvas_config.get("autocrop", True),
            crop_margin=canvas_config.get("crop_margin", 10),
        )

        # Generate and save protein structure (same as 3D generator)
        with st.spinner("Rendering protein structure..."):
            gen.generate(
                str(output_path),
                color_scheme=ColorScheme(cartoon_config["color_scheme"]),
                show_ligand=ligand_config.get("show_ligand", True),
                show_water=ligand_config.get("show_water", False),
            )

        print(f"✓ Rendered to {output_path}")
        return output_path

    except ProteinVisualizationError as e:
        st.error(f"Visualization Error: {e}")
        raise
    except Exception as e:
        st.error(f"Error: {type(e).__name__}: {e}")
        raise


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