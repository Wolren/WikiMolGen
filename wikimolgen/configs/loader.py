"""
wikimolgen.configs.loader - Configuration Loader

============================================

Loads configurations from multiple sources:
- Defaults
- JSON files
- Predefined templates
- Dictionary overrides

Provides unified interface for all configuration needs.
"""

import json
from pathlib import Path
from typing import Dict, Any, Union, Optional, Literal

# Import config classes (will be created)
from dataclasses import dataclass, field, asdict


@dataclass
class ConformerConfig:
    """Configuration for RDKit 3D conformer generation."""
    use_random_coords: bool = False
    clear_confs: bool = True
    use_macrocycle_torsions: bool = False
    use_basic_knowledge: bool = True
    enforce_chirality: bool = True
    use_small_ring_torsions: bool = False
    max_iterations: int = 200
    vdw_thresh: float = 10.0
    conf_energy_threshold: float = 10.0
    num_conformers: int = 1
    prune_rms_thresh: float = 0.5


@dataclass
class RenderConfig3D:
    """Configuration for 3D molecule rendering and generation"""

    # Conformer generation
    num_conformers: int = 1
    use_random_coords: bool = False
    clear_confs: bool = True
    use_macrocycle_torsions: bool = False
    use_basic_knowledge: bool = True
    enforce_chirality: bool = True
    use_small_ring_torsions: bool = False
    max_iterations: int = 200
    vdw_thresh: float = 10.0

    # Rendering
    auto_orient_2d: bool = True
    acs_mode: bool = True
    auto_orient_3d: bool = True
    width: int = 1800
    height: int = 1400
    auto_crop: bool = True
    crop_margin: int = 10

    # Molecular representation
    stick_radius: float = 0.2
    stick_ball_ratio: float = 1.8
    stick_quality: int = 64
    sphere_scale: float = 0.3
    sphere_quality: int = 6
    stick_transparency: float = 0.0
    sphere_transparency: float = 0.0
    valence: float = 0.0

    # Ray tracing
    ray_trace_mode: int = 0
    ray_trace_gain: float = 0.0
    ray_trace_color: str = "black"
    ray_transparency_contrast: float = 1.0
    ray_transparency_oblique: float = 0.0

    # Lighting
    ambient: float = 0.25
    specular: int = 1
    shininess: int = 30
    ray_shadows: int = 0
    antialias: int = 4
    depth_cue: int = 0
    fog_start: float = 1.0
    direct: float = 0.5
    reflect: float = 0.5

    # Orientation
    zoom_buffer: float = 2.0
    x_rotation: float = 0.0
    y_rotation: float = 0.0
    z_rotation: float = 0.0
    bg_color: str = "white"

    # Colors (stored as dict - user can override)
    stick_color: Optional[str] = "gray40"


@dataclass
class Config3D:
    """Combined 3D configuration for render + conformer."""
    render: RenderConfig3D = field(default_factory=RenderConfig3D)
    conformer: ConformerConfig = field(default_factory=ConformerConfig)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to nested dictionary."""
        return {
            "render": asdict(self.render),
            "conformer": asdict(self.conformer),
        }

    def reset_to_defaults(self) -> None:
        """Reset both to defaults."""
        self.render = RenderConfig3D()
        self.conformer = ConformerConfig()


@dataclass
class Config2D:
    """Configuration for 2D molecular rendering."""
    auto_orient_2d: bool = True
    acs_mode: bool = True
    auto_orient_3d: bool = True
    angle_degrees: float = 0.0
    scale: float = 30.0
    margin: float = 0.8
    bond_length: float = 50.0
    min_font_size: int = 32
    padding: float = 0.05
    use_bw_palette: bool = True
    transparent_background: bool = True
    auto_orient_amines: bool = True
    amine_target_angle: float = 0.0
    phenethylamine_target: float = 90.0
    additional_atom_label_padding = 0.2

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def update(self, **kwargs) -> None:
        """Update configuration with validation."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown config parameter: {key}")

    def reset_to_defaults(self) -> None:
        """Reset all parameters to defaults."""
        self.auto_orient_2d = True
        self.auto_orient_3d = True
        self.angle_degrees = 180.0
        self.scale = 30.0
        self.margin = 0.5
        self.bond_length = 45.0
        self.min_font_size = 36
        self.padding = 0.03
        self.use_bw_palette = True
        self.transparent_background = True
        self.auto_orient_amines = True
        self.amine_target_angle = 90.0
        self.phenethylamine_target = 90.0
        self.additional_atom_label_padding = 0.1


