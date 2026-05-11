"""
Raspberry Pi Configuration
Centralized configuration management for Raspberry Pi services.
"""

import os
from typing import Dict, Any

class Config:
    """Configuration class for Raspberry Pi services."""
    
    # Network Configuration
    RASPBERRY_PI_IP = os.getenv('RASPBERRY_PI_IP', '0.0.0.0')
    API_HOST = os.getenv('API_HOST', '0.0.0.0')
    API_PORT = int(os.getenv('API_PORT', '8000'))
    STREAM_PORT = int(os.getenv('STREAM_PORT', '8080'))
    
    # Camera Configuration
    DEFAULT_FPS = int(os.getenv('DEFAULT_FPS', '20'))
    CAMERA_RELOAD_DELAY_MS = int(os.getenv('CAMERA_RELOAD_DELAY_MS', '1000'))
    CAMERA_TIMEOUT_SECONDS = int(os.getenv('CAMERA_TIMEOUT_SECONDS', '5'))
    
    # Database Configuration
    DATABASE_NAME = os.getenv('DATABASE_NAME', 'DevicesSettings.db')
    DATABASE_TIMEOUT_SECONDS = int(os.getenv('DATABASE_TIMEOUT_SECONDS', '30'))
    
    # Data Storage Configuration
    DATA_DIR = os.getenv('DATA_DIR', os.path.join(os.path.dirname(__file__), '..', '..', 'data'))
    
    # API Configuration
    API_TIMEOUT_SECONDS = int(os.getenv('API_TIMEOUT_SECONDS', '5'))
    RETRY_ATTEMPTS = int(os.getenv('RETRY_ATTEMPTS', '3'))
    RETRY_DELAY_SECONDS = float(os.getenv('RETRY_DELAY_SECONDS', '1.0'))
    
    # Logging Configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    LOG_FORMAT = os.getenv('LOG_FORMAT', '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    
    # Camera validation constants
    MIN_EXPOSURE_TIME_US = 100
    MAX_EXPOSURE_TIME_US = 3000000
    MIN_ANALOG_GAIN = 0.0
    MAX_ANALOG_GAIN = 32.0
    MIN_EXPOSURE_VALUE = -10.0
    MAX_EXPOSURE_VALUE = 10.0
    MIN_COLOR_GAIN = 0.0
    MAX_COLOR_GAIN = 8.0
    
    # Available camera resolutions
    AVAILABLE_RESOLUTIONS = [
        '640x480',      # VGA - 4:3
        '800x600',      # SVGA - 4:3
        '1024x768',     # XGA - 4:3
        '1280x720',     # 720p HD - 16:9
        '1296x972',     # 4:3 mid-resolution
        '1640x1232',    # 4:3 aspect ratio
        '1920x1080',    # 1080p FHD - 16:9
        '2304x1296',    # 16:9 aspect ratio
        '2592x1944',    # High 4:3 resolution
        '3280x2464',    # Full 8MP resolution - 4:3
        '4608x2592',    # Full 12MP resolution - 16:9
    ]
    
    # Default camera settings
    DEFAULT_CAMERA_SETTINGS = {
        'SettingsName': 'Basic',
        'PhotoResolution': '3280x2464',
        'VideoResolution': '1920x1080',
        'AeEnable': True,
        'AwbEnable': True,
        'ExposureTime': 10000,
        'AnalogueGain': 1.0,
        'ExposureValue': 0.0,
        'RedGain': 1.0,
        'BlueGain': 1.0
    }
    
    @classmethod
    def get_api_base_url(cls) -> str:
        """Get API base URL."""
        return f"http://{cls.RASPBERRY_PI_IP}:{cls.API_PORT}/api"
    
    @classmethod
    def get_stream_url(cls) -> str:
        """Get stream URL."""
        return f"http://{cls.RASPBERRY_PI_IP}:{cls.STREAM_PORT}/video"
    
    @classmethod
    def get_database_path(cls) -> str:
        """Get full database path."""
        return os.path.join(os.path.dirname(__file__), cls.DATABASE_NAME)
    
    @classmethod
    def validate_camera_parameter(cls, parameter: str, value: Any) -> tuple[bool, str]:
        """Validate camera parameter against configuration rules."""
        if parameter == 'ExposureTime':
            if not isinstance(value, int):
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    return False, f"ExposureTime must be integer, got {type(value).__name__}"
            if not cls.MIN_EXPOSURE_TIME_US <= value <= cls.MAX_EXPOSURE_TIME_US:
                return False, f"ExposureTime {value} out of range [{cls.MIN_EXPOSURE_TIME_US}, {cls.MAX_EXPOSURE_TIME_US}]"
            return True, str(value)
        
        elif parameter == 'AnalogueGain':
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    return False, f"AnalogueGain must be number, got {type(value).__name__}"
            if not cls.MIN_ANALOG_GAIN <= value <= cls.MAX_ANALOG_GAIN:
                return False, f"AnalogueGain {value} out of range [{cls.MIN_ANALOG_GAIN}, {cls.MAX_ANALOG_GAIN}]"
            return True, str(value)
        
        elif parameter in ['RedGain', 'BlueGain']:
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    return False, f"{parameter} must be number, got {type(value).__name__}"
            if not cls.MIN_COLOR_GAIN <= value <= cls.MAX_COLOR_GAIN:
                return False, f"{parameter} {value} out of range [{cls.MIN_COLOR_GAIN}, {cls.MAX_COLOR_GAIN}]"
            return True, str(value)
        
        elif parameter == 'ExposureValue':
            if not isinstance(value, (int, float)):
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    return False, f"ExposureValue must be number, got {type(value).__name__}"
            if not cls.MIN_EXPOSURE_VALUE <= value <= cls.MAX_EXPOSURE_VALUE:
                return False, f"ExposureValue {value} out of range [{cls.MIN_EXPOSURE_VALUE}, {cls.MAX_EXPOSURE_VALUE}]"
            return True, str(value)
        
        elif parameter in ['PhotoResolution', 'VideoResolution']:
            if not isinstance(value, str):
                return False, f"{parameter} must be string, got {type(value).__name__}"
            if value not in cls.AVAILABLE_RESOLUTIONS:
                return False, f"Invalid {parameter}: {value}. Available: {', '.join(cls.AVAILABLE_RESOLUTIONS)}"
            return True, str(value)
        
        elif parameter in ['AeEnable', 'AwbEnable']:
            if isinstance(value, str):
                if value.lower() in ('true', '1', 'on'):
                    return True, '1'
                elif value.lower() in ('false', '0', 'off'):
                    return True, '0'
                else:
                    return False, f"Invalid boolean value for {parameter}: {value}"
            elif isinstance(value, bool):
                return True, '1' if value else '0'
            elif isinstance(value, int):
                return True, '1' if value else '0'
            else:
                return False, f"{parameter} must be boolean, got {type(value).__name__}"
        
        elif parameter == 'SettingsName':
            # Convert numeric values to string
            if isinstance(value, (int, float)):
                value = str(value)
            elif not isinstance(value, str):
                return False, f"SettingsName must be string or number, got {type(value).__name__}"
            
            if not str(value).strip():
                return False, "Settings name cannot be empty"
            if len(str(value)) > 50:
                return False, "Settings name too long (max 50 characters)"
            return True, str(value)
        
        else:
            return False, f"Unknown parameter: {parameter}"


# Global configuration instance
config = Config()
