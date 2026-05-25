#!/usr/bin/env python3
"""
Light Switcher Service for Desktop Application
Сервис для управления переключателем света из Desktop приложения
"""

import requests
import json
import logging
from typing import Optional, Tuple, Dict, Any
from enum import Enum
from PyQt5.QtCore import QObject, pyqtSignal, QThread
import threading

logger = logging.getLogger(__name__)

class SwitchState(Enum):
    """Состояния переключателя"""
    STATE_1 = "state1"  # Левый концевик - камера
    STATE_2 = "state2"  # Правый концевик - спектрометр
    UNKNOWN = "unknown"
    ERROR = "error"

class _SwitchWorker(QThread):
    """Фоновый поток для выполнения HTTP-запроса переключения, не блокирует GUI"""

    def __init__(self, service: 'LightSwitcherService', state: str):
        super().__init__()
        self._service = service
        self._state = state

    def run(self):
        state = self._state
        service = self._service
        print(f"DEBUG: Executing switch to {state} in background thread")

        data = {"state": state}
        success, result = service._make_request(
            "/light-switcher/switch", method="POST", data=data, timeout=service.switch_timeout
        )
        print(f"DEBUG: API request completed. Success: {success}")

        if success:
            message = result.get('message', 'Переключение успешно')
            data_result = result.get('data', {})
            current_state = data_result.get('current_state', 'unknown')

            with service._lock:
                try:
                    service.current_state = SwitchState(current_state)
                except ValueError:
                    service.current_state = SwitchState.ERROR

            if current_state == "state1":
                mode_text = "камера"
            elif current_state == "state2":
                mode_text = "спектрометр"
            else:
                mode_text = current_state

            user_message = f"Режим {mode_text}: {message}"
            print(f"DEBUG: Emitting switch_status_changed signal: {current_state}, {user_message}")
            service.switch_status_changed.emit(current_state, user_message)
        else:
            message = f"Ошибка переключения в {state}: {result}"
            with service._lock:
                service.current_state = SwitchState.ERROR

            print(f"DEBUG: Emitting error_occurred signal: {message}")
            service.error_occurred.emit(message)


