"""
web/rendering.py
=================
Core rendering logic for WikiMolGen web interface.
Handles 2D and 3D structure generation with adaptive quality settings.
"""

import streamlit as st
import tempfile
import base64
from pathlib import Path
from typing import Dict, Any, Tuple, Optional
from wikimolgen import MoleculeGenerator2D, MoleculeGenerator3D
from web.template_utils import apply_templates_to_generator

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
        "angle_degrees": None if auto_orient else st.session_state.get("angle_2d", 180),
        "scale": st.session_state.get("scale", 30.0),
        "margin": st.session_state.get("margin", 0.5),
        "bond_length": st.session_state.get("bond_length", 45.0),
        "min_font_size": st.session_state.get("min_font_size", 36),
        "padding": st.session_state.get("padding", 0.03),
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
        "x_rotation": 0.0 if auto_orient else st.session_state.get("x_rot_slider", 0.0),
        "y_rotation": 200.0 if auto_orient else st.session_state.get("y_rot_slider", 200.0),
        "z_rotation": 0.0 if auto_orient else st.session_state.get("z_rot_slider", 0.0),
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
        "width": st.session_state.get("width", 1320),
        "height": st.session_state.get("height", 990),
        "auto_crop": True,
        "crop_margin": st.session_state.get("crop_margin", 10),
    }

    return config


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
                img_width = 800 if structure_type == "3D" else 600

                image_html = (
                    f'<div style="text-align: center; margin: 5px 0;">'
                    f'<img src="data:image/{mime_type};base64,{img_base64}" '
                    f'style="max-width: {img_width}px; width: 100%; height: auto; '
                    f'box-shadow: 0 0px 0px rgba(0,0,0,0);" />'
                    f'</div>'
                )

                # Store in session state
                st.session_state.last_image_html = image_html
                st.session_state.last_output_path = str(output_path)
                st.session_state.last_compound = compound

                # Mark structure as successfully rendered
                st.session_state.rendered_structure = True

                # Store the actual file data for download
                with open(output_path, "rb") as f:
                    st.session_state.last_file_data = f.read()
                st.session_state.last_file_name = output_path.name
                st.session_state.last_file_mime = f"image/{mime_type}"

                return image_html
            else:
                st.error("❌ Failed to generate structure: Output file not created")
                return None

    except Exception as e:
        st.error(f"❌ Error generating structure: {str(e)}")
        import traceback
        with st.expander("🔍 Error Details"):
            st.code(traceback.format_exc())
        return None

def should_auto_render() -> bool:
    """
    Determine if structure should auto-render based on current state.

    Returns
    -------
    bool
        True if auto-render is enabled and settings changed
    """
    auto_generate = st.session_state.get("auto_generate", True)
    manual_trigger = st.session_state.get("manual_generate", False)

    return auto_generate or manual_trigger
