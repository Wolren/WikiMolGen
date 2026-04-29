import base64
import logging
import tempfile
from pathlib import Path
from typing import Any, Literal

import streamlit as st
from wikimolgen.configs import Config2D, Config3D
from wikimolgen.rendering.wikimol2d import MoleculeGenerator2D
from wikimolgen.rendering.wikimol3d import MoleculeGenerator3D

from session.config import ConfigSessionManager
from template.utils import apply_templates_to_generator

logger = logging.getLogger(__name__)

_CONFORMER_SESSION_KEYS = [
    "num_conformers",
    "use_random_coords",
    "clear_confs",
    "use_basic_knowledge",
    "enforce_chirality",
    "use_small_ring_torsions",
    "use_macrocycle_torsions",
    "use_exp_torsion_prefs",
    "max_iterations",
    "prune_rms_thresh",
]


def _filter_config(config: dict, ref_obj: object) -> dict:
    valid = {
        k for k in dir(ref_obj) if not k.startswith("_") and not callable(getattr(ref_obj, k, None))
    }
    return {k: v for k, v in config.items() if k in valid}


def get_config_manager(config_type: Literal["2d", "3d"]) -> ConfigSessionManager:
    key = f"config_manager_{config_type}"

    if st.session_state.get(key) is None:
        st.session_state[key] = ConfigSessionManager(config_type=config_type)

    return st.session_state[key]


def build_2d_config() -> dict[str, Any]:
    auto_orient_2d = st.session_state.get("auto_orient_2d", True)

    config = {
        "angle_degrees": None if auto_orient_2d else st.session_state.get("angle_degrees", 180.0),
        "scale": st.session_state.get("scale", 30.0),
        "margin": st.session_state.get("margin", 0.5),
        "bond_length": st.session_state.get("bond_length", 45.0),
        "min_font_size": st.session_state.get("min_font_size", 36),
        "padding": st.session_state.get("padding", 0.03),
        "use_bw_palette": st.session_state.get("use_bw_palette", True),
        "transparent_background": st.session_state.get("transparent_background", True),
        "auto_orient_2d": auto_orient_2d,
        "acs_mode": st.session_state.get("acs_mode", True),
        "additional_atom_label_padding": st.session_state.get("additional_atom_label_padding", 0.2),
        "auto_orient_amines": st.session_state.get("auto_orient_amines", True),
        "amine_target_angle": st.session_state.get("amine_target_angle", 0.0),
        "phenethylamine_target": st.session_state.get("phenethylamine_target", 90.0),
        "bond_line_width": st.session_state.get("bond_line_width", 1.0),
        "add_stereo_annotation": st.session_state.get("add_stereo_annotation", False),
        "include_radicals": st.session_state.get("include_radicals", False),
        "explicit_methyl": st.session_state.get("explicit_methyl", False),
        "scaling_factor": st.session_state.get("scaling_factor", 1.0),
        "no_atom_labels": st.session_state.get("no_atom_labels", False),
        "multiple_bond_offset": st.session_state.get("multiple_bond_offset", 0.15),
        "include_atom_tags": st.session_state.get("include_atom_tags", False),
        "include_chiral_flag": st.session_state.get("include_chiral_flag", False),
        "comic_mode": st.session_state.get("comic_mode", False),
        "fixed_font_size": st.session_state.get("fixed_font_size", -1),
    }
    return _filter_config(config, Config2D())


def build_3d_config() -> dict[str, Any]:
    auto_orient_3d = st.session_state.get("auto_orient_3d", True)

    config = {
        "auto_orient_3d": auto_orient_3d,
        "stick_radius": st.session_state.get("stick_radius", 0.2),
        "sphere_scale": st.session_state.get("sphere_scale", 0.3),
        "stick_ball_ratio": st.session_state.get("stick_ball_ratio", 1.8),
        "stick_quality": st.session_state.get("stick_quality", 64),
        "sphere_quality": st.session_state.get("sphere_quality", 6),
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
        "height": st.session_state.get("height", 1400),
        "auto_crop": st.session_state.get("auto_crop", True),
        "crop_margin": st.session_state.get("crop_margin", 10),
        "bg_color": st.session_state.get("bg_color", "white"),
        "stick_color": st.session_state.get("stick_color", "gray40"),
        "representation": st.session_state.get("representation", "sticks+spheres"),
        "two_sided_lighting": st.session_state.get("two_sided_lighting", True),
        "transparency_mode": st.session_state.get("transparency_mode", 1),
        "ambient_occlusion": st.session_state.get("ambient_occlusion", False),
        "ambient_occlusion_scale": st.session_state.get("ambient_occlusion_scale", 20.0),
        "ray_trace_fog": st.session_state.get("ray_trace_fog", 0.0),
        "fog_start": st.session_state.get("fog_start", 1.0),
        "zoom_buffer": st.session_state.get("zoom_buffer", 2.0),
        "ray_trace_mode": st.session_state.get("ray_trace_mode", 0),
        "ray_shadows": 1 if st.session_state.get("ray_shadows", False) else 0,
        "opaque_background": st.session_state.get("opaque_background", False),
        "stick_ball": st.session_state.get("stick_ball", True),
    }

    if not auto_orient_3d:
        config.update(
            {
                "x_rotation": st.session_state.get("x_rot_slider", 0.0),
                "y_rotation": st.session_state.get("y_rot_slider", 0.0),
                "z_rotation": st.session_state.get("z_rot_slider", 0.0),
            }
        )

    return _filter_config(config, Config3D().render)


