import json
from dataclasses import asdict, dataclass, field, fields
from pathlib import Path
from typing import Any


@dataclass
class ColorConfig:
    element_colors: dict[str, str] = field(default_factory=dict)
    stick_color: str | None = None
    bg_color: str = "white"


@dataclass
class ConformerConfig:
    use_random_coords: bool = False
    clear_confs: bool = True
    use_macrocycle_torsions: bool = False
    use_basic_knowledge: bool = True
    enforce_chirality: bool = True
    use_small_ring_torsions: bool = True
    max_iterations: int = 500
    num_conformers: int = 50
    prune_rms_thresh: float = 0.1
    use_exp_torsion_prefs: bool = True


@dataclass
class RenderConfig3D:
    auto_orient_3d: bool = False
    width: int = 1800
    height: int = 1600
    auto_crop: bool = True
    crop_margin: int = 10
    stick_radius: float = 0.2
    stick_ball_ratio: float = 1.8
    stick_quality: int = 64
    sphere_scale: float = 0.3
    sphere_quality: int = 6
    stick_transparency: float = 0.0
    sphere_transparency: float = 0.0
    valence: float = 0.0
    ray_trace_mode: int = 0
    ray_trace_gain: float = 0.0
    ray_trace_color: str = "black"
    ray_transparency_contrast: float = 1.0
    ray_transparency_oblique: float = 0.0
    ambient: float = 0.25
    specular: float = 1.0
    shininess: int = 30
    ray_shadows: int = 0
    antialias: int = 4
    depth_cue: int = 0
    fog_start: float = 1.0
    direct: float = 0.45
    reflect: float = 0.45
    auto_orient_tilt_x: float = 10.0
    auto_orient_tilt_y: float = 20.0
    zoom_buffer: float = 2.0
    x_rotation: float = 0.0
    y_rotation: float = 0.0
    z_rotation: float = 0.0
    bg_color: str = "white"
    stick_color: str | None = "gray50"
    element_colors: dict[str, str] | None = None
    representation: str = "sticks+spheres"
    two_sided_lighting: bool = True
    transparency_mode: int = 1
    ambient_occlusion: bool = False
    ambient_occlusion_scale: float = 20.0
    ambient_occlusion_mode: int = 1
    apply_element_colors: bool = True
    ray_trace_fog: float = 0.0
    ray_width: int | None = None
    ray_height: int | None = None
    opaque_background: bool = False
    stick_ball: bool = True
    zoom_buffer_linear: float = 1.5
    zoom_buffer_elongated: float = 2.0
    zoom_buffer_compact: float = 2.5
    pymol_view: list[float] | None = None


@dataclass
class Config3D:
    render: RenderConfig3D = field(default_factory=RenderConfig3D)
    conformer: ConformerConfig = field(default_factory=ConformerConfig)

    def to_dict(self) -> dict[str, Any]:
        return {"render": asdict(self.render), "conformer": asdict(self.conformer)}

    def reset_to_defaults(self) -> None:
        self.render = RenderConfig3D()
        self.conformer = ConformerConfig()


_RENDER_FIELDS = {f.name for f in fields(RenderConfig3D)}
_CONFORMER_FIELDS = {f.name for f in fields(ConformerConfig)}


@dataclass
class Config2D:
    auto_orient_2d: bool = False
    acs_mode: bool = True
    angle_degrees: float = 0.0
    scale: float = 30.0
    margin: float = 0.8
    bond_length: float = 50.0
    min_font_size: int = 32
    padding: float = 0.07
    use_bw_palette: bool = True
    transparent_background: bool = True
    auto_orient_amines: bool = True
    amine_target_angle: float = 0.0
    phenethylamine_target: float = 90.0
    additional_atom_label_padding: float = 0.1
    bond_line_width: float = 1.0
    add_stereo_annotation: bool = False
    include_radicals: bool = False
    explicit_methyl: bool = False
    scaling_factor: float = 1.0
    no_atom_labels: bool = False
    multiple_bond_offset: float = 0.15
    include_atom_tags: bool = False
    include_chiral_flag: bool = False
    comic_mode: bool = False
    fixed_font_size: int = -1
    strip_annotation_markers: bool = True
    use_coord_gen: bool = False
    legend_font_size: int = 12
    max_font_size: int = 40
    dots_per_angstrom: int = 100
    font_size_scale: float = 1.0
    svg_min_display_size: int = 600
    legend: str = ""
    highlight_atoms: str = ""
    highlight_bonds: str = ""
    highlight_color: str = "#FF8888"

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def update(self, **kwargs) -> None:
        valid = {f.name for f in fields(self)}
        for key, value in kwargs.items():
            if key in valid:
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown config parameter: {key}")

    def reset_to_defaults(self) -> None:
        for key, value in asdict(type(self)()).items():
            setattr(self, key, value)


