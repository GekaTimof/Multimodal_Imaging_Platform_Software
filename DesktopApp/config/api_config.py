"""
API Configuration
Centralized configuration for API endpoints and connection settings.
"""

# API endpoints
API_BASE_URL = "http://10.43.70.189:8000/api"
CAMERA_STREAM_URL = "http://10.43.70.189:8080/video"

# Connection settings
TIMEOUT_SECONDS = 5
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1.0

# API endpoints
ENDPOINTS = {
    "health": f"{API_BASE_URL}/health",
    "camera_settings": f"{API_BASE_URL}/settings/camera",
    "camera_settings_slot": f"{API_BASE_URL}/settings/camera/slot/{{slot_id}}",
    "camera_settings_slots": f"{API_BASE_URL}/settings/camera/slots",
    "update_parameter": f"{API_BASE_URL}/settings/update",
    "camera_validation": f"{API_BASE_URL}/settings/camera/validation-rules",
    "save_camera_slot": f"{API_BASE_URL}/settings/camera/save-slot/{{slot_id}}",
    "reload_camera": f"{API_BASE_URL}/settings/camera/reload",
    "video_stream": CAMERA_STREAM_URL,
    "stream_status": f"{CAMERA_STREAM_URL}/status"
}

# Headers for API requests
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}
