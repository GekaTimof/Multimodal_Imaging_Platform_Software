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
        self.arduino_responsive = False
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
                
                # Сброс буферов после загрузки — убираем мусор от предыдущих сессий
                self.serial_connection.reset_input_buffer()
                self.serial_connection.reset_output_buffer()
                
                # Проверка что порт открыт
                if self.serial_connection.is_open:
                    self.is_connected = True
                    self.logger.info(f"Connected to Arduino on {self.port}")
                    self._test_connection()
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
                self.arduino_responsive = False
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
            self.serial_connection.timeout = 2.0  # Таймаут для ожидания ответа Arduino
            
            # Drain any pending input (don't discard mid-flight bytes with reset)
            if self.serial_connection.in_waiting:
                self.serial_connection.read(self.serial_connection.in_waiting)
            self.serial_connection.reset_output_buffer()
            
            # Отправляем команду set1 - если концевик нажат, ответит "alreadyset"
            self.serial_connection.write(b"set1\n")
            self.serial_connection.flush()
            
            # Ждем ответ (любой - done, alreadyset, timeout)
            # Read up to 5 lines: Arduino may emit noise lines before the real response
            EXPECTED = {"done", "alreadyset", "timeout"}
            response = None
            for _ in range(5):
                raw = self.serial_connection.readline().decode('utf-8', errors='replace')
                if not raw:
                    break
                # Extract all tokens from line (handles 'lde\ralreadyset' style)
                tokens = [t.strip() for t in raw.replace('\r', '\n').split('\n') if t.strip()]
                for token in tokens:
                    if token in EXPECTED:
                        response = token
                        break
                if response:
                    break
                self.logger.debug(f"Noise line ignored: {repr(raw)}")
            
            # Восстанавливаем таймаут
            self.serial_connection.timeout = old_timeout
            
            if response in EXPECTED:
                self.arduino_responsive = True
                return True
            self.arduino_responsive = False
            self.logger.debug(f"No expected response received, last raw: {repr(raw)}")
            return False
            
        except (serial.SerialException, OSError) as e:
            # Порт отключен физически или ошибка
            self.logger.warning(f"Connection test failed - port disconnected: {e}")
            self.is_connected = False
            self.arduino_responsive = False
            return False
        except Exception as e:
            self.logger.warning(f"Connection test failed: {e}")
            self.is_connected = False
            self.arduino_responsive = False
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
            # Drain any pending input (don't discard mid-flight bytes with reset)
            if self.serial_connection.in_waiting:
                self.serial_connection.read(self.serial_connection.in_waiting)
            self.serial_connection.reset_output_buffer()
            
            # Отправка команды
            cmd_with_newline = f"{command}\n"
            self.serial_connection.write(cmd_with_newline.encode('utf-8'))
            self.serial_connection.flush()
            
            self.logger.debug(f"Sent command: {command}")
            
            if expect_response:
                # Read up to 5 lines to find the actual keyword among noise lines
                EXPECTED = {"done", "alreadyset", "timeout", "unknown"}
                response = None
                raw = ''
                for _ in range(5):
                    raw = self.serial_connection.readline().decode('utf-8', errors='replace')
                    if not raw:
                        break
                    tokens = [t.strip() for t in raw.replace('\r', '\n').split('\n') if t.strip()]
                    for token in tokens:
                        if token in EXPECTED:
                            response = token
                            break
                    if response:
                        break
                    self.logger.debug(f"Noise line ignored: {repr(raw)}")
                result = response if response else ''
                self.logger.debug(f"Received response: {repr(raw)} -> parsed: {repr(result)}")
                return result
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
        for attempt in range(2):
            if not self.is_connected and not self.connect():
                return False, "Not connected to Arduino"
            old_timeout = self.serial_connection.timeout
            try:
                self.serial_connection.timeout = self.movement_timeout
                response = self._send_command("set1")
                
                if response == "done":
                    self.current_state = SwitchState.STATE_1
                    self.arduino_responsive = True
                    return True, "Successfully switched to state 1 (left end switch)"
                elif response == "alreadyset":
                    self.current_state = SwitchState.STATE_1
                    self.arduino_responsive = True
                    return True, "Already in state 1 (left end switch)"
                elif response == "timeout":
                    self.current_state = SwitchState.ERROR
                    self.arduino_responsive = True
                    return False, "Timeout while moving to state 1"
                elif response == "unknown":
                    self.arduino_responsive = True
                    return False, "Unknown command received"
                else:
                    self.current_state = SwitchState.ERROR
                    return False, f"Unexpected response: {response}"
                    
            except (serial.SerialException, OSError):
                self.is_connected = False
                self.arduino_responsive = False
                if attempt == 0:
                    self.logger.warning("Serial error on state1, reconnecting...")
                    self.port = None
                    continue
                self.current_state = SwitchState.ERROR
                return False, "Serial connection lost, reconnect failed"
            except Exception as e:
                self.current_state = SwitchState.ERROR
                return False, f"Error switching to state 1: {str(e)}"
            finally:
                if self.serial_connection:
                    self.serial_connection.timeout = old_timeout
        return False, "Failed to switch to state 1 after reconnect"
    
    def switch_to_state_2(self) -> Tuple[bool, str]:
        """
        Switch to state 2 (right end switch).
        
        Returns:
            Tuple[bool, str]: (success, message)
        """
        for attempt in range(2):
            if not self.is_connected and not self.connect():
                return False, "Not connected to Arduino"
            old_timeout = self.serial_connection.timeout
            try:
                self.serial_connection.timeout = self.movement_timeout
                response = self._send_command("set2")
                
                if response == "done":
                    self.current_state = SwitchState.STATE_2
                    self.arduino_responsive = True
                    return True, "Successfully switched to state 2 (right end switch)"
                elif response == "alreadyset":
                    self.current_state = SwitchState.STATE_2
                    self.arduino_responsive = True
                    return True, "Already in state 2 (right end switch)"
                elif response == "timeout":
                    self.current_state = SwitchState.ERROR
                    self.arduino_responsive = True
                    return False, "Timeout while moving to state 2"
                elif response == "unknown":
                    self.arduino_responsive = True
                    return False, "Unknown command received"
                else:
                    self.current_state = SwitchState.ERROR
                    return False, f"Unexpected response: {response}"
                    
            except (serial.SerialException, OSError):
                self.is_connected = False
                self.arduino_responsive = False
                if attempt == 0:
                    self.logger.warning("Serial error on state2, reconnecting...")
                    self.port = None
                    continue
                self.current_state = SwitchState.ERROR
                return False, "Serial connection lost, reconnect failed"
            except Exception as e:
                self.current_state = SwitchState.ERROR
                return False, f"Error switching to state 2: {str(e)}"
            finally:
                if self.serial_connection:
                    self.serial_connection.timeout = old_timeout
        return False, "Failed to switch to state 2 after reconnect"
    
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
            "arduino_responsive": self.arduino_responsive
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
