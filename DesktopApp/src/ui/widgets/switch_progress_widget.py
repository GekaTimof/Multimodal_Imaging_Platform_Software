#!/usr/bin/env python3
"""
Switch Progress Widget
Центрированная плашка для отображения прогресса переключения камеры
"""

from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, 
                             QFrame, QGraphicsOpacityEffect, QSizePolicy)
from PyQt5.QtCore import Qt, pyqtSlot, QTimer, QPropertyAnimation, QEasingCurve
from PyQt5.QtGui import QFont, QColor, QPalette
import logging

logger = logging.getLogger(__name__)

class SwitchProgressWidget(QWidget):
    """Центрированная плашка для отображения прогресса переключения"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent_window = parent
        # Получаем Interface_text из родительского окна
        self.interface_text = getattr(parent, 'interface_text', None)
        self.setup_ui()
        self.setup_animation()
        
    def setup_ui(self):
        """Настроить интерфейс виджета"""
        # Растягиваем на весь родительский виджет
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        
        # Основной layout с центрированием
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Добавляем растягивающееся пространство для центрирования
        main_layout.addStretch()
        
        # Создаем центрированный контейнер
        center_container = QWidget()
        center_container.setFixedSize(400, 150)  # Фиксированный размер
        center_layout = QVBoxLayout(center_container)
        center_layout.setContentsMargins(20, 20, 20, 20)
        center_layout.setSpacing(15)
        
        # Стиль контейнера
        center_container.setStyleSheet("""
            QWidget {
                background-color: rgba(33, 33, 33, 0.95);
                border: 2px solid #2196f3;
                border-radius: 12px;
            }
        """)
        
        # Иконка загрузки
        self.icon_label = QLabel("🔄")
        self.icon_label.setAlignment(Qt.AlignCenter)
        self.icon_label.setStyleSheet("""
            QLabel {
                font-size: 48px;
                color: #2196f3;
                background-color: transparent;
                border: none;
            }
        """)
        center_layout.addWidget(self.icon_label)
        
        # Текст "Switch camera"
        self.text_label = QLabel("Switch camera")
        self.text_label.setAlignment(Qt.AlignCenter)
        self.text_label.setStyleSheet("""
            QLabel {
                font-size: 18px;
                font-weight: bold;
                color: white;
                background-color: transparent;
                border: none;
            }
        """)
        center_layout.addWidget(self.text_label)
        
        # Описание
        self.desc_label = QLabel("Please wait while switching...")
        self.desc_label.setAlignment(Qt.AlignCenter)
        self.desc_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                color: #b0b0b0;
                background-color: transparent;
                border: none;
            }
        """)
        center_layout.addWidget(self.desc_label)
        
        # Добавляем центрированный контейнер в основной layout
        h_center_layout = QHBoxLayout()
        h_center_layout.addStretch()
        h_center_layout.addWidget(center_container)
        h_center_layout.addStretch()
        main_layout.addLayout(h_center_layout)
        
        # Добавляем растягивающееся пространство для центрирования
        main_layout.addStretch()
        
        # Изначально скрываем виджет
        self.setVisible(False)
        
        # Устанавливаем полупрозрачный фон для всего виджета
        self.setStyleSheet("""
            SwitchProgressWidget {
                background-color: rgba(0, 0, 0, 0.7);
            }
        """)
        
    def setup_animation(self):
        """Настроить анимации"""
        # Анимация появления/исчезновения
        self.opacity_effect = QGraphicsOpacityEffect()
        self.setGraphicsEffect(self.opacity_effect)
        self.opacity_effect.setOpacity(1.0)  # Полная непрозрачность по умолчанию
        
        self.fade_animation = QPropertyAnimation(self.opacity_effect, b"opacity")
        self.fade_animation.setDuration(300)
        self.fade_animation.setEasingCurve(QEasingCurve.InOutQuad)
        
        # Анимация вращения иконки
        self.icon_timer = QTimer()
        self.icon_timer.timeout.connect(self.rotate_icon)
        self.icon_rotation = 0
        
    @pyqtSlot()
    def rotate_icon(self):
        """Вращать иконку"""
        self.icon_rotation += 45
        icons = ["🔄", "⏳", "🔄", "⏳"]
        self.icon_label.setText(icons[(self.icon_rotation // 90) % 2])
        
    @pyqtSlot(str)
    def show_switch_progress(self, mode_text="camera"):
        """
        Показать плашку прогресса переключения
        
        Args:
            mode_text: Текст режима (camera/spectrometer)
        """
        print(f"DEBUG: Showing switch progress for mode: {mode_text}")  # Отладка
        
        # Обновляем текст в зависимости от режима
        if self.interface_text:
            if mode_text.lower() in ["camera", "камера", "state1"]:
                camera_text = self.interface_text.camera()
                self.text_label.setText(f"Switch {camera_text}")
                self.desc_label.setText(self.interface_text.light_switcher_switching_camera())
            elif mode_text.lower() in ["spectrometer", "спектрометр", "state2"]:
                spectrometer_text = self.interface_text.spectrometer()
                self.text_label.setText(f"Switch {spectrometer_text}")
                self.desc_label.setText(self.interface_text.light_switcher_switching_spectrometer())
            else:
                self.text_label.setText(f"Switch {mode_text}")
                self.desc_label.setText(self.interface_text.light_switcher_switching())
        else:
            # Fallback если interface_text недоступен
            if mode_text.lower() in ["camera", "камера", "state1"]:
                self.text_label.setText("Switch camera")
                self.desc_label.setText("Please wait while switching camera position...")
            elif mode_text.lower() in ["spectrometer", "спектрометр", "state2"]:
                self.text_label.setText("Switch spectrometer")
                self.desc_label.setText("Please wait while switching spectrometer position...")
            else:
                self.text_label.setText(f"Switch {mode_text}")
                self.desc_label.setText("Please wait while switching...")
        
        # Устанавливаем полную непрозрачность сразу
        self.opacity_effect.setOpacity(1.0)
        
        # Показываем виджет немедленно
        self.setVisible(True)
        self.raise_()  # Поднимаем на передний план
        
        # Обновляем геометрию для правильного позиционирования
        self.update_geometry()
        
        # Запускаем анимацию иконки
        self.icon_timer.start(500)  # Меняем иконку каждые 500мс
        
    def hide_switch_progress(self):
        """Скрыть плашку прогресса"""
        print("DEBUG: Hiding switch progress")  # Отладка
        
        # Останавливаем анимацию иконки
        self.icon_timer.stop()
        
        # Скрываем виджет немедленно (без анимации для надежности)
        self.setVisible(False)
        
    def _hide_widget(self):
        """Скрыть виджет после анимации"""
        self.setVisible(False)
        
    def resizeEvent(self, event):
        """Обработка изменения размера для сохранения центрирования"""
        super().resizeEvent(event)
        # Пересчитываем позицию при изменении размера родителя
        self.update_geometry()
    
    def update_geometry(self):
        """Обновить геометрию для правильного позиционирования"""
        if self.parent():
            # Занимаем всю область родительского виджета
            parent_rect = self.parent().rect()
            self.setGeometry(0, 0, parent_rect.width(), parent_rect.height())
            print(f"DEBUG: Updated geometry to {parent_rect.width()}x{parent_rect.height()}")
    
    def showEvent(self, event):
        """Обработка показа виджета"""
        super().showEvent(event)
        self.update_geometry()
        
    def parentChanged(self, parent):
        """Обработка смены родителя"""
        super().parentChanged(parent)
        if parent:
            # Поднимаем виджет на передний план
            self.raise_()