# ── Protein Config (single source of truth for all protein keys) ──────────


@dataclass
class ProteinConfig:
    """Single source of truth for all protein rendering settings."""

    # Color scheme
    protein_color_scheme: str = "Chain"
    helix_color: str = "#3399FF"
    sheet_color: str = "#FFCC00"
    loop_color: str = "#99AABB"
    # Cartoon
    cartoon_transparency: float = 0.0
    cartoon_fancy: bool = True
    cartoon_sheets: bool = True
    # Ligand
    show_ligand: bool = False
    show_water: bool = False
    ligand_style: str = "sticks"
    ligand_transparency: float = 0.0
    ligand_color: str = "element"
    ligand_single_color: str = "#FF6B6B"
    ligand_stick_radius: float = 0.25
    ligand_stick_quality: int = 10
    ligand_ball_ratio: float = 1.5
    protein_bindsites: bool = True
    protein_bind_radius: float = 5.0
    protein_bind_color: str = "yellow"
    protein_res_labels: bool = False
    protein_label_size: int = 14
    # Canvas
    protein_width: int = 1920
    protein_height: int = 1080
    protein_antialias: int = 2
    protein_specular: int = 1
    protein_ambient: float = 0.40
    protein_bg: str = "black"
    protein_shininess: int = 10
    protein_ray_shadows: bool = False
    protein_ray_trace: bool = False
    protein_auto_rot: bool = True
    protein_autocrop: bool = True
    protein_crop_margin: int = 10
    # Effects
    protein_direct: float = 0.45
    protein_reflect: float = 0.45
    protein_depth_cue: bool = False
    protein_orthoscopic: bool = False
    protein_ray_opaque: bool = False
    protein_zoom_buffer: float = 2.0

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    def update(self, **kwargs) -> None:
        valid = {f.name for f in fields(self)}
        for key, value in kwargs.items():
            if key in valid:
                setattr(self, key, value)
            else:
                raise ValueError(f"Unknown protein config parameter: {key}")

    def reset_to_defaults(self) -> None:
        for key, value in asdict(type(self)()).items():
            setattr(self, key, value)


_BUILTIN_TEMPLATES = {
    "publication_2d": {
        "type": "2d",
        "settings": {
            "scale": 40.0,
            "bond_length": 50.0,
            "min_font_size": 40,
            "padding": 0.05,
            "margin": 0.8,
            "auto_orient_2d": False,
        },
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
        },
    },
    "high_quality_3d": {
        "type": "3d",
        "settings": {
            "render_stick_radius": 0.18,
            "render_sphere_scale": 0.28,
            "render_antialias": 4,
            "render_ray_trace_mode": 1,
            "render_ray_shadows": 1,
        },
    },
    "web_preview_3d": {
        "type": "3d",
        "settings": {
            "render_stick_radius": 0.2,
            "render_sphere_scale": 0.3,
            "render_antialias": 2,
            "render_ray_trace_mode": 0,
        },
    },
    "dramatic_3d": {
        "type": "3d",
        "settings": {
            "render_stick_radius": 0.2,
            "render_sphere_scale": 0.3,
            "render_antialias": 3,
            "render_ambient": 0.1,
            "render_specular": 1.5,
            "render_direct": 0.7,
            "render_reflect": 0.3,
            "render_shininess": 50,
            "render_ray_trace_mode": 1,
            "render_ray_shadows": 1,
            "render_depth_cue": 1,
            "render_bg_color": "black",
        },
    },
    "minimal_clean_3d": {
        "type": "3d",
        "settings": {
            "render_stick_radius": 0.15,
            "render_sphere_scale": 0.20,
            "render_stick_ball_ratio": 1.5,
            "render_antialias": 2,
            "render_ambient": 0.4,
            "render_specular": 0.5,
            "render_direct": 0.4,
            "render_reflect": 0.3,
            "render_shininess": 20,
            "render_ray_trace_mode": 0,
            "render_ray_shadows": 0,
            "render_depth_cue": 0,
        },
    },
}

