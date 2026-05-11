import sqlite3
import os
import logging
from typing import Dict, Any, Tuple, Optional

# Import configuration and error handlers
from src.config.settings import config
from ..utils.error_handlers import database_error_handler, api_error_handler, log_execution_time

# Get database path from config
db_path = config.get_database_path()

# Setup logging
logger = logging.getLogger(__name__)


class DatabaseService:
    """Service for managing device settings in the database with validation."""
    
    def __init__(self):
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database and tables exist."""
        if not os.path.exists(db_path):
            import sys
            from . import database_ini
            database_ini.main()
    
    def _validate_parameter(self, table_name: str, parameter: str, value: Any) -> Tuple[bool, str]:
        """Validate parameter value against configuration rules."""
        if table_name == 'CameraSettings':
            try:
                return config.validate_camera_parameter(parameter, value)
            except Exception as e:
                logger.error(f"Validation error for {parameter}: {e}")
                return False, f"Validation error: {str(e)}"
        
        logger.error(f"Unsupported table: {table_name}")
        return False, f"Unsupported table: {table_name}"
    
    @log_execution_time
    @database_error_handler
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
                default_settings = config.DEFAULT_CAMERA_SETTINGS.copy()
                default_settings['id'] = 0
                
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
            logger.error(f"Database error in get_camera_settings: {e}")
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()
    
    @api_error_handler
    @log_execution_time
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
