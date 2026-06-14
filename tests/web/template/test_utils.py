"""
Tests for web/template/utils.py
================================

Covers validation, export, upload, and apply functions with mocked Streamlit
session state.
"""

import io
import json
from unittest.mock import MagicMock, patch

import pytest
from template.utils import (
    apply_templates_to_generator,
    export_color_template,
    export_current_settings_as_template,
    load_custom_template,
    save_template_to_session,
    validate_color_template,
    validate_settings_template,
    validate_uploaded_json,
)

# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


class _MockSessionState(dict):
    """Dict that also supports attribute-style access like real ``st.session_state``."""

    def __getattr__(self, name: str):
        return self.get(name)

    def __setattr__(self, name: str, value):
        self[name] = value


@pytest.fixture
def mock_st():
    """Mock the ``streamlit`` module so all ``st.*`` calls are safe.

    Session state is pre-populated with the keys that ``initialize_session_state``
    normally sets up, so utility functions don't encounter ``None`` where they
    expect a ``dict`` or other value.
    """
    with patch("template.utils.st") as mock_st:
        ss = mock_st.session_state = _MockSessionState()
        ss.custom_color_templates = {}
        ss.custom_settings_templates = {}
        ss.uploaded_color_template = None
        ss.uploaded_settings_template = None
        ss.template_applied_once = False
        ss.color_template_selector = "None"
        ss.settings_template_selector = "None"
        ss.bg_color = "white"
        mock_st.error = MagicMock()
        mock_st.warning = MagicMock()
        mock_st.success = MagicMock()
        mock_st.info = MagicMock()
        yield mock_st


# ═══════════════════════════════════════════════════════════════════
# validate_uploaded_json
# ═══════════════════════════════════════════════════════════════════


class TestValidateUploadedJson:
    def test_valid_dict(self):
        file = io.StringIO(json.dumps({"a": 1}))
        data, err = validate_uploaded_json(file)
        assert err is None
        assert data == {"a": 1}

    def test_invalid_json(self):
        file = io.StringIO("not json")
        data, err = validate_uploaded_json(file)
        assert data is None
        assert "Invalid JSON" in err

    def test_non_dict_json(self):
        file = io.StringIO(json.dumps([1, 2, 3]))
        data, err = validate_uploaded_json(file)
        assert data is None
        assert "object (dict)" in err


# ═══════════════════════════════════════════════════════════════════
# validate_color_template
# ═══════════════════════════════════════════════════════════════════


class TestValidateColorTemplate:
    def test_valid_minimal(self):
        assert validate_color_template({"name": "test"}) == []

    def test_valid_full(self):
        data = {
            "name": "CPK",
            "description": "Standard CPK colors",
            "element_colors": {"C": "gray", "O": "red"},
            "stick_color": "gray40",
            "bg_color": "white",
        }
        assert validate_color_template(data) == []

    def test_valid_omits_optionals(self):
        assert validate_color_template({"element_colors": {}}) == []

    def test_invalid_name_type(self):
        errors = validate_color_template({"name": 123})
        assert any("name" in e for e in errors)

    def test_invalid_description_type(self):
        errors = validate_color_template({"name": "x", "description": 42})
        assert any("description" in e for e in errors)

    def test_invalid_element_colors_type(self):
        errors = validate_color_template({"element_colors": "not a dict"})
        assert any("element_colors" in e for e in errors)

    def test_invalid_element_colors_value(self):
        errors = validate_color_template({"element_colors": {"C": 123}})
        assert any("element_colors" in e for e in errors)

    def test_valid_null_stick_color(self):
        assert validate_color_template({"stick_color": None}) == []

    def test_invalid_stick_color_type(self):
        errors = validate_color_template({"stick_color": 42})
        assert any("stick_color" in e for e in errors)

    def test_invalid_bg_color_type(self):
        errors = validate_color_template({"bg_color": 123})
        assert any("bg_color" in e for e in errors)

    @pytest.mark.parametrize("field", ["name", "description"])
    def test_optional_fields_absent(self, field):
        data = {"name": "x", "description": "desc"}
        data.pop(field, None)
        assert validate_color_template(data) == []


