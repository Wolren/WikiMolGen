import json
import tempfile
from pathlib import Path

import pytest

from wikimolgen.configs.loader import (
    ColorConfig,
    Config2D,
    Config3D,
    ConformerConfig,
    ConfigLoader,
    ProteinConfig,
    RenderConfig3D,
)


class TestColorConfig:
    def test_default_values(self):
        cfg = ColorConfig()
        assert cfg.element_colors == {}
        assert cfg.stick_color is None
        assert cfg.bg_color == "white"

    def test_field_types(self):
        cfg = ColorConfig()
        assert isinstance(cfg.element_colors, dict)
        assert cfg.stick_color is None or isinstance(cfg.stick_color, str)
        assert isinstance(cfg.bg_color, str)

    def test_custom_values(self):
        cfg = ColorConfig(
            element_colors={"C": "black"},
            stick_color="gray40",
            bg_color="black",
        )
        assert cfg.element_colors == {"C": "black"}
        assert cfg.stick_color == "gray40"
        assert cfg.bg_color == "black"


class TestConfig2D:
    def test_default_values(self):
        cfg = Config2D()
        assert cfg.auto_orient_2d is False
        assert cfg.acs_mode is True
        assert cfg.angle_degrees == 0.0
        assert cfg.scale == 30.0
        assert cfg.margin == 0.8
        assert cfg.bond_length == 50.0
        assert cfg.min_font_size == 32
        assert cfg.padding == 0.07
        assert cfg.use_bw_palette is True
        assert cfg.transparent_background is True
        assert cfg.auto_orient_amines is True
        assert cfg.amine_target_angle == 0.0
        assert cfg.phenethylamine_target == 90.0
        assert cfg.additional_atom_label_padding == 0.1
        assert cfg.bond_line_width == 1.0
        assert cfg.add_stereo_annotation is False
        assert cfg.include_radicals is False
        assert cfg.explicit_methyl is False
        assert cfg.scaling_factor == 1.0
        assert cfg.no_atom_labels is False
        assert cfg.multiple_bond_offset == 0.15
        assert cfg.include_atom_tags is False
        assert cfg.include_chiral_flag is False
        assert cfg.comic_mode is False
        assert cfg.fixed_font_size == -1
        assert cfg.strip_annotation_markers is True
        assert cfg.use_coord_gen is False
        assert cfg.legend_font_size == 12
        assert cfg.max_font_size == 40
        assert cfg.dots_per_angstrom == 100
        assert cfg.font_size_scale == 1.0

    def test_update_method(self):
        cfg = Config2D()
        cfg.update(scale=50.0, bond_length=60.0)
        assert cfg.scale == 50.0
        assert cfg.bond_length == 60.0
        assert cfg.margin == 0.8

    def test_update_unknown_field(self):
        cfg = Config2D()
        with pytest.raises(ValueError, match="Unknown config parameter"):
            cfg.update(nonexistent=42)

    def test_reset_to_defaults(self):
        cfg = Config2D()
        cfg.update(scale=99.0, margin=99.0)
        cfg.reset_to_defaults()
        assert cfg.scale == 30.0
        assert cfg.margin == 0.8

    def test_to_dict(self):
        cfg = Config2D()
        d = cfg.to_dict()
        assert isinstance(d, dict)
        assert d["scale"] == 30.0
        assert d["bond_length"] == 50.0


class TestRenderConfig3D:
    def test_default_values(self):
        cfg = RenderConfig3D()
        assert cfg.auto_orient_3d is False
        assert cfg.width == 1800
        assert cfg.height == 1600
        assert cfg.auto_crop is True
        assert cfg.crop_margin == 10
        assert cfg.stick_radius == 0.2
        assert cfg.stick_ball_ratio == 1.8
        assert cfg.stick_quality == 64
        assert cfg.sphere_scale == 0.3
        assert cfg.sphere_quality == 6
        assert cfg.stick_transparency == 0.0
        assert cfg.sphere_transparency == 0.0
        assert cfg.valence == 0.0
        assert cfg.ray_trace_mode == 0
        assert cfg.ray_trace_gain == 0.0
        assert cfg.ray_trace_color == "black"
        assert cfg.ray_transparency_contrast == 1.0
        assert cfg.ray_transparency_oblique == 0.0
        assert cfg.ambient == 0.25
        assert cfg.specular == 1.0
        assert cfg.shininess == 30
        assert cfg.ray_shadows == 0
        assert cfg.antialias == 4
        assert cfg.depth_cue == 0
        assert cfg.fog_start == 1.0
        assert cfg.direct == 0.45
        assert cfg.reflect == 0.45
        assert cfg.zoom_buffer == 2.0
        assert cfg.x_rotation == 0.0
        assert cfg.y_rotation == 0.0
        assert cfg.z_rotation == 0.0
        assert cfg.bg_color == "white"
        assert cfg.stick_color == "gray50"
        assert cfg.representation == "sticks+spheres"
        assert cfg.two_sided_lighting is True
        assert cfg.transparency_mode == 1
        assert cfg.ambient_occlusion is False
        assert cfg.ambient_occlusion_scale == 20.0
        assert cfg.ambient_occlusion_mode == 1
        assert cfg.apply_element_colors is True
        assert cfg.ray_trace_fog == 0.0
        assert cfg.ray_width is None
        assert cfg.ray_height is None
        assert cfg.opaque_background is False
        assert cfg.stick_ball is True
        assert cfg.auto_orient_tilt_x == 10.0
        assert cfg.auto_orient_tilt_y == 20.0
        assert cfg.zoom_buffer_linear == 1.5
        assert cfg.zoom_buffer_elongated == 2.0
        assert cfg.zoom_buffer_compact == 2.5


