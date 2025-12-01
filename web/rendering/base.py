"""
web/base.py
=================
Core rendering logic for WikiMolGen web interface.
Handles 2D and 3D structure generation with adaptive quality settings.
"""

import streamlit as st
import tempfile
import base64
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, Optional

from wikimolgen.rendering.wikimol2d import MoleculeGenerator2D
from wikimolgen.rendering.wikimol3d import MoleculeGenerator3D
from template.utils import apply_templates_to_generator

def build_2d_config() -> Dict[str, Any]:
    """
    Build 2D generator configuration from session state.

    Returns
    -------
    Dict[str, Any]
        Configuration dictionary for MoleculeGenerator2D
    """
    auto_orient = st.session_state.get("auto_orient_2d", True)
    return {
        "angle_degrees": None if auto_orient else st.session_state.get("angle_2d", 0),
        "scale": st.session_state.get("scale", 30.0),
        "margin": st.session_state.get("margin", 0.8),
        "bond_length": st.session_state.get("bond_length", 50.0),
        "min_font_size": st.session_state.get("min_font_size", 36),
        "padding": st.session_state.get("padding", 0.07),
        "use_bw_palette": st.session_state.get("use_bw", True),
        "transparent_background": st.session_state.get("transparent", True),
        "auto_orient": auto_orient,
    }


def build_3d_config() -> Dict[str, Any]:
    """
    Build 3D rendering configuration from session state.

    Returns
    -------
    Dict[str, Any]
        Configuration dictionary for MoleculeGenerator3D rendering
    """
    auto_orient = st.session_state.get("auto_orient_3d", True)
    config = {
        "auto_orient": auto_orient,
        "stick_radius": st.session_state.get("stick_radius", 0.2),
        "sphere_scale": st.session_state.get("sphere_scale", 0.3),
        "stick_ball_ratio": st.session_state.get("stick_ball_ratio", 1.8),
        "stick_transparency": st.session_state.get("stick_transparency", 0.0),
        "sphere_transparency": st.session_state.get("sphere_transparency", 0.0),
        "valence": st.session_state.get("valence", 0.0),
        "ambient": st.session_state.get("ambient", 0.25),
        "specular": st.session_state.get("specular", 1.0),
        "direct": st.session_state.get("direct", 0.45),
        "reflect": st.session_state.get("reflect", 0.45),
        "shininess": st.session_state.get("shininess", 30),
        "depth_cue": 1 if st.session_state.get("depth_cue", False) else 0,
        "width": st.session_state.get("width", 1800),
        "height": st.session_state.get("height", 1600),
        "auto_crop": st.session_state.get("auto_crop", True),
        "crop_margin": st.session_state.get("crop_margin", 10),
    }

    if not auto_orient:
        config.update({
            "x_rotation": st.session_state.get("x_rot_slider", 0.0),
            "y_rotation": st.session_state.get("y_rot_slider", 0.0),
            "z_rotation": st.session_state.get("z_rot_slider", 0.0),
        })

    return config


def generate_dynamic_filename(compound: str, structure_type: str, file_extension: str) -> str:
    """
    Generate a dynamic filename based on compound, structure type, and current timestamp.

    Parameters
    ----------
    compound : str
        Compound identifier (name, CID, or SMILES)
    structure_type : str
        "2D" or "3D"
    file_extension : str
        File extension (e.g., ".png", ".svg")

    Returns
    -------
    str
        Dynamic filename with timestamp
    """
    # Sanitize compound name for filename
    safe_compound = "".join(c for c in compound if c.isalnum() or c in ('-', '_')).rstrip()
    if not safe_compound:
        safe_compound = "structure"

    # Format: compound_structuretype_timestamp.ext
    filename = f"{safe_compound} {structure_type}"
    return filename


def encode_image_to_base64(image_path: Path) -> Tuple[str, str]:
    """
    Encode image file to base64 string.

    Parameters
    ----------
    image_path : Path
        Path to image file

    Returns
    -------
    Tuple[str, str]
        (base64_string, mime_type)
    """
    with open(image_path, "rb") as img_file:
        img_base64 = base64.b64encode(img_file.read()).decode()
    mime_type = "svg+xml" if str(image_path).endswith(".svg") else "png"
    return img_base64, mime_type


def render_structure_dynamic(compound: str, structure_type: str) -> Optional[str]:
    """
    Render molecular structure dynamically based on current settings.

    Parameters
    ----------
    compound : str
        PubChem CID, compound name, or SMILES string
    structure_type : str
        "2D" or "3D"

    Returns
    -------
    Optional[str]
        HTML string with embedded image, or None on error
    """
    try:
        # Reset rendered_structure at start of new generation
        st.session_state.rendered_structure = False

        with tempfile.TemporaryDirectory() as tmpdir:
            output_base = Path(tmpdir) / f"{compound}_{structure_type}"

            if structure_type == "2D":
                config = build_2d_config()
                gen = MoleculeGenerator2D(compound, **config)
                apply_templates_to_generator(gen, "2D")
                gen.generate(compound)
                output_path = gen.generate(str(output_base) + ".svg")
            else:
                gen = MoleculeGenerator3D(compound)
                render_config = build_3d_config()
                apply_templates_to_generator(gen, "3D")
                gen.configure_rendering(**render_config)
                gen.generate(optimize=True, render=True, output_base=str(output_base))
                output_path = output_base.with_suffix(".png")

            # Encode and create HTML
            if output_path.exists():
                img_base64, mime_type = encode_image_to_base64(output_path)
                data_type = f'data-type="{structure_type}"'
                image_html = (
                    f'<img src="data:image/{mime_type};base64,{img_base64}" '
                    f'{data_type} class="compound-preview-image" />'
                )

                # Read file data for download
                with open(output_path, "rb") as f:
                    file_data = f.read()

                # Generate dynamic filename
                file_extension = ".png" if structure_type == "3D" else ".svg"
                dynamic_filename = generate_dynamic_filename(
                    compound, structure_type, file_extension
                )

                # Update session state with dynamic filename and file data
                st.session_state.last_image_html = image_html
                st.session_state.last_compound = compound
                st.session_state.last_file_data = file_data
                st.session_state.last_file_name = dynamic_filename
                st.session_state.last_file_mime = f"image/{mime_type}"
                st.session_state.rendered_structure = True
                st.session_state.download_filename_input = Path(dynamic_filename).stem

                return image_html
            else:
                st.error(f"Failed to generate {structure_type} structure image")
                return None

    except Exception as e:
        st.error(f"Error rendering structure: {str(e)}")
        return None