# ═══════════════════════════════════════════════════════════════════
# validate_settings_template
# ═══════════════════════════════════════════════════════════════════


class TestValidateSettingsTemplate:
    @pytest.mark.parametrize("type_val", ["2d", "3d", "protein"])
    def test_valid_types(self, type_val):
        data = {"type": type_val, "settings": {"key": "val"}}
        assert validate_settings_template(data) == []

    def test_invalid_type(self):
        errors = validate_settings_template({"type": "invalid"})
        assert any("type" in e for e in errors)

    def test_missing_type(self):
        errors = validate_settings_template({})
        assert any("type" in e for e in errors)

    def test_invalid_settings_type(self):
        errors = validate_settings_template({"type": "2d", "settings": "not a dict"})
        assert any("settings" in e for e in errors)

    def test_missing_settings_is_ok(self):
        assert validate_settings_template({"type": "2d"}) == []

    def test_invalid_name_type(self):
        errors = validate_settings_template({"type": "2d", "name": 123})
        assert any("name" in e for e in errors)

    def test_invalid_description_type(self):
        errors = validate_settings_template({"type": "2d", "description": 456})
        assert any("description" in e for e in errors)


# ═══════════════════════════════════════════════════════════════════
# export_current_settings_as_template
# ═══════════════════════════════════════════════════════════════════


class TestExportCurrentSettingsAsTemplate:
    @pytest.mark.parametrize(
        "gen_type, expected_type",
        [("2D", "2d"), ("3D", "3d"), ("Protein", "protein")],
    )
    def test_type_mapping(self, mock_st, gen_type, expected_type):
        result = export_current_settings_as_template(gen_type)
        assert result["type"] == expected_type

    def test_2d_overrides(self, mock_st):
        mock_st.session_state["scale"] = 42.0
        mock_st.session_state["margin"] = 0.9
        result = export_current_settings_as_template("2D")
        assert result["settings"]["scale"] == 42.0
        assert result["settings"]["margin"] == 0.9

    def test_2d_defaults(self, mock_st):
        result = export_current_settings_as_template("2D")
        assert result["settings"]["scale"] == 30.0
        assert result["settings"]["min_font_size"] == 32

    def test_3d_overrides(self, mock_st):
        mock_st.session_state["ambient"] = 0.5
        mock_st.session_state["width"] = 2000
        result = export_current_settings_as_template("3D")
        assert result["settings"]["ambient"] == 0.5
        assert result["settings"]["width"] == 2000

    def test_3d_defaults(self, mock_st):
        result = export_current_settings_as_template("3D")
        assert result["settings"]["stick_radius"] == 0.2
        assert result["settings"]["height"] == 1600

    def test_protein_overrides(self, mock_st):
        mock_st.session_state["protein_color_scheme"] = "Rainbow"
        mock_st.session_state["protein_ambient"] = 0.6
        result = export_current_settings_as_template("Protein")
        assert result["settings"]["protein_color_scheme"] == "Rainbow"
        assert result["settings"]["protein_ambient"] == 0.6

    def test_protein_defaults(self, mock_st):
        result = export_current_settings_as_template("Protein")
        assert result["settings"]["helix_color"] == "#3399FF"
        assert result["settings"]["protein_width"] == 1920

    def test_name_includes_gen_type(self, mock_st):
        for gt in ("2D", "3D", "Protein"):
            assert f"Custom {gt}" in export_current_settings_as_template(gt)["name"]

    def test_unknown_gen_type_falls_back_to_3d(self, mock_st):
        result = export_current_settings_as_template("Unknown")
        assert result["type"] == "3d"
        assert result["settings"]["width"] == 1800


# ═══════════════════════════════════════════════════════════════════
# export_color_template
# ═══════════════════════════════════════════════════════════════════


