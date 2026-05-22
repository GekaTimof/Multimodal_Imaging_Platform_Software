#!/usr/bin/env python3
"""
Light Switcher Service for Arduino End Switch Control
Сервис для управления Arduino переключателем концевиков
"""

import serial
import time
import logging
import threading
from typing import Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class SwitchState(Enum):
    """Состояния переключателя"""
    STATE_1 = "state1"  # Левый концевик
    STATE_2 = "state2"  # Правый концевик
    UNKNOWN = "unknown"
    ERROR = "error"

class LightSwitcherService:
    """Сервис для управления Arduino переключателем"""
    
    def __init__(self, port: str = "/dev/ttyUSB0", baudrate: int = 9600, timeout: float = 2.0):
        """
        Инициализация сервиса
        
        Args:
            port: Serial порт для подключения Arduino
            baudrate: Скорость передачи данных
            timeout: Таймаут ожидания ответа
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.current_state = SwitchState.UNKNOWN
        self._lock = threading.Lock()
        self.logger = logger
        
    def connect(self) -> bool:
        """
        Подключение к Arduino
        
        Returns:
            bool: True если подключение успешно
        """
        try:
            with self._lock:
                if self.serial_connection and self.serial_connection.is_open:
                    self.serial_connection.close()
                    
                self.serial_connection = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout,
                    write_timeout=self.timeout
                )
                
                # Ожидание инициализации Arduino
                time.sleep(2)
                
                # Проверка связи
                if self._test_connection():
                    self.is_connected = True
                    self.logger.info(f"Connected to Arduino on {self.port}")
                    return True
                else:
                    self.serial_connection.close()
                    self.is_connected = False
                    return False
                    
        except serial.SerialException as e:
            self.logger.error(f"Failed to connect to Arduino on {self.port}: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            self.logger.error(f"Unexpected error during connection: {e}")
            self.is_connected = False
            return False
    
    def disconnect(self):
        """Отключение от Arduino"""
        try:
            with self._lock:
                if self.serial_connection and self.serial_connection.is_open:
                    self.serial_connection.close()
                self.is_connected = False
                self.logger.info("Disconnected from Arduino")
        except Exception as e:
            self.logger.error(f"Error during disconnection: {e}")
    
    def _test_connection(self) -> bool:
        """
        Тестирование соединения с Arduino
        
        Returns:
            bool: True если связь установлена
        """
        try:
            # Отправка тестовой команды для проверки
            response = self._send_command("test", expect_response=False)
            # Если нет исключений, соединение работает
            return True
        except Exception:
            return False
    
    def _send_command(self, command: str, expect_response: bool = True) -> Optional[str]:
        """
        Отправка команды в Arduino
        
        Args:
            command: Команда для отправки
            expect_response: Ожидать ли ответ
            
        Returns:
            Optional[str]: Ответ от Arduino или None
        """
        if not self.is_connected or not self.serial_connection:
            raise ConnectionError("Not connected to Arduino")
        
        try:
            # Очистка буферов
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            # Отправка команды
            cmd_with_newline = f"{command}\n"
            self.serial_connection.write(cmd_with_newline.encode('utf-8'))
            self.serial_connection.flush()
            
            self.logger.debug(f"Sent command: {command}")
            
            if expect_response:
                # Ожидание ответа
                response = self.serial_connection.readline().decode('utf-8').strip()
                self.logger.debug(f"Received response: {response}")
                return response
            else:
                return None
                
        except serial.SerialTimeoutException:
            self.logger.error(f"Timeout sending command: {command}")
            raise
        except serial.SerialException as e:
            self.logger.error(f"Serial error sending command {command}: {e}")
            self.is_connected = False
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error sending command {command}: {e}")
            raise
    
    def switch_to_state_1(self) -> Tuple[bool, str]:
        """
        Переключение в состояние 1 (левый концевик)
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            response = self._send_command("set1")
            
            if response == "done":
                self.current_state = SwitchState.STATE_1
                return True, "Successfully switched to state 1 (left end switch)"
            elif response == "alreadyset":
                self.current_state = SwitchState.STATE_1
                return True, "Already in state 1 (left end switch)"
            elif response == "timeout":
                self.current_state = SwitchState.ERROR
                return False, "Timeout while moving to state 1"
            elif response == "unknown":
                return False, "Unknown command received"
            else:
                self.current_state = SwitchState.ERROR
                return False, f"Unexpected response: {response}"
                
        except Exception as e:
            self.current_state = SwitchState.ERROR
            return False, f"Error switching to state 1: {str(e)}"
    
    def switch_to_state_2(self) -> Tuple[bool, str]:
        """
        Переключение в состояние 2 (правый концевик)
        
        Returns:
            Tuple[bool, str]: (успех, сообщение)
        """
        try:
            response = self._send_command("set2")
            
            if response == "done":
                self.current_state = SwitchState.STATE_2
                return True, "Successfully switched to state 2 (right end switch)"
            elif response == "alreadyset":
                self.current_state = SwitchState.STATE_2
                return True, "Already in state 2 (right end switch)"
            elif response == "timeout":
                self.current_state = SwitchState.ERROR
                return False, "Timeout while moving to state 2"
            elif response == "unknown":
                return False, "Unknown command received"
            else:
                self.current_state = SwitchState.ERROR
                return False, f"Unexpected response: {response}"
                
        except Exception as e:
            self.current_state = SwitchState.ERROR
            return False, f"Error switching to state 2: {str(e)}"
    
    def get_status(self) -> dict:
        """
        Получение статуса сервиса
        
        Returns:
            dict: Информация о статусе
        """
        return {
            "connected": self.is_connected,
            "port": self.port,
            "baudrate": self.baudrate,
            "current_state": self.current_state.value,
            "arduino_responsive": self._test_connection() if self.is_connected else False
        }
    
    def __enter__(self):
        """Context manager entry"""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit"""
        self.disconnect()

# Глобальный экземпляр сервиса
light_switcher_service = LightSwitcherService()

if __name__ == "__main__":
    # Тестирование сервиса
    service = LightSwitcherService()
    
    try:
        print("Testing Light Switcher Service...")
        
        # Подключение
        if service.connect():
            print("✓ Connected to Arduino")
            
            # Получение статуса
            status = service.get_status()
            print(f"Status: {status}")
            
            # Тест переключения в состояние 1
            print("\nTesting switch to state 1...")
            success, message = service.switch_to_state_1()
            print(f"Result: {success}, Message: {message}")
            
            time.sleep(2)
            
            # Тест переключения в состояние 2
            print("\nTesting switch to state 2...")
            success, message = service.switch_to_state_2()
            print(f"Result: {success}, Message: {message}")
            
        else:
            print("✗ Failed to connect to Arduino")
            
    except KeyboardInterrupt:
        print("\nTest interrupted by user")
    except Exception as e:
        print(f"Error during test: {e}")
    finally:
        service.disconnect()
        print("Test completed")
