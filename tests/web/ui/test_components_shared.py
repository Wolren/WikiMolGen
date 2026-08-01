"""Tests for web/ui/components_shared._validate_atom_scheme."""

from ui.components_shared import _validate_atom_scheme


class TestValidateAtomScheme:
    def test_valid_scheme(self):
        data = {
            "element_colors": {"C": "gray", "H": "#FFFFFF", "O": "red", "N": "gray50"},
        }
        assert _validate_atom_scheme(data) is None

    def test_valid_short_hex(self):
        assert _validate_atom_scheme({"element_colors": {"C": "#FFF"}}) is None

    def test_invalid_hex_rejected(self):
        err = _validate_atom_scheme({"element_colors": {"C": "#GGGGGG"}})
        assert err is not None
        assert "color" in err

    def test_punctuation_rejected(self):
        assert _validate_atom_scheme({"element_colors": {"C": "!!red"}}) is not None
        assert _validate_atom_scheme({"element_colors": {"C": "gray 50"}}) is not None

    def test_empty_color_rejected(self):
        assert _validate_atom_scheme({"element_colors": {"C": ""}}) is not None

    def test_non_string_color_rejected(self):
        assert _validate_atom_scheme({"element_colors": {"C": 42}}) is not None

    def test_invalid_element_symbol(self):
        assert _validate_atom_scheme({"element_colors": {"Carbon": "gray"}}) is not None

    def test_element_colors_must_be_dict(self):
        assert _validate_atom_scheme({"element_colors": ["C", "gray"]}) is not None

    def test_name_validation(self):
        assert _validate_atom_scheme({"name": "x" * 101}) is not None
        assert _validate_atom_scheme({"name": 42}) is not None
        assert _validate_atom_scheme({"name": "ok"}) is None
