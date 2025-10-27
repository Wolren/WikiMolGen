"""
wikimolgen.templates - Template System with Organized Settings
==============================================================

Load and manage color style templates and settings templates for molecular rendering.
Comprehensive element color organization by category and settings grouped by function.
"""

import json
from pathlib import Path
from typing import Dict, Any, Optional, Union


class TemplateError(Exception):
    """Raised when template loading or parsing fails."""
    pass


class ColorStyleTemplate:
    """
    Color style template for molecular rendering.

    Supports element colors organized by category, stick colors, and background settings.
    Element colors include: organic elements, halogens, metals (alkali, alkaline earth,
    transition), and noble gases.
    """

    def __init__(self, template_dict: Dict[str, Any]):
        """
        Initialize from template dictionary.

        Parameters
        ----------
        template_dict : dict
            Template configuration with element_colors, stick_color, bg_color, etc.
        """
        self.name = template_dict.get('name', 'Custom Template')
        self.description = template_dict.get('description', '')
        self.element_colors = template_dict.get('element_colors', {})
        self.stick_color = template_dict.get('stick_color', None)
        self.bg_color = template_dict.get('bg_color', 'white')
        self.use_bw_palette = template_dict.get('use_bw_palette', False)
        self.transparent_background = template_dict.get('transparent_background', False)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'element_colors': self.element_colors,
            'stick_color': self.stick_color,
            'bg_color': self.bg_color,
            'use_bw_palette': self.use_bw_palette,
            'transparent_background': self.transparent_background,
        }


class SettingsTemplate:
    """
    Settings template for 2D/3D rendering parameters.

    Supports all rendering configuration options organized by category:
    - Rendering: stick/sphere properties, quality settings
    - Lighting: ambient, specular, direct, reflect, shininess
    - Effects: transparency, valence, depth cue
    - Canvas: width, height, background, crop settings

    For 2D: scale, margin, bond_length, min_font_size, padding, auto_orient
    For 3D: Full rendering pipeline with all PyMOL settings
    """

    def __init__(self, template_dict: Dict[str, Any]):
        """
        Initialize from template dictionary.

        Parameters
        ----------
        template_dict : dict
            Template configuration with rendering parameters
        """
        self.name = template_dict.get('name', 'Custom Settings')
        self.description = template_dict.get('description', '')
        self.dimension = template_dict.get('dimension', '2D')  # '2D' or '3D'
        self.settings = template_dict.get('settings', {})

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            'name': self.name,
            'description': self.description,
            'dimension': self.dimension,
            'settings': self.settings,
        }


