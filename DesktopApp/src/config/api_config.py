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
TIMEOUT_SECONDS = 3
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
    "light_switcher_disconnect": f"{API_BASE_URL}/light-switcher/disconnect",
    # Spectrometer endpoints
    "spectrometer_settings": f"{API_BASE_URL}/spectrometer/settings",
    "spectrometer_info": f"{API_BASE_URL}/spectrometer/info",
    "spectrometer_spectrum": f"{API_BASE_URL}/spectrometer/spectrum",
    "spectrometer_integral_time": f"{API_BASE_URL}/spectrometer/integral-time",
    "spectrometer_dark_capture": f"{API_BASE_URL}/spectrometer/dark-spectrum/capture",
    "spectrometer_dark_clear": f"{API_BASE_URL}/spectrometer/dark-spectrum/clear",
    "spectrometer_dark_load": f"{API_BASE_URL}/spectrometer/dark-spectrum/load",
    "spectrometer_validation": f"{API_BASE_URL}/spectrometer/validation-rules",
    "spectrometer_reconnect": f"{API_BASE_URL}/spectrometer/reconnect",
    # Positioner endpoints
    "positioner_settings": f"{API_BASE_URL}/positioner/settings",
    "positioner_status": f"{API_BASE_URL}/positioner/status",
    "positioner_connect": f"{API_BASE_URL}/positioner/connect",
    "positioner_move": f"{API_BASE_URL}/positioner/move",
    "positioner_home": f"{API_BASE_URL}/positioner/home",
    "positioner_stop": f"{API_BASE_URL}/positioner/stop",
    "positioner_calibrate": f"{API_BASE_URL}/positioner/calibrate",
    "positioner_calibrate_axis": f"{API_BASE_URL}/positioner/calibrate/{{axis}}",
}

# Headers for API requests
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}


# ------------------------------------------------------------------ #
#  Dynamic reconfiguration (used by the device-discovery dialog)      #
# ------------------------------------------------------------------ #

def _build_endpoints(api_base: str, cam_stream: str) -> dict:
    """Build the full ENDPOINTS dict from base URLs."""
    return {
        "health": f"{api_base}/health",
        "camera_settings": f"{api_base}/settings/camera",
        "camera_settings_slot": f"{api_base}/settings/camera/slot/{{slot_id}}",
        "camera_settings_slots": f"{api_base}/settings/camera/slots",
        "update_parameter": f"{api_base}/settings/update",
        "camera_validation": f"{api_base}/settings/camera/validation-rules",
        "save_camera_slot": f"{api_base}/settings/camera/save-slot/{{slot_id}}",
        "load_camera_slot": f"{api_base}/settings/camera/load-slot/{{slot_id}}",
        "apply_camera": f"{api_base}/settings/camera/apply",
        "video_stream": cam_stream,
        "stream_status": f"{cam_stream}/status",
        # Light switcher
        "light_switcher_status": f"{api_base}/light-switcher/status",
        "light_switcher_connect": f"{api_base}/light-switcher/connect",
        "light_switcher_switch": f"{api_base}/light-switcher/switch",
        "light_switcher_disconnect": f"{api_base}/light-switcher/disconnect",
        # Spectrometer
        "spectrometer_settings": f"{api_base}/spectrometer/settings",
        "spectrometer_info": f"{api_base}/spectrometer/info",
        "spectrometer_spectrum": f"{api_base}/spectrometer/spectrum",
        "spectrometer_integral_time": f"{api_base}/spectrometer/integral-time",
        "spectrometer_dark_capture": f"{api_base}/spectrometer/dark-spectrum/capture",
        "spectrometer_dark_clear": f"{api_base}/spectrometer/dark-spectrum/clear",
        "spectrometer_dark_load": f"{api_base}/spectrometer/dark-spectrum/load",
        "spectrometer_validation": f"{api_base}/spectrometer/validation-rules",
        "spectrometer_reconnect": f"{api_base}/spectrometer/reconnect",
        # Positioner
        "positioner_settings": f"{api_base}/positioner/settings",
        "positioner_status": f"{api_base}/positioner/status",
        "positioner_connect": f"{api_base}/positioner/connect",
        "positioner_move": f"{api_base}/positioner/move",
        "positioner_home": f"{api_base}/positioner/home",
        "positioner_stop": f"{api_base}/positioner/stop",
        "positioner_calibrate": f"{api_base}/positioner/calibrate",
        "positioner_calibrate_axis": f"{api_base}/positioner/calibrate/{{axis}}",
    }


def reconfigure(ip: str, api_port: str | None = None,
                stream_port: str | None = None,
                spectrum_stream_port: str | None = None) -> None:
    """
    Update all module-level URL constants for a new Raspberry Pi IP
    and persist the change to ``resources/settings.json``.

    This must be called **before** any service singleton (e.g.
    ``LightSwitcherService``) is created, because they capture the
    URL at construction time.
    """
    global API_BASE_URL, CAMERA_STREAM_URL, SPECTRUM_STREAM_URL, ENDPOINTS

    _api_port = api_port or _DEFAULT_API_PORT
    _stream_port = stream_port or _DEFAULT_STREAM_PORT
    _spec_port = spectrum_stream_port or _DEFAULT_SPECTRUM_STREAM_PORT

    API_BASE_URL = f"http://{ip}:{_api_port}/api"
    CAMERA_STREAM_URL = f"http://{ip}:{_stream_port}/video"
    SPECTRUM_STREAM_URL = f"http://{ip}:{_spec_port}/spectrum"

    ENDPOINTS.update(_build_endpoints(API_BASE_URL, CAMERA_STREAM_URL))

    _save_ip_to_settings(ip, _api_port, _stream_port, _spec_port)
    logger.info(f"API reconfigured for {ip} (api={_api_port}, stream={_stream_port}, spectrum={_spec_port})")


def get_saved_ip() -> str | None:
    """Return the IP currently stored in settings.json, or None."""
    settings = _load_settings()
    base_url = settings.get("api", {}).get("base_url", "")
    try:
        from urllib.parse import urlparse
        parsed = urlparse(base_url)
        host = parsed.hostname
        if host and not host.startswith("127."):
            return host
    except Exception:
        pass
    return None


def _save_ip_to_settings(ip: str, api_port: str, stream_port: str, spectrum_port: str) -> None:
    """Write the updated IP/ports back to settings.json."""
    try:
        settings = _load_settings()
        settings.setdefault("api", {})["base_url"] = f"http://{ip}:{api_port}/api"
        settings.setdefault("camera", {})["stream_url"] = f"http://{ip}:{stream_port}/video"
        settings.setdefault("spectrometer", {})["stream_url"] = f"http://{ip}:{spectrum_port}/spectrum"

        with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
            json.dump(settings, f, indent=4, ensure_ascii=False)
    except Exception as e:
        logger.warning(f"Could not persist settings.json: {e}")
