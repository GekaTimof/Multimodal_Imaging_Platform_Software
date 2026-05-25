"""
Main Window Controller
Manages the main application window with tabbed interface for different device modes.

The application provides three main tabs:
- Spectrometer: For spectrometer device control
- Camera: For camera device control and imaging
- Acquisition: For acquisition analysis functionality
"""

import logging

from PyQt5.QtWidgets import QMainWindow, QTabWidget, QVBoxLayout, QWidget, QHBoxLayout
from PyQt5.QtCore import QTimer
from ui.tabs.spectrometer_tab import SpectrometerTab
from ui.tabs.camera_tab import CameraTab
from ui.tabs.Acquisition_tab import AcquisitionTab
from ui.widgets.light_switcher_status_widget import LightSwitcherStatusWidget
from ui.widgets.switch_progress_widget import SwitchProgressWidget
from models.interface_text import Interface_text
from config import interface_config
from config.theme_manager import ThemeManager
from services.raspberry_mode import (
    switch_to_camera_mode,
    switch_to_spectrometer_mode,
    switch_to_Acquisition_mode,
    check_switcher_connection,
    get_light_switcher_service,
)

logger = logging.getLogger(__name__)


class MainWindow(QMainWindow):
    """
    Main application window with tabbed interface.
    
    Manages three device tabs and handles mode switching when tabs are changed.
    """
    
    def __init__(self):
        """Initialize main window with configuration-based settings."""
        super().__init__()
        
        # Load language from config
        default_language = interface_config.get('language.default', 'English')
        self.interface_text = Interface_text(default_language)

        # Theme manager — single source of truth for dark/light theme
        self.theme_manager = ThemeManager(interface_config)
        self.theme_manager.apply_current_theme()
        
        # Configure window from config
        window_config = interface_config.get_window_config()
        self.setWindowTitle(window_config.get('title', 'Lab App'))
        self.resize(window_config.get('width', 1400), window_config.get('height', 800))
        
        if window_config.get('start_maximized', True):
            self.showMaximized()
        
        # Set resizable property
        if not window_config.get('resizable', True):
            self.setFixedSize(self.size())

        # Create main widget and layout
        main_widget = QWidget()
        main_layout = QVBoxLayout(main_widget)
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)

        # Create tab widget
        self.tabs = QTabWidget()
        main_layout.addWidget(self.tabs)

        # Create status container with fixed height to prevent layout shifts
        status_container = QWidget()
        status_container.setMinimumHeight(44)
        status_container.setMaximumHeight(44)
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 2, 0, 2)
        status_layout.setSpacing(0)

        # Create status widget for light switcher
        self.light_switcher_status = LightSwitcherStatusWidget(self)
        status_layout.addWidget(self.light_switcher_status)
        main_layout.addWidget(status_container)
        
        # Create centered switch progress widget (overlay)
        self.switch_progress = SwitchProgressWidget(self)
        self.switch_progress.setParent(self.tabs)  # Накладываем на вкладки
        self.switch_progress.raise_()  # Поднимаем на передний план
        
        # Set main widget as central widget
        self.setCentralWidget(main_widget)

        # Initialize device tabs
        self.spectrometer_tab = SpectrometerTab(self.interface_text, self.theme_manager)
        self.camera_tab = CameraTab(self.interface_text, self.theme_manager)
        self.Acquisition_tab = AcquisitionTab(self.interface_text, self.theme_manager)

        # Track previous tab index for cleanup when leaving camera tab
        self._previous_tab_index = 0
        
        # Connect tab change handler
        self.tabs.currentChanged.connect(self.handle_tab_change)

        # Add tabs to interface
        self.tabs.addTab(self.spectrometer_tab, self.interface_text.spectrometer())
        self.tabs.addTab(self.camera_tab, self.interface_text.camera())
        self.tabs.addTab(self.Acquisition_tab, self.interface_text.Acquisition())
        
        # Set default tab from config
        tabs_config = interface_config.get_tabs_config()
        default_tab = tabs_config.get('default_tab', 0)
        self.tabs.setCurrentIndex(default_tab)
        
        # Setup light switcher service connections
        self.setup_light_switcher_connections()
        
        # Check light switcher connection on startup
        self.check_initial_connection()
        
        # Switch to mode corresponding to initial tab
        QTimer.singleShot(1000, self.switch_to_initial_mode)  # Задержка 1 секунда для инициализации

    def setup_light_switcher_connections(self):
        """Настроить соединения для сервиса переключателя"""
        try:
            light_switcher_service = get_light_switcher_service()
            
            # Подключаем сигналы к слотам виджета статуса
            light_switcher_service.connection_status_changed.connect(
                self.light_switcher_status.update_connection_status
            )
            light_switcher_service.switch_started.connect(
                self.light_switcher_status.show_switching_progress
            )
            light_switcher_service.switch_status_changed.connect(
                self.light_switcher_status.update_switch_status
            )
            light_switcher_service.error_occurred.connect(
                self.light_switcher_status.show_error
            )
            
            # Подключаем сигналы к центрированной плашке прогресса
            light_switcher_service.switch_started.connect(
                self.switch_progress.show_switch_progress
            )
            light_switcher_service.switch_status_changed.connect(
                self.switch_progress.hide_switch_progress
            )
            light_switcher_service.error_occurred.connect(
                self.switch_progress.hide_switch_progress
            )

        except Exception as e:
            logger.error(f"Error setting up light switcher connections: {e}")
    
    def check_initial_connection(self):
        """Проверить начальное подключение переключателя"""
        try:
            # Показать статус проверки
            self.light_switcher_status.show_checking_status()
            
            # Проверить подключение
            success, message = check_switcher_connection()
            
            if success:
                self.light_switcher_status.update_connection_status(True, message)
            else:
                self.light_switcher_status.update_connection_status(False, message)
                
        except Exception as e:
            logger.error(f"Error checking initial connection: {e}")
            self.light_switcher_status.show_error(f"Ошибка при проверке подключения: {str(e)}")

    def handle_tab_change(self, index):
        """
        Handle tab switching by activating appropriate device mode
        and switching device settings to the corresponding type.
        
        Args:
            index (int): Index of selected tab (0=Spectrometer, 1=Camera, 2=Acquisition)
        """
        try:
            # Stop camera when leaving camera tab (index 1)
            if self._previous_tab_index == 1 and index != 1:
                self.camera_tab.stop_camera()
            
            if index == 0:
                # Switch to spectrometer mode
                success, message = switch_to_spectrometer_mode()
                if not success:
                    # Показать ошибку, но продолжить переключение вкладки
                    self.light_switcher_status.show_error(f"Ошибка запуска переключения: {message}")
                
                # Switch device settings to Spectrometer
                self.spectrometer_tab.device_settings_widget.switch_to_settings(self.interface_text.spectrometer())
                
            elif index == 1:
                # Switch to camera mode
                success, message = switch_to_camera_mode()
                if not success:
                    # Показать ошибку, но продолжить переключение вкладки
                    self.light_switcher_status.show_error(f"Ошибка запуска переключения: {message}")
                
                self.camera_tab.device_settings_widget.switch_to_settings(self.interface_text.camera())
                
            elif index == 2:
                # Switch to Acquisition mode (uses camera state)
                success, message = switch_to_Acquisition_mode()
                if not success:
                    # Показать ошибку, но продолжить переключение вкладки
                    self.light_switcher_status.show_error(f"Ошибка запуска переключения: {message}")
                
                # Switch device settings to Positioner for Acquisition
                self.Acquisition_tab.device_settings_widget.switch_to_settings(self.interface_text.positioner())
            
            # Update previous tab index for next change
            self._previous_tab_index = index
            
        except Exception as e:
            logger.error(f"Error handling tab change: {e}")
            self.light_switcher_status.show_error(f"Ошибка при смене вкладки: {str(e)}")
            # Still update the index even on error
            self._previous_tab_index = index
    
    def switch_to_initial_mode(self):
        """Переключиться в режим соответствующий начальной вкладке"""
        try:
            current_tab = self.tabs.currentIndex()
            logger.debug(f"Switching to initial mode for tab {current_tab}")
            
            if current_tab == 0:
                # Spectrometer mode
                success, message = switch_to_spectrometer_mode()
                logger.debug(f"Initial spectrometer switch result: {success}, {message}")
            elif current_tab == 1:
                # Camera mode
                success, message = switch_to_camera_mode()
                logger.debug(f"Initial camera switch result: {success}, {message}")
            elif current_tab == 2:
                # Acquisition mode (uses camera state)
                success, message = switch_to_Acquisition_mode()
                logger.debug(f"Initial Acquisition switch result: {success}, {message}")
                
        except Exception as e:
            logger.error(f"Error switching to initial mode: {e}")
            self.light_switcher_status.show_error(f"Ошибка при начальном переключении: {str(e)}")
    
    def resizeEvent(self, event):
        """Обработка изменения размера окна для обновления позиции центрированной плашки"""
        super().resizeEvent(event)
        if hasattr(self, 'switch_progress'):
            # Обновляем геометрию центрированной плашки
            self.switch_progress.setGeometry(self.tabs.rect())
            self.switch_progress.update_geometry()
    
    def showEvent(self, event):
        """Обработка показа главного окна"""
        super().showEvent(event)
        if hasattr(self, 'switch_progress'):
            # Убедимся что плашка правильно позиционирована
            self.switch_progress.setGeometry(self.tabs.rect())
            self.switch_progress.raise_()  # Поднимаем на передний план
