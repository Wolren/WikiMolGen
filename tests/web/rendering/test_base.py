"""Tests for web/rendering/base.py — with full mocks for Streamlit and generators."""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest


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
    with patch("rendering.base.st") as mock_st:
        ss = mock_st.session_state = _MockSessionState()
        mock_st.error = MagicMock()
        yield mock_st


@pytest.fixture
def session_with_2d_defaults(mock_st):
    ss = mock_st.session_state
    ss.scale = 30.0
    ss.bond_length = 50.0
    ss.margin = 0.8
    ss.min_font_size = 32
    ss.padding = 0.07
    ss.use_bw_palette = True
    ss.transparent_background = True
    ss.auto_orient_2d = True
    ss.angle_degrees = 0.0
    ss.auto_orient_amines = True
    ss.amine_target_angle = 0.0
    ss.phenethylamine_target = 90.0
    ss.auto_generate = True
    ss.config_changed = False
    ss.rendered_structure = False
    return mock_st


@pytest.fixture
def session_with_3d_defaults(mock_st):
    ss = mock_st.session_state
    ss.stick_radius = 0.2
    ss.sphere_scale = 0.3
    ss.stick_ball_ratio = 1.8
    ss.stick_transparency = 0.0
    ss.sphere_transparency = 0.0
    ss.valence = 0.0
    ss.antialias = 4
    ss.ambient = 0.25
    ss.specular = 1.0
    ss.shininess = 30
    ss.direct = 0.45
    ss.reflect = 0.45
    ss.width = 1800
    ss.height = 1600
    ss.bg_color = "white"
    ss.crop_margin = 10
    ss.auto_crop = True
    ss.auto_orient_3d = True
    ss.representation = "sticks+spheres"
    ss.two_sided_lighting = True
    ss.transparency_mode = 1
    ss.depth_cue = False
    ss.fog_start = 1.0
    ss.ambient_occlusion = False
    ss.ambient_occlusion_scale = 20.0
    ss.ray_shadows = False
    ss.ray_trace_mode = 0
    ss.ray_trace_fog = 0.0
    ss.opaque_background = False
    ss.stick_ball = True
    ss.stick_color = "gray50"
    ss.zoom_buffer = 2.0
    ss.num_conformers = 50
    ss.max_iterations = 500
    ss.prune_rms_thresh = 0.1
    ss.use_random_coords = False
    ss.use_basic_knowledge = True
    ss.enforce_chirality = True
    ss.use_small_ring_torsions = True
    ss.use_macrocycle_torsions = False
    ss.use_exp_torsion_prefs = True
    return mock_st


# ═══════════════════════════════════════════════════════════════════
# _session_overrides
# ═══════════════════════════════════════════════════════════════════


class TestSessionOverrides:
    def test_returns_matching_fields(self, mock_st):
        from rendering.base import _session_overrides
        from wikimolgen.configs import Config2D

        ss = mock_st.session_state
        ss.scale = 42.0
        ss.bond_length = 60.0
        result = _session_overrides(Config2D)
        assert result["scale"] == 42.0
        assert result["bond_length"] == 60.0

    def test_skips_absent_keys(self, mock_st):
        from rendering.base import _session_overrides
        from wikimolgen.configs import Config2D

        result = _session_overrides(Config2D)
        assert result == {}

    def test_with_prefix(self, mock_st):
        from rendering.base import _session_overrides
        from wikimolgen.configs import RenderConfig3D

        ss = mock_st.session_state
        ss.render_stick_radius = 0.5
        ss.render_antialias = 8
        result = _session_overrides(RenderConfig3D, prefix="render_")
        assert result["stick_radius"] == 0.5
        assert result["antialias"] == 8


# ═══════════════════════════════════════════════════════════════════
# build_2d_config
# ═══════════════════════════════════════════════════════════════════


class TestBuild2DConfig:
    def test_builds_config2d(self, session_with_2d_defaults):
        from rendering.base import build_2d_config

        cfg = build_2d_config()
        assert cfg.scale == 30.0
        assert cfg.auto_orient_2d is True

    def test_auto_orient_removes_angle(self, session_with_2d_defaults):
        from rendering.base import build_2d_config

        cfg = build_2d_config()
        assert cfg.angle_degrees == 0.0

    def test_white_bg_sets_bw_palette(self, session_with_2d_defaults):
        from rendering.base import build_2d_config

        session_with_2d_defaults.session_state.preview_white_bg = True
        cfg = build_2d_config()
        assert cfg.use_bw_palette is True

    def test_with_session_overrides(self, session_with_2d_defaults):
        from rendering.base import build_2d_config

        session_with_2d_defaults.session_state.scale = 55.0
        cfg = build_2d_config()
        assert cfg.scale == 55.0


# ═══════════════════════════════════════════════════════════════════
# build_3d_config
# ═══════════════════════════════════════════════════════════════════


