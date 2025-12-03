"""
wikimolgen.configs - Centralized Configuration System

=====================================================

Unified configuration management for 2D, 3D, and Protein rendering.
Single source of truth for all default settings.

Usage:
    from wikimolgen.configs import ConfigLoader, get_2d_config, get_3d_config
    
    # Get default configs
    cfg_2d = get_2d_config()
    cfg_3d = get_3d_config()
    
    # Or use ConfigLoader directly
    from wikimolgen.configs import ConfigLoader
    cfg = ConfigLoader.load_template("publication_2d")
    cfg = ConfigLoader.load_from_file("custom_config.json")
"""

from .loader import ConfigLoader, Config2D, Config3D

__all__ = [
    # Defaults (immutable)
    # Loader
    "ConfigLoader",
    "Config2D",
    "Config3D"
]


def get_2d_config(overrides=None):
    """Convenience function: get 2D config with optional overrides."""
    return ConfigLoader.get_2d_config(overrides)


def get_3d_config(overrides=None):
    """Convenience function: get 3D config with optional overrides."""
    return ConfigLoader.get_3d_config(overrides)


def get_protein_config(overrides=None):
    """Convenience function: get protein config with optional overrides."""
    return ConfigLoader.get_protein_config(overrides)