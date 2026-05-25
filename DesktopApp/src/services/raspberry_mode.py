"""Raspberry Pi mode switch functions.

These functions handle switching the light switcher to appropriate states
for different device modes.
"""

import logging
from typing import Tuple, Optional
from .light_switcher_service import LightSwitcherService
from config import api_config

logger = logging.getLogger(__name__)

# Глобальный экземпляр сервиса переключателя
_light_switcher_service: Optional[LightSwitcherService] = None

def get_light_switcher_service() -> LightSwitcherService:
    """Получить экземпляр сервиса переключателя (singleton pattern)"""
    global _light_switcher_service
    if _light_switcher_service is None:
        _light_switcher_service = LightSwitcherService(api_config.API_BASE_URL)
    return _light_switcher_service

def switch_to_spectrometer_mode() -> Tuple[bool, str]:
    """
    Переключить Raspberry Pi в режим спектрометра.
    
    Returns:
        Tuple[bool, str]: (успех, сообщение)
    """
    try:
        service = get_light_switcher_service()
        success, message = service.switch_to_spectrometer_mode()
        
        # При новой логике success всегда True (запущен процесс)
        # Результат придет через сигналы
        logger.info("Started switching to spectrometer mode")
        return success, message
            
    except Exception as e:
        error_msg = f"Error switching to spectrometer mode: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def switch_to_camera_mode() -> Tuple[bool, str]:
    """
    Переключить Raspberry Pi в режим камеры.
    
    Returns:
        Tuple[bool, str]: (успех, сообщение)
    """
    try:
        service = get_light_switcher_service()
        success, message = service.switch_to_camera_mode()
        
        # При новой логике success всегда True (запущен процесс)
        # Результат придет через сигналы
        logger.info("Started switching to camera mode")
        return success, message
            
    except Exception as e:
        error_msg = f"Error switching to camera mode: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def switch_to_Acquisition_mode() -> Tuple[bool, str]:
    """
    Переключить Raspberry Pi в режим Acquisition (анализ лунок).
    Для Acquisition используется тот же режим, что и для камеры (state1).
    
    Returns:
        Tuple[bool, str]: (успех, сообщение)
    """
    try:
        service = get_light_switcher_service()
        success, message = service.switch_to_camera_mode()  # Acquisition использует camera mode
        
        # При новой логике success всегда True (запущен процесс)
        # Результат придет через сигналы
        logger.info("Started switching to Acquisition mode (camera state)")
        return success, message
            
    except Exception as e:
        error_msg = f"Error switching to Acquisition mode: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def check_switcher_connection() -> Tuple[bool, str]:
    """
    Проверить подключение переключателя.
    
    Returns:
        Tuple[bool, str]: (подключен, сообщение)
    """
    try:
        service = get_light_switcher_service()
        return service.check_connection()
    except Exception as e:
        error_msg = f"Error checking switcher connection: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def connect_switcher() -> Tuple[bool, str]:
    """
    Подключиться к переключателю.
    
    Returns:
        Tuple[bool, str]: (успех, сообщение)
    """
    try:
        service = get_light_switcher_service()
        return service.connect()
    except Exception as e:
        error_msg = f"Error connecting switcher: {str(e)}"
        logger.error(error_msg)
        return False, error_msg


def get_switcher_status():
    """
    Получить текущий статус переключателя.
    
    Returns:
        Dict: Информация о статусе
    """
    try:
        service = get_light_switcher_service()
        return service.get_status()
    except Exception as e:
        logger.error(f"Error getting switcher status: {str(e)}")
        return {
            "connected": False,
            "current_state": "unknown",
            "base_url": api_config.API_BASE_URL
        }