class TestBuild3DConfig:
    def test_builds_overrides_dict(self, session_with_3d_defaults):
        from rendering.base import build_3d_config

        result = build_3d_config()
        assert result["stick_radius"] == 0.2
        assert result["auto_orient_3d"] is True

    def test_includes_session_overrides(self, session_with_3d_defaults):
        from rendering.base import build_3d_config

        session_with_3d_defaults.session_state.stick_radius = 0.5
        result = build_3d_config()
        assert result["stick_radius"] == 0.5


# ═══════════════════════════════════════════════════════════════════
# generate_dynamic_filename
# ═══════════════════════════════════════════════════════════════════


class TestGenerateDynamicFilename:
    def test_basic_name(self):
        from rendering.base import generate_dynamic_filename

        result = generate_dynamic_filename("aspirin", "2D")
        assert result == "aspirin_2D"

    def test_sanitizes_spaces(self):
        from rendering.base import generate_dynamic_filename

        result = generate_dynamic_filename("acetyl salicylic acid", "2D")
        assert result == "acetyl_salicylic_acid_2D"

    def test_truncates_long_names(self):
        from rendering.base import generate_dynamic_filename

        long_name = "a" * 50
        result = generate_dynamic_filename(long_name, "3D")
        assert len(result) <= 50
        assert result.startswith("a" * 30)

    def test_fallback_to_structure_for_empty(self):
        from rendering.base import generate_dynamic_filename

        result = generate_dynamic_filename("@@@", "2D")
        assert result == "structure_2D"

    def test_special_chars_removed(self):
        from rendering.base import generate_dynamic_filename

        result = generate_dynamic_filename("benzene!!", "2D")
        assert result == "benzene_2D"


# ═══════════════════════════════════════════════════════════════════
# encode_image_to_base64
# ═══════════════════════════════════════════════════════════════════


class TestEncodeImageToBase64:
    def test_svg_encoding(self, tmp_path):
        from rendering.base import encode_image_to_base64

        svg_path = tmp_path / "test.svg"
        svg_path.write_text('<svg xmlns="http://www.w3.org/2000/svg"></svg>')
        b64, mime = encode_image_to_base64(svg_path)
        assert mime == "svg+xml"
        assert isinstance(b64, str)
        assert len(b64) > 0

    def test_png_encoding(self, tmp_path):
        from rendering.base import encode_image_to_base64

        png_path = tmp_path / "test.png"
        png_path.write_bytes(b"PNG binary data here")
        b64, mime = encode_image_to_base64(png_path)
        assert mime == "png"
        assert isinstance(b64, str)


# ═══════════════════════════════════════════════════════════════════
# _store_result_in_session
# ═══════════════════════════════════════════════════════════════════


class TestStoreResultInSession:
    def test_sets_all_session_keys(self, mock_st):
        from rendering.base import _store_result_in_session

        _store_result_in_session(
            image_html="<img>",
            compound="aspirin",
            file_data=b"data",
            file_name="aspirin_2D",
            file_mime="image/svg+xml",
        )
        ss = mock_st.session_state
        assert ss.last_image_html == "<img>"
        assert ss.last_compound == "aspirin"
        assert ss.last_file_data == b"data"
        assert ss.last_file_name == "aspirin_2D"
        assert ss.last_file_mime == "image/svg+xml"
        assert ss.rendered_structure is True


# ═══════════════════════════════════════════════════════════════════
# _build_image_html
# ═══════════════════════════════════════════════════════════════════


class TestBuildImageHtml:
    def test_returns_img_tag(self):
        from rendering.base import _build_image_html

        html = _build_image_html("abc123", "png", "3D")
        assert 'src="data:image/png;base64,abc123"' in html
        assert 'data-type="3D"' in html
        assert 'class="compound-preview-image"' in html

    def test_svg_mime_type(self):
        from rendering.base import _build_image_html

        html = _build_image_html("xyz", "svg+xml", "2D")
        assert "data:image/svg+xml;base64,xyz" in html


# ═══════════════════════════════════════════════════════════════════
# render_structure_dynamic
# ═══════════════════════════════════════════════════════════════════


class TestRenderStructureDynamic:
    @patch("rendering.base.render_structure_2d", return_value="<img>2d</img>")
    def test_delegates_to_2d(self, mock_r2d):
        from rendering.base import render_structure_dynamic

        result = render_structure_dynamic("aspirin", "2D")
        assert result == "<img>2d</img>"
        mock_r2d.assert_called_once_with("aspirin", "2D")

    @patch("rendering.base.render_structure_3d", return_value="<img>3d</img>")
    def test_delegates_to_3d(self, mock_r3d):
        from rendering.base import render_structure_dynamic

        result = render_structure_dynamic("aspirin", "3D")
        assert result == "<img>3d</img>"
        mock_r3d.assert_called_once_with("aspirin", "3D")

    def test_unknown_type_returns_none(self):
        from rendering.base import render_structure_dynamic

        result = render_structure_dynamic("aspirin", "Protein")
        assert result is None


# ═══════════════════════════════════════════════════════════════════
# get_download_data
# ═══════════════════════════════════════════════════════════════════


