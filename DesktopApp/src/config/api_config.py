"""
API Configuration
Centralized configuration for API endpoints and connection settings.
IP address of Raspberry Pi is configured in resources/settings.json ("api.base_url" and "camera.stream_url").
"""

import json
import os

_SETTINGS_FILE = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "resources", "settings.json"))

def _load_settings() -> dict:
    try:
        with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: could not load settings.json: {e}")
        return {}

_settings = _load_settings()

API_BASE_URL: str = _settings.get("api", {}).get("base_url", "http://10.78.112.189:8000/api")
CAMERA_STREAM_URL: str = _settings.get("camera", {}).get("stream_url", "http://10.78.112.189:8080/video")

# Connection settings
TIMEOUT_SECONDS = 5
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1.0

# Timeout constants (centralized)
CAMERA_STREAM_TIMEOUT = 5
PHOTO_CAPTURE_TIMEOUT = 350.0
THREAD_WAIT_TIMEOUT = 1000
THREAD_TIMEOUT_MS = 3000
PROGRESS_UPDATE_INTERVAL_MS = 200
SPECTRUM_THREAD_SLEEP_MS = 100
API_THREAD_WAIT_TIMEOUT = 1000

# API endpoints
ENDPOINTS = {
    "health": f"{API_BASE_URL}/health",
    "camera_settings": f"{API_BASE_URL}/settings/camera",
    "camera_settings_slot": f"{API_BASE_URL}/settings/camera/slot/{{slot_id}}",
    "camera_settings_slots": f"{API_BASE_URL}/settings/camera/slots",
    "update_parameter": f"{API_BASE_URL}/settings/update",
    "camera_validation": f"{API_BASE_URL}/settings/camera/validation-rules",
    "save_camera_slot": f"{API_BASE_URL}/settings/camera/save-slot/{{slot_id}}",
    "load_camera_slot": f"{API_BASE_URL}/settings/camera/load-slot/{{slot_id}}",
    "apply_camera": f"{API_BASE_URL}/settings/camera/apply",
    "reload_camera": f"{API_BASE_URL}/settings/camera/reload",
    "video_stream": CAMERA_STREAM_URL,
    "stream_status": f"{CAMERA_STREAM_URL}/status"
}

# Headers for API requests
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}
