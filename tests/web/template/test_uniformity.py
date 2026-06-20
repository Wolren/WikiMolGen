"""
Tests for preset export/apply uniformity across 2D/3D/Protein modes.

Verifies that:
- Exported settings keys exactly match config dataclass fields (no drift)
- Round-trip (export → apply → export) is lossless
- No cross-contamination between modes
- Apply handles all key formats (prefixed, bare, bool↔int)
"""

import dataclasses
from unittest.mock import MagicMock, patch

import pytest
from template.utils import (
    apply_preset_to_session,
    export_current_as_preset,
    export_protein_preset,
)
from wikimolgen.configs import (
    Config2D,
    ConformerConfig,
    ProteinConfig,
    RenderConfig3D,
)


class _MockSessionState(dict):
    def __getattr__(self, name: str):
        return self.get(name)

    def __setattr__(self, name: str, value):
        self[name] = value


@pytest.fixture
def mock_st():
    with patch("template.utils.st") as mock_st:
        ss = mock_st.session_state = _MockSessionState()
        ss.bg_color = "white"
        mock_st.error = MagicMock()
        mock_st.warning = MagicMock()
        mock_st.success = MagicMock()
        mock_st.info = MagicMock()
        yield mock_st


# ═══════════════════════════════════════════════════════════════════
# 2D uniformity
# ═══════════════════════════════════════════════════════════════════


class TestUniform2D:
    def test_export_keys_match_config_fields(self, mock_st):
        expected = {f.name for f in dataclasses.fields(Config2D)}
        result = export_current_as_preset("2D")
        assert set(result["settings"].keys()) == expected

    def test_export_values_read_from_session(self, mock_st):
        mock_st.session_state["scale"] = 99.0
        mock_st.session_state["bond_length"] = 10.0
        result = export_current_as_preset("2D")
        assert result["settings"]["scale"] == 99.0
        assert result["settings"]["bond_length"] == 10.0

    def test_export_no_3d_keys_leak(self, mock_st):
        result = export_current_as_preset("2D")
        keys = set(result["settings"].keys())
        assert "width" not in keys
        assert "stick_radius" not in keys
        assert "protein_color_scheme" not in keys

    def test_export_auto_orient_sets_angle_none(self, mock_st):
        mock_st.session_state["auto_orient_2d"] = True
        result = export_current_as_preset("2D")
        assert result["settings"]["angle_degrees"] is None

    def test_export_auto_orient_false_keeps_angle(self, mock_st):
        mock_st.session_state["auto_orient_2d"] = False
        result = export_current_as_preset("2D")
        assert result["settings"]["angle_degrees"] == 0.0

    def test_round_trip_lossless(self, mock_st):
        mock_st.session_state["scale"] = 42.0
        mock_st.session_state["bond_length"] = 55.0
        mock_st.session_state["use_bw_palette"] = False
        first = export_current_as_preset("2D")
        apply_preset_to_session(first)
        second = export_current_as_preset("2D")
        assert first == second


# ═══════════════════════════════════════════════════════════════════
# 3D uniformity
# ═══════════════════════════════════════════════════════════════════


