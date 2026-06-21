import base64
import dataclasses
import logging
import tempfile
from pathlib import Path
from typing import Any

import streamlit as st

from wikimolgen.configs import Config2D, ConformerConfig, ConfigLoader, RenderConfig3D
from wikimolgen.rendering.wikimol2d import MoleculeGenerator2D
from wikimolgen.rendering.wikimol3d import MoleculeGenerator3D

logger = logging.getLogger(__name__)

_CONFORMER_SESSION_KEYS = [f.name for f in dataclasses.fields(ConformerConfig)]


def _session_overrides(dc: type, prefix: str = "") -> dict[str, Any]:
    """Build an overrides dict from session state matching dataclass fields."""
    overrides: dict[str, Any] = {}
    proto = dc()
    for field in dataclasses.fields(proto):
        key = prefix + field.name
        if key in st.session_state:
            overrides[field.name] = st.session_state[key]
    return overrides


def build_2d_config() -> Config2D:
    overrides = _session_overrides(Config2D)
    if st.session_state.get("auto_orient_2d", True):
        overrides.pop("angle_degrees", None)
    else:
        overrides.setdefault("angle_degrees", st.session_state.get("angle_degrees", 0.0))
    overrides["auto_orient_2d"] = st.session_state.get("auto_orient_2d", True)
    if st.session_state.get("preview_white_bg", False):
        overrides["use_bw_palette"] = True
    return ConfigLoader.get_2d_config(overrides=overrides)


def build_3d_config() -> dict[str, Any]:
    overrides = _session_overrides(RenderConfig3D)
    overrides["auto_orient_3d"] = st.session_state.get("auto_orient_3d", True)
    return overrides


def generate_dynamic_filename(
    compound: str, structure_type: str, file_ext: str | None = None
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
        with open(image_path, encoding="utf-8") as svg_file:
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
            gen = MoleculeGenerator2D(compound, config=config)
            output_path = gen.draw(str(output_base.with_suffix(".svg")))

            if output_path and Path(output_path).exists():
                img_base64, mime_type = encode_image_to_base64(Path(output_path))
                image_html = (
                    f'<div style="max-width: 800px; height: 500px; '
                    f"display: flex; align-items: center; justify-content: center; "
                    f'background: transparent;">'
                    f'<img src="data:image/{mime_type};base64,{img_base64}" '
                    f'data-type="{structure_type}" class="compound-preview-image" '
                    f'style="width: 100%; height: 100%; object-fit: contain; display: block;" />'
                    f"</div>"
                )

                with open(output_path, "rb") as f:
                    file_data = f.read()

                filename = generate_dynamic_filename(compound, "2D")
                _store_result_in_session(image_html, compound, file_data, filename, "image/svg+xml")
                logger.info("Successfully rendered 2D structure: %s", compound)
                return image_html

            st.error("Failed to generate 2D structure image")
            return None

    except Exception as e:
        logger.error("Error rendering 2D structure: %s", e, exc_info=True)
        st.error(f"Error rendering 2D structure: {e}")
        return None


def _build_image_html(img_base64: str, mime_type: str, structure_type: str) -> str:
    return (
        f'<img src="data:image/{mime_type};base64,{img_base64}" '
        f'data-type="{structure_type}" class="compound-preview-image" />'
    )


def render_structure_3d(compound: str, structure_type: str) -> str | None:
    try:
        render_config = build_3d_config()
        sdf_content = st.session_state.get("sdf_content")
        same_compound = st.session_state.get("last_compound") == compound

        proto = ConformerConfig()
        conformer_changed = any(
            st.session_state.get(f.name, getattr(proto, f.name)) != getattr(proto, f.name)
            for f in dataclasses.fields(ConformerConfig)
        )

        with tempfile.TemporaryDirectory() as tmpdir:
            output_base = Path(tmpdir) / generate_dynamic_filename(compound, "3D")

            if same_compound and sdf_content and not conformer_changed:
                gen = MoleculeGenerator3D(compound)
                gen.configure_rendering(**render_config)
                png_path = gen.render_only(sdf_content, str(output_base.with_suffix(".png")))
            else:
                gen = MoleculeGenerator3D(compound)
                gen.configure_rendering(**render_config)

                raw = {
                    k: st.session_state.get(k)
                    for k in _CONFORMER_SESSION_KEYS
                    if st.session_state.get(k) is not None
                }
                conformer_overrides = {
                    k: v for k, v in _session_overrides(ConformerConfig).items() if k in raw
                }
                if conformer_overrides:
                    gen.configure_conformer(**conformer_overrides)

                sdf_path, png_path = gen.generate(
                    optimize=True, render=True, output_base=str(output_base)
                )

                if sdf_path and Path(sdf_path).exists():
                    with open(sdf_path, encoding="utf-8") as f:
                        st.session_state.sdf_content = f.read()

            if png_path and Path(png_path).exists():
                img_base64, mime_type = encode_image_to_base64(Path(png_path))
                image_html = _build_image_html(img_base64, mime_type, structure_type)

                with open(png_path, "rb") as f:
                    file_data = f.read()

                filename = generate_dynamic_filename(compound, "3D")
                _store_result_in_session(
                    image_html, compound, file_data, filename, f"image/{mime_type}"
                )
                logger.info("Successfully rendered 3D structure: %s", compound)
                return image_html

            st.error("Failed to generate 3D structure image")
            return None

    except Exception as e:
        logger.error("Error rendering 3D structure: %s", e, exc_info=True)
        st.error(f"Error rendering 3D structure: {e}")
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