# Single source of truth for CPK-style element → color mappings.
# Used by both 3D rendering and color template loading.
DEFAULT_ELEMENT_COLORS: dict[str, str] = {
    # Period 1
    "H": "gray85",
    "D": "#FFFFCC",
    "T": "#FFFFCC",
    "He": "cyan",
    # Period 2
    "Li": "violet",
    "Be": "#228B22",
    "B": "salmon",
    "C": "gray35",
    "N": "blue",
    "O": "red",
    "F": "palegreen",
    "Ne": "cyan",
    # Period 3
    "Na": "slate",
    "Mg": "forest",
    "Al": "#808080",
    "Si": "goldenrod",
    "P": "orange",
    "S": "yellow",
    "Cl": "green",
    "Ar": "cyan",
    # Period 4
    "K": "violet",
    "Ca": "forest",
    "Sc": "#E8C8A0",
    "Ti": "gray",
    "V": "#E8C8A0",
    "Cr": "gray50",
    "Mn": "violet",
    "Fe": "darkorange",
    "Co": "salmon",
    "Ni": "forest",
    "Cu": "chocolate",
    "Zn": "brown",
    "Ga": "#E8C8A0",
    "Ge": "#E8C8A0",
    "As": "violet",
    "Se": "orange",
    "Br": "firebrick",
    "Kr": "cyan",
    # Period 5
    "Rb": "violet",
    "Sr": "#228B22",
    "Y": "#E8C8A0",
    "Zr": "#E8C8A0",
    "Nb": "#E8C8A0",
    "Mo": "#E8C8A0",
    "Tc": "#E8C8A0",
    "Ru": "#E8C8A0",
    "Rh": "#E8C8A0",
    "Pd": "forest",
    "Ag": "gray70",
    "Cd": "#E8C8A0",
    "In": "#E8C8A0",
    "Sn": "#E8C8A0",
    "Sb": "#E8C8A0",
    "Te": "#E8C8A0",
    "I": "purple",
    "Xe": "cyan",
    # Period 6
    "Cs": "violet",
    "Ba": "#228B22",
    "La": "#E8C8A0",
    "Ce": "#E8C8A0",
    "Pr": "#E8C8A0",
    "Nd": "#E8C8A0",
    "Pm": "#E8C8A0",
    "Sm": "#E8C8A0",
    "Eu": "#E8C8A0",
    "Gd": "#E8C8A0",
    "Tb": "#E8C8A0",
    "Dy": "#E8C8A0",
    "Ho": "#E8C8A0",
    "Er": "#E8C8A0",
    "Tm": "#E8C8A0",
    "Yb": "#E8C8A0",
    "Lu": "#E8C8A0",
    "Hf": "#E8C8A0",
    "Ta": "#E8C8A0",
    "W": "#E8C8A0",
    "Re": "#E8C8A0",
    "Os": "#E8C8A0",
    "Ir": "#E8C8A0",
    "Pt": "gray50",
    "Au": "gold",
    "Hg": "#E8C8A0",
    "Tl": "#E8C8A0",
    "Pb": "#E8C8A0",
    "Bi": "#E8C8A0",
    "Po": "#E8C8A0",
    "At": "#E8C8A0",
    "Rn": "cyan",
    # Period 7
    "Fr": "violet",
    "Ra": "#228B22",
    "Ac": "#E8C8A0",
    "Th": "#E8C8A0",
    "Pa": "#E8C8A0",
    "U": "#E8C8A0",
    "Np": "#E8C8A0",
    "Pu": "#E8C8A0",
    "Am": "#E8C8A0",
    "Cm": "#E8C8A0",
    "Bk": "#E8C8A0",
    "Cf": "#E8C8A0",
    "Es": "#E8C8A0",
    "Fm": "#E8C8A0",
    "Md": "#E8C8A0",
    "No": "#E8C8A0",
    "Lr": "#E8C8A0",
    "Rf": "#E8C8A0",
    "Db": "#E8C8A0",
    "Sg": "#E8C8A0",
    "Bh": "#E8C8A0",
    "Hs": "#E8C8A0",
    "Mt": "#E8C8A0",
    "Ds": "#E8C8A0",
    "Rg": "#E8C8A0",
    "Cn": "#E8C8A0",
    "Nh": "#E8C8A0",
    "Fl": "#E8C8A0",
    "Mc": "#E8C8A0",
    "Lv": "#E8C8A0",
    "Ts": "#E8C8A0",
    "Og": "cyan",
}