class LightSwitcherService(QObject):
    """Сервис для управления переключателем света через API"""
    
    # Сигналы для UI
    connection_status_changed = pyqtSignal(bool, str)  # (connected, message)
    switch_started = pyqtSignal(str)  # (target_state)
    switch_status_changed = pyqtSignal(str, str)  # (state, message)
    error_occurred = pyqtSignal(str)  # (error_message)
    
    def __init__(self, base_url: str):
        super().__init__()
        self.base_url = base_url.rstrip('/')
        self.is_connected = False
        self.current_state = SwitchState.UNKNOWN
        self._lock = threading.Lock()
        self.logger = logger
        
        # Таймауты
        self.connection_timeout = 10.0
        self.switch_timeout = 25.0  # Больше чем на RaspberryPi для надежности
        
    def _make_request(self, endpoint: str, method: str = "GET", data: Optional[Dict] = None, timeout: float = 10.0) -> Tuple[bool, Any]:
        """
        Выполнить HTTP запрос к API
        
        Args:
            endpoint: Эндпоинт API
            method: HTTP метод
            data: Данные для POST запросов
            timeout: Таймаут запроса
            
        Returns:
            Tuple[bool, Any]: (успех, ответ или ошибка)
        """
        url = f"{self.base_url}{endpoint}"
        headers = {"Content-Type": "application/json", "Accept": "application/json"}
        
        try:
            if method.upper() == "GET":
                response = requests.get(url, headers=headers, timeout=timeout)
            elif method.upper() == "POST":
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
            else:
                return False, f"Unsupported HTTP method: {method}"
            
            if response.status_code == 200:
                return True, response.json()
            else:
                error_msg = f"HTTP {response.status_code}: {response.text}"
                self.logger.error(f"API request failed: {error_msg}")
                return False, error_msg
                
        except requests.exceptions.Timeout:
            error_msg = f"Request timeout after {timeout}s"
            self.logger.error(f"API request timeout: {url}")
            return False, error_msg
        except requests.exceptions.ConnectionError:
            error_msg = "Connection error - unable to reach server"
            self.logger.error(f"Connection error: {url}")
            return False, error_msg
        except requests.exceptions.RequestException as e:
            error_msg = f"Request exception: {str(e)}"
            self.logger.error(f"Request exception: {e}")
            return False, error_msg
        except Exception as e:
            error_msg = f"Unexpected error: {str(e)}"
            self.logger.error(f"Unexpected error: {e}")
            return False, error_msg
    
    def check_connection(self) -> Tuple[bool, str]:
        """
        Проверить статус подключения переключателя
        
        Returns:
            Tuple[bool, str]: (подключен, сообщение)
        """
        success, result = self._make_request("/light-switcher/status", timeout=self.connection_timeout)
        
        if success:
            status_data = result
            connected = status_data.get('connected', False)
            arduino_responsive = status_data.get('arduino_responsive', False)
            current_state = status_data.get('current_state', 'unknown')
            port = status_data.get('port', 'unknown')
            
            with self._lock:
                self.is_connected = connected and arduino_responsive
                try:
                    self.current_state = SwitchState(current_state)
                except ValueError:
                    self.current_state = SwitchState.UNKNOWN
            
            if self.is_connected:
                message = f"Переключатель подключен ({port}), состояние: {current_state}"
                self.connection_status_changed.emit(True, message)
                return True, message
            else:
                if not connected:
                    message = f"Переключатель не найден (автопоиск портов)"
                else:
                    message = f"Переключатель найден ({port}) но Arduino не отвечает"
                self.connection_status_changed.emit(False, message)
                return False, message
        else:
            with self._lock:
                self.is_connected = False
                self.current_state = SwitchState.UNKNOWN
            
            message = f"Ошибка проверки статуса: {result}"
            self.connection_status_changed.emit(False, message)
            return False, message
    
    def connect(self) -> Tuple[bool, str]:
        """
        Подключиться к переключателю
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        success, result = self._make_request("/light-switcher/connect", method="POST", timeout=self.connection_timeout)
        
        if success:
            message = result.get('message', 'Подключение успешно')
            data = result.get('data', {})
            port = data.get('port', 'unknown')
            
            # После подключения проверяем реальный статус
            check_success, check_message = self.check_connection()
            if check_success:
                return True, f"Подключено к {port}: {check_message}"
            else:
                return False, f"Подключение установлено но проверка не прошла: {check_message}"
        else:
            message = f"Ошибка подключения: {result}"
            with self._lock:
                self.is_connected = False
            
            self.connection_status_changed.emit(False, message)
            return False, message
    
    def disconnect(self) -> Tuple[bool, str]:
        """
        Отключиться от переключателя
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        success, result = self._make_request("/light-switcher/disconnect", method="POST")
        
        if success:
            message = result.get('message', 'Disconnection successful')
            with self._lock:
                self.is_connected = False
                self.current_state = SwitchState.UNKNOWN
            
            self.connection_status_changed.emit(False, message)
            return True, message
        else:
            message = f"Failed to disconnect: {result}"
            return False, message
    
    def switch_to_state(self, state: str) -> Tuple[bool, str]:
        """
        Переключить в указанное состояние
        
        Args:
            state: Целевое состояние ('state1' или 'state2')
            
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        if state not in ['state1', 'state2']:
            return False, f"Invalid state: {state}"
        
        with self._lock:
            if not self.is_connected:
                return False, "Switcher not connected"
        
        # Отправляем сигнал о начале переключения
        print(f"DEBUG: Emitting switch_started signal for state: {state}")
        self.switch_started.emit(state)
        
        # Запускаем HTTP-запрос в фоновом потоке, чтобы не блокировать GUI
        self._switch_worker = _SwitchWorker(self, state)
        self._switch_worker.start()
        
        return True, "Switching in progress..."
    
    def switch_to_camera_mode(self) -> Tuple[bool, str]:
        """Переключиться в режим камеры (state1)"""
        return self.switch_to_state("state1")
    
    def switch_to_spectrometer_mode(self) -> Tuple[bool, str]:
        """Переключиться в режим спектрометра (state2)"""
        return self.switch_to_state("state2")
    
    def get_status(self) -> Dict[str, Any]:
        """
        Получить текущий статус сервиса
        
        Returns:
            Dict[str, Any]: Информация о статусе
        """
        with self._lock:
            return {
                "connected": self.is_connected,
                "current_state": self.current_state.value,
                "base_url": self.base_url
            }
    
    def is_in_camera_mode(self) -> bool:
        """Проверить, находится ли переключатель в режиме камеры"""
        with self._lock:
            return self.current_state == SwitchState.STATE_1
    
    def is_in_spectrometer_mode(self) -> bool:
        """Проверить, находится ли переключатель в режиме спектрометра"""
        with self._lock:
            return self.current_state == SwitchState.STATE_2