@dataclass
class ConfigProtein:
    """Configuration for protein structure rendering."""
    width: int = 1920
    height: int = 1080
    bg_color: str = "black"
    auto_orient_2d: bool = True
    auto_orient_3d: bool = True
    autocrop: bool = True
    crop_margin: int = 10
    cartoon_transparency: float = 0.0
    cartoon_fancy_helices: bool = True
    cartoon_flat_sheets: bool = True
    color_scheme: str = "secondary_structure"
    helix_color: str = "#00FF00"
    sheet_color: str = "#00FFFF"
    loop_color: str = "#FFA500"
    show_ligand: bool = True
    show_water: bool = False
    ligand_style: str = "sticks"
    ligand_color: str = "element"
    ligand_single_color: str = "#FF6B6B"
    antialias: int = 2
    ray_trace: bool = False
    ambient: float = 0.4

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)

    def update(self, **kwargs) -> None:
        """Update configuration with validation."""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown config parameter: {key}")

    def reset_to_defaults(self) -> None:
        """Reset all parameters to defaults."""
        self.width = 1920
        self.height = 1080
        self.bg_color = "black"
        self.auto_orient_2d = True
        self.auto_orient_3d = True
        self.autocrop = True
        self.crop_margin = 10
        self.cartoon_transparency = 0.0
        self.cartoon_fancy_helices = True
        self.cartoon_flat_sheets = True
        self.color_scheme = "secondary_structure"
        self.helix_color = "#00FF00"
        self.sheet_color = "#00FFFF"
        self.loop_color = "#FFA500"
        self.show_ligand = True
        self.show_water = False
        self.ligand_style = "sticks"
        self.ligand_color = "element"
        self.ligand_single_color = "#FF6B6B"
        self.antialias = 2
        self.ray_trace = False
        self.ambient = 0.4


class ConfigLoader:
    """
    Unified configuration loader for all rendering modes.
    
    Supports:
    - Loading from JSON templates
    - Loading from files
    - Merging partial configurations
    - Type validation
    
    Examples:
        # Get defaults
        cfg_2d = ConfigLoader.get_2d_config()
        cfg_3d = ConfigLoader.get_3d_config()
        cfg_protein = ConfigLoader.get_protein_config()
        
        # Load from template
        cfg = ConfigLoader.load_template("publication_2d")
        
        # Load and override
        cfg = ConfigLoader.load_from_file("config.json")
        cfg.update(scale=50.0, margin=0.8)
    """
    
    # Predefined template directory (relative to this file)
    TEMPLATE_DIR = Path(__file__).parent / "templates"
    
    @staticmethod
    def get_2d_config(overrides: Optional[Dict[str, Any]] = None) -> Config2D:
        """
        Get 2D configuration with optional overrides.
        
        Parameters
        ----------
        overrides : dict, optional
            Override defaults with these values
            
        Returns
        -------
        Config2D
            2D configuration object
        """
        cfg = Config2D()
        if overrides:
            cfg.update(**overrides)
        return cfg

    @staticmethod
    def get_3d_config(overrides: Optional[Dict[str, Any]] = None) -> Config3D:
        """
        Get 3D configuration with optional overrides.

        Parameters
        ----------
        overrides : dict, optional
            Override defaults with these values.
            Use "render_*" prefix for render settings,
            "conformer_*" prefix for conformer settings.

        Returns
        -------
        Config3D
            3D configuration object
        """
        cfg = Config3D()

        if overrides:
            render_overrides = {}
            conformer_overrides = {}

            for key, value in overrides.items():
                if key.startswith("render_"):
                    render_overrides[key[7:]] = value
                elif key.startswith("conformer_"):
                    conformer_overrides[key[10:]] = value

            if render_overrides:
                for k, v in render_overrides.items():
                    if hasattr(cfg.render, k):
                        setattr(cfg.render, k, v)

            if conformer_overrides:
                for k, v in conformer_overrides.items():
                    if hasattr(cfg.conformer, k):
                        setattr(cfg.conformer, k, v)

        return cfg
    
    @staticmethod
    def get_protein_config(overrides: Optional[Dict[str, Any]] = None) -> ConfigProtein:
        """
        Get Protein configuration with optional overrides.
        
        Parameters
        ----------
        overrides : dict, optional
            Override defaults with these values
            
        Returns
        -------
        ConfigProtein
            Protein configuration object
        """
        cfg = ConfigProtein()
        if overrides:
            cfg.update(**overrides)
        return cfg
    
    @staticmethod
    def load_from_file(filepath: Union[str, Path]) -> Union[Config2D, Config3D, ConfigProtein]:
        """
        Load configuration from JSON file.
        
        The JSON file should have a "type" field indicating 2d, 3d, or protein.
        
        Parameters
        ----------
        filepath : str or Path
            Path to JSON configuration file
            
        Returns
        -------
        Config2D, Config3D, or ConfigProtein
            Loaded configuration object
            
        Raises
        ------
        FileNotFoundError
            If file doesn't exist
        ValueError
            If JSON format is invalid or type not specified
        """
        filepath = Path(filepath)
        
        if not filepath.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")
        
        with open(filepath, 'r') as f:
            data = json.load(f)
        
        config_type = data.get("type", "").lower()
        
        if config_type == "2d":
            return ConfigLoader.get_2d_config(overrides=data.get("settings", {}))
        elif config_type == "3d":
            return ConfigLoader.get_3d_config(overrides=data.get("settings", {}))
        elif config_type == "protein":
            return ConfigLoader.get_protein_config(overrides=data.get("settings", {}))
        else:
            raise ValueError(f"Unknown config type: {config_type}. Expected 2d, 3d, or protein.")
    
    @staticmethod
    def load_template(template_name: str) -> Union[Config2D, Config3D, ConfigProtein]:
        """
        Load a predefined template.
        
        Predefined templates:
        - 2D: publication_2d, web_optimized_2d
        - 3D: high_quality_3d, web_preview_3d, dramatic_3d, minimal_clean_3d
        - Protein: default_protein, high_quality_protein
        
        Parameters
        ----------
        template_name : str
            Name of the template
            
        Returns
        -------
        Config2D, Config3D, or ConfigProtein
            Loaded template configuration
            
        Raises
        ------
        FileNotFoundError
            If template doesn't exist
        """
        # Try to load from templates directory
        template_file = ConfigLoader.TEMPLATE_DIR / f"{template_name}.json"
        
        if template_file.exists():
            return ConfigLoader.load_from_file(template_file)
        
        # Fallback to built-in templates
        try:
            return _load_builtin_template(template_name)
        except KeyError:
            raise FileNotFoundError(
                f"Template not found: {template_name}\n"
                f"Available templates in {ConfigLoader.TEMPLATE_DIR.resolve()}"
            )
    
    @staticmethod
    def save_config(
        config: Union[Config2D, Config3D, ConfigProtein],
        filepath: Union[str, Path],
    ) -> None:
        """
        Save configuration to JSON file.
        
        Parameters
        ----------
        config : Config2D, Config3D, or ConfigProtein
            Configuration to save
        filepath : str or Path
            Output file path
        """
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        
        # Determine type
        if isinstance(config, Config2D):
            config_type = "2d"
        elif isinstance(config, Config3D):
            config_type = "3d"
        elif isinstance(config, ConfigProtein):
            config_type = "protein"
        else:
            raise TypeError(f"Unknown config type: {type(config)}")
        
        data = {
            "type": config_type,
            "settings": config.to_dict(),
        }
        
        with open(filepath, 'w') as f:
            json.dump(data, f, indent=2)