BUILTIN_COLOR_TEMPLATES: dict[str, dict[str, Any]] = {
    "cpk_standard": {
        "element_colors": dict(DEFAULT_ELEMENT_COLORS),
        "stick_color": "gray50",
        "bg_color": "white",
    },
    "minimal_bw": {
        "element_colors": {},
        "stick_color": None,
        "bg_color": "white",
    },
    "jmol": {
        "element_colors": dict(
            DEFAULT_ELEMENT_COLORS,
            **{
                "C": "gray40",
                "H": "white",
                "N": "skyblue",
                "O": "red",
                "S": "yellow",
                "P": "orange",
                "F": "palegreen",
                "Cl": "green",
                "Br": "firebrick",
                "I": "purple",
                "Li": "violet",
                "Na": "slate",
                "K": "violet",
                "Mg": "forest",
                "Ca": "forest",
                "Fe": "darkorange",
                "Cu": "chocolate",
                "Zn": "brown",
                "Ni": "forest",
                "Co": "salmon",
                "Mn": "violet",
                "Cr": "gray50",
                "Pd": "forest",
                "Pt": "gray50",
                "Au": "gold",
                "Ag": "gray70",
                "B": "salmon",
                "Si": "goldenrod",
                "Se": "orange",
                "As": "violet",
                "He": "cyan",
                "Ne": "cyan",
                "Ar": "cyan",
                "Kr": "cyan",
                "Xe": "cyan",
            },
        ),
        "stick_color": "gray50",
        "bg_color": "white",
    },
    "rasmol": {
        "element_colors": dict(
            DEFAULT_ELEMENT_COLORS,
            **{
                "C": "gray30",
                "H": "white",
                "N": "lightblue",
                "O": "red",
                "S": "yellow",
                "P": "orange",
                "F": "green",
                "Cl": "green",
                "Br": "firebrick",
                "I": "purple",
                "Li": "violet",
                "Na": "slate",
                "K": "violet",
                "Mg": "forest",
                "Ca": "forest",
                "Fe": "salmon",
                "Cu": "chocolate",
                "Zn": "brown",
                "Ni": "forest",
                "Co": "salmon",
                "Mn": "violet",
                "Cr": "gray50",
                "Pd": "forest",
                "Pt": "gray50",
                "Au": "gold",
                "Ag": "gray70",
                "B": "salmon",
                "Si": "goldenrod",
                "Se": "orange",
                "As": "violet",
            },
        ),
        "stick_color": "gray40",
        "bg_color": "white",
    },
    "chemdraw": {
        "element_colors": dict(
            DEFAULT_ELEMENT_COLORS,
            **{
                "C": "black",
                "H": "white",
                "N": "blue",
                "O": "red",
                "S": "yellow",
                "P": "orange",
                "F": "green",
                "Cl": "green",
                "Br": "firebrick",
                "I": "purple",
                "B": "salmon",
                "Si": "goldenrod",
                "Se": "orange",
                "As": "violet",
            },
        ),
        "stick_color": "black",
        "bg_color": "white",
    },
    "vmd": {
        "element_colors": dict(
            DEFAULT_ELEMENT_COLORS,
            **{
                "C": "cyan",
                "H": "white",
                "N": "blue",
                "O": "red",
                "S": "yellow",
                "P": "tan",
                "F": "palegreen",
                "Cl": "green",
                "Br": "firebrick",
                "I": "purple",
                "Fe": "darkorange",
                "Cu": "chocolate",
                "Zn": "brown",
                "Mg": "forest",
                "Ca": "forest",
                "Na": "slate",
                "K": "violet",
            },
        ),
        "stick_color": "gray50",
        "bg_color": "black",
    },
}

COLOR_TEMPLATE_META: dict[str, dict[str, str]] = {
    "cpk_standard": {
        "name": "CPK Standard",
        "desc": "Traditional Corey-Pauling-Koltun coloring, the classic chemical convention",
    },
    "minimal_bw": {
        "name": "Minimal B/W",
        "desc": "Black-and-white only, no element-specific colors",
    },
    "jmol": {
        "name": "Jmol Default",
        "desc": "Jmol molecular viewer default color scheme — lighter nitrogen, darker carbon",
    },
    "rasmol": {
        "name": "RasMol",
        "desc": "RasMol / Chime default colors — light blue nitrogen, darker carbons",
    },
    "chemdraw": {
        "name": "ChemDraw Style",
        "desc": "ChemDraw-style rendering — black carbons for high contrast",
    },
    "vmd": {
        "name": "VMD Default",
        "desc": "VMD molecular viewer scheme — cyan carbons, tan phosphorus",
    },
}


