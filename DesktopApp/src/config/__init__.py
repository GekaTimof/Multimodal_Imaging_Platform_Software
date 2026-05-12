"""
Configuration module for Desktop Application
Provides centralized configuration management for interface settings and file paths.
"""

from .interface_config import InterfaceConfig, interface_config
from .path_manager import PathManager, path_manager

__all__ = [
    'InterfaceConfig',
    'interface_config', 
    'PathManager',
    'path_manager'
]