class TestConformerConfig:
    def test_default_values(self):
        cfg = ConformerConfig()
        assert cfg.use_random_coords is False
        assert cfg.clear_confs is True
        assert cfg.use_macrocycle_torsions is False
        assert cfg.use_basic_knowledge is True
        assert cfg.enforce_chirality is True
        assert cfg.use_small_ring_torsions is True
        assert cfg.max_iterations == 500
        assert cfg.num_conformers == 50
        assert cfg.prune_rms_thresh == 0.1
        assert cfg.use_exp_torsion_prefs is True


class TestConfig3D:
    def test_default_values(self):
        cfg = Config3D()
        assert isinstance(cfg.render, RenderConfig3D)
        assert isinstance(cfg.conformer, ConformerConfig)

    def test_to_dict(self):
        cfg = Config3D()
        d = cfg.to_dict()
        assert "render" in d
        assert "conformer" in d
        assert d["render"]["stick_radius"] == 0.2
        assert d["conformer"]["max_iterations"] == 500

    def test_reset_to_defaults(self):
        cfg = Config3D()
        cfg.render.stick_radius = 999.0
        cfg.conformer.max_iterations = 999
        cfg.reset_to_defaults()
        assert cfg.render.stick_radius == 0.2
        assert cfg.conformer.max_iterations == 500


class TestConfigLoaderGet2D:
    def test_returns_config2d(self):
        cfg = ConfigLoader.get_2d_config()
        assert isinstance(cfg, Config2D)

    def test_no_overrides_uses_defaults(self):
        cfg = ConfigLoader.get_2d_config()
        assert cfg.scale == 30.0
        assert cfg.bond_length == 50.0

    def test_empty_overrides(self):
        cfg = ConfigLoader.get_2d_config(overrides={})
        assert cfg.scale == 30.0

    def test_partial_overrides(self):
        cfg = ConfigLoader.get_2d_config(overrides={"scale": 50.0})
        assert cfg.scale == 50.0
        assert cfg.bond_length == 50.0

    def test_full_overrides(self):
        cfg = ConfigLoader.get_2d_config(
            overrides={"scale": 10.0, "bond_length": 20.0, "margin": 0.1}
        )
        assert cfg.scale == 10.0
        assert cfg.bond_length == 20.0
        assert cfg.margin == 0.1