class TemplateLoader:
    """
    Template loader for color styles and settings.
    Supports JSON format with comprehensive validation and error handling.
    """

    @staticmethod
    def load_from_file(filepath: Union[str, Path]) -> Union[ColorStyleTemplate, SettingsTemplate]:
        """
        Load template from file.

        Parameters
        ----------
        filepath : str or Path
            Path to template file (JSON)

        Returns
        -------
        ColorStyleTemplate or SettingsTemplate
            Loaded template object

        Raises
        ------
        TemplateError
            If file cannot be read or parsed
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise TemplateError(f"Template file not found: {filepath}")

        # Parse JSON file
        try:
            with open(filepath, 'r') as f:
                data = json.load(f)
        except Exception as e:
            raise TemplateError(f"Failed to parse template file: {e}")

        # Determine template type
        template_type = data.get('type', 'settings')
        if template_type == 'color_style':
            return ColorStyleTemplate(data)
        elif template_type == 'settings':
            return SettingsTemplate(data)
        else:
            raise TemplateError(f"Unknown template type: {template_type}")

    @staticmethod
    def load_from_dict(template_dict: Dict[str, Any]) -> Union[ColorStyleTemplate, SettingsTemplate]:
        """
        Load template from dictionary.

        Parameters
        ----------
        template_dict : dict
            Template configuration dictionary

        Returns
        -------
        ColorStyleTemplate or SettingsTemplate
            Loaded template object
        """
        template_type = template_dict.get('type', 'settings')
        if template_type == 'color_style':
            return ColorStyleTemplate(template_dict)
        elif template_type == 'settings':
            return SettingsTemplate(template_dict)
        else:
            raise TemplateError(f"Unknown template type: {template_type}")

    @staticmethod
    def save_template(template: Union[ColorStyleTemplate, SettingsTemplate],
                      filepath: Union[str, Path]) -> None:
        """
        Save template to JSON file.

        Parameters
        ----------
        template : ColorStyleTemplate or SettingsTemplate
            Template to save
        filepath : str or Path
            Output file path
        """
        filepath = Path(filepath)
        data = template.to_dict()

        # Add type field
        if isinstance(template, ColorStyleTemplate):
            data['type'] = 'color_style'
        else:
            data['type'] = 'settings'

        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


# ===== PREDEFINED COLOR TEMPLATES =====

PREDEFINED_COLOR_TEMPLATES = {
    'cpk_standard': {
        'type': 'color_style',
        'name': 'CPK Standard',
        'description': 'Standard CPK coloring scheme for publication-quality renders',
        'element_colors': {
            # Common Organic Elements
            'C': 'gray25', 'H': 'gray85', 'N': 'blue', 'O': 'red',
            'S': 'yellow', 'P': 'orange',
            # Halogens
            'F': 'palegreen', 'Cl': 'green', 'Br': 'firebrick', 'I': 'purple',
            # Metals - Alkali & Alkaline Earth
            'Li': 'violet', 'Na': 'slate', 'K': 'violet', 'Mg': 'forest', 'Ca': 'forest',
            # Transition Metals
            'Fe': 'darkorange', 'Cu': 'chocolate', 'Zn': 'brown', 'Ni': 'forest',
            'Co': 'salmon', 'Mn': 'violet', 'Cr': 'gray50', 'Pd': 'forest',
            'Pt': 'gray50', 'Au': 'gold', 'Ag': 'gray70',
            # Other Elements
            'B': 'salmon', 'Si': 'goldenrod', 'Se': 'orange', 'As': 'violet',
            # Noble Gases
            'He': 'cyan', 'Ne': 'cyan', 'Ar': 'cyan', 'Kr': 'cyan', 'Xe': 'cyan',
        },
        'stick_color': 'gray40',
        'bg_color': 'white',
        'use_bw_palette': False,
        'transparent_background': False,
    },

    'minimal_bw': {
        'type': 'color_style',
        'name': 'Minimal Black & White',
        'description': 'Publication-ready black and white style for high contrast',
        'element_colors': {},  # Uses B/W palette
        'stick_color': None,
        'bg_color': 'white',
        'use_bw_palette': True,
        'transparent_background': True,
    },

    'dark_mode': {
        'type': 'color_style',
        'name': 'Dark Mode',
        'description': 'Dark background with bright colors for screen display',
        'element_colors': {
            'C': 'gray70', 'H': 'white', 'N': 'cyan', 'O': 'red',
            'S': 'yellow', 'P': 'orange', 'F': 'palegreen', 'Cl': 'green',
            'Br': 'firebrick', 'I': 'purple',
        },
        'stick_color': 'gray60',
        'bg_color': 'black',
        'use_bw_palette': False,
        'transparent_background': False,
    },
}

# ===== PREDEFINED SETTINGS TEMPLATES =====

PREDEFINED_SETTINGS_TEMPLATES = {
    # 2D TEMPLATES
    'publication_2d': {
        'type': 'settings',
        'name': 'Publication 2D',
        'description': 'High-quality 2D rendering for academic publications',
        'dimension': '2D',
        'settings': {
            'scale': 40.0,
            'bond_length': 50.0,
            'min_font_size': 40,
            'padding': 0.05,
            'margin': 0.8,
            'auto_orient': True,
        },
    },

    'web_optimized_2d': {
        'type': 'settings',
        'name': 'Web Optimized 2D',
        'description': 'Optimized for web display with smaller file size',
        'dimension': '2D',
        'settings': {
            'scale': 25.0,
            'bond_length': 35.0,
            'min_font_size': 28,
            'padding': 0.03,
            'margin': 0.5,
            'auto_orient': True,
        },
    },

    # 3D TEMPLATES - RENDERING
    'high_quality_3d': {
        'type': 'settings',
        'name': 'High Quality 3D',
        'description': 'Publication-quality 3D rendering with ray tracing',
        'dimension': '3D',
        'settings': {
            # Rendering
            'stick_radius': 0.18,
            'sphere_scale': 0.28,
            'stick_ball_ratio': 1.8,
            'antialias': 4,
            # Lighting
            'ambient': 0.25,
            'specular': 1.0,
            'direct': 0.5,
            'reflect': 0.5,
            'shininess': 30,
            # Effects
            'ray_trace_mode': 1,
            'ray_shadows': 1,
            'depth_cue': 0,
            # Canvas
            'width': 2000,
            'height': 1500,
            'bg_color': 'white',
            'auto_crop': True,
            'crop_margin': 10,
            'auto_orient': True,
        },
    },

    'web_preview_3d': {
        'type': 'settings',
        'name': 'Web Preview 3D',
        'description': 'Fast rendering for quick web previews',
        'dimension': '3D',
        'settings': {
            # Rendering
            'stick_radius': 0.2,
            'sphere_scale': 0.3,
            'stick_ball_ratio': 1.8,
            'antialias': 2,
            # Lighting
            'ambient': 0.3,
            'specular': 1.0,
            'direct': 0.45,
            'reflect': 0.45,
            'shininess': 30,
            # Effects
            'ray_trace_mode': 0,
            'ray_shadows': 0,
            'depth_cue': 0,
            # Canvas
            'width': 1320,
            'height': 990,
            'bg_color': 'white',
            'auto_crop': True,
            'crop_margin': 10,
            'auto_orient': True,
        },
    },

    'dramatic_3d': {
        'type': 'settings',
        'name': 'Dramatic Lighting 3D',
        'description': 'High contrast lighting for dramatic effect',
        'dimension': '3D',
        'settings': {
            # Rendering
            'stick_radius': 0.2,
            'sphere_scale': 0.3,
            'stick_ball_ratio': 1.8,
            'antialias': 3,
            # Lighting - Dramatic
            'ambient': 0.1,  # Low ambient
            'specular': 1.5,  # High specular
            'direct': 0.7,  # Strong direct light
            'reflect': 0.3,
            'shininess': 50,  # Very shiny
            # Effects
            'ray_trace_mode': 1,
            'ray_shadows': 1,
            'depth_cue': 1,
            # Canvas
            'width': 1320,
            'height': 990,
            'bg_color': 'black',
            'auto_crop': True,
            'crop_margin': 10,
            'auto_orient': True,
        },
    },

    'minimal_clean_3d': {
        'type': 'settings',
        'name': 'Minimal Clean 3D',
        'description': 'Clean, minimalist style with thin representations',
        'dimension': '3D',
        'settings': {
            # Rendering - Minimal
            'stick_radius': 0.15,
            'sphere_scale': 0.20,
            'stick_ball_ratio': 1.5,
            'antialias': 2,
            # Lighting - Bright
            'ambient': 0.4,
            'specular': 0.5,
            'direct': 0.4,
            'reflect': 0.3,
            'shininess': 20,
            # Effects
            'ray_trace_mode': 0,
            'ray_shadows': 0,
            'depth_cue': 0,
            # Canvas
            'width': 1320,
            'height': 990,
            'bg_color': 'white',
            'auto_crop': True,
            'crop_margin': 10,
            'auto_orient': True,
        },
    },
}


def get_predefined_color_template(name: str) -> ColorStyleTemplate:
    """Get a predefined color template by name."""
    if name not in PREDEFINED_COLOR_TEMPLATES:
        raise TemplateError(f"Unknown predefined color template: {name}")
    return ColorStyleTemplate(PREDEFINED_COLOR_TEMPLATES[name])


def get_predefined_settings_template(name: str) -> SettingsTemplate:
    """Get a predefined settings template by name."""
    if name not in PREDEFINED_SETTINGS_TEMPLATES:
        raise TemplateError(f"Unknown predefined settings template: {name}")
    return SettingsTemplate(PREDEFINED_SETTINGS_TEMPLATES[name])


def list_predefined_templates() -> Dict[str, list]:
    """List all predefined templates."""
    return {
        'color_templates': list(PREDEFINED_COLOR_TEMPLATES.keys()),
        'settings_templates': list(PREDEFINED_SETTINGS_TEMPLATES.keys()),
    }
