"""
UI String Constants
Centralized string resources for UI components.
"""

class CameraTabStrings:
    """Strings for camera tab interface."""
    NO_VIDEO = "No video"
    START_CAMERA = "Start Camera"
    STOP_CAMERA = "Stop Camera"
    SAVE_IMAGE = "Save Image"
    CAMERA_STATUS = "Camera status: {}"
    IMAGE_SAVED = "Image saved: {}"
    ERROR_SAVING_IMAGE = "Error saving image: {}"
    STOPPING_CAMERA = "Stopping camera..."
    CAMERA_STOPPED = "Camera stopped"
    FORCE_TERMINATING = "Force terminating camera..."

class SettingsWidgetStrings:
    """Strings for settings widget interface."""
    SETTINGS_NAME = "Settings Name:"
    PHOTO_RESOLUTION = "Photo Resolution:"
    VIDEO_RESOLUTION = "Video Resolution:"
    AUTO_EXPOSURE = "Auto Exposure"
    AUTO_WHITE_BALANCE = "Auto White Balance"
    EXPOSURE_TIME = "Exposure Time"
    ANALOGUE_GAIN = "Analogue Gain"
    EXPOSURE_VALUE = "Exposure Value"
    RED_GAIN = "Red Gain"
    BLUE_GAIN = "Blue Gain"
    
    REFRESH = "Refresh"
    LOAD = "Load"
    SAVE = "Save"
    APPLY = "Apply"
    
    READY = "Ready"
    LOADING_SETTINGS = "Loading settings..."
    SETTINGS_LOADED = "Settings loaded and applied successfully"
    FAILED_TO_LOAD = "Failed to load settings from API"
    APPLYING_SETTINGS = "Applying settings..."
    ALL_SETTINGS_APPLIED = "All settings applied successfully"
    
    LOADING_SLOT = "Loading settings from slot {}: {}"
    API_ERROR_SLOT = "API error loading slot {}: {}"
    ERROR_OPENING_DIALOG = "Error opening slot dialog: {}"
    ERROR_UPDATING_UI = "Error updating UI: {}"
    API_ERROR_PARAMETER = "API error for {}: {}"
    FAILED_SETTING = "Failed to apply setting: {}"

class StatusMessages:
    """General status messages."""
    SUCCESS = "Operation completed successfully"
    ERROR = "An error occurred"
    CONNECTION_ERROR = "API connection failed"
    TIMEOUT_ERROR = "Request timeout"
    VALIDATION_ERROR = "Invalid input data"
    NETWORK_ERROR = "Network error: {}"
    UNEXPECTED_ERROR = "Unexpected error: {}"

class DialogStrings:
    """Strings for dialog windows."""
    CAMERA_SETTINGS_SLOTS = "Camera Settings Slots"
    SELECT_SETTINGS_SLOT = "Select a settings slot to load:"
    SLOT_LOADED = "Loaded settings from slot {}: {}"

class ValidationMessages:
    """Validation error messages."""
    INVALID_SLOT_ID = "Invalid slot ID"
    SLOT_OUT_OF_RANGE = "Slot ID must be between 0 and 9"
    EMPTY_SETTINGS_NAME = "Settings name cannot be empty"
    SETTINGS_NAME_TOO_LONG = "Settings name too long (max 50 characters)"
    INVALID_RESOLUTION = "Invalid resolution: {}"
    INVALID_EXPOSURE_TIME = "Exposure time must be between {} and {}"
    INVALID_GAIN = "Gain must be between {} and {}"
