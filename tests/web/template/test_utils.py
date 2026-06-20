"""
Tests for web/template/utils.py
================================

Covers validation, export, and upload functions with mocked Streamlit
session state.
"""

import io
import json
from unittest.mock import MagicMock, patch

import pytest
from template.utils import (
    export_current_as_preset,
    load_uploaded_preset,
    validate_preset,
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
    """Mock the ``streamlit`` module so all ``st.*`` calls are safe."""
    with patch("template.utils.st") as mock_st:
        ss = mock_st.session_state = _MockSessionState()
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
# validate_preset
# ═══════════════════════════════════════════════════════════════════


class TestValidatePreset:
    @pytest.mark.parametrize("type_val", ["2d", "3d", "protein"])
    def test_valid_types(self, type_val):
        data = {"type": type_val, "settings": {"key": "val"}}
        assert validate_preset(data) == []

    def test_invalid_type(self):
        errors = validate_preset({"type": "invalid"})
        assert any("type" in e for e in errors)

    def test_missing_type(self):
        errors = validate_preset({})
        assert any("type" in e for e in errors)

    def test_invalid_settings_type(self):
        errors = validate_preset({"type": "2d", "settings": "not a dict"})
        assert any("settings" in e for e in errors)

    def test_missing_settings_is_ok(self):
        assert validate_preset({"type": "2d"}) == []

    def test_invalid_name_type(self):
        errors = validate_preset({"type": "2d", "name": 123})
        assert any("name" in e for e in errors)

    def test_invalid_description_type(self):
        errors = validate_preset({"type": "2d", "description": 456})
        assert any("description" in e for e in errors)


# ═══════════════════════════════════════════════════════════════════
# export_current_as_preset
# ═══════════════════════════════════════════════════════════════════


class TestExportCurrentAsPreset:
    @pytest.mark.parametrize(
        "gen_type, expected_type",
        [("2D", "2d"), ("3D", "3d"), ("Protein", "protein")],
    )
    def test_type_mapping(self, mock_st, gen_type, expected_type):
        result = export_current_as_preset(gen_type)
        assert result["type"] == expected_type

    def test_2d_overrides(self, mock_st):
        mock_st.session_state["scale"] = 42.0
        mock_st.session_state["margin"] = 0.9
        result = export_current_as_preset("2D")
        assert result["settings"]["scale"] == 42.0
        assert result["settings"]["margin"] == 0.9

    def test_2d_defaults(self, mock_st):
        result = export_current_as_preset("2D")
        assert result["settings"]["scale"] == 30.0
        assert result["settings"]["min_font_size"] == 32

    def test_3d_overrides(self, mock_st):
        mock_st.session_state["ambient"] = 0.5
        mock_st.session_state["width"] = 2000
        result = export_current_as_preset("3D")
        assert result["settings"]["ambient"] == 0.5
        assert result["settings"]["width"] == 2000

    def test_3d_defaults(self, mock_st):
        result = export_current_as_preset("3D")
        assert result["settings"]["stick_radius"] == 0.2
        assert result["settings"]["height"] == 1600

    def test_3d_includes_element_colors(self, mock_st):
        mock_st.session_state["element_colors"] = {"C": "gray"}
        result = export_current_as_preset("3D")
        assert result["settings"].get("element_colors") == {"C": "gray"}

    def test_protein_overrides(self, mock_st):
        mock_st.session_state["protein_color_scheme"] = "Rainbow"
        mock_st.session_state["protein_ambient"] = 0.6
        result = export_current_as_preset("Protein")
        assert result["settings"]["protein_color_scheme"] == "Rainbow"
        assert result["settings"]["protein_ambient"] == 0.6

    def test_protein_defaults(self, mock_st):
        result = export_current_as_preset("Protein")
        assert result["settings"]["helix_color"] == "#3399FF"
        assert result["settings"]["protein_width"] == 1920

    def test_name_includes_gen_type(self, mock_st):
        for gt in ("2D", "3D", "Protein"):
            assert f"Custom {gt}" in export_current_as_preset(gt)["name"]

    def test_unknown_gen_type_falls_back_to_3d(self, mock_st):
        result = export_current_as_preset("Unknown")
        assert result["type"] == "3d"
        assert result["settings"]["width"] == 1800


# ═══════════════════════════════════════════════════════════════════
# load_uploaded_preset
# ═══════════════════════════════════════════════════════════════════


class TestLoadUploadedPreset:
    def test_valid_json(self, mock_st):
        data = {"name": "test", "settings": {"key": "val"}}
        file = io.StringIO(json.dumps(data))
        result = load_uploaded_preset(file)
        assert result is not None
        assert result["name"] == "test"
        assert result["data"]["settings"]["key"] == "val"

    def test_invalid_json(self, mock_st):
        file = io.StringIO("not json")
        result = load_uploaded_preset(file)
        assert result is None
        mock_st.error.assert_called_once()

    def test_missing_name_generates_fallback(self, mock_st):
        data = {"settings": {}}
        file = io.StringIO(json.dumps(data))
        result = load_uploaded_preset(file)
        assert result is not None
        assert result["name"].startswith("Custom_")

    def test_non_dict_json(self, mock_st):
        file = io.StringIO(json.dumps([1, 2, 3]))
        result = load_uploaded_preset(file)
        assert result is None
        mock_st.error.assert_called_once()
