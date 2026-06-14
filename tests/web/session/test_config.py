from __future__ import annotations

import json
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from session.config import ConfigSessionManager


# ═══════════════════════════════════════════════════════════════════
# Fixtures
# ═══════════════════════════════════════════════════════════════════


@pytest.fixture
def manager_2d() -> ConfigSessionManager:
    return ConfigSessionManager(config_type="2d")


@pytest.fixture
def manager_3d() -> ConfigSessionManager:
    return ConfigSessionManager(config_type="3d")


class _MockConfig:
    def __init__(self, **kwargs):
        self._data = kwargs

    def to_dict(self) -> dict:
        return dict(self._data)


# ═══════════════════════════════════════════════════════════════════
# __init__
# ═══════════════════════════════════════════════════════════════════


class TestInit:
    def test_default_config_type(self):
        mgr = ConfigSessionManager()
        assert mgr.config_type == "2d"

    def test_explicit_config_type(self):
        mgr = ConfigSessionManager(config_type="3d")
        assert mgr.config_type == "3d"


# ═══════════════════════════════════════════════════════════════════
# _safe_path
# ═══════════════════════════════════════════════════════════════════


class TestSafePath:
    def test_normal_path(self, manager_2d: ConfigSessionManager):
        result = manager_2d._safe_path(__file__)
        assert isinstance(result, Path)
        assert result.is_absolute()

    def test_relative_path_resolves(self, manager_2d: ConfigSessionManager):
        result = manager_2d._safe_path("test_config.py")
        assert result.is_absolute()
        assert result.name == "test_config.py"

    def test_path_with_dotdot_raises_value_error(self, manager_2d: ConfigSessionManager):
        with pytest.raises(ValueError, match="Path traversal detected"):
            manager_2d._safe_path("../../etc/passwd")

    def test_path_with_backslash_dotdot_raises_value_error(self, manager_2d: ConfigSessionManager):
        with pytest.raises(ValueError, match="Path traversal detected"):
            manager_2d._safe_path("..\\..\\etc")

    def test_simple_filename_resolves_to_cwd(self, manager_2d: ConfigSessionManager):
        result = manager_2d._safe_path("some_file.txt")
        assert result.name == "some_file.txt"
        assert result.parent == Path.cwd()


# ═══════════════════════════════════════════════════════════════════
# export_to_file
# ═══════════════════════════════════════════════════════════════════


class TestExportToFile:
    def test_writes_valid_json(self, manager_2d: ConfigSessionManager):
        config = _MockConfig(foo=1, bar="baz")
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            tmp = f.name

        try:
            manager_2d.export_to_file(config, tmp)
            with open(tmp) as f:
                data = json.load(f)
            assert data["config"] == {"foo": 1, "bar": "baz"}
            assert data["type"] == "2d"
            assert "_metadata" in data
            assert data["_metadata"]["version"] == "1.0"
        finally:
            os.unlink(tmp)

    def test_returns_correct_path(self, manager_2d: ConfigSessionManager):
        config = _MockConfig()
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "out.json")
            result = manager_2d.export_to_file(config, filepath)
            assert result == str(Path(filepath).resolve())
            assert os.path.isfile(filepath)

    def test_creates_parent_directories(self, manager_2d: ConfigSessionManager):
        config = _MockConfig()
        with tempfile.TemporaryDirectory() as tmpdir:
            nested = os.path.join(tmpdir, "a", "b", "c", "out.json")
            manager_2d.export_to_file(config, nested)
            assert os.path.isfile(nested)

    def test_includes_metadata(self, manager_2d: ConfigSessionManager):
        config = _MockConfig(x=10)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            tmp = f.name

        try:
            manager_2d.export_to_file(config, tmp)
            with open(tmp) as f:
                data = json.load(f)
            assert "exported_at" in data["_metadata"]
        finally:
            os.unlink(tmp)


# ═══════════════════════════════════════════════════════════════════
# import_from_file
# ═══════════════════════════════════════════════════════════════════