class TestUniform3D:
    def test_export_keys_match_config_fields(self, mock_st):
        render_fields = {f.name for f in dataclasses.fields(RenderConfig3D)}
        conformer_fields = {f.name for f in dataclasses.fields(ConformerConfig)}
        expected = render_fields | conformer_fields | {"atom_color_choice"}
        result = export_current_as_preset("3D")
        assert set(result["settings"].keys()) == expected

    def test_export_no_2d_keys_leak(self, mock_st):
        result = export_current_as_preset("3D")
        keys = set(result["settings"].keys())
        assert "auto_orient_2d" not in keys
        assert "use_bw_palette" not in keys
        assert "protein_color_scheme" not in keys

    def test_export_ray_shadows_is_int(self, mock_st):
        result = export_current_as_preset("3D")
        assert isinstance(result["settings"]["ray_shadows"], int)

    def test_export_depth_cue_is_int(self, mock_st):
        result = export_current_as_preset("3D")
        assert isinstance(result["settings"]["depth_cue"], int)

    def test_round_trip_lossless(self, mock_st):
        mock_st.session_state["ambient"] = 0.75
        mock_st.session_state["width"] = 2000
        mock_st.session_state["stick_radius"] = 0.25
        mock_st.session_state["ray_shadows"] = True
        mock_st.session_state["depth_cue"] = True
        first = export_current_as_preset("3D")
        apply_preset_to_session(first)
        second = export_current_as_preset("3D")
        assert first == second

    def test_round_trip_with_element_colors(self, mock_st):
        mock_st.session_state["element_colors"] = {"C": "red", "N": "blue"}
        first = export_current_as_preset("3D")
        apply_preset_to_session(first)
        second = export_current_as_preset("3D")
        assert first == second

    def test_round_trip_with_atom_color_choice(self, mock_st):
        mock_st.session_state["atom_color_choice"] = "cpk_standard"
        first = export_current_as_preset("3D")
        apply_preset_to_session(first)
        second = export_current_as_preset("3D")
        assert first == second


# ═══════════════════════════════════════════════════════════════════
# Protein uniformity
# ═══════════════════════════════════════════════════════════════════


class TestUniformProtein:
    def test_export_keys_match_protein_config(self, mock_st):
        expected = {f.name for f in dataclasses.fields(ProteinConfig)}
        result = export_protein_preset()
        assert set(result.keys()) == expected

    def test_export_no_2d_3d_keys_leak(self, mock_st):
        result = export_protein_preset()
        keys = set(result.keys())
        assert "auto_orient_2d" not in keys
        assert "stick_radius" not in keys
        assert "width" not in keys

    def test_export_keys_via_main_function(self, mock_st):
        expected = {f.name for f in dataclasses.fields(ProteinConfig)}
        result = export_current_as_preset("Protein")
        assert set(result["settings"].keys()) == expected

    def test_round_trip_lossless(self, mock_st):
        mock_st.session_state["protein_ambient"] = 0.8
        mock_st.session_state["protein_width"] = 2560
        mock_st.session_state["protein_color_scheme"] = "Rainbow"
        first = export_current_as_preset("Protein")
        apply_preset_to_session(first)
        second = export_current_as_preset("Protein")
        assert first == second


# ═══════════════════════════════════════════════════════════════════
# Apply uniformity (cross-format)
# ═══════════════════════════════════════════════════════════════════


class TestApplyUniform:
    def test_apply_bare_keys(self, mock_st):
        mock_st.session_state["scale"] = 10.0
        preset = {"type": "2d", "settings": {"scale": 50.0}}
        apply_preset_to_session(preset)
        assert mock_st.session_state["scale"] == 50.0

    def test_apply_render_prefixed_keys(self, mock_st):
        mock_st.session_state["ambient"] = 0.1
        preset = {"type": "3d", "settings": {"render_ambient": 0.9}}
        apply_preset_to_session(preset)
        assert mock_st.session_state["ambient"] == 0.9

    def test_apply_conformer_prefixed_keys(self, mock_st):
        mock_st.session_state["max_iterations"] = 100
        preset = {"type": "3d", "settings": {"conformer_max_iterations": 999}}
        apply_preset_to_session(preset)
        assert mock_st.session_state["max_iterations"] == 999

    def test_apply_mixed_prefixes(self, mock_st):
        mock_st.session_state.update({"ambient": 0.1, "max_iterations": 100})
        preset = {
            "type": "3d",
            "settings": {
                "render_ambient": 0.5,
                "conformer_max_iterations": 500,
            },
        }
        apply_preset_to_session(preset)
        assert mock_st.session_state["ambient"] == 0.5
        assert mock_st.session_state["max_iterations"] == 500

    def test_apply_int_to_bool_conversion(self, mock_st):
        mock_st.session_state["ray_shadows"] = False
        preset = {"type": "3d", "settings": {"ray_shadows": 1}}
        apply_preset_to_session(preset)
        assert mock_st.session_state["ray_shadows"] is True

        preset2 = {"type": "3d", "settings": {"ray_shadows": 0}}
        apply_preset_to_session(preset2)
        assert mock_st.session_state["ray_shadows"] is False

    def test_apply_bool_preserved(self, mock_st):
        mock_st.session_state["ray_shadows"] = False
        preset = {"type": "3d", "settings": {"ray_shadows": True}}
        apply_preset_to_session(preset)
        assert mock_st.session_state["ray_shadows"] is True

    def test_apply_unknown_keys_ignored(self, mock_st):
        preset = {"type": "3d", "settings": {"nonexistent_key": 42}}
        apply_preset_to_session(preset)

    def test_apply_flat_data_no_settings_wrapper(self, mock_st):
        mock_st.session_state["scale"] = 10.0
        flat = {"scale": 50.0}
        apply_preset_to_session(flat)
        assert mock_st.session_state["scale"] == 50.0