class TestGetDownloadData:
    def test_returns_svg_data(self, mock_st):
        from rendering.base import get_download_data

        ss = mock_st.session_state
        ss.last_file_data = b"svgdata"
        ss.last_file_name = "aspirin_2D"
        ss.last_file_mime = "image/svg+xml"

        data, name, mime = get_download_data()
        assert data == b"svgdata"
        assert ".svg" in name
        assert mime == "image/svg+xml"

    def test_returns_png_data(self, mock_st):
        from rendering.base import get_download_data

        ss = mock_st.session_state
        ss.last_file_data = b"pngdata"
        ss.last_file_name = "aspirin_3D"
        ss.last_file_mime = "image/png"

        data, name, mime = get_download_data()
        assert data == b"pngdata"
        assert ".png" in name
        assert mime == "image/png"

    def test_no_data_returns_none_tuple(self, mock_st):
        from rendering.base import get_download_data

        data, name, mime = get_download_data()
        assert data is None
        assert name is None
        assert mime is None


# ═══════════════════════════════════════════════════════════════════
# render_structure_2d (integrated with mocks)
# ═══════════════════════════════════════════════════════════════════


class TestRenderStructure2D:
    @patch("rendering.base.MoleculeGenerator2D")
    @patch("rendering.base.build_2d_config")
    @patch("rendering.base.encode_image_to_base64")
    def test_success_path(
        self,
        mock_encode,
        mock_build_config,
        MockGen2D,
        mock_st,
    ):
        from rendering.base import render_structure_2d

        mock_config = MagicMock()
        mock_build_config.return_value = mock_config
        mock_gen = MagicMock()
        MockGen2D.return_value = mock_gen
        mock_gen.draw.return_value = "output.svg"
        mock_encode.return_value = ("base64data", "svg+xml")

        # create the output file on disk
        svg_path = Path("output.svg")
        svg_path.write_text("<svg></svg>")

        try:
            result = render_structure_2d("aspirin", "2D")
            assert result is not None
            assert "base64data" in result
            mock_gen.draw.assert_called_once()
            MockGen2D.assert_called_once_with("aspirin", config=mock_config)
        finally:
            svg_path.unlink(missing_ok=True)

    @patch("rendering.base.MoleculeGenerator2D")
    def test_failure_returns_none(self, MockGen2D, mock_st):
        from rendering.base import render_structure_2d

        mock_gen = MagicMock()
        MockGen2D.return_value = mock_gen
        mock_gen.draw.return_value = None

        result = render_structure_2d("aspirin", "2D")
        assert result is None
        mock_st.error.assert_called()


# ═══════════════════════════════════════════════════════════════════
# render_structure_3d (integrated with mocks)
# ═══════════════════════════════════════════════════════════════════


class TestRenderStructure3D:
    @patch("rendering.base.MoleculeGenerator3D")
    @patch("rendering.base.build_3d_config")
    @patch("rendering.base.encode_image_to_base64")
    def test_render_only_path(
        self,
        mock_encode,
        mock_build_config,
        MockGen3D,
        session_with_3d_defaults,
    ):
        from rendering.base import render_structure_3d

        mock_build_config.return_value = {"stick_radius": 0.2}
        mock_gen = MagicMock()
        MockGen3D.return_value = mock_gen
        mock_gen.render_only.return_value = "output.png"
        mock_encode.return_value = ("base64data", "png")

        ss = session_with_3d_defaults.session_state
        ss.sdf_content = "SDF content here"
        ss.last_compound = "aspirin"

        png_path = Path("output.png")
        png_path.write_bytes(b"PNG data")

        try:
            result = render_structure_3d("aspirin", "3D")
            assert result is not None
            mock_gen.render_only.assert_called_once()
        finally:
            png_path.unlink(missing_ok=True)

    @patch("rendering.base.MoleculeGenerator3D")
    @patch("rendering.base.build_3d_config")
    @patch("rendering.base.encode_image_to_base64")
    def test_generate_path(
        self,
        mock_encode,
        mock_build_config,
        MockGen3D,
        session_with_3d_defaults,
    ):
        from rendering.base import render_structure_3d

        mock_build_config.return_value = {"stick_radius": 0.2}
        mock_gen = MagicMock()
        MockGen3D.return_value = mock_gen
        mock_gen.generate.return_value = ("output.sdf", "output.png")
        mock_encode.return_value = ("base64data", "png")

        ss = session_with_3d_defaults.session_state
        ss.last_compound = "different_compound"
        ss.sdf_content = ""

        sdf_path = Path("output.sdf")
        sdf_path.write_text("SDF content")
        png_path = Path("output.png")
        png_path.write_bytes(b"PNG data")

        try:
            result = render_structure_3d("aspirin", "3D")
            assert result is not None
            mock_gen.generate.assert_called_once()
        finally:
            sdf_path.unlink(missing_ok=True)
            png_path.unlink(missing_ok=True)
