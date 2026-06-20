import base64
import dataclasses
import json
import logging
import tempfile
from pathlib import Path
from typing import Any

import streamlit as st

from wikimolgen.configs import Config2D, Config3D, ConformerConfig, RenderConfig3D
from wikimolgen.rendering.wikimol2d import MoleculeGenerator2D
from wikimolgen.rendering.wikimol3d import MoleculeGenerator3D

logger = logging.getLogger(__name__)

_CONFORMER_SESSION_KEYS = [f.name for f in dataclasses.fields(ConformerConfig)]


def _build_from_dataclass(dc: type, session_prefix: str = "") -> dict[str, Any]:
    """Build a config dict from session state using dataclass field defaults.

    For each field in *dc*, reads the matching key from ``st.session_state``
    (prefixed with *session_prefix* if given).  Falls back to the dataclass
    field default when the key is absent.
    """
    result: dict[str, Any] = {}
    proto = dc()
    for field in dataclasses.fields(proto):
        key = session_prefix + field.name
        result[field.name] = st.session_state.get(key, getattr(proto, field.name))
    return result


def build_2d_config() -> dict[str, Any]:
    auto_orient = st.session_state.get("auto_orient_2d", True)
    defaults = {f.name: getattr(Config2D(), f.name) for f in dataclasses.fields(Config2D)}
    config = {}
    for key, default in defaults.items():
        if key in st.session_state:
            config[key] = st.session_state[key]
        else:
            config[key] = default
    if auto_orient:
        config["angle_degrees"] = None
    config["auto_orient_2d"] = auto_orient
    return config


def build_3d_config() -> dict[str, Any]:
    auto_orient = st.session_state.get("auto_orient_3d", True)
    defaults = {
        f.name: getattr(RenderConfig3D(), f.name) for f in dataclasses.fields(RenderConfig3D)
    }
    config = {}
    for key, default in defaults.items():
        if key in st.session_state:
            config[key] = st.session_state[key]
        else:
            config[key] = default
    config["auto_orient_3d"] = auto_orient
    return config


def generate_dynamic_filename(
    compound: str, structure_type: str, file_extension: str = None
) -> str:
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


def _store_result_in_session(
    image_html: str,
    compound: str,
    file_data: bytes,
    file_name: str,
    file_mime: str,
) -> None:
    st.session_state.last_image_html = image_html
    st.session_state.last_compound = compound
    st.session_state.last_file_data = file_data
    st.session_state.last_file_name = file_name
    st.session_state.last_file_mime = file_mime
    st.session_state.rendered_structure = True
    st.session_state.download_filename_input = file_name


def render_structure_2d(compound: str, structure_type: str) -> str | None:
    try:
        with tempfile.TemporaryDirectory() as tmpdir:
            output_base = Path(tmpdir) / generate_dynamic_filename(compound, "2D")
            config = build_2d_config()
            gen = MoleculeGenerator2D(compound, **config)
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
                _store_result_in_session(image_html, compound, file_data, filename, "image/svg+xml")

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

            gen.configure_rendering(**render_config)

            raw = {
                k: st.session_state.get(k)
                for k in _CONFORMER_SESSION_KEYS
                if st.session_state.get(k) is not None
            }
            conformer_config = _build_from_dataclass(gen.config.conformer.__class__)
            conformer_keys = {k: v for k, v in conformer_config.items() if k in raw}
            if conformer_keys:
                gen.configure_conformer(**conformer_keys)

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

                # Cache SDF content for interactive 3D preview
                if sdf_path and Path(sdf_path).exists():
                    with open(sdf_path) as f:
                        st.session_state.sdf_content = f.read()

                filename = generate_dynamic_filename(compound, "3D")
                _store_result_in_session(
                    image_html, compound, file_data, filename, f"image/{mime_type}"
                )

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
