#!/usr/bin/env python3
"""
Light Switcher Status Widget
Виджет для отображения статуса переключателя и управления подключением
"""

from PyQt5.QtWidgets import (QFrame, QHBoxLayout, QLabel, QPushButton, 
                             QMessageBox)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
from PyQt5.QtGui import QFont, QColor, QPalette
import logging

logger = logging.getLogger(__name__)

class LightSwitcherStatusWidget(QFrame):
    """Виджет для отображения статуса переключателя света"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.setup_ui()
        self.setup_timer()
        
    def setup_ui(self):
        """Настроить интерфейс виджета"""
        # Основной layout
        layout = QHBoxLayout(self)
        layout.setContentsMargins(10, 5, 10, 5)
        layout.setSpacing(10)
        
        # Стиль виджета
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin: 2px;
            }
            QLabel {
                font-size: 12px;
                font-weight: bold;
            }
            QPushButton {
                font-size: 11px;
                padding: 4px 8px;
                border-radius: 3px;
            }
        """)
        
        # Иконка статуса
        self.status_icon = QLabel("⚪")
        self.status_icon.setFixedSize(16, 16)
        self.status_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_icon)
        
        # Текст статуса
        self.status_label = QLabel("Проверка подключения...")
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.status_label)
        
        # Кнопка повторного подключения
        self.retry_button = QPushButton("Повторить")
        self.retry_button.clicked.connect(self.retry_connection)
        self.retry_button.setVisible(False)
        layout.addWidget(self.retry_button)
        
        # Кнопка сброса ошибки
        self.reset_button = QPushButton("Сбросить ошибку")
        self.reset_button.clicked.connect(self.reset_error)
        self.reset_button.setVisible(False)
        layout.addWidget(self.reset_button)
        
        # Растягивающийся spacer
        layout.addStretch()
        
        # Изначально скрываем виджет
        self.setVisible(False)
        
    def setup_timer(self):
        """Настроить таймер для автоматического скрытия сообщений"""
        self.hide_timer = QTimer()
        self.hide_timer.timeout.connect(self.hide_widget)
        self.hide_timer.setSingleShot(True)
        
    @pyqtSlot(bool, str)
    def update_connection_status(self, connected: bool, message: str):
        """
        Обновить статус подключения
        
        Args:
            connected: Статус подключения
            message: Сообщение о статусе
        """
        self.setVisible(True)
        
        if connected:
            # Успешное подключение
            self.status_icon.setText("🟢")
            self.status_label.setText(f"Переключатель подключен: {message}")
            self.retry_button.setVisible(False)
            self.reset_button.setVisible(False)
            
            # Зеленый фон для успеха
            self.setStyleSheet("""
                QFrame {
                    background-color: #e8f5e8;
                    border: 1px solid #4caf50;
                    border-radius: 5px;
                    margin: 2px;
                }
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: #2e7d32;
                }
                QPushButton {
                    font-size: 11px;
                    padding: 4px 8px;
                    border-radius: 3px;
                }
            """)
            
            # Автоматически скрыть через 5 секунд
            self.hide_timer.start(5000)
            
        else:
            # Ошибка подключения
            self.status_icon.setText("🔴")
            self.status_label.setText(f"Переключатель не подключен: {message}")
            self.retry_button.setVisible(True)
            self.reset_button.setVisible(False)
            
            # Красный фон для ошибки
            self.setStyleSheet("""
                QFrame {
                    background-color: #ffebee;
                    border: 1px solid #f44336;
                    border-radius: 5px;
                    margin: 2px;
                }
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: #c62828;
                }
                QPushButton {
                    font-size: 11px;
                    padding: 4px 8px;
                    border-radius: 3px;
                    background-color: #f44336;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #d32f2f;
                }
            """)
            
            # Не скрывать автоматически - нужно действие от пользователя
            
    @pyqtSlot(str)
    def show_switching_progress(self, target_state: str):
        """
        Показать прогресс переключения
        
        Args:
            target_state: Целевое состояние переключения
        """
        self.setVisible(True)
        
        # Определяем текст режима
        mode_text = "камера" if target_state == "state1" else "спектрометр"
        
        self.status_icon.setText("⏳")
        self.status_label.setText(f"Переключение в режим {mode_text}...")
        self.retry_button.setVisible(False)
        self.reset_button.setVisible(False)
        
        # Синий фон для ожидания
        self.setStyleSheet("""
            QFrame {
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 5px;
                margin: 2px;
            }
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #1976d2;
            }
            QPushButton {
                font-size: 11px;
                padding: 4px 8px;
                border-radius: 3px;
            }
        """)
        
        # Отменяем таймер скрытия - показываем пока идет переключение
        self.hide_timer.stop()

    @pyqtSlot(str, str)
    def update_switch_status(self, state: str, message: str):
        """
        Обновить статус переключения
        
        Args:
            state: Текущее состояние
            message: Сообщение о переключении
        """
        self.setVisible(True)
        
        if state in ["state1", "state2"]:
            # Успешное переключение
            self.status_icon.setText("🟢")
            mode_text = "камера" if state == "state1" else "спектрометр"
            self.status_label.setText(f"Режим {mode_text}: {message}")
            self.retry_button.setVisible(False)
            self.reset_button.setVisible(False)
            
            # Зеленый фон
            self.setStyleSheet("""
                QFrame {
                    background-color: #e8f5e8;
                    border: 1px solid #4caf50;
                    border-radius: 5px;
                    margin: 2px;
                }
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: #2e7d32;
                }
                QPushButton {
                    font-size: 11px;
                    padding: 4px 8px;
                    border-radius: 3px;
                }
            """)
            
            # Автоматически скрыть через 3 секунды
            self.hide_timer.start(3000)
            
        else:
            # Ошибка переключения
            self.status_icon.setText("🟡")
            self.status_label.setText(f"Ошибка переключения: {message}")
            self.retry_button.setVisible(False)
            self.reset_button.setVisible(True)
            
            # Желтый фон для предупреждения
            self.setStyleSheet("""
                QFrame {
                    background-color: #fff8e1;
                    border: 1px solid #ff9800;
                    border-radius: 5px;
                    margin: 2px;
                }
                QLabel {
                    font-size: 12px;
                    font-weight: bold;
                    color: #f57c00;
                }
                QPushButton {
                    font-size: 11px;
                    padding: 4px 8px;
                    border-radius: 3px;
                    background-color: #ff9800;
                    color: white;
                    border: none;
                }
                QPushButton:hover {
                    background-color: #f57c00;
                }
            """)
            
            # Не скрывать автоматически - нужно действие от пользователя
            
    @pyqtSlot(str)
    def show_error(self, error_message: str):
        """
        Показать ошибку
        
        Args:
            error_message: Текст ошибки
        """
        self.setVisible(True)
        self.status_icon.setText("🔴")
        self.status_label.setText(f"Ошибка: {error_message}")
        self.retry_button.setVisible(True)
        self.reset_button.setVisible(False)
        
        # Красный фон
        self.setStyleSheet("""
            QFrame {
                background-color: #ffebee;
                border: 1px solid #f44336;
                border-radius: 5px;
                margin: 2px;
            }
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #c62828;
            }
            QPushButton {
                font-size: 11px;
                padding: 4px 8px;
                border-radius: 3px;
                background-color: #f44336;
                color: white;
                border: none;
            }
            QPushButton:hover {
                background-color: #d32f2f;
            }
        """)
        
    def retry_connection(self):
        """Повторить подключение"""
        try:
            from services.raspberry_mode import connect_switcher
            success, message = connect_switcher()
            
            if success:
                self.update_connection_status(True, message)
            else:
                self.update_connection_status(False, message)
                
        except Exception as e:
            logger.error(f"Error retrying connection: {e}")
            self.show_error(f"Ошибка при повторном подключении: {str(e)}")
            
    def reset_error(self):
        """Сбросить ошибку переключения"""
        try:
            from services.raspberry_mode import check_switcher_connection
            success, message = check_switcher_connection()
            
            if success:
                self.update_connection_status(True, message)
            else:
                self.update_connection_status(False, message)
                
        except Exception as e:
            logger.error(f"Error resetting error: {e}")
            self.show_error(f"Ошибка при сбросе: {str(e)}")
            
    def hide_widget(self):
        """Скрыть виджет"""
        self.setVisible(False)
        
    def show_checking_status(self):
        """Показать статус проверки"""
        self.setVisible(True)
        self.status_icon.setText("⚪")
        self.status_label.setText("Проверка подключения...")
        self.retry_button.setVisible(False)
        self.reset_button.setVisible(False)
        
        # Нейтральный фон
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin: 2px;
            }
            QLabel {
                font-size: 12px;
                font-weight: bold;
                color: #666666;
            }
            QPushButton {
                font-size: 11px;
                padding: 4px 8px;
                border-radius: 3px;
            }
        """)
