"""
Error Handling Utilities
Provides decorators and utilities for consistent error handling.
"""

import logging
import requests
from functools import wraps
from typing import Tuple, Any, Callable

logger = logging.getLogger(__name__)


def handle_api_error(func: Callable) -> Callable:
    """
    Decorator for handling API-related errors consistently.
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Tuple[bool, Any]:
        try:
            return func(*args, **kwargs)
        except requests.exceptions.ConnectionError as e:
            logger.error(f"API connection failed: {e}")
            return False, "Connection error"
        except requests.exceptions.Timeout as e:
            logger.error(f"API timeout: {e}")
            return False, "Request timeout"
        except requests.exceptions.HTTPError as e:
            logger.error(f"HTTP error: {e}")
            return False, f"HTTP error: {e}"
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error: {e}")
            return False, f"Request error: {str(e)}"
        except ValueError as e:
            logger.error(f"JSON parsing error: {e}")
            return False, "Invalid response format"
        except Exception as e:
            logger.error(f"Unexpected error in {func.__name__}: {e}")
            return False, f"Unexpected error: {str(e)}"
    return wrapper


def handle_camera_error(func: Callable) -> Callable:
    """
    Decorator for handling camera-related errors.
    
    Returns:
        Tuple[bool, str]: (success, message)
    """
    @wraps(func)
    def wrapper(*args, **kwargs) -> Tuple[bool, Any]:
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(f"Camera error in {func.__name__}: {e}")
            return False, f"Camera error: {str(e)}"
    return wrapper


def validate_slot_id(slot_id: int) -> Tuple[bool, str]:
    """
    Validate camera settings slot ID.
    
    Args:
        slot_id: Slot ID to validate
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not isinstance(slot_id, int):
        return False, "Slot ID must be an integer"
    
    if not 0 <= slot_id <= 10:
        return False, "Slot ID must be between 0 and 10"
    
    return True, ""


def validate_resolution(resolution: str, available_resolutions: list) -> Tuple[bool, str]:
    """
    Validate camera resolution.
    
    Args:
        resolution: Resolution string (e.g., "1920x1080")
        available_resolutions: List of valid resolutions
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    if not isinstance(resolution, str):
        return False, "Resolution must be a string"
    
    if resolution not in available_resolutions:
        return False, f"Invalid resolution: {resolution}"
    
    return True, ""


def validate_range(value: float, min_val: float, max_val: float, name: str) -> Tuple[bool, str]:
    """
    Validate that a value is within the specified range.
    
    Args:
        value: Value to validate
        min_val: Minimum allowed value
        max_val: Maximum allowed value
        name: Parameter name for error message
        
    Returns:
        Tuple[bool, str]: (is_valid, error_message)
    """
    try:
        numeric_value = float(value)
    except (ValueError, TypeError):
        return False, f"{name} must be a number"
    
    if not (min_val <= numeric_value <= max_val):
        return False, f"{name} must be between {min_val} and {max_val}"
    
    return True, ""
