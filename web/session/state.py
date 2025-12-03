"""
web/state.py - Enhanced Session State with Cookie & Config Support
===================================================================

Centralized session state initialization and default values for WikiMolGen web interface.

Now includes:
  - Cookie persistence integration (via ConfigSessionManager)
  - Config loading from cookies
  - Template state management
  - Enhanced defaults
"""

import logging
from typing import Dict, Any, Optional, Literal

import streamlit as st

logger = logging.getLogger(__name__)


def get_2d_defaults() -> Dict[str, Any]:
    """Get default values for 2D rendering settings."""
    return {
        "auto_orient_2d": False,
        "angle_degrees": 0,
        "scale": 30.0,
        "margin": 0.8,
        "bond_length": 50.0,
        "min_font_size": 36,
        "padding": 0.07,
        "use_bw_palette": True,
        "transparent_background": True,
        "additional_atom_label_padding": 0.2
    }


def get_3d_defaults() -> Dict[str, Any]:
    """Get default values for 3D rendering settings."""
    return {
        "auto_orient_3d": False,
        "x_rot_slider": 0.0,
        "y_rot_slider": 0.0,
        "z_rot_slider": 0.0,
        "stick_radius": 0.2,
        "sphere_scale": 0.3,
        "stick_ball_ratio": 1.8,
        "ray_trace": False,
        "ray_shadows": False,
        "stick_transparency": 0.0,
        "sphere_transparency": 0.0,
        "valence": 0.0,
        "antialias": 2,
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
    }


def get_session_defaults() -> Dict[str, Any]:
    """
    Get all default session state values.

    Returns
    -------
    Dict[str, Any]
        Dictionary containing all default session state variables.
    """
    defaults = {
        # Core rendering state
        "rendered_structure": False,
        "compound_data": None,
        "last_image_html": None,
        "last_output_path": None,
        "last_compound": None,
        "last_compound_fetched": None,  # Track last compound fetched from PubChem

        # File download state
        "last_file_data": None,
        "last_file_name": None,
        "last_file_mime": None,
        "download_filename_input": "molecule",

        # PubChem data
        "pubchem_data": None,

        # Template state
        "uploaded_color_template": None,
        "uploaded_settings_template": None,
        "custom_color_templates": {},
        "custom_settings_templates": {},
        "template_applied_once": False,

        # UI state
        "structure_type": "2D",
        "manual_generate": False,
        "save_filename": "",

        # Template selectors
        "color_template_selector": "None",
        "settings_template_selector": "None",

        # Config manager instances (non-serializable)
        "config_manager_2d": None,
        "config_manager_3d": None,
        "config_manager_protein": None,

        # Cookie state
        "last_loaded_from_cookie": None,
        "config_changed": False,
    }

    # Add 2D and 3D defaults
    defaults.update(get_2d_defaults())
    defaults.update(get_3d_defaults())

    return defaults


def initialize_session_state(load_from_cookie: bool = False, cookie_data: Optional[Dict[str, Any]] = None) -> None:
    """
    Initialize Streamlit session state with default values.

    Only sets values for keys that don't already exist in session state,
    preserving user modifications across reruns.

    Can optionally load configuration from cookies via ConfigSessionManager.

    Parameters
    ----------
    load_from_cookie : bool, optional
        Whether to attempt loading from cookie (default: False)
    cookie_data : Dict[str, Any], optional
        Cookie data dict {config_type: cookie_json} for loading
        (default: None)
    """
    defaults = get_session_defaults()

    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

    # Load from cookies if requested and data provided
    if load_from_cookie and cookie_data:
        _load_config_from_cookies(cookie_data)
    if "last_loaded_mode" not in st.session_state:
        st.session_state.last_loaded_mode = None

    if "last_structure_type" not in st.session_state:
        st.session_state.last_structure_type = "2D"

    if "config_changed" not in st.session_state:
        st.session_state.config_changed = False

    logger.info(f"Session state initialized with {len(defaults)} keys")


