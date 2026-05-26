"""
Theme Manager
Single source of truth for application-wide dark/light theme.
Applies a QSS stylesheet to QApplication and persists the choice via InterfaceConfig.
"""

import logging
from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtWidgets import QApplication

logger = logging.getLogger(__name__)

DARK_QSS = """
QWidget {
    background-color: #2b2b2b;
    color: #f0f0f0;
}
QMainWindow, QDialog {
    background-color: #2b2b2b;
}
QTabWidget::pane {
    border: 1px solid #555;
    background-color: #2b2b2b;
}
QTabBar::tab {
    background-color: #3c3f41;
    color: #f0f0f0;
    padding: 6px 14px;
    border: 1px solid #555;
    border-bottom: none;
}
QTabBar::tab:selected {
    background-color: #4c5052;
}
QPushButton {
    background-color: #4c5052;
    color: #f0f0f0;
    border: 1px solid #666;
    padding: 4px 8px;
    border-radius: 3px;
}
QPushButton:hover {
    background-color: #5c6062;
}
QPushButton:pressed {
    background-color: #3c3f41;
}
QPushButton:disabled {
    color: #888;
    background-color: #3a3a3a;
}
QComboBox {
    background-color: #3c3f41;
    color: #f0f0f0;
    border: 1px solid #666;
    padding: 3px 6px;
    border-radius: 3px;
}
QComboBox QAbstractItemView {
    background-color: #3c3f41;
    color: #f0f0f0;
    selection-background-color: #4c5052;
}
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #3c3f41;
    color: #f0f0f0;
    border: 1px solid #666;
    padding: 3px;
    border-radius: 3px;
}
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #303030;
    color: #777;
    border: 1px solid #444;
}
QLabel {
    background-color: transparent;
    color: #f0f0f0;
}
QScrollArea, QScrollBar {
    background-color: #2b2b2b;
}
QListWidget {
    background-color: #3c3f41;
    color: #f0f0f0;
    border: 1px solid #666;
}
QListWidget::item:selected {
    background-color: #4c5052;
}
QProgressBar {
    background-color: #3c3f41;
    border: 1px solid #666;
    border-radius: 3px;
    text-align: center;
    color: #f0f0f0;
}
QProgressBar::chunk {
    background-color: #4a90d9;
}
QGroupBox {
    color: #f0f0f0;
    border: 1px solid #555;
    margin-top: 6px;
    padding-top: 4px;
}
QGroupBox::title {
    color: #f0f0f0;
}
QCheckBox {
    color: #f0f0f0;
}
QRadioButton {
    color: #f0f0f0;
}
"""

LIGHT_QSS = """
QWidget {
    background-color: #f5f5f5;
    color: #1a1a1a;
}
QMainWindow, QDialog {
    background-color: #f5f5f5;
}
QTabWidget::pane {
    border: 1px solid #bbb;
    background-color: #f5f5f5;
}
QTabBar::tab {
    background-color: #e0e0e0;
    color: #1a1a1a;
    padding: 6px 14px;
    border: 1px solid #bbb;
    border-bottom: none;
}
QTabBar::tab:selected {
    background-color: #f5f5f5;
}
QPushButton {
    background-color: #e0e0e0;
    color: #1a1a1a;
    border: 1px solid #aaa;
    padding: 4px 8px;
    border-radius: 3px;
}
QPushButton:hover {
    background-color: #d0d0d0;
}
QPushButton:pressed {
    background-color: #c0c0c0;
}
QPushButton:disabled {
    color: #888;
    background-color: #e8e8e8;
}
QComboBox {
    background-color: #ffffff;
    color: #1a1a1a;
    border: 1px solid #aaa;
    padding: 3px 6px;
    border-radius: 3px;
}
QComboBox QAbstractItemView {
    background-color: #ffffff;
    color: #1a1a1a;
    selection-background-color: #d0e4f7;
}
QLineEdit, QSpinBox, QDoubleSpinBox {
    background-color: #ffffff;
    color: #1a1a1a;
    border: 1px solid #aaa;
    padding: 3px;
    border-radius: 3px;
}
QLineEdit:disabled, QSpinBox:disabled, QDoubleSpinBox:disabled {
    background-color: #eeeeee;
    color: #888;
    border: 1px solid #ccc;
}
QLabel {
    background-color: transparent;
    color: #1a1a1a;
}
QScrollArea, QScrollBar {
    background-color: #f5f5f5;
}
QListWidget {
    background-color: #ffffff;
    color: #1a1a1a;
    border: 1px solid #aaa;
}
QListWidget::item:selected {
    background-color: #d0e4f7;
}
QProgressBar {
    background-color: #e0e0e0;
    border: 1px solid #aaa;
    border-radius: 3px;
    text-align: center;
    color: #1a1a1a;
}
QProgressBar::chunk {
    background-color: #4a90d9;
}
QGroupBox {
    color: #1a1a1a;
    border: 1px solid #bbb;
    margin-top: 6px;
    padding-top: 4px;
}
QGroupBox::title {
    color: #1a1a1a;
}
QCheckBox {
    color: #1a1a1a;
}
QRadioButton {
    color: #1a1a1a;
}
"""


class ThemeManager(QObject):
    """
    Application-wide theme manager.

    Usage:
        theme_manager = ThemeManager(interface_config)
        theme_manager.apply_current_theme()
        theme_manager.theme_changed.connect(some_slot)
        theme_manager.toggle()
    """

    theme_changed = pyqtSignal(bool)  # True = dark

    def __init__(self, interface_config, parent=None):
        super().__init__(parent)
        self._config = interface_config
        self._is_dark = interface_config.get('theme.default', 'light') == 'dark'

    @property
    def is_dark(self) -> bool:
        return self._is_dark

    def apply_current_theme(self):
        """Apply the currently stored theme to QApplication."""
        app = QApplication.instance()
        if app is None:
            return
        app.setStyleSheet(DARK_QSS if self._is_dark else LIGHT_QSS)

    def set_dark(self, dark: bool):
        """Set theme and apply it application-wide."""
        if self._is_dark == dark:
            return
        self._is_dark = dark
        self._config.set_theme('dark' if dark else 'light')
        self.apply_current_theme()
        self.theme_changed.emit(self._is_dark)
        logger.debug(f"Theme switched to {'dark' if dark else 'light'}")

    def toggle(self):
        """Toggle between dark and light theme."""
        self.set_dark(not self._is_dark)
