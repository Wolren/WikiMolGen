import json
from datetime import datetime
from typing import Any

import streamlit as st


def export_current_settings_as_template(gen_type: str) -> dict[str, Any]:
    if gen_type == "2D":
        settings_dict = {
            "scale": st.session_state.get("scale", 30.0),
            "margin": st.session_state.get("margin", 0.5),
            "bond_length": st.session_state.get("bond_length", 45.0),
            "min_font_size": st.session_state.get("min_font_size", 36),
            "padding": st.session_state.get("padding", 0.03),
            "use_bw_palette": st.session_state.get("use_bw_palette", True),
            "transparent_background": st.session_state.get("transparent_background", True),
            "auto_orient_2d": st.session_state.get("auto_orient_2d", True),
        }
        template_dict = {
            "type": "2d",
            "name": "Custom 2D",
            "description": "Exported from web interface",
            "settings": settings_dict,
        }
    else:
        settings_dict = {
            "auto_orient_3d": st.session_state.get("auto_orient_3d", True),
            "x_rotation": st.session_state.get("x_rot_slider", 0.0),
            "y_rotation": st.session_state.get("y_rot_slider", 0.0),
            "z_rotation": st.session_state.get("z_rot_slider", 0.0),
            "stick_radius": st.session_state.get("stick_radius", 0.2),
            "sphere_scale": st.session_state.get("sphere_scale", 0.3),
            "stick_ball_ratio": st.session_state.get("stick_ball_ratio", 1.8),
            "ray_trace_mode": 1 if st.session_state.get("ray_trace", False) else 0,
            "ray_shadows": 1 if st.session_state.get("ray_shadows", False) else 0,
            "stick_transparency": st.session_state.get("stick_transparency", 0.0),
            "sphere_transparency": st.session_state.get("sphere_transparency", 0.0),
            "valence": st.session_state.get("valence", 0.0),
            "antialias": st.session_state.get("antialias", 2),
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
        template_dict = {
            "type": "3d",
            "name": "Custom 3D",
            "description": "Exported from web interface",
            "settings": settings_dict,
        }

    return template_dict


def export_color_template() -> dict[str, Any]:
    color_dict = {
        "name": f"Custom Colors - {datetime.now().strftime('%Y%m%d_%H%M%S')}",
        "description": "Exported from web interface",
        "element_colors": {},
        "stick_color": None,
        "bg_color": st.session_state.get("bg_color", "white"),
    }
    return color_dict


def load_custom_template(
    uploaded_file,
    template_type: str,
) -> dict[str, Any] | None:
    try:
        template_data = json.load(uploaded_file)
        template_name = template_data.get(
            "name", f'Custom_{datetime.now().strftime("%H%M%S")}'
        )
        return {"name": template_name, "data": template_data}
    except Exception as e:
        st.error(f"Failed to load {template_type} template: {e}")
        return None


def save_template_to_session(
    template_name: str,
    template_data: dict[str, Any],
    template_type: str,
) -> None:
    if template_type == "color":
        st.session_state.custom_color_templates[template_name] = template_data
        st.session_state.uploaded_color_template = template_data
    elif template_type == "settings":
        st.session_state.custom_settings_templates[template_name] = template_data
        st.session_state.uploaded_settings_template = template_data

        settings = template_data.get("settings", template_data)
        for key, value in settings.items():
            if key in st.session_state:
                st.session_state[key] = value
        st.session_state.template_applied_once = True


def apply_templates_to_generator(
    gen: Any,
    gen_type: str,
) -> bool:
    if st.session_state.get("template_applied_once", False):
        return False

    template_applied = False

    color_choice = st.session_state.get("color_template_selector", "None")
    if color_choice != "None":
        try:
            if color_choice in st.session_state.custom_color_templates:
                gen.load_color_template(
                    st.session_state.custom_color_templates[color_choice]
                )
            else:
                gen.load_color_template(color_choice)
            template_applied = True
        except Exception as e:
            st.warning(f"Color template error: {e}")

    if st.session_state.uploaded_color_template:
        try:
            gen.load_color_template(st.session_state.uploaded_color_template)
            template_applied = True
        except Exception as e:
            st.warning(f"Uploaded color template error: {e}")

    settings_choice = st.session_state.get("settings_template_selector", "None")
    if settings_choice != "None":
        try:
            if settings_choice in st.session_state.custom_settings_templates:
                st.session_state.template_applied_once = True
                gen.load_settings_template(
                    st.session_state.custom_settings_templates[settings_choice]
                )
                template_applied = True
            else:
                gen.load_settings_template(settings_choice)
                template_applied = True
        except Exception as e:
            st.warning(f"Settings template error: {e}")

    if st.session_state.uploaded_settings_template:
        try:
            gen.load_settings_template(st.session_state.uploaded_settings_template)
            template_applied = True
        except Exception as e:
            st.warning(f"Uploaded settings template error: {e}")

    return template_applied