class TestConfigLoaderGet3D:
    def test_returns_config3d(self):
        cfg = ConfigLoader.get_3d_config()
        assert isinstance(cfg, Config3D)

    def test_no_overrides_uses_defaults(self):
        cfg = ConfigLoader.get_3d_config()
        assert cfg.render.stick_radius == 0.2
        assert cfg.conformer.max_iterations == 500

    def test_empty_overrides(self):
        cfg = ConfigLoader.get_3d_config(overrides={})
        assert cfg.render.stick_radius == 0.2
        assert cfg.conformer.max_iterations == 500

    def test_render_overrides(self):
        cfg = ConfigLoader.get_3d_config(
            overrides={"render_stick_radius": 0.5, "render_antialias": 8}
        )
        assert cfg.render.stick_radius == 0.5
        assert cfg.render.antialias == 8

    def test_conformer_overrides(self):
        cfg = ConfigLoader.get_3d_config(
            overrides={"conformer_max_iterations": 500, "conformer_num_conformers": 10}
        )
        assert cfg.conformer.max_iterations == 500
        assert cfg.conformer.num_conformers == 10

    def test_mixed_overrides(self):
        cfg = ConfigLoader.get_3d_config(
            overrides={
                "render_stick_radius": 0.5,
                "conformer_max_iterations": 500,
            }
        )
        assert cfg.render.stick_radius == 0.5
        assert cfg.conformer.max_iterations == 500
        assert cfg.render.antialias == 4
        assert cfg.conformer.num_conformers == 50

    def test_partial_render_overrides(self):
        cfg = ConfigLoader.get_3d_config(overrides={"render_stick_radius": 0.1})
        assert cfg.render.stick_radius == 0.1
        assert cfg.render.sphere_scale == 0.3

    def test_nested_render_dict(self):
        cfg = ConfigLoader.get_3d_config(
            overrides={"render": {"stick_radius": 0.5, "antialias": 8}}
        )
        assert cfg.render.stick_radius == 0.5
        assert cfg.render.antialias == 8
        assert cfg.conformer.max_iterations == 500

    def test_nested_conformer_dict(self):
        cfg = ConfigLoader.get_3d_config(
            overrides={"conformer": {"max_iterations": 100, "num_conformers": 10}}
        )
        assert cfg.conformer.max_iterations == 100
        assert cfg.conformer.num_conformers == 10
        assert cfg.render.stick_radius == 0.2

    def test_nested_mixed_dicts(self):
        cfg = ConfigLoader.get_3d_config(
            overrides={
                "render": {"stick_radius": 0.99},
                "conformer": {"num_conformers": 5},
            }
        )
        assert cfg.render.stick_radius == 0.99
        assert cfg.conformer.num_conformers == 5


class TestConfigLoaderListTemplates:
    def test_returns_dict_with_expected_keys(self):
        result = ConfigLoader.list_templates()
        assert isinstance(result, dict)
        assert "settings_templates" in result
        assert "color_templates" in result

    def test_settings_templates_is_list_of_strings(self):
        result = ConfigLoader.list_templates()
        assert isinstance(result["settings_templates"], list)
        assert all(isinstance(n, str) for n in result["settings_templates"])

    def test_color_templates_is_list_of_strings(self):
        result = ConfigLoader.list_templates()
        assert isinstance(result["color_templates"], list)
        assert all(isinstance(n, str) for n in result["color_templates"])

    def test_known_templates_present(self):
        result = ConfigLoader.list_templates()
        assert "publication_2d" in result["settings_templates"]
        assert "high_quality_3d" in result["settings_templates"]
        assert "cpk_standard" in result["color_templates"]
        assert "minimal_bw" in result["color_templates"]


class TestConfigLoaderLoadTemplate:
    def test_publication_2d_returns_config2d(self):
        cfg = ConfigLoader.load_template("publication_2d")
        assert isinstance(cfg, Config2D)

    def test_publication_2d_overrides(self):
        cfg = ConfigLoader.load_template("publication_2d")
        assert cfg.scale == 40.0
        assert cfg.bond_length == 50.0
        assert cfg.min_font_size == 40

    def test_high_quality_3d_returns_config3d(self):
        cfg = ConfigLoader.load_template("high_quality_3d")
        assert isinstance(cfg, Config3D)

    def test_high_quality_3d_overrides(self):
        cfg = ConfigLoader.load_template("high_quality_3d")
        assert cfg.render.stick_radius == 0.18
        assert cfg.render.sphere_scale == 0.28
        assert cfg.render.ray_trace_mode == 1

    def test_web_optimized_2d(self):
        cfg = ConfigLoader.load_template("web_optimized_2d")
        assert isinstance(cfg, Config2D)
        assert cfg.scale == 25.0

    def test_web_preview_3d(self):
        cfg = ConfigLoader.load_template("web_preview_3d")
        assert isinstance(cfg, Config3D)
        assert cfg.render.antialias == 2

    def test_dramatic_3d(self):
        cfg = ConfigLoader.load_template("dramatic_3d")
        assert isinstance(cfg, Config3D)
        assert cfg.render.bg_color == "black"

    def test_minimal_clean_3d(self):
        cfg = ConfigLoader.load_template("minimal_clean_3d")
        assert isinstance(cfg, Config3D)
        assert cfg.render.stick_radius == 0.15

    def test_invalid_name_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown template"):
            ConfigLoader.load_template("nonexistent_template")

    def test_case_sensitivity(self):
        with pytest.raises(ValueError, match="Unknown template"):
            ConfigLoader.load_template("Publication_2d")


