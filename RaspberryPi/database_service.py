import sqlite3
import os
from typing import Dict, Any, Tuple

# Get the directory where this script is located (RaspberryPi directory)
db_folder = os.path.dirname(os.path.abspath(__file__))
db_name = "DevicesSettings.db"
db_path = os.path.join(db_folder, db_name)


class DatabaseService:
    """Service for managing device settings in the database with validation."""
    
    # Camera parameter validation rules
    CAMERA_VALIDATION_RULES = {
        'SettingsName': {'type': str, 'range': None},
        'PhotoResolution': {'type': str, 'range': None},
        'VideoResolution': {'type': str, 'range': None},
        'AeEnable': {'type': bool, 'range': None},
        'AwbEnable': {'type': bool, 'range': None},
        'ExposureTime': {'type': int, 'range': (100, 3000000)},
        'AnalogueGain': {'type': float, 'range': (0.0, 32.0)},
        'ExposureValue': {'type': float, 'range': (-10.0, 10.0)},
        'RedGain': {'type': float, 'range': (0.0, 8.0)},
        'BlueGain': {'type': float, 'range': (0.0, 8.0)}
    }
    
    # Available camera resolutions for Raspberry Pi Camera Modules
    # Based on Pi Camera v2 (8MP) and v3 (12MP) capabilities
    # Sorted by ascending resolution (total pixels)
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
    
    def __init__(self):
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database and tables exist."""
        if not os.path.exists(db_path):
            import sys
            # Add services directory to path for import
            services_dir = os.path.join(os.path.dirname(__file__), 'services')
            if services_dir not in sys.path:
                sys.path.insert(0, services_dir)
            import database_ini
            database_ini.main()
    
    def _validate_parameter(self, table_name: str, parameter: str, value: Any) -> Tuple[bool, str]:
        """Validate parameter value against type and range constraints."""
        if table_name == 'CameraSettings':
            if parameter not in self.CAMERA_VALIDATION_RULES:
                return False, f"Unknown parameter: {parameter}"
            
            rules = self.CAMERA_VALIDATION_RULES[parameter]
            
            # Type validation
            if rules['type'] is bool:
                if isinstance(value, str):
                    if value.lower() in ('true', '1', 'on'):
                        value = 1  # Convert to integer for database
                    elif value.lower() in ('false', '0', 'off'):
                        value = 0  # Convert to integer for database
                    else:
                        return False, f"Invalid boolean value: {value}"
                elif isinstance(value, bool):
                    value = 1 if value else 0  # Convert boolean to integer for database
                else:
                    return False, f"Expected boolean, got {type(value).__name__}"
            
            elif rules['type'] is int:
                try:
                    value = int(value)
                except (ValueError, TypeError):
                    return False, f"Expected integer, got: {value}"
            
            elif rules['type'] is float:
                try:
                    value = float(value)
                except (ValueError, TypeError):
                    return False, f"Expected float, got: {value}"
            
            elif rules['type'] is str:
                if not isinstance(value, str):
                    return False, f"Expected string, got {type(value).__name__}"
                
                # Special validation for Resolution parameters
                if parameter in ['PhotoResolution', 'VideoResolution'] and value not in self.AVAILABLE_RESOLUTIONS:
                    return False, f"Invalid {parameter}: {value}. Available: {', '.join(self.AVAILABLE_RESOLUTIONS)}"
                
                # Special validation for SettingsName
                if parameter == 'SettingsName':
                    if not value.strip():
                        return False, "Settings name cannot be empty"
                    if len(value) > 50:
                        return False, "Settings name too long (max 50 characters)"
            
            # Range validation
            if rules['range'] is not None:
                min_val, max_val = rules['range']
                if not (min_val <= value <= max_val):
                    return False, f"Value {value} out of range [{min_val}, {max_val}]"
            
            return True, str(value)
        
        return False, f"Unsupported table: {table_name}"
    
    def get_camera_settings(self) -> Dict[str, Any]:
        """Get current camera settings from database (always from slot 0 - main settings)."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM CameraSettings WHERE id = 0")
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                settings = dict(zip(columns, row))
                # Convert boolean fields properly
                settings['AeEnable'] = bool(settings['AeEnable'])
                settings['AwbEnable'] = bool(settings['AwbEnable'])
                return settings
            else:
                # Create default settings for slot 0 if doesn't exist
                default_settings = {
                    'id': 0,
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
                
                # Insert the default settings into database
                cursor.execute("""
                INSERT OR IGNORE INTO CameraSettings 
                (id, SettingsName, PhotoResolution, VideoResolution, AeEnable, AwbEnable, ExposureTime, AnalogueGain, ExposureValue, RedGain, BlueGain)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    0, default_settings['SettingsName'],
                    default_settings['PhotoResolution'], default_settings['VideoResolution'],
                    int(default_settings['AeEnable']), int(default_settings['AwbEnable']),
                    default_settings['ExposureTime'], default_settings['AnalogueGain'],
                    default_settings['ExposureValue'], default_settings['RedGain'], default_settings['BlueGain']
                ))
                conn.commit()
                
                return default_settings
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()
    
    def update_parameter(self, table_name: str, parameter: str, value: Any) -> Tuple[bool, str]:
        """Update a single parameter in the specified table."""
        # Validate the parameter
        is_valid, validated_value = self._validate_parameter(table_name, parameter, value)
        if not is_valid:
            return False, validated_value
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if table exists
            cursor.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not cursor.fetchone():
                return False, f"Table {table_name} does not exist"
            
            # Check if parameter exists in table
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            if parameter not in columns:
                return False, f"Parameter {parameter} does not exist in table {table_name}"
            
            # For CameraSettings, always update slot 0 (main settings)
            if table_name == 'CameraSettings':
                target_id = 0
            else:
                target_id = "(SELECT MAX(id) FROM {table_name})"
            
            # Update the parameter
            query = f"UPDATE {table_name} SET {parameter} = ? WHERE id = ?"
            cursor.execute(query, (validated_value, target_id))
            
            if cursor.rowcount == 0:
                # If no rows exist for CameraSettings slot 0, insert default settings
                if table_name == 'CameraSettings':
                    # Ensure slot 0 exists with default values
                    cursor.execute("""
                    INSERT OR IGNORE INTO CameraSettings 
                    (id, SettingsName, PhotoResolution, VideoResolution, AeEnable, AwbEnable, ExposureTime, AnalogueGain, ExposureValue, RedGain, BlueGain)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        0, 'Basic', '3280x2464', '1920x1080', 1, 1, 10000, 1.0, 0.0, 1.0, 1.0
                    ))
                    
                    # Try updating again
                    cursor.execute(query, (validated_value, target_id))
                else:
                    # For other tables, insert a new row
                    columns_str = ', '.join(columns)
                    placeholders = ', '.join(['?' for _ in columns])
                    values = [None] * len(columns)  # id will be auto-incremented
                    param_index = columns.index(parameter)
                    values[param_index] = validated_value
                    
                    query = f"INSERT INTO {table_name} ({columns_str}) VALUES ({placeholders})"
                    cursor.execute(query, values)
            
            conn.commit()
            return True, f"Updated {parameter} to {validated_value}"
            
        except sqlite3.Error as e:
            return False, f"Database error: {e}"
        finally:
            conn.close()
    
    def get_all_settings(self, table_name: str) -> Dict[str, Any]:
        """Get all settings from the specified table."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # For CameraSettings, always get slot 0 (main settings)
            if table_name == 'CameraSettings':
                cursor.execute(f"SELECT * FROM {table_name} WHERE id = 0")
            else:
                cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 1")
            
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                settings = dict(zip(columns, row))
                # Convert boolean fields properly for CameraSettings
                if table_name == 'CameraSettings':
                    settings['AeEnable'] = bool(settings['AeEnable'])
                    settings['AwbEnable'] = bool(settings['AwbEnable'])
                return settings
            else:
                return {}
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()
    
    def get_camera_settings_by_slot(self, slot_id: int) -> Dict[str, Any]:
        """Get camera settings for a specific slot (0-9)."""
        if not 0 <= slot_id <= 9:
            raise ValueError("Slot ID must be between 0 and 9")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM CameraSettings WHERE id = ?", (slot_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                settings = dict(zip(columns, row))
                # Convert boolean fields properly
                settings['AeEnable'] = bool(settings['AeEnable'])
                settings['AwbEnable'] = bool(settings['AwbEnable'])
                return settings
            else:
                # Create default settings for slot if doesn't exist
                default_name = "Basic" if slot_id == 0 else f"Slot {slot_id}"
                default_settings = {
                    'id': slot_id,
                    'SettingsName': default_name,
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
                
                # Insert the default settings into database
                cursor.execute("""
                INSERT OR IGNORE INTO CameraSettings 
                (id, SettingsName, PhotoResolution, VideoResolution, AeEnable, AwbEnable, ExposureTime, AnalogueGain, ExposureValue, RedGain, BlueGain)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    slot_id, default_name,
                    default_settings['PhotoResolution'], default_settings['VideoResolution'],
                    int(default_settings['AeEnable']), int(default_settings['AwbEnable']),
                    default_settings['ExposureTime'], default_settings['AnalogueGain'],
                    default_settings['ExposureValue'], default_settings['RedGain'], default_settings['BlueGain']
                ))
                conn.commit()
                
                return default_settings
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()
    
    def save_camera_settings_to_slot(self, slot_id: int, settings: Dict[str, Any]) -> Tuple[bool, str]:
        """Save camera settings to a specific slot (0-9)."""
        if not 0 <= slot_id <= 9:
            return False, "Slot ID must be between 0 and 9"
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            # Check if slot exists
            cursor.execute("SELECT id FROM CameraSettings WHERE id = ?", (slot_id,))
            exists = cursor.fetchone()
            
            if exists:
                # Update existing slot
                query = """
                UPDATE CameraSettings 
                SET SettingsName = ?, PhotoResolution = ?, VideoResolution = ?, AeEnable = ?, AwbEnable = ?,
                    ExposureTime = ?, AnalogueGain = ?, ExposureValue = ?, RedGain = ?, BlueGain = ?
                WHERE id = ?
                """
                cursor.execute(query, (
                    settings.get('SettingsName', f"Slot {slot_id}"),
                    settings.get('PhotoResolution', '3280x2464'),
                    settings.get('VideoResolution', '1920x1080'),
                    int(settings.get('AeEnable', True)),
                    int(settings.get('AwbEnable', True)),
                    settings.get('ExposureTime', 10000),
                    settings.get('AnalogueGain', 1.0),
                    settings.get('ExposureValue', 0.0),
                    settings.get('RedGain', 1.0),
                    settings.get('BlueGain', 1.0),
                    slot_id
                ))
            else:
                # Insert new slot
                query = """
                INSERT INTO CameraSettings 
                (id, SettingsName, PhotoResolution, VideoResolution, AeEnable, AwbEnable, ExposureTime, AnalogueGain, ExposureValue, RedGain, BlueGain)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (
                    slot_id,
                    settings.get('SettingsName', f"Slot {slot_id}"),
                    settings.get('PhotoResolution', '3280x2464'),
                    settings.get('VideoResolution', '1920x1080'),
                    int(settings.get('AeEnable', True)),
                    int(settings.get('AwbEnable', True)),
                    settings.get('ExposureTime', 10000),
                    settings.get('AnalogueGain', 1.0),
                    settings.get('ExposureValue', 0.0),
                    settings.get('RedGain', 1.0),
                    settings.get('BlueGain', 1.0)
                ))
            
            conn.commit()
            return True, f"Settings saved to slot {slot_id}"
            
        except sqlite3.Error as e:
            return False, f"Database error: {e}"
        finally:
            conn.close()
    
    def get_all_camera_settings_slots(self) -> Dict[int, Dict[str, Any]]:
        """Get all camera settings slots (0-9)."""
        slots = {}
        for slot_id in range(10):
            slots[slot_id] = self.get_camera_settings_by_slot(slot_id)
        return slots


# Global instance
db_service = DatabaseService()