# ═══════════════════════════════════════════════════════════════════
# Cross-mode contamination
# ═══════════════════════════════════════════════════════════════════


class TestCrossModeContamination:
    def test_2d_export_not_contain_3d_keys(self, mock_st):
        mock_st.session_state["stick_radius"] = 0.5
        mock_st.session_state["ambient"] = 0.9
        result = export_current_as_preset("2D")
        keys = set(result["settings"].keys())
        assert "stick_radius" not in keys
        assert "ambient" not in keys

    def test_3d_export_not_contain_2d_keys(self, mock_st):
        mock_st.session_state["scale"] = 99.0
        mock_st.session_state["use_bw_palette"] = True
        result = export_current_as_preset("3D")
        keys = set(result["settings"].keys())
        assert "scale" not in keys
        assert "use_bw_palette" not in keys

    def test_protein_export_not_contain_common_keys(self, mock_st):
        mock_st.session_state["scale"] = 99.0
        mock_st.session_state["stick_radius"] = 0.5
        mock_st.session_state["bg_color"] = "red"
        result = export_protein_preset()
        keys = set(result.keys())
        assert "scale" not in keys
        assert "stick_radius" not in keys
        assert "bg_color" not in keys


# ═══════════════════════════════════════════════════════════════════
# Round-trip with prefixed CLI format
# ═══════════════════════════════════════════════════════════════════


class TestRoundTripCLIFormat:
    def test_cli_prefixed_3d_matches_export(self, mock_st):
        mock_st.session_state["ambient"] = 0.99
        mock_st.session_state["max_iterations"] = 777
        mock_st.session_state["width"] = 1000

        cli_format = {
            "type": "3d",
            "settings": {
                "render_ambient": 0.99,
                "conformer_max_iterations": 777,
                "render_width": 1800,
            },
        }

        apply_preset_to_session(cli_format)
        assert mock_st.session_state["ambient"] == 0.99
        assert mock_st.session_state["max_iterations"] == 777
        assert mock_st.session_state["width"] == 1800

        exported = export_current_as_preset("3D")
        assert exported["settings"]["ambient"] == 0.99
        assert exported["settings"]["max_iterations"] == 777
        assert exported["settings"]["width"] == 1800

    def test_cli_prefixed_with_bool_fields(self, mock_st):
        mock_st.session_state["auto_crop"] = True
        mock_st.session_state["ray_shadows"] = False

        cli_format = {
            "type": "3d",
            "settings": {
                "render_auto_crop": False,
                "render_ray_shadows": 1,
            },
        }

        apply_preset_to_session(cli_format)
        assert mock_st.session_state["auto_crop"] is False
        assert mock_st.session_state["ray_shadows"] is True

        exported = export_current_as_preset("3D")
        assert exported["settings"]["auto_crop"] is False
        assert exported["settings"]["ray_shadows"] == 1
