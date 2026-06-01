"""
API Configuration
Centralized configuration for API endpoints and connection settings.

Приоритет настроек (от высшего к низшему):
1. Переменные окружения (RASPBERRY_PI_IP, API_PORT, STREAM_PORT)
2. Файл resources/settings.json
3. Значения по умолчанию
"""

import json
import logging
import os

logger = logging.getLogger(__name__)

# Значения по умолчанию
_DEFAULT_RASPBERRY_PI_IP = "10.136.106.189"
_DEFAULT_API_PORT = "8000"
_DEFAULT_STREAM_PORT = "8080"
_DEFAULT_SPECTRUM_STREAM_PORT = "8081"

_SETTINGS_FILE = os.path.normpath(
    os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "resources", "settings.json")
)


def _load_settings() -> dict:
    """Загрузить настройки из JSON-файла."""
    try:
        with open(_SETTINGS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        logger.warning(f"Could not load settings.json: {e}")
        return {}


def _get_base_url_from_env() -> str | None:
    """Получить базовый URL из переменных окружения."""
    ip = os.getenv("RASPBERRY_PI_IP")
    port = os.getenv("API_PORT", _DEFAULT_API_PORT)
    if ip:
        return f"http://{ip}:{port}/api"
    return None


def _get_stream_url_from_env() -> str | None:
    """Получить URL видеопотока из переменных окружения."""
    ip = os.getenv("RASPBERRY_PI_IP")
    port = os.getenv("STREAM_PORT", _DEFAULT_STREAM_PORT)
    if ip:
        return f"http://{ip}:{port}/video"
    return None


def _get_spectrum_stream_url_from_env() -> str | None:
    """Получить URL потока спектрометра из переменных окружения."""
    ip = os.getenv("RASPBERRY_PI_IP")
    port = os.getenv("SPECTRUM_STREAM_PORT", _DEFAULT_SPECTRUM_STREAM_PORT)
    if ip:
        return f"http://{ip}:{port}/spectrum"
    return None


_settings = _load_settings()

# Приоритет: переменные окружения > settings.json > значения по умолчанию
API_BASE_URL: str = (
    _get_base_url_from_env()
    or _settings.get("api", {}).get("base_url")
    or f"http://{_DEFAULT_RASPBERRY_PI_IP}:{_DEFAULT_API_PORT}/api"
)

CAMERA_STREAM_URL: str = (
    _get_stream_url_from_env()
    or _settings.get("camera", {}).get("stream_url")
    or f"http://{_DEFAULT_RASPBERRY_PI_IP}:{_DEFAULT_STREAM_PORT}/video"
)

SPECTRUM_STREAM_URL: str = (
    _get_spectrum_stream_url_from_env()
    or _settings.get("spectrometer", {}).get("stream_url")
    or f"http://{_DEFAULT_RASPBERRY_PI_IP}:{_DEFAULT_SPECTRUM_STREAM_PORT}/spectrum"
)

# Connection settings
TIMEOUT_SECONDS = 5
RETRY_ATTEMPTS = 3
RETRY_DELAY = 1.0

# Timeout constants (centralized)
CAMERA_STREAM_TIMEOUT = 5
PHOTO_CAPTURE_TIMEOUT = 350.0
PROGRESS_UPDATE_INTERVAL_MS = 200
SPECTRUM_THREAD_SLEEP_MS = 100
API_THREAD_WAIT_TIMEOUT = 1000
LIGHT_SWITCHER_CONNECTION_TIMEOUT = 10.0
LIGHT_SWITCHER_SWITCH_TIMEOUT = 25.0

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
    "video_stream": CAMERA_STREAM_URL,
    "stream_status": f"{CAMERA_STREAM_URL}/status",
    # Light switcher endpoints
    "light_switcher_status": f"{API_BASE_URL}/light-switcher/status",
    "light_switcher_connect": f"{API_BASE_URL}/light-switcher/connect",
    "light_switcher_switch": f"{API_BASE_URL}/light-switcher/switch",
    "light_switcher_disconnect": f"{API_BASE_URL}/light-switcher/disconnect"
}

# Headers for API requests
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}