class TestImportFromFile:
    def test_reads_exported_file(self, manager_2d: ConfigSessionManager):
        config = _MockConfig(scale=42.0, margin=0.5)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            tmp = f.name

        try:
            manager_2d.export_to_file(config, tmp)

            with patch.object(
                manager_2d, "_get_config_with_overrides", return_value={"scale": 42.0}
            ) as mock_get:
                result = manager_2d.import_from_file(tmp)
                mock_get.assert_called_once_with({"scale": 42.0, "margin": 0.5})
                assert result == {"scale": 42.0}
        finally:
            os.unlink(tmp)

    def test_file_not_found_error(self, manager_2d: ConfigSessionManager):
        with pytest.raises(FileNotFoundError, match="Config file not found"):
            manager_2d.import_from_file("C:/nonexistent_dir_xyzzy/config.json")


# ═══════════════════════════════════════════════════════════════════
# compare_configs
# ═══════════════════════════════════════════════════════════════════


class TestCompareConfigs:
    def test_identical_configs_return_empty(self, manager_2d: ConfigSessionManager):
        cfg1 = _MockConfig(a=1, b=2)
        cfg2 = _MockConfig(a=1, b=2)
        assert manager_2d.compare_configs(cfg1, cfg2) == {}

    def test_different_configs_show_differences(self, manager_2d: ConfigSessionManager):
        cfg1 = _MockConfig(a=1, b=2, c=3)
        cfg2 = _MockConfig(a=1, b=99, d=4)
        diff = manager_2d.compare_configs(cfg1, cfg2)
        assert diff["b"] == {"old": 2, "new": 99}
        assert diff["c"] == {"old": 3, "new": None}
        assert diff["d"] == {"old": None, "new": 4}
        assert len(diff) == 3

    def test_accepts_plain_dicts(self, manager_2d: ConfigSessionManager):
        assert manager_2d.compare_configs({"x": 1}, {"x": 1}) == {}
        diff = manager_2d.compare_configs({"x": 1}, {"x": 2})
        assert diff == {"x": {"old": 1, "new": 2}}

    def test_empty_configs_return_empty(self, manager_2d: ConfigSessionManager):
        assert manager_2d.compare_configs({}, {}) == {}


# ═══════════════════════════════════════════════════════════════════
# merge_configs
# ═══════════════════════════════════════════════════════════════════


class TestMergeConfigs:
    def test_overrides_applied(self, manager_2d: ConfigSessionManager):
        base = _MockConfig(a=1, b=2, c=3)
        overrides = {"b": 99, "d": 4}

        with patch.object(
            manager_2d, "_get_config_with_overrides", return_value={"a": 1, "b": 99, "d": 4}
        ) as mock_get:
            result = manager_2d.merge_configs(base, overrides)
            mock_get.assert_called_once_with({"a": 1, "b": 99, "c": 3, "d": 4})
            assert result == {"a": 1, "b": 99, "d": 4}

    def test_base_values_preserved_when_not_overridden(self, manager_2d: ConfigSessionManager):
        base = _MockConfig(a=1, b=2)
        overrides = {"b": 99}

        with patch.object(
            manager_2d, "_get_config_with_overrides", return_value={"a": 1, "b": 99}
        ) as mock_get:
            result = manager_2d.merge_configs(base, overrides)
            mock_get.assert_called_once_with({"a": 1, "b": 99})
            assert result == {"a": 1, "b": 99}

    def test_empty_overrides_returns_base_copy(self, manager_2d: ConfigSessionManager):
        base = _MockConfig(a=1, b=2)

        with patch.object(
            manager_2d, "_get_config_with_overrides", return_value={"a": 1, "b": 2}
        ) as mock_get:
            result = manager_2d.merge_configs(base, {})
            mock_get.assert_called_once_with({"a": 1, "b": 2})
            assert result == {"a": 1, "b": 2}


# ═══════════════════════════════════════════════════════════════════
# load_template
# ═══════════════════════════════════════════════════════════════════


class TestLoadTemplate:
    def test_delegates_to_config_loader(self, manager_2d: ConfigSessionManager):
        mock_result = MagicMock()
        with patch(
            "session.config.ConfigLoader.load_template", return_value=mock_result
        ) as mock_load:
            result = manager_2d.load_template("publication_2d")
            mock_load.assert_called_once_with("publication_2d")
            assert result is mock_result

    def test_passes_through_template_name(self, manager_3d: ConfigSessionManager):
        mock_result = MagicMock()
        with patch(
            "session.config.ConfigLoader.load_template", return_value=mock_result
        ) as mock_load:
            manager_3d.load_template("high_quality_3d")
            mock_load.assert_called_once_with("high_quality_3d")