class TestExportColorTemplate:
    def test_without_uploaded(self, mock_st):
        mock_st.session_state["bg_color"] = "black"
        result = export_color_template()
        assert result["element_colors"] == {}
        assert result["stick_color"] is None
        assert result["bg_color"] == "black"

    def test_with_uploaded_template(self, mock_st):
        mock_st.session_state["uploaded_color_template"] = {
            "name": "My Colors",
            "element_colors": {"C": "gray", "O": "red"},
            "stick_color": "gray40",
            "bg_color": "white",
        }
        result = export_color_template()
        assert result["name"] == "My Colors"
        assert result["element_colors"] == {"C": "gray", "O": "red"}
        assert result["stick_color"] == "gray40"

    def test_uploaded_partial_data(self, mock_st):
        mock_st.session_state["uploaded_color_template"] = {"name": "Partial"}
        result = export_color_template()
        assert result["element_colors"] == {}
        assert result["stick_color"] is None

    def test_uploaded_bg_color_falls_back(self, mock_st):
        mock_st.session_state["uploaded_color_template"] = {"element_colors": {}}
        mock_st.session_state["bg_color"] = "black"
        result = export_color_template()
        # uploaded dict has no bg_color -> falls back to session state's bg_color
        assert result["bg_color"] == "black"

    def test_uploaded_non_dict(self, mock_st):
        mock_st.session_state["uploaded_color_template"] = None
        result = export_color_template()
        assert result["element_colors"] == {}
        assert result["stick_color"] is None


# ═══════════════════════════════════════════════════════════════════
# load_custom_template
# ═══════════════════════════════════════════════════════════════════


class TestLoadCustomTemplate:
    def test_valid_json(self, mock_st):
        data = {"name": "test", "element_colors": {"C": "gray"}}
        file = io.StringIO(json.dumps(data))
        result = load_custom_template(file, "color")
        assert result is not None
        assert result["name"] == "test"
        assert result["data"]["element_colors"]["C"] == "gray"

    def test_invalid_json(self, mock_st):
        file = io.StringIO("not json")
        result = load_custom_template(file, "color")
        assert result is None
        mock_st.error.assert_called_once()

    def test_missing_name_generates_fallback(self, mock_st):
        data = {"element_colors": {}}
        file = io.StringIO(json.dumps(data))
        result = load_custom_template(file, "color")
        assert result is not None
        assert result["name"].startswith("Custom_")

    def test_non_dict_json(self, mock_st):
        file = io.StringIO(json.dumps([1, 2, 3]))
        result = load_custom_template(file, "settings")
        assert result is None
        mock_st.error.assert_called_once()


# ═══════════════════════════════════════════════════════════════════
# save_template_to_session
# ═══════════════════════════════════════════════════════════════════


class TestSaveTemplateToSession:
    def test_save_color_template(self, mock_st):
        save_template_to_session("My Colors", {"element_colors": {"C": "gray"}}, "color")
        assert mock_st.session_state["custom_color_templates"]["My Colors"] == {
            "element_colors": {"C": "gray"}
        }
        assert mock_st.session_state["uploaded_color_template"] == {"element_colors": {"C": "gray"}}

    def test_save_settings_template_syncs_existing_keys(self, mock_st):
        mock_st.session_state["existing_key"] = "old"
        save_template_to_session(
            "My Settings",
            {"type": "2d", "settings": {"existing_key": "new_value", "unknown_key": 42}},
            "settings",
        )
        assert mock_st.session_state["custom_settings_templates"]["My Settings"] is not None
        assert mock_st.session_state["uploaded_settings_template"] is not None
        assert mock_st.session_state["existing_key"] == "new_value"
        # unknown_key is NOT in session state, so it should NOT be synced (safety guard)
        assert "unknown_key" not in mock_st.session_state
        assert mock_st.session_state["template_applied_once"] is True

    def test_save_settings_skips_unknown_keys(self, mock_st):
        save_template_to_session(
            "Test",
            {"type": "2d", "settings": {"nonexistent_key": "val"}},
            "settings",
        )
        assert "nonexistent_key" not in mock_st.session_state

    def test_save_settings_without_settings_key(self, mock_st):
        mock_st.session_state["existing_key"] = "old"
        save_template_to_session(
            "Flat",
            {"existing_key": "new_value"},
            "settings",
        )
        # Falls back to top-level dict when no "settings" key
        assert mock_st.session_state["existing_key"] == "new_value"


