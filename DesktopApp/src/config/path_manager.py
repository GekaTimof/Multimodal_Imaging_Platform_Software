"""
Path Manager for Desktop Application
Handles all file paths for saving and loading operations without hardcoding.
Provides centralized path management for different file types and operations.
"""

import logging
import os
import json
import sys
from typing import Dict, Any, Optional
from services.directory_control import get_home_directory

logger = logging.getLogger(__name__)


class PathManager:
    """Centralized path management for file operations."""
    
    DEFAULT_PATHS = {
        "file_operations": {
            "photo": {
                "default_save_dir": "",
                "filename_template": "camera_snapshot_{timestamp}.png",
                "format": "PNG",
                "allowed_formats": ["PNG", "JPG", "JPEG", "BMP", "TIFF"],
                "create_subdirs": False,
                "subdir_format": "{date}"
            },
            "spectrum": {
                "default_save_dir": "",
                "filename_template": "spectrum_{timestamp}.txt",
                "format": "TXT",
                "allowed_formats": ["TXT", "CSV", "JSON"],
                "create_subdirs": False,
                "subdir_format": "{date}"
            },
            "Acquisition": {
                "default_save_dir": "",
                "filename_template": "Acquisition_analysis_{timestamp}.csv",
                "format": "CSV",
                "allowed_formats": ["CSV", "XLSX", "JSON"],
                "create_subdirs": False,
                "subdir_format": "{date}"
            },
            "logs": {
                "default_save_dir": "",
                "filename_template": "app_log_{date}.txt",
                "format": "TXT",
                "max_log_files": 10
            }
        },
        "path_validation": {
            "require_home_subdir": True,
            "allowed_base_dirs": ["home", "downloads", "documents", "desktop", "app_data"],
            "max_path_length": 255,
            "forbidden_chars": ["<", ">", ":", "\"", "|", "?", "*"]
        }
    }
    
    def __init__(self, config_file: Optional[str] = None):
        """
        Initialize path manager.
        
        Args:
            config_file: Path to paths config file. If None, uses default location.
        """
        if config_file is None:
            config_file = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "resources", "paths_config.json")
        
        self.config_file = config_file
        self._ensure_config_dir()
        self.paths = self._load_paths()
    
    def _ensure_config_dir(self):
        """Ensure config directory exists."""
        config_dir = os.path.dirname(self.config_file)
        os.makedirs(config_dir, exist_ok=True)
    
    def _load_paths(self) -> Dict[str, Any]:
        """Load paths configuration from file or create default."""
        if os.path.exists(self.config_file):
            try:
                with open(self.config_file, 'r', encoding='utf-8') as f:
                    loaded_paths = json.load(f)
                # Merge with defaults
                return self._merge_configs(self.DEFAULT_PATHS, loaded_paths)
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"Error loading paths config, using defaults: {e}")
                return self.DEFAULT_PATHS.copy()
        else:
            # Create default config file
            self._save_paths(self.DEFAULT_PATHS)
            return self.DEFAULT_PATHS.copy()
    
    def _merge_configs(self, default: Dict, loaded: Dict) -> Dict:
        """Merge loaded config with defaults."""
        result = default.copy()
        for key, value in loaded.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._merge_configs(result[key], value)
            else:
                result[key] = value
        return result
    
    def _save_paths(self, paths: Dict[str, Any]):
        """Save paths configuration to file."""
        try:
            with open(self.config_file, 'w', encoding='utf-8') as f:
                json.dump(paths, f, indent=4, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving paths config: {e}")
    
    def get_save_directory(self, operation: str) -> str:
        """
        Get configured save directory for specific operation.

        Args:
            operation: Operation type ('photo', 'spectrometer', 'Acquisition')

        Returns:
            Save directory path

        Raises:
            ValueError: If no save directory has been configured for the operation
        """
        save_dir = self.get_configured_save_directory(operation)
        if not save_dir:
            raise ValueError(f"No save directory configured for '{operation}'. "
                             f"Please set it in File Settings.")
        return save_dir
    
    def get_configured_save_directory(self, operation: str) -> str:
        """Return only the stored directory path, without fallback or makedirs.
        
        Returns empty string if no directory has been configured yet.
        """
        file_ops = self.paths.get('file_operations', {})
        save_dir = file_ops.get(operation, {}).get('default_save_dir', '')
        if save_dir:
            is_valid, reason = self.validate_directory(save_dir)
            if not is_valid:
                logger.warning(f"Ignoring invalid saved directory for '{operation}': {reason}")
                return ''
        return save_dir

    def set_save_directory(self, operation: str, directory: str):
        """
        Set save directory for specific operation.
        
        Args:
            operation: Operation type ('photo', 'spectrometer', 'Acquisition')
            directory: Directory path
        """
        is_valid, reason = self.validate_directory(directory)
        if not is_valid:
            raise ValueError(reason)
        if 'file_operations' not in self.paths:
            self.paths['file_operations'] = {}
        if operation not in self.paths['file_operations']:
            self.paths['file_operations'][operation] = {}
        self.paths['file_operations'][operation]['default_save_dir'] = directory
        self._save_paths(self.paths)
    
    def validate_directory(self, path: str) -> tuple:
        """Validate a directory path and return (is_valid: bool, reason: str).

        Checks (in order):
        1. Not empty
        2. No forbidden characters
        3. Does not exceed max path length
        4. Must be inside the user home directory
        5. The directory actually exists on disk
        """
        if not path or not path.strip():
            return False, "Path is empty"

        validation = self.paths.get('path_validation', {})

        check_path = path
        if sys.platform == "win32" and len(path) >= 2 and path[1] == ":":
            check_path = path[2:]
        forbidden_chars = validation.get('forbidden_chars', [])
        for char in forbidden_chars:
            if char in check_path:
                return False, f"Path contains forbidden character: '{char}'"

        max_length = validation.get('max_path_length', 255)
        if len(path) > max_length:
            return False, f"Path exceeds maximum length of {max_length} characters"

        if validation.get('require_home_subdir', True):
            home_dir = get_home_directory()
            from services.directory_control import is_path_inside
            if not is_path_inside(path, home_dir):
                return False, f"Path must be inside the home directory: {home_dir}"

        if not os.path.isdir(path):
            return False, f"Directory does not exist: {path}"

        return True, ""

    def reset_to_defaults(self):
        """Reset all paths to defaults."""
        self.paths = self.DEFAULT_PATHS.copy()
        self._save_paths(self.paths)


# Global instance
path_manager = PathManager()