def _load_config_from_cookies(cookie_data: Dict[str, Any]) -> None:
    """
    Load configuration from cookie data.

    Parameters
    ----------
    cookie_data : Dict[str, Any]
        Cookie data dict {config_type: cookie_json}
        Example: {"2d": "{\\"config\\": {...}}", "3d": "{\\"config\\": {...}}"}
    """
    try:
        from .session.config_manager import ConfigSessionManager
    except ImportError:
        logger.warning("ConfigSessionManager not available, skipping cookie loading")
        return

    for config_type, cookie_json in cookie_data.items():
        if not cookie_json:
            continue

        try:
            manager = ConfigSessionManager(config_type=config_type)
            config = manager.init_from_cookie_or_default(cookie_json)

            # Apply config values to session state
            if hasattr(config, 'to_dict'):
                config_dict = config.to_dict()
                for key, value in config_dict.items():
                    if key in st.session_state:
                        st.session_state[key] = value
                        logger.debug(f"Loaded {config_type} config key: {key}")

            st.session_state.last_loaded_from_cookie = config_type
            logger.info(f"Loaded {config_type} configuration from cookie")

        except Exception as e:
            logger.warning(f"Failed to load {config_type} from cookie: {e}")
            continue


def reset_to_defaults(dimension: str = "all") -> None:
    """
    Reset session state to default values.

    Parameters
    ----------
    dimension : str, optional
        Which settings to reset: "2D", "3D", or "all" (default: "all")
    """
    if dimension == "2D" or dimension == "all":
        for key, value in get_2d_defaults().items():
            st.session_state[key] = value

    if dimension == "3D" or dimension == "all":
        for key, value in get_3d_defaults().items():
            st.session_state[key] = value

    if dimension == "all":
        st.session_state.template_applied_once = False
        st.session_state.uploaded_color_template = None
        st.session_state.uploaded_settings_template = None
        st.session_state.config_changed = True

    logger.info(f"Reset session state to defaults: {dimension}")


def save_current_config_to_cookie(
    dimension: Literal["2d", "3d", "protein"] = "2d"
) -> Optional[str]:
    """
    Save current session config to cookie format.

    Extracts relevant session state variables and serializes them
    for cookie storage using ConfigSessionManager.

    Parameters
    ----------
    dimension : {"2d", "3d", "protein"}, optional
        Which config type to save (default: "2d")

    Returns
    -------
    Optional[str]
        JSON string suitable for cookie, or None on error
    """
    try:
        from .session.config_manager import ConfigSessionManager
    except ImportError:
        logger.warning("ConfigSessionManager not available")
        return None

    try:
        manager = ConfigSessionManager(config_type=dimension)

        # Build config dict from session state
        if dimension in ["2d", "2D"]:
            config_dict = {key: st.session_state.get(key) for key in get_2d_defaults().keys()}
        elif dimension in ["3d", "3D"]:
            config_dict = {key: st.session_state.get(key) for key in get_3d_defaults().keys()}
        else:
            config_dict = {}

        # Create mock config object
        config_obj = type('Config', (), {'to_dict': lambda: config_dict})()

        # Serialize
        cookie_json = manager.serialize_for_cookie(config_obj, template_name="auto_saved")
        logger.info(f"Saved {dimension} config to cookie format")
        return cookie_json

    except Exception as e:
        logger.error(f"Failed to save config to cookie: {e}")
        return None


def get_config_for_rendering(dimension: Literal["2d", "3d"] = "2d") -> Dict[str, Any]:
    """
    Get rendering config from current session state.

    Extracts and returns only the relevant rendering parameters
    for the specified dimension.

    Parameters
    ----------
    dimension : {"2d", "3d"}, optional
        Which config to build (default: "2d")

    Returns
    -------
    Dict[str, Any]
        Config dictionary ready for generator initialization
    """
    if dimension == "2d":
        return {key: st.session_state.get(key) for key in get_2d_defaults().keys()}
    elif dimension == "3d":
        return {key: st.session_state.get(key) for key in get_3d_defaults().keys()}
    else:
        logger.warning(f"Unknown dimension: {dimension}")
        return {}


def mark_config_changed() -> None:
    """
    Mark that configuration has been modified.

    Useful for determining if config should be saved to cookie.
    """
    st.session_state.config_changed = True


def is_config_changed() -> bool:
    """
    Check if configuration has been modified since last save.

    Returns
    -------
    bool
        True if config has changed, False otherwise
    """
    return st.session_state.get("config_changed", False)


def clear_config_change_flag() -> None:
    """Clear the config changed flag after saving."""
    st.session_state.config_changed = False