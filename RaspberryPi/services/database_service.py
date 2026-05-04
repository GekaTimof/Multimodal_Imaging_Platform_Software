import sqlite3
import os
from typing import Dict, Any, Tuple

db_folder = "RaspberryPi"
db_name = "DevicesSettings.db"
db_path = os.path.join(db_folder, db_name)


class DatabaseService:
    """Service for managing device settings in the database with validation."""
    
    # Camera parameter validation rules
    CAMERA_VALIDATION_RULES = {
        'AeEnable': {'type': bool, 'range': None},
        'AwbEnable': {'type': bool, 'range': None},
        'ExposureTime': {'type': int, 'range': (100, 3000000)},
        'AnalogueGain': {'type': float, 'range': (0.0, 32.0)},
        'ExposureValue': {'type': float, 'range': (-10.0, 10.0)},
        'RedGain': {'type': float, 'range': (0.0, 8.0)},
        'BlueGain': {'type': float, 'range': (0.0, 8.0)}
    }
    
    def __init__(self):
        self._ensure_database_exists()
    
    def _ensure_database_exists(self):
        """Ensure database and tables exist."""
        if not os.path.exists(db_path):
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
                        value = True
                    elif value.lower() in ('false', '0', 'off'):
                        value = False
                    else:
                        return False, f"Invalid boolean value: {value}"
                elif not isinstance(value, bool):
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
            
            # Range validation
            if rules['range'] is not None:
                min_val, max_val = rules['range']
                if not (min_val <= value <= max_val):
                    return False, f"Value {value} out of range [{min_val}, {max_val}]"
            
            return True, str(value)
        
        return False, f"Unsupported table: {table_name}"
    
    def get_camera_settings(self) -> Dict[str, Any]:
        """Get current camera settings from database."""
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            
            cursor.execute("SELECT * FROM CameraSettings ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                settings = dict(zip(columns, row))
                # Convert boolean fields properly
                settings['AeEnable'] = bool(settings['AeEnable'])
                settings['AwbEnable'] = bool(settings['AwbEnable'])
                return settings
            else:
                return {}
                
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
            
            # Update the parameter
            query = f"UPDATE {table_name} SET {parameter} = ? WHERE id = (SELECT MAX(id) FROM {table_name})"
            cursor.execute(query, (validated_value,))
            
            if cursor.rowcount == 0:
                # If no rows exist, insert a new one
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
            
            cursor.execute(f"SELECT * FROM {table_name} ORDER BY id DESC LIMIT 1")
            row = cursor.fetchone()
            
            if row:
                columns = [desc[0] for desc in cursor.description]
                return dict(zip(columns, row))
            else:
                return {}
                
        except sqlite3.Error as e:
            raise Exception(f"Database error: {e}")
        finally:
            conn.close()


# Global instance
db_service = DatabaseService()