class _TemplateSerializer:
    @staticmethod
    def template_to_dict(
        config: Config2D | Config3D | ProteinConfig, name: str = "custom"
    ) -> dict[str, Any]:
        if isinstance(config, Config2D):
            return {"type": "2d", "name": name, "settings": config.to_dict()}
        elif isinstance(config, Config3D):
            return {"type": "3d", "name": name, "settings": config.to_dict()}
        elif isinstance(config, ProteinConfig):
            return {"type": "protein", "name": name, "settings": config.to_dict()}
        raise TypeError(f"Unknown config type: {type(config)}")

    @staticmethod
    def dict_to_config(data: dict[str, Any]) -> Config2D | Config3D | ProteinConfig:
        config_type = data.get("type", "").lower()
        overrides = data.get("settings", {})
        if config_type == "2d":
            return ConfigLoader.get_2d_config(overrides=overrides)
        elif config_type == "3d":
            return ConfigLoader.get_3d_config(overrides=overrides)
        elif config_type == "protein":
            return ConfigLoader.get_protein_config(overrides=overrides)
        raise ValueError(f"Unknown config type: {config_type}")


class ConfigLoader:
    @staticmethod
    def get_2d_config(overrides: dict[str, Any] | None = None) -> Config2D:
        cfg = Config2D()
        if overrides:
            cfg.update(**overrides)
        return cfg

    @staticmethod
    def get_3d_config(overrides: dict[str, Any] | None = None) -> Config3D:
        cfg = Config3D()
        if overrides:
            render_overrides = {}
            conformer_overrides = {}
            for key, value in overrides.items():
                if key == "render" and isinstance(value, dict):
                    render_overrides.update(value)
                elif key == "conformer" and isinstance(value, dict):
                    conformer_overrides.update(value)
                elif key.startswith("render_"):
                    render_overrides[key[7:]] = value
                elif key.startswith("conformer_"):
                    conformer_overrides[key[10:]] = value
                elif key in _RENDER_FIELDS:
                    render_overrides[key] = value
                elif key in _CONFORMER_FIELDS:
                    conformer_overrides[key] = value
            if render_overrides:
                for k, v in render_overrides.items():
                    setattr(cfg.render, k, v)
            if conformer_overrides:
                for k, v in conformer_overrides.items():
                    setattr(cfg.conformer, k, v)
        return cfg

    @staticmethod
    def get_protein_config(overrides: dict[str, Any] | None = None) -> ProteinConfig:
        cfg = ProteinConfig()
        if overrides:
            cfg.update(**overrides)
        return cfg

    @staticmethod
    def load_template(template_name: str) -> Config2D | Config3D:
        if template_name in _BUILTIN_TEMPLATES:
            return _load_builtin_template(template_name)
        raise ValueError(
            f"Unknown template: {template_name}. Available: {list(_BUILTIN_TEMPLATES.keys())}"
        )

    @staticmethod
    def load_color_template(template_name: str) -> ColorConfig:
        if template_name in BUILTIN_COLOR_TEMPLATES:
            data = BUILTIN_COLOR_TEMPLATES[template_name]
            return ColorConfig(**data)
        raise ValueError(
            f"Unknown color template: {template_name}. "
            f"Available: {list(BUILTIN_COLOR_TEMPLATES.keys())}"
        )

    @staticmethod
    def list_templates() -> dict[str, Any]:
        return {
            "settings_templates": list(_BUILTIN_TEMPLATES.keys()),
            "color_templates": list(BUILTIN_COLOR_TEMPLATES.keys()),
        }

    @staticmethod
    def load_from_file(filepath: str | Path) -> Config2D | Config3D | ProteinConfig:
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"Config file not found: {filepath}")
        with open(filepath, encoding="utf-8") as f:
            data = json.load(f)
        return _TemplateSerializer.dict_to_config(data)

    @staticmethod
    def save_config(
        config: Config2D | Config3D,
        filepath: str | Path,
    ) -> None:
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        data = _TemplateSerializer.template_to_dict(config)
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    @staticmethod
    def export_default_template(
        name: str,
        filepath: str | Path,
    ) -> None:
        config = ConfigLoader.load_template(name)
        ConfigLoader.save_config(config, filepath)


def _load_builtin_template(name: str) -> Config2D | Config3D:
    if name not in _BUILTIN_TEMPLATES:
        raise KeyError(f"No builtin template: {name}")
    template = _BUILTIN_TEMPLATES[name]
    config_type = template["type"]
    if config_type == "2d":
        return ConfigLoader.get_2d_config(overrides=template.get("settings", {}))
    elif config_type == "3d":
        return ConfigLoader.get_3d_config(overrides=template.get("settings", {}))
    raise ValueError(f"Unknown template type: {config_type}")
