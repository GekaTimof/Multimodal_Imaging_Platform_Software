#!/usr/bin/env python3
"""
Light Switcher Service for Arduino End Switch Control
Service for managing Arduino end switch controller
"""

import serial
import time
import logging
import threading
import glob
from typing import Optional, Tuple
from enum import Enum

logger = logging.getLogger(__name__)

class SwitchState(Enum):
    """Switch states"""
    STATE_1 = "state1"  # Left end switch
    STATE_2 = "state2"  # Right end switch
    UNKNOWN = "unknown"
    ERROR = "error"

class LightSwitcherService:
    """Service for managing Arduino switch controller"""
    
    def __init__(self, port: str = None, baudrate: int = 9600, timeout: float = 2.0, movement_timeout: float = 20.0):
        """
        Initialize the service.
        
        Args:
            port: Serial port for Arduino connection (None for auto-detection)
            baudrate: Communication baud rate
            timeout: Response timeout
        """
        self.port = port
        self.baudrate = baudrate
        self.timeout = timeout
        self.movement_timeout = movement_timeout  # Timeout for motor movement commands
        self.serial_connection: Optional[serial.Serial] = None
        self.is_connected = False
        self.current_state = SwitchState.UNKNOWN
        self._lock = threading.Lock()
        self.logger = logger
        
    def _find_arduino_port(self) -> Optional[str]:
        """
        Auto-detect Arduino port.
        Checks /dev/ttyUSB* and /dev/ttyACM*.
        
        Returns:
            str: Port path or None if not found
        """
        # Ищем USB Serial порты
        patterns = ['/dev/ttyUSB*', '/dev/ttyACM*']
        for pattern in patterns:
            ports = glob.glob(pattern)
            for port in sorted(ports):
                try:
                    # Пробуем открыть порт
                    ser = serial.Serial(port, self.baudrate, timeout=1)
                    ser.close()
                    # Если порт открылся - считаем что это Arduino
                    self.logger.info(f"Found Arduino on {port}")
                    return port
                except (serial.SerialException, OSError):
                    continue
                except Exception:
                    continue
        
        return None
        
    def connect(self) -> bool:
        """
        Connect to Arduino.
        If no port was specified, automatically searches for Arduino.
        
        Returns:
            bool: True if connection was successful
        """
        try:
            with self._lock:
                if self.serial_connection and self.serial_connection.is_open:
                    self.serial_connection.close()
                
                # Если порт не указан или не существует - ищем автоматически
                if self.port is None or not glob.glob(self.port):
                    found_port = self._find_arduino_port()
                    if found_port:
                        self.port = found_port
                        self.logger.info(f"Auto-detected Arduino on {self.port}")
                    else:
                        self.logger.error("Arduino not found on any port")
                        self.is_connected = False
                        return False
                
                self.serial_connection = serial.Serial(
                    port=self.port,
                    baudrate=self.baudrate,
                    timeout=self.timeout,
                    write_timeout=self.timeout
                )
                
                # Ожидание инициализации Arduino (reset after open)
                time.sleep(2.5)
                
                # Проверка что порт открыт
                if self.serial_connection.is_open:
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
        """Disconnect from Arduino"""
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
        Test connection to Arduino.
        Sends a real command to verify Arduino is responding.
        
        Returns:
            bool: True if connection is established and Arduino is responsive
        """
        if not self.is_connected or not self.serial_connection:
            return False
        if not self.serial_connection.is_open:
            self.is_connected = False
            return False
        try:
            # Реальная проверка - отправляем команду и проверяем ответ
            # Используем "set1" с очень коротким таймаутом как ping
            old_timeout = self.serial_connection.timeout
            self.serial_connection.timeout = 0.5  # Короткий таймаут для проверки
            
            # Очистка буферов
            self.serial_connection.reset_input_buffer()
            self.serial_connection.reset_output_buffer()
            
            # Отправляем команду set1 - если концевик нажат, ответит "alreadyset"
            self.serial_connection.write(b"set1\n")
            self.serial_connection.flush()
            
            # Ждем ответ (любой - done, alreadyset, timeout)
            response = self.serial_connection.readline().decode('utf-8').strip()
            
            # Восстанавливаем таймаут
            self.serial_connection.timeout = old_timeout
            
            # Если получили любой ответ - Arduino жив
            if response in ["done", "alreadyset", "timeout"]:
                return True
            return False
            
        except (serial.SerialException, OSError) as e:
            # Порт отключен физически или ошибка
            self.logger.warning(f"Connection test failed - port disconnected: {e}")
            self.is_connected = False
            return False
        except Exception as e:
            self.logger.warning(f"Connection test failed: {e}")
            self.is_connected = False
            return False
        finally:
            # Восстанавливаем таймаут в любом случае
            try:
                if self.serial_connection:
                    self.serial_connection.timeout = old_timeout
            except:
                pass
    
    def _send_command(self, command: str, expect_response: bool = True) -> Optional[str]:
        """
        Send command to Arduino.
        
        Args:
            command: Command to send
            expect_response: Whether to wait for a response
            
        Returns:
            Optional[str]: Response from Arduino or None
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
        except (serial.SerialException, OSError) as e:
            self.logger.error(f"Serial error sending command {command}: {e}")
            self.is_connected = False
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error sending command {command}: {e}")
            raise
    
    def switch_to_state_1(self) -> Tuple[bool, str]:
        """
        Switch to state 1 (left end switch).
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Temporarily increase timeout for movement command (up to 15s + buffer)
            old_timeout = self.serial_connection.timeout
            self.serial_connection.timeout = self.movement_timeout
            response = self._send_command("set1")
            self.serial_connection.timeout = old_timeout
            
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
        Switch to state 2 (right end switch).
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        try:
            # Temporarily increase timeout for movement command
            old_timeout = self.serial_connection.timeout
            self.serial_connection.timeout = self.movement_timeout
            response = self._send_command("set2")
            self.serial_connection.timeout = old_timeout
            
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
        Get service status.
        
        Returns:
            dict: Status information
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

# Global service instance (with auto port detection)
light_switcher_service = LightSwitcherService(port=None)

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