# ═══════════════════════════════════════════════════════════════════
# apply_templates_to_generator
# ═══════════════════════════════════════════════════════════════════


class TestApplyTemplatesToGenerator:
    def test_nothing_applied(self, mock_st):
        gen = MagicMock()
        result = apply_templates_to_generator(gen, "2d")
        assert result is False
        gen.load_color_template.assert_not_called()
        gen.load_settings_template.assert_not_called()

    def test_already_applied(self, mock_st):
        mock_st.session_state["template_applied_once"] = True
        gen = MagicMock()
        result = apply_templates_to_generator(gen, "2d")
        assert result is False

    def test_color_selector_builtin(self, mock_st):
        mock_st.session_state["color_template_selector"] = "cpk_standard"
        gen = MagicMock()
        result = apply_templates_to_generator(gen, "2d")
        assert result is True
        gen.load_color_template.assert_called_once_with("cpk_standard")

    def test_color_selector_custom(self, mock_st):
        mock_st.session_state["color_template_selector"] = "My Colors"
        mock_st.session_state["custom_color_templates"] = {
            "My Colors": {"element_colors": {"C": "gray"}}
        }
        gen = MagicMock()
        result = apply_templates_to_generator(gen, "2d")
        assert result is True
        gen.load_color_template.assert_called_once_with({"element_colors": {"C": "gray"}})

    def test_uploaded_color(self, mock_st):
        mock_st.session_state["uploaded_color_template"] = {"element_colors": {"O": "red"}}
        gen = MagicMock()
        result = apply_templates_to_generator(gen, "2d")
        assert result is True
        gen.load_color_template.assert_called_once_with({"element_colors": {"O": "red"}})

    def test_settings_selector_builtin(self, mock_st):
        mock_st.session_state["settings_template_selector"] = "high_quality_3d"
        gen = MagicMock()
        result = apply_templates_to_generator(gen, "3d")
        assert result is True
        gen.load_settings_template.assert_called_once_with("high_quality_3d")

    def test_settings_selector_custom(self, mock_st):
        mock_st.session_state["settings_template_selector"] = "My Settings"
        mock_st.session_state["custom_settings_templates"] = {
            "My Settings": {"type": "3d", "settings": {"ambient": 0.1}}
        }
        gen = MagicMock()
        result = apply_templates_to_generator(gen, "3d")
        assert result is True
        gen.load_settings_template.assert_called_once_with(
            {"type": "3d", "settings": {"ambient": 0.1}}
        )

    def test_uploaded_settings(self, mock_st):
        mock_st.session_state["uploaded_settings_template"] = {"type": "3d", "settings": {}}
        gen = MagicMock()
        result = apply_templates_to_generator(gen, "3d")
        assert result is True
        gen.load_settings_template.assert_called_once_with({"type": "3d", "settings": {}})

    def test_both_templates(self, mock_st):
        mock_st.session_state["color_template_selector"] = "minimal_bw"
        mock_st.session_state["settings_template_selector"] = "web_preview_3d"
        gen = MagicMock()
        result = apply_templates_to_generator(gen, "3d")
        assert result is True
        gen.load_color_template.assert_called_once_with("minimal_bw")
        gen.load_settings_template.assert_called_once_with("web_preview_3d")

    def test_error_handling(self, mock_st):
        mock_st.session_state["color_template_selector"] = "broken"
        gen = MagicMock()
        gen.load_color_template.side_effect = ValueError("Bad template")
        result = apply_templates_to_generator(gen, "2d")
        assert result is False  # error occurred, nothing applied
        mock_st.warning.assert_called_once()
