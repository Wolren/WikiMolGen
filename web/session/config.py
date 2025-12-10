"""
web/session/config.py

Session management for web UI with config persistence.
Handles template selection and user changes
"""

import json
from typing import Optional, Dict, Any, Literal
from datetime import datetime
from pathlib import Path
import logging

# Import from core package (OK - web depends on core)
from wikimolgen.configs import ConfigLoader

logger = logging.getLogger(__name__)


class ConfigSessionManager:
    """
    """

    def __init__(self, config_type: Literal["2d", "3d", "protein"] = "2d"):
        """
        Initialize manager.

        Parameters
        ----------
        config_type : {"2d", "3d", "protein"}
            Type of configuration to manage
        """
        self.config_type = config_type
        self.metadata_key = "_metadata"
        logger.info(f"ConfigSessionManager initialized for {config_type}")

    def load_template(self, template_name: str):
        """
        Load predefined template using core ConfigLoader.

        Parameters
        ----------
        template_name : str
            Name of template (e.g., "publication_2d")

        Returns
        -------
        Config2D, Config3D, or ConfigProtein
            Loaded template

        Raises
        ------
        FileNotFoundError
            If template doesn't exist
        """
        cfg = ConfigLoader.load_template(template_name)
        logger.info(f"Loaded template: {template_name}")
        return cfg

    def export_to_file(self, config, filepath: str) -> str:
        """
        Export config to JSON file.

        Useful for letting users download their settings.

        Parameters
        ----------
        config : Config2D, Config3D, or ConfigProtein
            Configuration to export
        filepath : str
            Output file path

        Returns
        -------
        str
            Path to exported file
        """
        path = Path(filepath)
        path.parent.mkdir(parents=True, exist_ok=True)

        data = {
            "config": config.to_dict(),
            "type": self.config_type,
            self.metadata_key: {
                "exported_at": datetime.now().isoformat(),
                "version": "1.0",
            }
        }

        with open(path, 'w') as f:
            json.dump(data, f, indent=2)

        logger.info(f"Exported config to {path}")
        return str(path)

    def import_from_file(self, filepath: str):
        """
        Import config from JSON file.

        Useful for letting users upload saved settings.

        Parameters
        ----------
        filepath : str
            Input file path

        Returns
        -------
        Config2D, Config3D, or ConfigProtein
            Imported configuration

        Raises
        ------
        FileNotFoundError
            If file doesn't exist
        json.JSONDecodeError
            If JSON is invalid
        """
        path = Path(filepath)

        if not path.exists():
            raise FileNotFoundError(f"Config file not found: {path}")

        with open(path, 'r') as f:
            data = json.load(f)

        config_dict = data.get("config", {})
        cfg = self._get_config_with_overrides(config_dict)

        logger.info(f"Imported config from {path}")
        return cfg

    def compare_configs(self, cfg1, cfg2) -> Dict[str, Any]:
        """
        Compare two configs and return differences.

        Useful for showing what changed.

        Parameters
        ----------
        cfg1 : Config2D, Config3D, or ConfigProtein
            First configuration
        cfg2 : Config2D, Config3D, or ConfigProtein
            Second configuration

        Returns
        -------
        dict
            Differences mapping {key: {"old": value1, "new": value2}}
        """
        dict1 = cfg1.to_dict()
        dict2 = cfg2.to_dict()

        differences = {}

        for key in set(list(dict1.keys()) + list(dict2.keys())):
            val1 = dict1.get(key)
            val2 = dict2.get(key)

            if val1 != val2:
                differences[key] = {
                    "old": val1,
                    "new": val2,
                }

        return differences

    def merge_configs(self, base_config, user_overrides: Dict[str, Any]):
        """
        Merge user overrides with base config.

        Useful for applying partial updates.

        Parameters
        ----------
        base_config : Config2D, Config3D, or ConfigProtein
            Base configuration
        user_overrides : dict
            User modifications to merge

        Returns
        -------
        Config2D, Config3D, or ConfigProtein
            Merged configuration
        """
        merged = base_config.to_dict()
        merged.update(user_overrides)

        cfg = self._get_config_with_overrides(merged)
        logger.info(f"Merged config with {len(user_overrides)} overrides")
        return cfg

    def _get_default_config(self):
        """Get default config for configured type."""
        if self.config_type == "2d":
            return ConfigLoader.get_2d_config()
        elif self.config_type == "3d":
            return ConfigLoader.get_3d_config()
        elif self.config_type == "protein":
            return ConfigLoader.get_protein_config()
        else:
            raise ValueError(f"Unknown config type: {self.config_type}")

    def _get_config_with_overrides(self, overrides: Dict[str, Any]):
        """Get config with overrides applied."""
        if self.config_type == "2d":
            return ConfigLoader.get_2d_config(overrides=overrides)
        elif self.config_type == "3d":
            return ConfigLoader.get_3d_config(overrides=overrides)
        elif self.config_type == "protein":
            return ConfigLoader.get_protein_config(overrides=overrides)
        else:
            raise ValueError(f"Unknown config type: {self.config_type}")
