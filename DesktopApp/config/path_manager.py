"""
Path Manager for Desktop Application
Handles all file paths for saving and loading operations without hardcoding.
Provides centralized path management for different file types and operations.
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, Optional, List
from DesktopApp.services.directory_control import get_home_directory


class PathManager:
    """Centralized path management for file operations."""
    
    DEFAULT_PATHS = {
        "base_directories": {
            "home": get_home_directory(),
            "downloads": os.path.join(get_home_directory(), "Downloads"),
            "documents": os.path.join(get_home_directory(), "Documents"),
            "desktop": os.path.join(get_home_directory(), "Desktop"),
            "app_data": os.path.join(get_home_directory(), ".lab_app_data")
        },
        "file_operations": {
            "photo": {
                "default_save_dir": "",
                "filename_template": "camera_snapshot_{timestamp}.png",
                "format": "PNG",
                "allowed_formats": ["PNG", "JPG", "JPEG", "BMP", "TIFF"],
                "create_subdirs": False,
                "subdir_format": "{date}"
            },
            "spectrometer": {
                "default_save_dir": "",
                "filename_template": "spectrum_{timestamp}.txt",
                "format": "TXT",
                "allowed_formats": ["TXT", "CSV", "JSON"],
                "create_subdirs": False,
                "subdir_format": "{date}"
            },
            "wells": {
                "default_save_dir": "",
                "filename_template": "wells_analysis_{timestamp}.csv",
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
            config_file = os.path.join(os.path.dirname(__file__), "..", "config", "paths_config.json")
        
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
                print(f"Error loading paths config, using defaults: {e}")
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
            print(f"Error saving paths config: {e}")
    
    def get_base_directory(self, dir_name: str) -> str:
        """
        Get base directory path.
        
        Args:
            dir_name: Name of base directory ('home', 'downloads', etc.)
            
        Returns:
            Full path to base directory
        """
        base_dirs = self.paths.get('base_directories', {})
        path = base_dirs.get(dir_name, get_home_directory())
        
        # Ensure directory exists
        os.makedirs(path, exist_ok=True)
        return path
    
    def get_save_directory(self, operation: str) -> str:
        """
        Get save directory for specific operation.
        
        Args:
            operation: Operation type ('photo', 'spectrometer', 'wells')
            
        Returns:
            Save directory path
        """
        file_ops = self.paths.get('file_operations', {})
        op_config = file_ops.get(operation, {})
        save_dir = op_config.get('default_save_dir', '')
        
        if not save_dir:
            # Use default base directory
            if operation == 'photo':
                save_dir = self.get_base_directory('downloads')
            else:
                save_dir = self.get_base_directory('documents')
        
        # Ensure directory exists
        os.makedirs(save_dir, exist_ok=True)
        return save_dir
    
    def set_save_directory(self, operation: str, directory: str):
        """
        Set save directory for specific operation.
        
        Args:
            operation: Operation type ('photo', 'spectrometer', 'wells')
            directory: Directory path
        """
        if self.validate_path(directory):
            if 'file_operations' not in self.paths:
                self.paths['file_operations'] = {}
            if operation not in self.paths['file_operations']:
                self.paths['file_operations'][operation] = {}
            
            self.paths['file_operations'][operation]['default_save_dir'] = directory
            self._save_paths(self.paths)
        else:
            raise ValueError(f"Invalid path: {directory}")
    
    def generate_filename(self, operation: str, custom_template: Optional[str] = None) -> str:
        """
        Generate filename for operation using template.
        
        Args:
            operation: Operation type
            custom_template: Custom filename template (overrides default)
            
        Returns:
            Generated filename
        """
        file_ops = self.paths.get('file_operations', {})
        op_config = file_ops.get(operation, {})
        
        template = custom_template or op_config.get('filename_template', 'file_{timestamp}.txt')
        file_format = op_config.get('format', 'txt')
        
        # Prepare template variables
        now = datetime.now()
        variables = {
            'timestamp': now.strftime('%Y%m%d_%H%M%S'),
            'date': now.strftime('%Y%m%d'),
            'time': now.strftime('%H%M%S'),
            'datetime': now.strftime('%Y-%m-%d_%H-%M-%S'),
            'year': now.strftime('%Y'),
            'month': now.strftime('%m'),
            'day': now.strftime('%d'),
            'hour': now.strftime('%H'),
            'minute': now.strftime('%M'),
            'second': now.strftime('%S')
        }
        
        try:
            filename = template.format(**variables)
        except KeyError as e:
            print(f"Template variable not found: {e}")
            filename = f"file_{variables['timestamp']}.{file_format.lower()}"
        
        # Ensure correct extension
        if not filename.lower().endswith(f'.{file_format.lower()}'):
            filename = f"{filename}.{file_format.lower()}"
        
        return filename
    
    def get_full_path(self, operation: str, custom_template: Optional[str] = None) -> str:
        """
        Get full file path for operation.
        
        Args:
            operation: Operation type
            custom_template: Custom filename template
            
        Returns:
            Full file path
        """
        save_dir = self.get_save_directory(operation)
        filename = self.generate_filename(operation, custom_template)
        
        # Check if subdirectories should be created
        file_ops = self.paths.get('file_operations', {})
        op_config = file_ops.get(operation, {})
        
        if op_config.get('create_subdirs', False):
            subdir_format = op_config.get('subdir_format', '{date}')
            try:
                now = datetime.now()
                subdir = subdir_format.format(
                    date=now.strftime('%Y%m%d'),
                    year=now.strftime('%Y'),
                    month=now.strftime('%m'),
                    day=now.strftime('%d')
                )
                save_dir = os.path.join(save_dir, subdir)
                os.makedirs(save_dir, exist_ok=True)
            except KeyError:
                pass  # Use main directory if template fails
        
        return os.path.join(save_dir, filename)
    
    def validate_path(self, path: str) -> bool:
        """
        Validate path according to configuration rules.
        
        Args:
            path: Path to validate
            
        Returns:
            True if path is valid
        """
        validation = self.paths.get('path_validation', {})
        
        # Check forbidden characters
        forbidden_chars = validation.get('forbidden_chars', [])
        for char in forbidden_chars:
            if char in path:
                return False
        
        # Check path length
        max_length = validation.get('max_path_length', 255)
        if len(path) > max_length:
            return False
        
        # Check if path must be under home directory
        if validation.get('require_home_subdir', True):
            home_dir = get_home_directory()
            if not os.path.abspath(path).startswith(os.path.abspath(home_dir)):
                return False
        
        return True
    
    def get_allowed_formats(self, operation: str) -> List[str]:
        """Get allowed file formats for operation."""
        file_ops = self.paths.get('file_operations', {})
        op_config = file_ops.get(operation, {})
        return op_config.get('allowed_formats', ['TXT'])
    
    def set_filename_template(self, operation: str, template: str):
        """Set filename template for operation."""
        if 'file_operations' not in self.paths:
            self.paths['file_operations'] = {}
        if operation not in self.paths['file_operations']:
            self.paths['file_operations'][operation] = {}
        
        self.paths['file_operations'][operation]['filename_template'] = template
        self._save_paths(self.paths)
    
    def set_file_format(self, operation: str, format_name: str):
        """Set file format for operation."""
        allowed_formats = self.get_allowed_formats(operation)
        if format_name.upper() not in allowed_formats:
            raise ValueError(f"Format {format_name} not allowed for {operation}")
        
        if 'file_operations' not in self.paths:
            self.paths['file_operations'] = {}
        if operation not in self.paths['file_operations']:
            self.paths['file_operations'][operation] = {}
        
        self.paths['file_operations'][operation]['format'] = format_name.upper()
        self._save_paths(self.paths)
    
    def reset_to_defaults(self):
        """Reset all paths to defaults."""
        self.paths = self.DEFAULT_PATHS.copy()
        self._save_paths(self.paths)


# Global instance
path_manager = PathManager()
