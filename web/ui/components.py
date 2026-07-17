"""
web/ui/components.py
=====================
Re-export hub for all UI components.
Sub-modules: components_shared, components_core, components_2d, components_3d.
"""

from ui.components_shared import (
    _validate_atom_scheme,
    _sync_slider_to_config,
    _sync_input_to_slider,
    _sync_number_input,
    _s,
    _cb,
    _ni,
    _sb,
    _s2,
    _s3,
    _cb2,
    _cb3,
    _ni3,
    _sb3,
    save_config_to_session,
)

from ui.components_core import (
    render_compound_input,
    render_preset_manager,
    _apply_preset_now,
    _on_mode_change,
    render_mode_selector,
    render_rotation_settings,
    render_generate_button,
)

from ui.components_2d import (
    render_2d_settings,
)

from ui.components_3d import (
    render_canvas_settings,
    render_rendering_settings,
    render_color_palette,
    render_lighting_settings,
    render_effects_settings,
    render_conformer_settings,
)

__all__ = [
    "_validate_atom_scheme",
    "_sync_slider_to_config",
    "_sync_input_to_slider",
    "_sync_number_input",
    "_s", "_cb", "_ni", "_sb",
    "_s2", "_s3", "_cb2", "_cb3", "_ni3", "_sb3",
    "save_config_to_session",
    "render_compound_input",
    "render_preset_manager",
    "_apply_preset_now",
    "_on_mode_change",
    "render_mode_selector",
    "render_rotation_settings",
    "render_generate_button",
    "render_2d_settings",
    "render_canvas_settings",
    "render_rendering_settings",
    "render_color_palette",
    "render_lighting_settings",
    "render_effects_settings",
    "render_conformer_settings",
]