def generate_dynamic_filename(
    compound: str, structure_type: str, file_extension: str = None
) -> str:
    compound.replace("@", "at").replace("/", "sl").replace("\\", "bs").replace("#", "hash")

    safe_compound = "".join(c for c in compound if c.isalnum() or c in ("-", "_", " ")).strip()

    if len(safe_compound) > 30:
        safe_compound = safe_compound[:30]

    if not safe_compound or len(safe_compound) > 50:
        safe_compound = "structure"

    return f"{safe_compound}_{structure_type}".replace(" ", "_")


def encode_image_to_base64(image_path: Path) -> tuple[str, str]:
    if str(image_path).endswith(".svg"):
        mime_type = "svg+xml"
        with open(image_path) as svg_file:
            svg_content = svg_file.read()
        img_base64 = base64.b64encode(svg_content.encode()).decode()
    else:
        mime_type = "png"
        with open(image_path, "rb") as img_file:
            img_base64 = base64.b64encode(img_file.read()).decode()

    return img_base64, mime_type


def render_structure_2d(compound: str, structure_type: str) -> str | None:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_base = Path(tmpdir) / generate_dynamic_filename(compound, "2D")
            config = build_2d_config()
            gen = MoleculeGenerator2D(compound, **config)

            apply_templates_to_generator(gen, "2D")
            output_path = gen.draw(str(output_base.with_suffix(".svg")))

            if output_path and Path(output_path).exists():
                img_base64, mime_type = encode_image_to_base64(Path(output_path))
                data_type = f'data-type="{structure_type}"'

                image_html = (
                    f'<div style="max-width: 800px; height: 500px; '
                    f"display: flex; align-items: center; justify-content: center; "
                    f'background: transparent;">'
                    f'<img src="data:image/{mime_type};base64,{img_base64}" '
                    f'{data_type} class="compound-preview-image" '
                    f'style="width: 100%; height: 100%; object-fit: contain; display: block;" />'
                    f"</div>"
                )

                with open(output_path, "rb") as f:
                    file_data = f.read()

                filename = generate_dynamic_filename(compound, "2D")

                st.session_state.last_image_html = image_html
                st.session_state.last_compound = compound
                st.session_state.last_file_data = file_data
                st.session_state.last_file_name = filename
                st.session_state.last_file_mime = "image/svg+xml"
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


def render_structure_3d(compound: str, structure_type: str) -> str | None:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_base = Path(tmpdir) / generate_dynamic_filename(compound, "3D")

            gen = MoleculeGenerator3D(compound)
            render_config = build_3d_config()

            apply_templates_to_generator(gen, "3D")

            gen.configure_rendering(**render_config)

            raw = {
                k: st.session_state.get(k)
                for k in _CONFORMER_SESSION_KEYS
                if st.session_state.get(k) is not None
            }
            conformer_config = _filter_config(raw, gen.config.conformer)
            if conformer_config:
                gen.configure_conformer(**conformer_config)

            sdf_path, png_path = gen.generate(
                optimize=True, render=True, output_base=str(output_base)
            )

            if png_path and Path(png_path).exists():
                img_base64, mime_type = encode_image_to_base64(Path(png_path))
                data_type = f'data-type="{structure_type}"'
                image_html = (
                    f'<img src="data:image/{mime_type};base64,{img_base64}" '
                    f'{data_type} class="compound-preview-image" />'
                )

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


def render_structure_dynamic(compound: str, structure_type: str) -> str | None:
    if structure_type == "2D":
        return render_structure_2d(compound, structure_type)
    elif structure_type == "3D":
        return render_structure_3d(compound, structure_type)
    return None


def get_download_data() -> tuple[bytes | None, str | None, str | None]:
    file_data = st.session_state.get("last_file_data")
    file_name = st.session_state.get("last_file_name")
    file_mime = st.session_state.get("last_file_mime")

    if file_data and file_name:
        if "svg" in str(file_mime):
            file_name = f"{file_name}.svg"
        elif "png" in str(file_mime):
            file_name = f"{file_name}.png"

        return file_data, file_name, file_mime

    return None, None, None
