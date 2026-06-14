"""
Tests for web/ui/icons.py
=========================

Covers icon(), header(), and indirect coverage of _svg().
"""

import pytest
from ui.icons import icon, header, _ICON_DEFS

# ═══════════════════════════════════════════════════════════════════
# icon()
# ═══════════════════════════════════════════════════════════════════


class TestIcon:
    def test_valid_name_returns_expected_structure(self):
        result = icon("check")
        assert result.startswith('<span class="wk-icon">')
        assert result.endswith("</span>")
        assert "<svg" in result
        assert 'viewBox="0 0 24 24"' in result
        assert 'aria-hidden="true"' in result

    def test_invalid_name_raises_key_error(self):
        with pytest.raises(KeyError, match="Unknown icon"):
            icon("nonexistent")

    def test_size_parameter(self):
        result = icon("check", size=32)
        assert 'width="32"' in result
        assert 'height="32"' in result

    def test_default_size(self):
        result = icon("check")
        assert 'width="16"' in result
        assert 'height="16"' in result

    @pytest.mark.parametrize("stroke, expected", [(4, "4"), (0, "0"), (None, "2")])
    def test_stroke_parameter(self, stroke, expected):
        result = icon("check", stroke=stroke)
        assert f'stroke-width="{expected}"' in result

    @pytest.mark.parametrize("name", sorted(_ICON_DEFS))
    def test_all_icon_names_produce_valid_svg(self, name):
        """Every registered icon name returns a non-empty SVG."""
        result = icon(name)
        assert result.startswith('<span class="wk-icon">')
        assert result.endswith("</span>")
        assert any(tag in result for tag in ("<path", "<circle", "<ellipse", "<rect", "<line"))


# ═══════════════════════════════════════════════════════════════════
# header()
# ═══════════════════════════════════════════════════════════════════


class TestHeader:
    def test_valid_call_returns_expected_structure(self):
        result = header("folder", "Templates")
        assert result.startswith('<div class="wk-section-header">')
        assert result.endswith("</div>")
        assert "<svg" in result
        assert 'class="wk-section-header__icon"' in result
        assert 'class="wk-section-header__text"' in result
        assert "Templates" in result

    def test_text_is_html_escaped(self):
        result = header("check", "<script>alert('xss')</script>")
        assert "&lt;script&gt;" in result
        assert "<script>" not in result

    def test_text_with_special_chars(self):
        result = header("x", "a & b < c > d \" e ' f")
        assert "&amp;" in result
        assert "&lt;" in result
        assert "&gt;" in result
        assert "&#x27;" in result
        assert "&quot;" in result

    def test_very_long_text(self):
        long_text = "x" * 10_000
        result = header("info", long_text)
        assert long_text in result

    def test_invalid_name_raises_key_error(self):
        with pytest.raises(KeyError, match="Unknown icon"):
            header("nonexistent", "Title")

    def test_size_parameter(self):
        result = header("folder", "Test", size=24)
        assert 'width="24"' in result
        assert 'height="24"' in result


# ═══════════════════════════════════════════════════════════════════
# _svg() attributes  (tested indirectly via icon / header)
# ═══════════════════════════════════════════════════════════════════


class TestSvgAttributes:
    """Verify SVG element attributes are correctly rendered."""

    def test_standard_attributes(self):
        result = icon("atom")
        assert 'xmlns="http://www.w3.org/2000/svg"' in result
        assert 'fill="none"' in result
        assert 'stroke="currentColor"' in result
        assert 'stroke-linecap="round"' in result
        assert 'stroke-linejoin="round"' in result

    def test_svg_markup_via_header(self):
        result = header("database", "DB")
        svg_start = result.find("<svg")
        svg_end = result.find("</svg>") + len("</svg>")
        svg = result[svg_start:svg_end]
        assert svg.startswith("<svg")
        assert svg.endswith("</svg>")
        assert 'viewBox="0 0 24 24"' in svg


# ═══════════════════════════════════════════════════════════════════
# Edge cases
# ═══════════════════════════════════════════════════════════════════


class TestEdgeCases:
    def test_empty_string_name_icon(self):
        with pytest.raises(KeyError):
            icon("")

    def test_empty_string_name_header(self):
        with pytest.raises(KeyError):
            header("", "Title")

    def test_empty_text_in_header(self):
        result = header("check", "")
        assert 'class="wk-section-header__text"></span>' in result

    @pytest.mark.parametrize("size", [0, 1, 64, 128])
    def test_various_sizes(self, size):
        result = icon("check", size=size)
        assert f'width="{size}"' in result
        assert f'height="{size}"' in result

    @pytest.mark.parametrize("stroke", [0, 1, 3, 5])
    def test_various_strokes(self, stroke):
        result = icon("check", stroke=stroke)
        assert f'stroke-width="{stroke}"' in result
