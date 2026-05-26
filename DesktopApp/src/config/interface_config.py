"""
Interface Configuration Manager
Handles all interface-related settings without hardcoding values.
Provides centralized configuration management for themes, languages,
window settings, and other UI preferences.
"""

import json
import logging
import os
from typing import Dict, Any, Optional

logger = logging.getLogger(__name__)


class InterfaceConfig:
    """Centralized interface configuration manager."""
    
    DEFAULT_CONFIG = {
        "window": {
            "title": "Lab App",
            "width": 1400,
            "height": 800,
            "start_maximized": True,
            "resizable": True
        },
        "theme": {
            "default": "light",
            "available_themes": ["light", "dark"],
            "auto_switch": False
        },
        "language": {
            "default": "English",
            "available_languages": ["English", "Russian"],
            "auto_detect": False
        },
        "tabs": {
            "default_tab": 0,
            "remember_last_tab": True,
            "tab_positions": ["spectrometer", "camera", "Acquisition"]
        },
        "ui_behavior": {
            "confirmations": True,
            "tooltips": True,
            "animations": True,
            "auto_save": True
        },
        "ui_scaling": {
            "font_family": "DejaVu Sans",
            "font_point_size": 11,
            "status_bar_height": 52,
            "side_panel_min_width": 320
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize interface configuration manager.
        
        Args:
            config_file: Path to config file. If None, uses default location.
        """
        if config_file is None:
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "resources", "interface_settings.json")
        
        self.config_file = config_file
        self._ensure_config_dir()
        self.config = self._load_config()
    
    def _ensure_config_dir(self):
        """Ensure config directory exists."""
        config_dir = os.path.dirname(self.config_file)
        os.makedirs(config_dir, exist_ok=True)
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from file or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_config = json.load(f)
                # Merge with defaults to ensure all keys exist
                return self._merge_configs(self.DEFAULT_CONFIG, loaded_config)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Error loading config, using defaults: {e}")
                return self.DEFAULT_CONFIG.copy()
        else:
            # Create default config file
            self._save_config(self.DEFAULT_CONFIG)
            return self.DEFAULT_CONFIG.copy()
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Merge loaded config with defaults, preserving new keys."""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _save_config(self, config: Dict[str, Any]):
        """Save configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving config: {e}")
    
    def get(self, key_path: str, default=None):
        """
        Get configuration value by key path (e.g., 'window.title').
        
        Args:
            key_path: Dot-separated path to config value
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        keys = key_path.split('.')
        value = self.config
        
        try:
            for key in keys:
                value = value[key]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key_path: str, value: Any):
        """
        Set configuration value by key path.
        
        Args:
            key_path: Dot-separated path to config value
            value: Value to set
        """
        keys = key_path.split('.')
        config = self.config
        
        # Navigate to parent of target key
        for key in keys[:-1]:
            if key not in config:
                config[key] = {}
            config = config[key]
        
        # Set the value
        config[keys[-1]] = value
        self._save_config(self.config)
    
    def get_window_config(self) -> Dict[str, Any]:
        """Get window configuration."""
        return self.get('window', {})
    
    def get_theme_config(self) -> Dict[str, Any]:
        """Get theme configuration."""
        return self.get('theme', {})
    
    def get_language_config(self) -> Dict[str, Any]:
        """Get language configuration."""
        return self.get('language', {})
    
    def get_tabs_config(self) -> Dict[str, Any]:
        """Get tabs configuration."""
        return self.get('tabs', {})
    
    def get_ui_behavior_config(self) -> Dict[str, Any]:
        """Get UI behavior configuration."""
        return self.get('ui_behavior', {})
    
    def is_theme_available(self, theme: str) -> bool:
        """Check if theme is available."""
        available_themes = self.get('theme.available_themes', [])
        return theme in available_themes
    
    def is_language_available(self, language: str) -> bool:
        """Check if language is available."""
        available_languages = self.get('language.available_languages', [])
        return language in available_languages
    
    def set_theme(self, theme: str):
        """Set current theme if available."""
        if self.is_theme_available(theme):
            self.set('theme.default', theme)
        else:
            raise ValueError(f"Theme '{theme}' not available")
    
    def set_language(self, language: str):
        """Set current language if available."""
        if self.is_language_available(language):
            self.set('language.default', language)
        else:
            raise ValueError(f"Language '{language}' not available")
    
    def reset_to_defaults(self):
        """Reset all configuration to defaults."""
        self.config = self.DEFAULT_CONFIG.copy()
        self._save_config(self.config)


# Global instance
interface_config = InterfaceConfig()
