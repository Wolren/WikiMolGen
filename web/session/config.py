import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

from wikimolgen.configs import ConfigLoader

logger = logging.getLogger(__name__)


class ConfigSessionManager:
    def __init__(self, config_type: Literal["2d", "3d"] = "2d"):
        self.config_type = config_type
        self.metadata_key = "_metadata"

    def load_template(self, template_name: str):
        cfg = ConfigLoader.load_template(template_name)
        logger.info(f"Loaded template: {template_name}")
        return cfg

    def _safe_path(self, filepath: str) -> Path:
        path = Path(filepath)
        if ".." in path.parts:
            raise ValueError(f"Path traversal detected: {filepath}")
        return path.resolve()

    def export_to_file(self, config, filepath: str) -> str:
        path = self._safe_path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "config": config.to_dict(),
            "type": self.config_type,
            self.metadata_key: {
                "exported_at": datetime.now().isoformat(),
                "version": "1.0",
            },
        }

        with open(path, "w") as f:
            json.dump(data, f, indent=2)

        return str(path)

    def import_from_file(self, filepath: str):
        path = self._safe_path(filepath)
        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")
        with open(path) as f:
            data = json.load(f)
        config_dict = data.get("config", {})
        return self._get_config_with_overrides(config_dict)

    def compare_configs(self, cfg1, cfg2) -> dict[str, Any]:
        dict1 = cfg1.to_dict() if hasattr(cfg1, "to_dict") else cfg1
        dict2 = cfg2.to_dict() if hasattr(cfg2, "to_dict") else cfg2

        differences = {}
        all_keys = set(
            list(dict1.keys()) + list(dict2.keys())
            if isinstance(dict1, dict) and isinstance(dict2, dict)
            else []
        )
        for key in all_keys:
            val1 = dict1.get(key) if isinstance(dict1, dict) else None
            val2 = dict2.get(key) if isinstance(dict2, dict) else None
            if val1 != val2:
                differences[key] = {"old": val1, "new": val2}
        return differences

    def merge_configs(self, base_config, user_overrides: dict[str, Any]):
        merged = base_config.to_dict()
        merged.update(user_overrides)
        return self._get_config_with_overrides(merged)

    def _get_default_config(self):
        if self.config_type == "2d":
            return ConfigLoader.get_2d_config()
        elif self.config_type == "3d":
            return ConfigLoader.get_3d_config()
        raise ValueError(f"Unknown config type: {self.config_type}")

    def _get_config_with_overrides(self, overrides: dict[str, Any]):
        if self.config_type == "2d":
            return ConfigLoader.get_2d_config(overrides=overrides)
        elif self.config_type == "3d":
            return ConfigLoader.get_3d_config(overrides=overrides)
        raise ValueError(f"Unknown config type: {self.config_type}")
