"""
web/base.py - Core Web Rendering Layer
======================================

Integrated rendering logic with session config management.

Handles:
  - 2D/3D structure generation with session state
  - Config persistence via ConfigSessionManager (cookies)
  - Template loading and user preferences
  - Dynamic file generation and download
  - Error handling with graceful fallbacks

Dependencies:
  - Streamlit (web framework)
  - ConfigSessionManager (session/config_manager.py)
  - MoleculeGenerator2D/3D (core wikimolgen)
"""

import streamlit as st
import tempfile
import base64
import logging
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Tuple, Optional, Literal

from wikimolgen.rendering.wikimol2d import MoleculeGenerator2D
from wikimolgen.rendering.wikimol3d import MoleculeGenerator3D

from session.config_manager import ConfigSessionManager

logger = logging.getLogger(__name__)


# ============================================================================
# SESSION STATE INITIALIZATION
# ============================================================================

def init_session_state():
    """Initialize Streamlit session state with defaults."""
    defaults = {
        # Rendering state
        "rendered_structure": False,
        "last_image_html": None,
        "last_compound": None,
        "last_file_data": None,
        "last_file_name": None,
        "last_file_mime": None,
        "download_filename_input": "molecule",

        # 2D Config
        "auto_orient_2d": True,
        "angle_degrees": 0.0,
        "scale": 30.0,
        "margin": 0.8,
        "bond_length": 50.0,
        "min_font_size": 36,
        "padding": 0.07,
        "use_bw": True,
        "transparent": True,
        "additionalAtomLabelPadding": 0.2,

        # 3D Config
        "auto_orient_3d": True,
        "stick_radius": 0.2,
        "sphere_scale": 0.3,
        "stick_ball_ratio": 1.8,
        "stick_transparency": 0.0,
        "sphere_transparency": 0.0,
        "valence": 0.0,
        "ambient": 0.25,
        "specular": 1.0,
        "direct": 0.45,
        "reflect": 0.45,
        "shininess": 30,
        "depth_cue": False,
        "width": 1800,
        "height": 1600,
        "auto_crop": True,
        "crop_margin": 10,
        "x_rot_slider": 0.0,
        "y_rot_slider": 0.0,
        "z_rot_slider": 0.0,

        # Config managers
        "config_manager_2d": None,
        "config_manager_3d": None,
        "config_manager_protein": None,
    }

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value


def get_config_manager(config_type: Literal["2d", "3d", "protein"]) -> ConfigSessionManager:
    """
    Get or create ConfigSessionManager for given type.

    Parameters
    ----------
    config_type : {"2d", "3d", "protein"}
        Type of configuration manager to get

    Returns
    -------
    ConfigSessionManager
        Session config manager instance
    """
    key = f"config_manager_{config_type}"

    if st.session_state.get(key) is None:
        st.session_state[key] = ConfigSessionManager(config_type=config_type)

    return st.session_state[key]


# ============================================================================
# CONFIG BUILDERS - Convert Session State to Generator Config
# ============================================================================

def build_2d_config() -> Dict[str, Any]:
    """
    Build 2D generator configuration from session state.

    Returns
    -------
    Dict[str, Any]
        Configuration dictionary for MoleculeGenerator2D
    """
    auto_orient_2d = st.session_state.get("auto_orient_2d", True)

    return {
        "angle_degrees": None if auto_orient_2d else st.session_state.get("angle_degrees", 0),
        "scale": st.session_state.get("scale", 30.0),
        "margin": st.session_state.get("margin", 0.8),
        "bond_length": st.session_state.get("bond_length", 50.0),
        "min_font_size": st.session_state.get("min_font_size", 32),
        "padding": st.session_state.get("padding", 0.07),
        "use_bw_palette": st.session_state.get("use_bw", True),
        "transparent_background": st.session_state.get("transparent", True),
        "auto_orient_2d": auto_orient_2d,
        "additional_atom_label_padding": st.session_state.get("additional_atom_label_padding", 0.2),
    }


