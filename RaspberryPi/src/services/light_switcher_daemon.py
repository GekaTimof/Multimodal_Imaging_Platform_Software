#!/usr/bin/env python3
"""
Light Switcher Daemon
Демон для поддержания постоянной работы Arduino переключателя
"""

import time
import signal
import sys
import logging
import os
from threading import Event
from src.services.light_switcher_service import light_switcher_service, SwitchState

class LightSwitcherDaemon:
    """Демон для управления световым переключателем"""
    
    def __init__(self):
        self.running = Event()
        self.logger = self._setup_logging()
        
    def _setup_logging(self):
        """Настройка логирования"""
        # Derive log directory relative to this file's location (…/RaspberryPi/logs)
        base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
        log_dir = os.path.join(base_dir, 'logs')
        os.makedirs(log_dir, exist_ok=True)
        
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(f"{log_dir}/light_switcher_daemon.log"),
                logging.StreamHandler(sys.stdout)
            ]
        )
        return logging.getLogger(__name__)
    
    def _signal_handler(self, signum, frame):
        """Обработчик сигналов для graceful shutdown"""
        self.logger.info(f"Received signal {signum}, shutting down...")
        self.running.clear()
    
    def _monitor_connection(self):
        """Мониторинг и восстановление соединения с Arduino"""
        while self.running.is_set():
            try:
                # Проверка статуса соединения
                status = light_switcher_service.get_status()
                
                if not status['connected'] or not status['arduino_responsive']:
                    self.logger.warning("Connection lost or Arduino not responsive, attempting to reconnect...")
                    
                    # Попытка переподключения
                    if light_switcher_service.connect():
                        self.logger.info("Successfully reconnected to Arduino")
                    else:
                        self.logger.error("Failed to reconnect to Arduino, will retry in 30 seconds")
                
                # Пауза между проверками
                self.running.wait(30)
                
            except Exception as e:
                self.logger.error(f"Error in connection monitoring: {e}")
                self.running.wait(30)
    
    def start(self):
        """Запуск демона"""
        self.logger.info("Starting Light Switcher Daemon...")
        
        # Установка обработчиков сигналов
        signal.signal(signal.SIGTERM, self._signal_handler)
        signal.signal(signal.SIGINT, self._signal_handler)
        
        # Установка флага работы
        self.running.set()
        
        try:
            # Первичное подключение к Arduino
            self.logger.info("Attempting to connect to Arduino...")
            if light_switcher_service.connect():
                self.logger.info("Successfully connected to Arduino")
                status = light_switcher_service.get_status()
                self.logger.info(f"Initial status: {status}")
            else:
                self.logger.warning("Failed to connect to Arduino on startup, will retry...")
            
            # Основной цикл демона
            self.logger.info("Daemon started, monitoring connection...")
            self._monitor_connection()
            
        except KeyboardInterrupt:
            self.logger.info("Daemon interrupted by user")
        except Exception as e:
            self.logger.error(f"Unexpected error in daemon: {e}")
        finally:
            self.stop()
    
    def stop(self):
        """Остановка демона"""
        self.logger.info("Stopping Light Switcher Daemon...")
        self.running.clear()
        
        # Отключение от Arduino
        try:
            light_switcher_service.disconnect()
            self.logger.info("Disconnected from Arduino")
        except Exception as e:
            self.logger.error(f"Error during disconnection: {e}")
        
        self.logger.info("Daemon stopped")

def main():
    """Главная функция"""
    daemon = LightSwitcherDaemon()
    
    try:
        daemon.start()
    except Exception as e:
        logging.error(f"Failed to start daemon: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
