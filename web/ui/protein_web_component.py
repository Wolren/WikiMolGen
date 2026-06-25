"""
wikimolgen.web.protein_components - Streamlit Components for Protein Visualization
===================================================================================

Reusable Streamlit UI components for protein structure rendering.
"""

import re
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
    ColorScheme = None  # type: ignore[assignment, misc]
    ProteinGenerator = None  # type: ignore[assignment, misc]
    ProteinVisualizationError = Exception  # type: ignore[assignment, misc]
    _PROTEIN_BACKEND_AVAILABLE = False
    _PROTEIN_IMPORT_ERROR: Exception = _protein_import_error


_PDB_RE = re.compile(r"^[0-9][A-Za-z0-9]{3}$")


def render_protein_selector() -> str:
    """Render protein PDB ID selector with format validation."""
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
    if pdb_id and not _PDB_RE.match(pdb_id):
        st.warning("Invalid PDB ID: must start with a digit followed by 3 alphanumeric characters.")
        return ""
    return pdb_id


def render_protein_cartoon_settings() -> dict[str, Any]:
    """Render protein cartoon rendering controls."""

    config: dict[str, Any] = {}

    with st.expander("Cartoon", expanded=False):
        color_scheme = st.selectbox(
            "Color Scheme",
            [
                "Chain",
                "Secondary Structure",
                "Rainbow",
                "Hydrophobicity",
                "Element",
                "B Factor",
                "Occupancy",
                "B Factor (Temperature)",
                "Per-Chain Rainbow",
            ],
            index=2,
            key="protein_color_scheme",
            help="How to color the protein structure",
        )

        config["color_scheme"] = {
            "Chain": "chain",
            "Secondary Structure": "secondary_structure",
            "Rainbow": "rainbow",
            "Hydrophobicity": "hydrophobicity",
            "Element": "element",
            "B Factor": "bfactor",
            "Occupancy": "occupancy",
            "B Factor (Temperature)": "b_factor_temperature",
            "Per-Chain Rainbow": "chain_rainbow",
        }[color_scheme]

        if color_scheme == "Secondary Structure":
            col1, col2, col3 = st.columns(3)
            with col1:
                config["helix_color"] = st.color_picker("α-Helix", "#3399FF", key="helix_color")
            with col2:
                config["sheet_color"] = st.color_picker("β-Sheet", "#FFCC00", key="sheet_color")
            with col3:
                config["loop_color"] = st.color_picker("Coil/Loop", "#99AABB", key="loop_color")

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

    config: dict[str, Any] = {}

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

            col1, col2 = st.columns(2)
            with col1:
                config["stick_quality"] = st.slider(
                    "Stick Quality",
                    8,
                    128,
                    64,
                    8,
                    key="ligand_stick_quality",
                    help="Smoothness of stick representation",
                )
            with col2:
                config["stick_ball_ratio"] = st.slider(
                    "Ball Ratio",
                    0.5,
                    3.0,
                    1.5,
                    0.1,
                    key="ligand_ball_ratio",
                    help="Ratio of ball to stick (higher = bigger atoms)",
                )

            config["show_bindsites"] = st.checkbox(
                "Show Binding Sites",
                value=True,
                key="protein_bindsites",
                help="Highlight binding site residues near ligands",
            )
            if config["show_bindsites"]:
                col1, col2 = st.columns(2)
                with col1:
                    config["binding_site_radius"] = st.slider(
                        "Site Radius",
                        1.0,
                        15.0,
                        5.0,
                        0.5,
                        key="protein_bind_radius",
                        help="Distance from ligand to show binding site",
                    )
                with col2:
                    config["binding_site_color"] = st.color_picker(
                        "Site Color", "yellow", key="protein_bind_color"
                    )

            config["show_residue_labels"] = st.checkbox(
                "Show Labels",
                value=False,
                key="protein_res_labels",
                help="Display residue numbers and names",
            )
            if config["show_residue_labels"]:
                config["label_size"] = st.slider(
                    "Label Size", 8, 30, 14, 1, key="protein_label_size"
                )

        return config


def render_protein_canvas_settings() -> dict[str, Any]:
    """Render canvas and rendering quality controls."""

    config: dict[str, Any] = {}

    with st.expander("Canvas", expanded=False):
        col1, col2 = st.columns(2)

        with col1:
            config["width"] = st.slider("Width (px)", 800, 3840, 1920, 100, key="protein_width")

        with col2:
            config["height"] = st.slider("Height (px)", 600, 2160, 1080, 100, key="protein_height")

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
                0,
                key="protein_specular",
                help="Specular reflection intensity",
            )

        with col2:
            config["ambient"] = st.slider(
                "Ambient Light", 0.0, 1.0, 0.30, 0.05, key="protein_ambient"
            )

            config["bg_color"] = st.selectbox(
                "Background", ["transparent", "white", "black", "gray"], key="protein_bg"
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
            value=False,
            key="protein_ray_shadows",
            help="Cast shadows during ray tracing (slower but more depth)",
        )

        config["ray_trace"] = st.checkbox(
            "Ray Tracing",
            value=False,
            key="protein_ray_trace",
            help="Ray-traced rendering (slower but higher quality)",
        )

        col1, col2 = st.columns(2)

        with col1:
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


