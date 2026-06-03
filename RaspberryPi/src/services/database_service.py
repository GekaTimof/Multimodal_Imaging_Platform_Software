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

    @staticmethod
    def _convert_bool_fields(settings: Dict[str, Any]) -> Dict[str, Any]:
        """Convert AeEnable/AwbEnable to native Python bool (avoids numpy.bool_)."""
        settings['AeEnable'] = bool(int(settings['AeEnable']))
        settings['AwbEnable'] = bool(int(settings['AwbEnable']))
        return settings

    @staticmethod
    def _insert_default_camera_slot(cursor, slot_id: int, settings: Dict[str, Any]):
        """INSERT OR IGNORE a camera settings row for slot_id using provided settings dict."""
        cursor.execute("""
        INSERT OR IGNORE INTO CameraSettings
        (id, SettingsName, PhotoResolution, VideoResolution, AeEnable, AwbEnable,
         ExposureTime, AnalogueGain, ExposureValue, RedGain, BlueGain)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            slot_id,
            settings.get('SettingsName', f"Slot {slot_id}"),
            settings.get('PhotoResolution', '3280x2464'),
            settings.get('VideoResolution', '1920x1080'),
            int(settings.get('AeEnable', True)),
            int(settings.get('AwbEnable', True)),
            settings.get('ExposureTime', 10000),
            settings.get('AnalogueGain', 1.0),
            settings.get('ExposureValue', 0.0),
            settings.get('RedGain', 2.0),
            settings.get('BlueGain', 2.0),
        ))
    
    def _validate_parameter(self, table_name: str, parameter: str, value: Any) -> Tuple[bool, str]:
        """Validate parameter value against configuration rules."""
        if table_name == 'CameraSettings':
            try:
                return config.validate_camera_parameter(parameter, value)
            except Exception as e:
                logger.error(f"Validation error for {parameter}: {e}")
                return False, f"Validation error: {str(e)}"
        elif table_name == 'SpectrometerSettings':
            try:
                return self._validate_spectrometer_parameter(parameter, value)
            except Exception as e:
                logger.error(f"Validation error for {parameter}: {e}")
                return False, f"Validation error: {str(e)}"
        
        logger.error(f"Unsupported table: {table_name}")
        return False, f"Unsupported table: {table_name}"
    
    def _validate_spectrometer_parameter(self, parameter: str, value: Any) -> Tuple[bool, str]:
        """Validate spectrometer parameter values (delegates to Config)."""
        return config.validate_spectrometer_parameter(parameter, value)
    
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
                return self._convert_bool_fields(settings)
            else:
                # Create default settings for slot 0 if doesn't exist
                default_settings = config.DEFAULT_CAMERA_SETTINGS.copy()
                default_settings['id'] = 0
                self._insert_default_camera_slot(cursor, 0, default_settings)
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
        
        # table_name and parameter are validated by _validate_parameter / Pydantic before reaching here.
        # SQLite does not support ? placeholders for identifiers (table/column names),
        # so we use the already-whitelisted values directly in the query string.
        ALLOWED_TABLES = {'CameraSettings', 'SpectrometerSettings', 'PositionerSettings'}
        if table_name not in ALLOWED_TABLES:
            return False, f"Table {table_name} is not allowed"

        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if table exists (parameterized — sqlite_master lookup)
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name=?", (table_name,))
            if not cursor.fetchone():
                return False, f"Table {table_name} does not exist"

            # Check if parameter (column) exists — PRAGMA doesn't support ? for table names,
            # but table_name is whitelisted above so f-string is safe here.
            cursor.execute(f"PRAGMA table_info({table_name})")
            columns = [row[1] for row in cursor.fetchall()]
            if parameter not in columns:
                return False, f"Parameter {parameter} does not exist in table {table_name}"

            # For CameraSettings, always update slot 0 (main settings)
            if table_name == 'CameraSettings':
                target_id = 0
            else:
                cursor.execute(f"SELECT MAX(id) FROM {table_name}")
                row = cursor.fetchone()
                target_id = row[0] if row and row[0] is not None else 0

            # Update the parameter — identifiers whitelisted above
            query = f"UPDATE {table_name} SET {parameter} = ? WHERE id = ?"
            cursor.execute(query, (validated_value, target_id))
            
            if cursor.rowcount == 0:
                # If no rows exist for CameraSettings slot 0, insert default settings
                if table_name == 'CameraSettings':
                    # Ensure slot 0 exists with default values
                    self._insert_default_camera_slot(cursor, 0, config.DEFAULT_CAMERA_SETTINGS)
                    
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
                if table_name == 'CameraSettings':
                    self._convert_bool_fields(settings)
                return settings
            else:
                return {}
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()
    
    def get_camera_settings_by_slot(self, slot_id: int) -> Dict[str, Any]:
        """Get camera settings for a specific slot (0-10). Slot 0 is current session, 1-10 are saved presets."""
        if not 0 <= slot_id <= 10:
            raise ValueError("Slot ID must be between 0 and 10")
        
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM CameraSettings WHERE id = ?", (slot_id,))
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                settings = dict(zip(columns, row))
                return self._convert_bool_fields(settings)
            else:
                # Create default settings for slot if doesn't exist
                default_name = "Current Session" if slot_id == 0 else f"Slot {slot_id}"
                default_settings = config.DEFAULT_CAMERA_SETTINGS.copy()
                default_settings['id'] = slot_id
                default_settings['SettingsName'] = default_name
                self._insert_default_camera_slot(cursor, slot_id, default_settings)
                conn.commit()
                return default_settings
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()
    
    def save_camera_settings_to_slot(self, slot_id: int, settings: Dict[str, Any]) -> Tuple[bool, str]:
        """Save camera settings to a specific slot (0-10). Slot 0 is current session, 1-10 are saved presets."""
        if not 0 <= slot_id <= 10:
            return False, "Slot ID must be between 0 and 10"
        
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
                    settings.get('RedGain', 2.0),
                    settings.get('BlueGain', 2.0),
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
                    settings.get('RedGain', 2.0),
                    settings.get('BlueGain', 2.0)
                ))
            
            conn.commit()
            return True, f"Settings saved to slot {slot_id}"
            
        except sqlite3.Error as e:
            return False, f"Database error: {e}"
        finally:
            conn.close()
    
    def get_all_camera_settings_slots(self) -> Dict[int, Dict[str, Any]]:
        """Get all camera settings slots (0-10). Slot 0 is current session, 1-10 are saved presets."""
        slots = {}
        for slot_id in range(11):  # 0-10 inclusive
            slots[slot_id] = self.get_camera_settings_by_slot(slot_id)
        return slots

    def copy_slot_to_session(self, source_slot_id: int) -> Tuple[bool, str, Dict[str, Any]]:
        """Copy settings from a slot (1-10) to the current session (slot 0).

        Args:
            source_slot_id: Slot ID to copy from (1-10)

        Returns:
            Tuple of (success: bool, message: str, settings: dict)
        """
        if not 1 <= source_slot_id <= 10:
            return False, "Source slot must be between 1 and 10", {}

        try:
            # Get settings from source slot
            source_settings = self.get_camera_settings_by_slot(source_slot_id)

            if not source_settings:
                return False, f"Slot {source_slot_id} not found or empty", {}

            # Copy to slot 0 (session), preserving the SettingsName from source
            success, message = self.save_camera_settings_to_slot(0, source_settings)

            if success:
                # Return the settings that were copied (with slot 0 as target)
                session_settings = self.get_camera_settings_by_slot(0)
                return True, f"Settings from slot {source_slot_id} loaded to session", session_settings
            else:
                return False, f"Failed to copy to session: {message}", {}

        except Exception as e:
            return False, f"Error copying slot to session: {e}", {}
    
    @log_execution_time
    @database_error_handler
    def get_spectrometer_settings(self) -> Dict[str, Any]:
        """Get current spectrometer settings from database (always from slot 0 - main settings)."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM SpectrometerSettings WHERE id = 0")
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                settings = dict(zip(columns, row))
                # Convert boolean fields properly
                settings['UseDarkSpectrum'] = bool(settings['UseDarkSpectrum'])
                settings['AutoDarkCorrection'] = bool(settings['AutoDarkCorrection'])
                return settings
            else:
                # Create default settings for slot 0 if doesn't exist
                default_settings = {**config.DEFAULT_SPECTROMETER_SETTINGS, 'id': 0, 'LastUpdated': ''}
                cursor.execute("""
                INSERT OR IGNORE INTO SpectrometerSettings
                (id, SettingsName, IntegralTime, UseDarkSpectrum, AutoDarkCorrection, OverilluminationThreshold, LastUpdated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    0, default_settings['SettingsName'],
                    default_settings['IntegralTime'], int(default_settings['UseDarkSpectrum']),
                    int(default_settings['AutoDarkCorrection']), default_settings['OverilluminationThreshold'],
                    default_settings['LastUpdated']
                ))
                conn.commit()
                return default_settings
                
        except sqlite3.Error as e:
            logger.error(f"Database error in get_spectrometer_settings: {e}")
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()
    
    @api_error_handler
    @log_execution_time
    def save_spectrometer_settings(self, settings: Dict[str, Any]) -> Tuple[bool, str]:
        """Save spectrometer settings to database (always to slot 0 - main settings)."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()

            # Check if slot 0 exists
            cursor.execute("SELECT id FROM SpectrometerSettings WHERE id = 0")
            exists = cursor.fetchone()

            if exists:
                # Update existing settings
                query = """
                UPDATE SpectrometerSettings
                SET SettingsName = ?, IntegralTime = ?, UseDarkSpectrum = ?, AutoDarkCorrection = ?,
                    OverilluminationThreshold = ?, LastUpdated = ?
                WHERE id = ?
                """
                cursor.execute(query, (
                    settings.get('SettingsName', 'Basic'),
                    settings.get('IntegralTime', 100),
                    int(settings.get('UseDarkSpectrum', False)),
                    int(settings.get('AutoDarkCorrection', True)),
                    settings.get('OverilluminationThreshold', 65535),
                    settings.get('LastUpdated', ''),
                    0
                ))
            else:
                # Insert new settings
                query = """
                INSERT INTO SpectrometerSettings
                (id, SettingsName, IntegralTime, UseDarkSpectrum, AutoDarkCorrection, OverilluminationThreshold, LastUpdated)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """
                cursor.execute(query, (
                    0,
                    settings.get('SettingsName', 'Basic'),
                    settings.get('IntegralTime', 100),
                    int(settings.get('UseDarkSpectrum', False)),
                    int(settings.get('AutoDarkCorrection', True)),
                    settings.get('OverilluminationThreshold', 65535),
                    settings.get('LastUpdated', '')
                ))

            conn.commit()
            return True, "Spectrometer settings saved successfully"

        except sqlite3.Error as e:
            return False, f"Database error: {e}"
        finally:
            conn.close()


# Global instance
db_service = DatabaseService()