def _load_builtin_template(name: str) -> Union[Config2D, Config3D, ConfigProtein]:
    """Load built-in templates (fallback)."""
    
    builtin_templates = {
        # 2D templates
        "publication_2d": {
            "type": "2d",
            "settings": {
                "scale": 40.0,
                "bond_length": 50.0,
                "min_font_size": 40,
                "padding": 0.05,
                "margin": 0.8,
                "auto_orient_2d": False,
                "auto_orient_3d": False,
            }
        },
        "web_optimized_2d": {
            "type": "2d",
            "settings": {
                "scale": 25.0,
                "bond_length": 35.0,
                "min_font_size": 28,
                "padding": 0.03,
                "margin": 0.5,
                "auto_orient_2d": False,
                "auto_orient_3d": False,
            }
        },
        # 3D templates
        "high_quality_3d": {
            "type": "3d",
            "settings": {
                "render_stick_radius": 0.18,
                "render_sphere_scale": 0.28,
                "render_antialias": 4,
                "render_ray_trace_mode": 1,
                "render_ray_shadows": 1,
            }
        },
        "web_preview_3d": {
            "type": "3d",
            "settings": {
                "render_stick_radius": 0.2,
                "render_sphere_scale": 0.3,
                "render_antialias": 2,
                "render_ray_trace_mode": 0,
            }
        },
        # Protein templates
        "default_protein": {
            "type": "protein",
            "settings": {
                "width": 1920,
                "height": 1080,
                "bg_color": "black",
            }
        },
    }
    
    if name not in builtin_templates:
        raise KeyError(f"No builtin template: {name}")
    
    template = builtin_templates[name]
    config_type = template["type"]
    
    if config_type == "2d":
        return ConfigLoader.get_2d_config(overrides=template.get("settings", {}))
    elif config_type == "3d":
        return ConfigLoader.get_3d_config(overrides=template.get("settings", {}))
    elif config_type == "protein":
        return ConfigLoader.get_protein_config(overrides=template.get("settings", {}))
    else:
        raise ValueError(f"Unknown template type: {config_type}")