def build_3d_config() -> Dict[str, Any]:
    """
    Build 3D rendering configuration from session state.

    Returns
    -------
    Dict[str, Any]
        Configuration dictionary for MoleculeGenerator3D
    """
    auto_orient_3d = st.session_state.get("auto_orient_3d", True)

    config = {
        "auto_orient_3d": auto_orient_3d,
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

    if not auto_orient_3d:
        config.update({
            "x_rotation": st.session_state.get("x_rot_slider", 0.0),
            "y_rotation": st.session_state.get("y_rot_slider", 0.0),
            "z_rotation": st.session_state.get("z_rot_slider", 0.0),
        })

    return config


# ============================================================================
# FILENAME & ENCODING UTILITIES
# ============================================================================

def generate_dynamic_filename(
    compound: str,
    structure_type: str,
    file_extension: str = None
) -> str:
    """
    Generate a dynamic filename based on compound and structure type.

    Parameters
    ----------
    compound : str
        Compound identifier (name, CID, or SMILES)
    structure_type : str
        "2D" or "3D"
    file_extension : str, optional
        File extension (auto-determined if None)

    Returns
    -------
    str
        Clean filename without extension
    """
    # Sanitize compound name for filename
    safe_compound = "".join(
        c for c in compound if c.isalnum() or c in ('-', '_', ' ')
    ).strip()

    if not safe_compound or len(safe_compound) > 50:
        safe_compound = "structure"

    # Format: compound_structuretype
    return f"{safe_compound}_{structure_type}".replace(' ', '_')


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

    # Determine MIME type
    if str(image_path).endswith(".svg"):
        mime_type = "svg+xml"
    else:
        mime_type = "png"

    return img_base64, mime_type


# ============================================================================
# TEMPLATE INTEGRATION (Placeholder)
# ============================================================================

def apply_templates_to_generator(generator, structure_type: str):
    """
    Apply user-selected template to generator.

    Placeholder for template system integration.

    Parameters
    ----------
    generator : MoleculeGenerator2D or MoleculeGenerator3D
        Generator to configure
    structure_type : str
        "2D" or "3D"
    """
    # Get template selection from session state
    template_name = st.session_state.get(
        f"template_{structure_type.lower()}",
        "default"
    )

    if template_name and template_name != "default":
        try:
            config_manager = get_config_manager(structure_type.lower())
            template_config = config_manager.load_template(template_name)
            logger.info(f"Applied template: {template_name}")
        except Exception as e:
            logger.warning(f"Failed to apply template {template_name}: {e}")

def render_structure_2d(compound: str, structure_type: str) -> Optional[str]:
    """
    Render 2D molecular structure.

    Parameters
    ----------
    compound : str
        PubChem CID, compound name, or SMILES string

    Returns
    -------
    Optional[str]
        HTML string with embedded SVG image, or None on error
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_base = Path(tmpdir) / generate_dynamic_filename(compound, "2D")

            # Build config
            config = build_2d_config()
            gen = MoleculeGenerator2D(compound, **config)

            # Apply templates
            apply_templates_to_generator(gen, "2D")
            gen.draw(compound)

            # Generate
            output_path = gen.draw(str(output_base.with_suffix(".svg")))

            if output_path and Path(output_path).exists():
                img_base64, mime_type = encode_image_to_base64(Path(output_path))
                data_type = f'data-type="{structure_type}"'

                # Create HTML
                image_html = (
                    f'<img src="data:image/{mime_type};base64,{img_base64}" '
                    f'{data_type} class="compound-preview-image" />'
                )

                # Store in session for download
                with open(output_path, "rb") as f:
                    file_data = f.read()

                filename = generate_dynamic_filename(compound, "2D")

                st.session_state.last_image_html = image_html
                st.session_state.last_compound = compound
                st.session_state.last_file_data = file_data
                st.session_state.last_file_name = filename
                st.session_state.last_file_mime = f"image/{mime_type}"
                st.session_state.rendered_structure = True
                st.session_state.download_filename_input = filename

                logger.info(f"Successfully rendered 2D structure: {compound}")
                return image_html
            else:
                st.error("Failed to generate 2D structure image")
                return None

    except Exception as e:
        logger.error(f"Error rendering 2D structure: {e}", exc_info=True)
        st.error(f"Error rendering 2D structure: {str(e)}")
        return None


def render_structure_3d(compound: str, structure_type: str) -> Optional[str]:
    """
    Render 3D molecular structure with PyMOL.

    Parameters
    ----------
    compound : str
        PubChem CID, compound name, or SMILES string

    Returns
    -------
    Optional[str]
        HTML string with embedded PNG image, or None on error
    """
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_base = Path(tmpdir) / generate_dynamic_filename(compound, "3D")

            # Build config
            gen = MoleculeGenerator3D(compound)
            render_config = build_3d_config()

            # Apply templates
            apply_templates_to_generator(gen, "3D")

            # Configure and generate
            gen.configure_rendering(**render_config)
            sdf_path, png_path = gen.generate(
                optimize=True,
                render=True,
                output_base=str(output_base)
            )

            if png_path and Path(png_path).exists():
                img_base64, mime_type = encode_image_to_base64(Path(png_path))

                data_type = f'data-type="{structure_type}"'
                image_html = (
                    f'<img src="data:image/{mime_type};base64,{img_base64}" '
                    f'{data_type} class="compound-preview-image" />'
                )

                # Store in session for download
                with open(png_path, "rb") as f:
                    file_data = f.read()

                filename = generate_dynamic_filename(compound, "3D")

                st.session_state.last_image_html = image_html
                st.session_state.last_compound = compound
                st.session_state.last_file_data = file_data
                st.session_state.last_file_name = filename
                st.session_state.last_file_mime = f"image/{mime_type}"
                st.session_state.rendered_structure = True
                st.session_state.download_filename_input = filename

                logger.info(f"Successfully rendered 3D structure: {compound}")
                return image_html
            else:
                st.error("Failed to generate 3D structure image")
                return None

    except Exception as e:
        logger.error(f"Error rendering 3D structure: {e}", exc_info=True)
        st.error(f"Error rendering 3D structure: {str(e)}")
        return None


def render_structure_dynamic(compound: str, structure_type: str) -> Optional[str]:
    """
    Render molecular structure dynamically based on type.

    Wrapper that routes to 2D or 3D renderer.

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
    if structure_type == "2D":
        return render_structure_2d(compound, structure_type)
    elif structure_type == "3D":
        return render_structure_3d(compound, structure_type)
    return None

def get_download_data() -> Tuple[Optional[bytes], Optional[str], Optional[str]]:
    """
    Get file data for download button.

    Returns
    -------
    Tuple[Optional[bytes], Optional[str], Optional[str]]
        (file_data, filename, mime_type) or (None, None, None) if no file
    """
    file_data = st.session_state.get("last_file_data")
    file_name = st.session_state.get("last_file_name")
    file_mime = st.session_state.get("last_file_mime")

    if file_data and file_name:
        # Append extension based on MIME type
        if "svg" in str(file_mime):
            file_name = f"{file_name}.svg"
        elif "png" in str(file_mime):
            file_name = f"{file_name}.png"

        return file_data, file_name, file_mime

    return None, None, None
