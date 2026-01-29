"""Settings manager for configuration persistence"""

import os
import yaml
from pathlib import Path
from typing import Any, Optional
from copy import deepcopy

from .defaults import DEFAULT_SETTINGS


class SettingsManager:
    """Manages application settings with YAML persistence"""
    
    def __init__(self, config_dir: Optional[Path] = None):
        if config_dir is None:
            config_dir = Path.home() / "MeetingAssistant" / "config"
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(parents=True, exist_ok=True)
        self.settings_file = self.config_dir / "settings.yaml"
        self._settings = deepcopy(DEFAULT_SETTINGS)
        self._load()
    
    def _load(self) -> None:
        """Load settings from file, merging with defaults"""
        if self.settings_file.exists():
            try:
                with open(self.settings_file, 'r') as f:
                    user_settings = yaml.safe_load(f) or {}
                self._deep_merge(self._settings, user_settings)
            except Exception as e:
                print(f"Warning: Failed to load settings: {e}")
    
    def _deep_merge(self, base: dict, override: dict) -> None:
        """Recursively merge override into base"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._deep_merge(base[key], value)
            else:
                base[key] = value
    
    def save(self) -> None:
        """Save current settings to file"""
        with open(self.settings_file, 'w') as f:
            yaml.dump(self._settings, f, default_flow_style=False, sort_keys=False)
    
    def get(self, *keys: str, default: Any = None) -> Any:
        """Get a nested setting value using dot notation or multiple keys"""
        if len(keys) == 1 and '.' in keys[0]:
            keys = tuple(keys[0].split('.'))
        
        value = self._settings
        for key in keys:
            if isinstance(value, dict) and key in value:
                value = value[key]
            else:
                return default
        return value
    
    def set(self, *args) -> None:
        """Set a nested setting value"""
        if len(args) < 2:
            raise ValueError("Need at least key and value")
        
        *keys, value = args
        if len(keys) == 1 and '.' in keys[0]:
            keys = keys[0].split('.')
        
        target = self._settings
        for key in keys[:-1]:
            if key not in target:
                target[key] = {}
            target = target[key]
        target[keys[-1]] = value
    
    @property
    def all(self) -> dict:
        """Return all settings"""
        return deepcopy(self._settings)
    
    def get_log_dir(self) -> Path:
        """Get resolved log directory path"""
        log_dir = Path(os.path.expanduser(self.get('logging', 'log_dir')))
        log_dir.mkdir(parents=True, exist_ok=True)
        return log_dir
