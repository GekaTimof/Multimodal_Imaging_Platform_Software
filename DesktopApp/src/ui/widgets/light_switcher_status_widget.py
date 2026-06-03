#!/usr/bin/env python3
"""
Light Switcher Status Widget
Виджет для отображения статуса переключателя и управления подключением
"""

from PyQt5.QtWidgets import QFrame, QHBoxLayout, QLabel, QPushButton
from PyQt5.QtCore import Qt, pyqtSlot, QTimer
import logging
from config import interface_config
from models.interface_text import Interface_text

logger = logging.getLogger(__name__)

class LightSwitcherStatusWidget(QFrame):
    """Виджет для отображения статуса переключателя света"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        self.interface_text = getattr(parent, 'interface_text', Interface_text('English'))
        self.setup_ui()
        self.setup_timer()
        
    def _status_font_pt(self) -> int:
        """Return status label font size in pt from config."""
        return interface_config.get('ui_scaling.error_font_size', 12)

    def _btn_font_pt(self) -> int:
        """Return button font size in pt (1pt less than status font)."""
        return max(7, self._status_font_pt() - 1)

    def setup_ui(self):
        """Настроить интерфейс виджета"""
        # Основной layout
        layout = QHBoxLayout(self)
        m = interface_config.get('ui_scaling.font_point_size', 11) // 2
        layout.setContentsMargins(m * 2, m, m * 2, m)
        layout.setSpacing(m * 2)
        
        fs = self._status_font_pt()
        bfs = self._btn_font_pt()
        # Стиль виджета
        self.setFrameStyle(QFrame.StyledPanel)
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin: 2px;
            }}
            QLabel {{
                font-size: {fs}pt;
                font-weight: bold;
            }}
            QPushButton {{
                font-size: {bfs}pt;
                padding: 4px 8px;
                border-radius: 3px;
            }}
        """)
        
        # Иконка статуса
        self.status_icon = QLabel("⚪")
        self.status_icon.setFixedSize(16, 16)
        self.status_icon.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.status_icon)
        
        # Текст статуса
        self.status_label = QLabel(self.interface_text.light_switcher_checking())
        self.status_label.setAlignment(Qt.AlignLeft | Qt.AlignVCenter)
        layout.addWidget(self.status_label)
        
        # Кнопка повторного подключения
        self.retry_button = QPushButton(self.interface_text.light_switcher_reconnect())
        self.retry_button.clicked.connect(self.retry_connection)
        self.retry_button.setVisible(False)
        layout.addWidget(self.retry_button)
        
        # Кнопка сброса ошибки
        self.reset_button = QPushButton(self.interface_text.light_switcher_reset())
        self.reset_button.clicked.connect(self.reset_error)
        self.reset_button.setVisible(False)
        layout.addWidget(self.reset_button)
        
        # Растягивающийся spacer
        layout.addStretch()

        # Изначально скрываем виджет (контейнер в main_window сохраняет фиксированный размер)
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
            self.status_label.setText(self.interface_text.light_switcher_connected().format(message=message))
            self.retry_button.setVisible(False)
            self.reset_button.setVisible(False)
            
            # Зеленый фон для успеха
            fs = self._status_font_pt()
            bfs = self._btn_font_pt()
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #e8f5e8;
                    border: 1px solid #4caf50;
                    border-radius: 5px;
                    margin: 2px;
                }}
                QLabel {{
                    font-size: {fs}pt;
                    font-weight: bold;
                    color: #2e7d32;
                }}
                QPushButton {{
                    font-size: {bfs}pt;
                    padding: 4px 8px;
                    border-radius: 3px;
                }}
            """)
            
            # Автоматически скрыть через 5 секунд
            self.hide_timer.start(5000)
            
        else:
            # Ошибка подключения
            self.status_icon.setText("🔴")
            self.status_label.setText(self.interface_text.light_switcher_disconnected().format(message=message))
            self.retry_button.setVisible(True)
            self.reset_button.setVisible(False)
            
            # Красный фон для ошибки
            fs = self._status_font_pt()
            bfs = self._btn_font_pt()
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #ffebee;
                    border: 1px solid #f44336;
                    border-radius: 5px;
                    margin: 2px;
                }}
                QLabel {{
                    font-size: {fs}pt;
                    font-weight: bold;
                    color: #c62828;
                }}
                QPushButton {{
                    font-size: {bfs}pt;
                    padding: 4px 8px;
                    border-radius: 3px;
                    background-color: #f44336;
                    color: white;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: #d32f2f;
                }}
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
        mode_text = self.interface_text.camera() if target_state == "state1" else self.interface_text.spectrometer()
        
        self.status_icon.setText("⏳")
        self.status_label.setText(self.interface_text.light_switcher_switching().format(mode_text=mode_text))
        self.retry_button.setVisible(False)
        self.reset_button.setVisible(False)
        
        # Синий фон для ожидания
        fs = self._status_font_pt()
        bfs = self._btn_font_pt()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #e3f2fd;
                border: 1px solid #2196f3;
                border-radius: 5px;
                margin: 2px;
            }}
            QLabel {{
                font-size: {fs}pt;
                font-weight: bold;
                color: #1976d2;
            }}
            QPushButton {{
                font-size: {bfs}pt;
                padding: 4px 8px;
                border-radius: 3px;
            }}
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
            # Сообщение уже содержит информацию о режиме, используем его напрямую
            self.status_label.setText(message)
            self.retry_button.setVisible(False)
            self.reset_button.setVisible(False)
            
            # Зеленый фон
            fs = self._status_font_pt()
            bfs = self._btn_font_pt()
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #e8f5e8;
                    border: 1px solid #4caf50;
                    border-radius: 5px;
                    margin: 2px;
                }}
                QLabel {{
                    font-size: {fs}pt;
                    font-weight: bold;
                    color: #2e7d32;
                }}
                QPushButton {{
                    font-size: {bfs}pt;
                    padding: 4px 8px;
                    border-radius: 3px;
                }}
            """)
            
            # Автоматически скрыть через 3 секунды
            self.hide_timer.start(3000)
            
        else:
            # Ошибка переключения
            self.status_icon.setText("🟡")
            self.status_label.setText(self.interface_text.light_switcher_switch_error().format(message=message))
            self.retry_button.setVisible(False)
            self.reset_button.setVisible(True)
            
            # Желтый фон для предупреждения
            fs = self._status_font_pt()
            bfs = self._btn_font_pt()
            self.setStyleSheet(f"""
                QFrame {{
                    background-color: #fff8e1;
                    border: 1px solid #ff9800;
                    border-radius: 5px;
                    margin: 2px;
                }}
                QLabel {{
                    font-size: {fs}pt;
                    font-weight: bold;
                    color: #f57c00;
                }}
                QPushButton {{
                    font-size: {bfs}pt;
                    padding: 4px 8px;
                    border-radius: 3px;
                    background-color: #ff9800;
                    color: white;
                    border: none;
                }}
                QPushButton:hover {{
                    background-color: #f57c00;
                }}
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
        self.status_label.setText(self.interface_text.light_switcher_error().format(error_message=error_message))
        self.retry_button.setVisible(True)
        self.reset_button.setVisible(False)
        
        # Красный фон
        fs = self._status_font_pt()
        bfs = self._btn_font_pt()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #ffebee;
                border: 1px solid #f44336;
                border-radius: 5px;
                margin: 2px;
            }}
            QLabel {{
                font-size: {fs}pt;
                font-weight: bold;
                color: #c62828;
            }}
            QPushButton {{
                font-size: {bfs}pt;
                padding: 4px 8px;
                border-radius: 3px;
                background-color: #f44336;
                color: white;
                border: none;
            }}
            QPushButton:hover {{
                background-color: #d32f2f;
            }}
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
            self.show_error(self.interface_text.light_switcher_error().format(error_message=f"Reconnection error: {str(e)}"))
            
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
            self.show_error(self.interface_text.light_switcher_error().format(error_message=f"Reset error: {str(e)}"))
            
    def refresh_style(self):
        """Re-apply the current stylesheet with updated font sizes from config."""
        css = self.styleSheet()
        if not css:
            return
        import re
        fs = self._status_font_pt()
        bfs = self._btn_font_pt()
        css = re.sub(r'(QLabel\s*\{[^}]*font-size:\s*)\d+(pt)', rf'\g<1>{fs}\2', css)
        css = re.sub(r'(QPushButton\s*\{[^}]*font-size:\s*)\d+(pt)', rf'\g<1>{bfs}\2', css)
        self.setStyleSheet(css)

    def hide_widget(self):
        """Скрыть виджет"""
        self.setVisible(False)
        
    def show_checking_status(self):
        """Показать статус проверки"""
        self.setVisible(True)
        self.status_icon.setText("⚪")
        self.status_label.setText(self.interface_text.light_switcher_checking())
        self.retry_button.setVisible(False)
        self.reset_button.setVisible(False)
        
        # Нейтральный фон
        fs = self._status_font_pt()
        bfs = self._btn_font_pt()
        self.setStyleSheet(f"""
            QFrame {{
                background-color: #f0f0f0;
                border: 1px solid #cccccc;
                border-radius: 5px;
                margin: 2px;
            }}
            QLabel {{
                font-size: {fs}pt;
                font-weight: bold;
                color: #666666;
            }}
            QPushButton {{
                font-size: {bfs}pt;
                padding: 4px 8px;
                border-radius: 3px;
            }}
        """)