def render_protein_effects_settings() -> dict[str, Any]:
    """Render effects controls for protein rendering."""

    config: dict[str, Any] = {}

    with st.expander("Effects", expanded=False):
        col1, col2 = st.columns(2)
        with col1:
            config["direct"] = st.slider(
                "Direct Light",
                0.0,
                1.0,
                0.50,
                0.05,
                key="protein_direct",
                help="Direct lighting intensity",
            )
            config["reflect"] = st.slider(
                "Reflection",
                0.0,
                1.0,
                0.20,
                0.05,
                key="protein_reflect",
                help="Reflection intensity",
            )
        with col2:
            config["depth_cue"] = st.checkbox(
                "Depth Cueing",
                value=False,
                key="protein_depth_cue",
                help="Enable fog effect for depth perception",
            )
            config["orthoscopic"] = st.checkbox(
                "Orthoscopic View",
                value=False,
                key="protein_orthoscopic",
                help="Toggle orthographic projection (no perspective)",
            )
            config["ray_opaque_background"] = st.checkbox(
                "Opaque Background",
                value=True,
                key="protein_ray_opaque",
                help="Ensure background is opaque in ray-traced output",
            )

        config["zoom_buffer"] = st.slider(
            "Zoom Buffer",
            0.5,
            5.0,
            2.0,
            0.1,
            key="protein_zoom_buffer",
            help="Camera zoom padding around the structure",
        )

    return config


def render_protein_structure(
    pdb_id: str,
    cartoon_config: dict[str, Any],
    ligand_config: dict[str, Any],
    canvas_config: dict[str, Any],
    output_base: Path,
) -> Path | None:
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
            f"{_PROTEIN_IMPORT_ERROR}). Install: pip install pymol-open-source"
        )
        raise RuntimeError("pymol backend not available") from _PROTEIN_IMPORT_ERROR

    # Create output path with .png extension (same as 3D generator)
    output_path = output_base.with_suffix(".png")

    try:
        with st.spinner(f"Fetching PDB structure {pdb_id}..."):
            gen = ProteinGenerator(pdb_id)

        gen._ensure_fetched()
        assert gen.metadata is not None

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
            cartoon_fancy_helices=1 if cartoon_config.get("cartoon_fancy_helices", True) else 0,
            cartoon_flat_sheets=cartoon_config.get("cartoon_flat_sheets", True),
            width=canvas_config["width"],
            height=canvas_config["height"],
            bg_color=canvas_config.get("bg_color", "transparent"),
            ambient=canvas_config.get("ambient", 0.30),
            specular=canvas_config.get("specular", 0),
            shininess=canvas_config.get("shininess", 10),
            antialias=canvas_config.get("antialias", 2),
            ray_trace_mode=1 if canvas_config.get("ray_trace", False) else 0,
            ray_shadows=1 if canvas_config.get("ray_shadows", False) else 0,
            auto_orient=st.session_state.get("protein_auto_rot", True),
            autocrop=canvas_config.get("autocrop", True),
            crop_margin=canvas_config.get("crop_margin", 10),
            direct=canvas_config.get("direct", 0.50),
            reflect=canvas_config.get("reflect", 0.20),
            depth_cue=1 if canvas_config.get("depth_cue", False) else 0,
            ray_opaque_background=1 if canvas_config.get("ray_opaque_background", True) else 0,
            orthoscopic=1 if canvas_config.get("orthoscopic", False) else 0,
            zoom_buffer=canvas_config.get("zoom_buffer", 2.0),
            x_rotation=st.session_state.get("prot_x", 0.0),
            y_rotation=st.session_state.get("prot_y", 0.0),
            z_rotation=st.session_state.get("prot_z", 0.0),
        )

        gen.configure_ligand(
            ligand_style=ligand_config.get("ligand_style", "sticks"),
            ligand_transparency=ligand_config.get("ligand_transparency", 0.0),
            ligand_color_scheme=ligand_config.get("ligand_color", "element"),
            ligand_single_color=ligand_config.get("ligand_single_color", "#FF6B6B"),
            stick_radius=ligand_config.get("stick_radius", 0.25),
            stick_quality=ligand_config.get("stick_quality", 64),
            stick_ball_ratio=ligand_config.get("stick_ball_ratio", 1.5),
            show_bindsites=ligand_config.get("show_bindsites", True),
            binding_site_radius=ligand_config.get("binding_site_radius", 5.0),
            binding_site_color=ligand_config.get("binding_site_color", "yellow"),
            show_residue_labels=ligand_config.get("show_residue_labels", False),
            label_size=ligand_config.get("label_size", 14),
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
