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
from urllib.parse import urlparse

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


def _save_settings(settings: dict) -> None:
    """Сохранить настройки в JSON-файл."""
    with open(_SETTINGS_FILE, "w", encoding="utf-8") as f:
        json.dump(settings, f, indent=4, ensure_ascii=False)


def _host_from_url(url: str) -> str | None:
    """Извлечь хост (IP) из URL вида http://<host>:<port>/..."""
    try:
        return urlparse(url).hostname
    except ValueError:
        return None


def _port_from_url(url: str, default: str) -> str:
    """Извлечь порт из URL, вернуть значение по умолчанию при отсутствии."""
    try:
        port = urlparse(url).port
    except ValueError:
        port = None
    return str(port) if port else default


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


def get_raspberry_ip() -> str:
    """Текущий адрес Raspberry Pi, используемый приложением."""
    return _host_from_url(API_BASE_URL) or _DEFAULT_RASPBERRY_PI_IP


def get_api_port() -> int:
    """Порт API-сервера Raspberry Pi."""
    return int(_port_from_url(API_BASE_URL, _DEFAULT_API_PORT))


def set_raspberry_ip(ip: str, persist: bool = True) -> None:
    """Переключить приложение на новый адрес Raspberry Pi.

    Обновляет URL-адреса в памяти и (по умолчанию) сохраняет их в
    resources/settings.json. Уже созданные сервисы продолжают использовать
    старый адрес, поэтому после смены IP приложение нужно перезапустить.
    """
    global API_BASE_URL, CAMERA_STREAM_URL, SPECTRUM_STREAM_URL

    api_port = _port_from_url(API_BASE_URL, _DEFAULT_API_PORT)
    stream_port = _port_from_url(CAMERA_STREAM_URL, _DEFAULT_STREAM_PORT)
    spectrum_port = _port_from_url(SPECTRUM_STREAM_URL, _DEFAULT_SPECTRUM_STREAM_PORT)

    API_BASE_URL = f"http://{ip}:{api_port}/api"
    CAMERA_STREAM_URL = f"http://{ip}:{stream_port}/video"
    SPECTRUM_STREAM_URL = f"http://{ip}:{spectrum_port}/spectrum"
    ENDPOINTS.update(_build_endpoints(API_BASE_URL, CAMERA_STREAM_URL))

    if not persist:
        return

    settings = _load_settings()
    settings.setdefault("api", {})["base_url"] = API_BASE_URL
    settings.setdefault("camera", {})["stream_url"] = CAMERA_STREAM_URL
    settings.setdefault("spectrometer", {})["stream_url"] = SPECTRUM_STREAM_URL
    try:
        _save_settings(settings)
        logger.info(f"Raspberry Pi address saved: {ip}")
    except Exception as e:
        logger.error(f"Could not save settings.json: {e}")

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
def _build_endpoints(api_base_url: str, camera_stream_url: str) -> dict:
    """Собрать словарь эндпоинтов для заданных базовых URL."""
    return {
        "health": f"{api_base_url}/health",
        "camera_settings": f"{api_base_url}/settings/camera",
        "camera_settings_slot": f"{api_base_url}/settings/camera/slot/{{slot_id}}",
        "camera_settings_slots": f"{api_base_url}/settings/camera/slots",
        "update_parameter": f"{api_base_url}/settings/update",
        "camera_validation": f"{api_base_url}/settings/camera/validation-rules",
        "save_camera_slot": f"{api_base_url}/settings/camera/save-slot/{{slot_id}}",
        "load_camera_slot": f"{api_base_url}/settings/camera/load-slot/{{slot_id}}",
        "apply_camera": f"{api_base_url}/settings/camera/apply",
        "video_stream": camera_stream_url,
        "stream_status": f"{camera_stream_url}/status",
        # Light switcher endpoints
        "light_switcher_status": f"{api_base_url}/light-switcher/status",
        "light_switcher_connect": f"{api_base_url}/light-switcher/connect",
        "light_switcher_switch": f"{api_base_url}/light-switcher/switch",
        "light_switcher_disconnect": f"{api_base_url}/light-switcher/disconnect",
        # Spectrometer endpoints
        "spectrometer_settings": f"{api_base_url}/spectrometer/settings",
        "spectrometer_info": f"{api_base_url}/spectrometer/info",
        "spectrometer_spectrum": f"{api_base_url}/spectrometer/spectrum",
        "spectrometer_integral_time": f"{api_base_url}/spectrometer/integral-time",
        "spectrometer_dark_capture": f"{api_base_url}/spectrometer/dark-spectrum/capture",
        "spectrometer_dark_clear": f"{api_base_url}/spectrometer/dark-spectrum/clear",
        "spectrometer_dark_load": f"{api_base_url}/spectrometer/dark-spectrum/load",
        "spectrometer_validation": f"{api_base_url}/spectrometer/validation-rules",
        "spectrometer_reconnect": f"{api_base_url}/spectrometer/reconnect"
    }


ENDPOINTS = _build_endpoints(API_BASE_URL, CAMERA_STREAM_URL)

# Headers for API requests
HEADERS = {
    "Content-Type": "application/json",
    "Accept": "application/json"
}