class TestConfigLoaderLoadColorTemplate:
    def test_cpk_standard(self):
        cfg = ConfigLoader.load_color_template("cpk_standard")
        assert isinstance(cfg, ColorConfig)
        assert "C" in cfg.element_colors
        assert cfg.element_colors["C"] == "gray35"
        assert cfg.stick_color == "gray50"
        assert cfg.bg_color == "white"

    def test_minimal_bw(self):
        cfg = ConfigLoader.load_color_template("minimal_bw")
        assert isinstance(cfg, ColorConfig)
        assert cfg.element_colors == {}
        assert cfg.stick_color is None
        assert cfg.bg_color == "white"

    def test_invalid_name_raises_valueerror(self):
        with pytest.raises(ValueError, match="Unknown color template"):
            ConfigLoader.load_color_template("nonexistent")

    def test_case_sensitivity(self):
        with pytest.raises(ValueError, match="Unknown color template"):
            ConfigLoader.load_color_template("CPK_Standard")


class TestConfigLoaderLoadFromFile:
    def test_load_valid_2d_config(self):
        data = {"type": "2d", "settings": {"scale": 50.0, "bond_length": 60.0}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = f.name
        try:
            cfg = ConfigLoader.load_from_file(path)
            assert isinstance(cfg, Config2D)
            assert cfg.scale == 50.0
            assert cfg.bond_length == 60.0
        finally:
            Path(path).unlink(missing_ok=True)

    def test_load_valid_3d_config(self):
        data = {
            "type": "3d",
            "settings": {
                "render_stick_radius": 0.5,
                "conformer_max_iterations": 500,
            },
        }
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = f.name
        try:
            cfg = ConfigLoader.load_from_file(path)
            assert isinstance(cfg, Config3D)
            assert cfg.render.stick_radius == 0.5
            assert cfg.conformer.max_iterations == 500
        finally:
            Path(path).unlink(missing_ok=True)

    def test_load_minimal_2d_config(self):
        data = {"type": "2d", "settings": {}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = f.name
        try:
            cfg = ConfigLoader.load_from_file(path)
            assert isinstance(cfg, Config2D)
            assert cfg.scale == 30.0
        finally:
            Path(path).unlink(missing_ok=True)

    def test_invalid_json_file_not_found(self):
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            ConfigLoader.load_from_file("C:\\nonexistent\\path\\file.json")

    def test_invalid_json_syntax(self):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            f.write("{invalid json}")
            f.flush()
            path = f.name
        try:
            with pytest.raises(json.JSONDecodeError):
                ConfigLoader.load_from_file(path)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_unknown_type_raises_valueerror(self):
        data = {"type": "invalid_type", "settings": {}}
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(data, f)
            f.flush()
            path = f.name
        try:
            with pytest.raises(ValueError, match="Unknown config type"):
                ConfigLoader.load_from_file(path)
        finally:
            Path(path).unlink(missing_ok=True)


class TestConfigLoaderSaveConfig:
    def test_save_and_reload_2d(self):
        cfg = Config2D()
        cfg.update(scale=42.0)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            ConfigLoader.save_config(cfg, path)
            reloaded = ConfigLoader.load_from_file(path)
            assert isinstance(reloaded, Config2D)
            assert reloaded.scale == 42.0
            assert reloaded.bond_length == 50.0
        finally:
            Path(path).unlink(missing_ok=True)

    def test_save_and_reload_3d(self):
        cfg = ConfigLoader.get_3d_config(overrides={"render_stick_radius": 0.99})
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            ConfigLoader.save_config(cfg, path)
            with open(path) as f:
                data = json.load(f)
            assert data["type"] == "3d"
            assert data["settings"]["render"]["stick_radius"] == 0.99
            reloaded = ConfigLoader.load_from_file(path)
            assert isinstance(reloaded, Config3D)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_saved_json_has_expected_structure(self):
        cfg = Config2D()
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            path = f.name
        try:
            ConfigLoader.save_config(cfg, path)
            with open(path) as f:
                data = json.load(f)
            assert "type" in data
            assert data["type"] == "2d"
            assert "name" in data
            assert "settings" in data
            assert isinstance(data["settings"], dict)
        finally:
            Path(path).unlink(missing_ok=True)

    def test_save_creates_parent_directories(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = Path(tmpdir) / "sub" / "nested" / "config.json"
            cfg = Config2D()
            ConfigLoader.save_config(cfg, nested)
            assert nested.exists()
            reloaded = ConfigLoader.load_from_file(nested)
            assert isinstance(reloaded, Config2D)


class TestProteinConfig:
    def test_default_values(self):
        cfg = ProteinConfig()
        assert cfg.protein_color_scheme == "Chain"
        assert cfg.helix_color == "#3399FF"
        assert cfg.sheet_color == "#FFCC00"
        assert cfg.loop_color == "#99AABB"
        assert cfg.cartoon_transparency == 0.0
        assert cfg.cartoon_fancy is True
        assert cfg.cartoon_sheets is True
        assert cfg.show_ligand is False
        assert cfg.show_water is False
        assert cfg.ligand_style == "sticks"
        assert cfg.ligand_transparency == 0.0
        assert cfg.ligand_color == "element"
        assert cfg.ligand_single_color == "#FF6B6B"
        assert cfg.ligand_stick_radius == 0.25
        assert cfg.ligand_stick_quality == 10
        assert cfg.ligand_ball_ratio == 1.5
        assert cfg.protein_bindsites is True
        assert cfg.protein_bind_radius == 5.0
        assert cfg.protein_bind_color == "yellow"
        assert cfg.protein_res_labels is False
        assert cfg.protein_label_size == 14
        assert cfg.protein_width == 1920
        assert cfg.protein_height == 1080
        assert cfg.protein_antialias == 2
        assert cfg.protein_specular == 1
        assert cfg.protein_ambient == 0.40
        assert cfg.protein_bg == "black"
        assert cfg.protein_shininess == 10
        assert cfg.protein_ray_shadows is False
        assert cfg.protein_ray_trace is False
        assert cfg.protein_auto_rot is True
        assert cfg.protein_autocrop is True
        assert cfg.protein_crop_margin == 10
        assert cfg.protein_direct == 0.45
        assert cfg.protein_reflect == 0.45
        assert cfg.protein_depth_cue is False
        assert cfg.protein_orthoscopic is False
        assert cfg.protein_ray_opaque is False
        assert cfg.protein_zoom_buffer == 2.0

    def test_update_method(self):
        cfg = ProteinConfig()
        cfg.update(protein_width=800, protein_height=600)
        assert cfg.protein_width == 800
        assert cfg.protein_height == 600
        assert cfg.protein_ray_trace is False

    def test_update_unknown_field(self):
        cfg = ProteinConfig()
        with pytest.raises(ValueError, match="Unknown protein config parameter"):
            cfg.update(nonexistent_field=42)

    def test_to_dict(self):
        cfg = ProteinConfig()
        d = cfg.to_dict()
        assert isinstance(d, dict)
        assert d["protein_width"] == 1920
        assert d["protein_height"] == 1080
        assert d["show_ligand"] is False


class TestConfigLoaderGetProtein:
    def test_returns_protein_config(self):
        cfg = ConfigLoader.get_protein_config()
        assert isinstance(cfg, ProteinConfig)

    def test_no_overrides_uses_defaults(self):
        cfg = ConfigLoader.get_protein_config()
        assert cfg.protein_width == 1920
        assert cfg.protein_color_scheme == "Chain"

    def test_empty_overrides(self):
        cfg = ConfigLoader.get_protein_config(overrides={})
        assert cfg.protein_width == 1920

    def test_partial_overrides(self):
        cfg = ConfigLoader.get_protein_config(overrides={"protein_width": 800})
        assert cfg.protein_width == 800
        assert cfg.protein_height == 1080

    def test_full_overrides(self):
        cfg = ConfigLoader.get_protein_config(
            overrides={
                "protein_width": 800,
                "protein_height": 600,
                "show_ligand": True,
                "protein_ray_trace": True,
            }
        )
        assert cfg.protein_width == 800
        assert cfg.protein_height == 600
        assert cfg.show_ligand is True
        assert cfg.protein_ray_trace is True


class TestConfigLoaderExportDefaultTemplate:
    def test_export_and_reload_2d(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            ConfigLoader.export_default_template("publication_2d", path)
            reloaded = ConfigLoader.load_from_file(path)
            assert isinstance(reloaded, Config2D)
            assert reloaded.scale == 40.0
        finally:
            Path(path).unlink(missing_ok=True)

    def test_export_and_reload_3d(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            ConfigLoader.export_default_template("high_quality_3d", path)
            reloaded = ConfigLoader.load_from_file(path)
            assert isinstance(reloaded, Config3D)
            assert reloaded.render.stick_radius == 0.18
        finally:
            Path(path).unlink(missing_ok=True)

    def test_invalid_template_raises_error(self):
        with pytest.raises(ValueError, match="Unknown template"):
            ConfigLoader.export_default_template("nonexistent", "dummy.json")
