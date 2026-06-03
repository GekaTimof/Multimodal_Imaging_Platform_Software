"""
Main Window Controller
Manages the main application window with tabbed interface for different device modes.

The application provides three main tabs:
- Spectrometer: For spectrometer device control
- Camera: For camera device control and imaging
- Acquisition: For acquisition analysis functionality
"""

import logging
import sys
import os

from PyQt5.QtWidgets import (
    QMainWindow, QTabWidget, QVBoxLayout, QWidget, QHBoxLayout,
    QPushButton, QApplication, QMessageBox
)
from PyQt5.QtCore import QTimer, Qt, QThread, pyqtSignal, QProcess
from PyQt5.QtGui import QFont
from ui.tabs.spectrometer_tab import SpectrometerTab
from ui.tabs.camera_tab import CameraTab
from ui.tabs.Acquisition_tab import AcquisitionTab
from ui.widgets.light_switcher_status_widget import LightSwitcherStatusWidget
from ui.widgets.switch_progress_widget import SwitchProgressWidget
from ui.widgets.interface_settings_dialog import InterfaceSettingsDialog
from models.interface_text import Interface_text
from config import interface_config
from config.theme_manager import ThemeManager
from resources.language_variations.language_link import Languages
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

        # Startup worker thread (check connection + initial mode switch)
        self._startup_thread = None
        self._startup_overlay_shown = False
        # Skip network calls in handle_tab_change until startup is done
        self._init_complete = False
        
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
        self._start_maximized = window_config.get('start_maximized', True)

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
        status_height = interface_config.get('ui_scaling.status_bar_height', 52)
        status_container.setMinimumHeight(status_height)
        status_container.setMaximumHeight(status_height)
        status_layout = QHBoxLayout(status_container)
        status_layout.setContentsMargins(0, 2, 0, 2)
        status_layout.setSpacing(0)

        # Create status widget for light switcher
        self.light_switcher_status = LightSwitcherStatusWidget(self)
        status_layout.addWidget(self.light_switcher_status)
        main_layout.addWidget(status_container)
        
        # Create centered switch progress widget (overlay)
        self.switch_progress = SwitchProgressWidget(self)
        self.switch_progress.setParent(self.tabs)
        self.switch_progress.raise_()
        
        self.setCentralWidget(main_widget)

        # Corner widget: theme toggle + language switcher + interface settings
        self._build_corner_widget()

        # Apply current font from config
        self._apply_font()

        # Show window immediately WITH overlay, before heavy tab construction
        title = self.interface_text.connecting_title()
        desc = self.interface_text.connecting_desc()
        self.switch_progress.show_startup_progress(title, desc)

        if self._start_maximized:
            self.showMaximized()
        else:
            self.show()

        # Force Qt to paint the window + overlay now
        QApplication.processEvents()

        # Defer heavy tab creation to next event-loop tick
        QTimer.singleShot(0, self._deferred_init)

    def _deferred_init(self):
        """Create tabs and wire signals — runs after the window is already visible."""
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

        # Kick off background connection check + initial mode switch
        self._start_startup_worker()

    # ------------------------------------------------------------------ #
    #  Corner widget (top-right of tab bar)                               #
    # ------------------------------------------------------------------ #

    def _build_corner_widget(self):
        """Create the top-right corner widget with theme, language and settings buttons."""
        corner = QWidget()
        row = QHBoxLayout(corner)
        row.setContentsMargins(4, 2, 8, 2)
        row.setSpacing(4)

        # Theme toggle button
        self._theme_btn = QPushButton("☽" if self.theme_manager.is_dark else "☀")
        self._theme_btn.setFixedSize(38, 32)
        self._theme_btn.setToolTip("Toggle dark/light theme")
        self._theme_btn.clicked.connect(self._on_theme_toggle)
        self.theme_manager.theme_changed.connect(self._on_theme_changed)
        row.addWidget(self._theme_btn)

        # Language switcher button (shows current abbreviation)
        self._lang_btn = QPushButton(self.interface_text.abbreviation())
        self._lang_btn.setFixedSize(44, 32)
        self._lang_btn.setToolTip("Switch language")
        self._lang_btn.clicked.connect(self._on_language_toggle)
        row.addWidget(self._lang_btn)

        # Interface settings button
        self._settings_btn = QPushButton("⚙")
        self._settings_btn.setFixedSize(38, 32)
        self._settings_btn.setToolTip(
            self.interface_text.interface_settings()
            if hasattr(self.interface_text, 'interface_settings') else "Interface Settings"
        )
        self._settings_btn.clicked.connect(self._on_interface_settings)
        row.addWidget(self._settings_btn)

        self.tabs.setCornerWidget(corner, Qt.TopRightCorner)

    def _on_theme_toggle(self):
        """Toggle dark/light theme."""
        self.theme_manager.toggle()

    def _on_theme_changed(self, dark: bool):
        """Update theme button icon when theme changes."""
        self._theme_btn.setText("☽" if dark else "☀")

    def _on_language_toggle(self):
        """Cycle through available languages and restart the application."""
        available = list(Languages.keys())
        current = interface_config.get('language.default', 'English')
        try:
            idx = available.index(current)
        except ValueError:
            idx = 0
        next_lang = available[(idx + 1) % len(available)]

        # Save new language to config
        try:
            interface_config.set_language(next_lang)
        except Exception as e:
            logger.error(f"Error saving language: {e}")
            return

        # Restart application
        self._restart_application()

    def _restart_application(self):
        """Restart the application process."""
        logger.info("Restarting application...")
        # Use absolute path of the script for reliable restart
        args = sys.argv[:]
        if args and not os.path.isabs(args[0]):
            args[0] = os.path.abspath(args[0])
        QProcess.startDetached(sys.executable, args)
        QApplication.instance().quit()

    def _on_interface_settings(self):
        """Open the interface settings dialog."""
        dialog = InterfaceSettingsDialog(
            interface_text=self.interface_text,
            parent=self
        )
        dialog.settings_applied.connect(self._apply_font)
        dialog.exec_()

    def _apply_font(self):
        """Apply font family and size from config to the whole application."""
        try:
            family = interface_config.get('ui_scaling.font_family', 'DejaVu Sans')
            size = interface_config.get('ui_scaling.font_point_size', 11)
            font = QFont(family, size)
            app = QApplication.instance()
            app.setFont(font)
            # Force all existing widgets to pick up the new font
            for widget in app.allWidgets():
                widget.setFont(font)
        except Exception as e:
            logger.error(f"Error applying font: {e}")

    # ------------------------------------------------------------------ #
    #  Startup background worker                                           #
    # ------------------------------------------------------------------ #

    def _start_startup_worker(self):
        """Run connection check + initial mode switch in a background thread."""
        current_tab = self.tabs.currentIndex()

        worker = _StartupWorker(current_tab)
        worker.connection_result.connect(self._on_startup_connection_result)
        worker.mode_result.connect(self._on_startup_mode_result)
        worker.finished.connect(self._on_startup_finished)
        worker.finished.connect(worker.deleteLater)
        self._startup_thread = worker
        worker.start()

    def _on_startup_connection_result(self, success: bool, message: str):
        """Called from the main thread with the connection-check result."""
        self.light_switcher_status.show_checking_status()
        self.light_switcher_status.update_connection_status(success, message)

    def _on_startup_mode_result(self, success: bool, message: str):
        """Called from the main thread with the initial mode-switch result."""
        if not success:
            self.light_switcher_status.show_error(f"Ошибка при начальном переключении: {message}")

    def _on_startup_finished(self):
        """Hide the startup overlay once all background work is done."""
        if hasattr(self, 'switch_progress'):
            self.switch_progress.hide_switch_progress()
        self._startup_thread = None
        # Now that the background startup is done, allow normal tab switching
        self._init_complete = True

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
        """Проверить начальное подключение переключателя (deprecated — use _start_startup_worker)"""
        pass

    def handle_tab_change(self, index):
        """
        Handle tab switching by activating appropriate device mode
        and switching device settings to the corresponding type.
        
        Args:
            index (int): Index of selected tab (0=Spectrometer, 1=Camera, 2=Acquisition)
        """
        # During __init__ the initial mode switch is handled by _StartupWorker,
        # so skip network calls until the window is fully shown.
        if not self._init_complete:
            self._previous_tab_index = index
            return

        try:
            # Stop spectrometer when leaving spectrometer tab (index 0)
            if self._previous_tab_index == 0 and index != 0:
                self.spectrometer_tab.stop_spectrometer()

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
        """Переключиться в режим соответствующий начальной вкладке (deprecated — done by _StartupWorker)"""
        pass
    
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
            self.switch_progress.setGeometry(self.tabs.rect())
            self.switch_progress.raise_()

    def closeEvent(self, event):
        """Handle window close - stop all devices."""
        logger.info("Closing application - stopping all devices...")
        
        # Stop spectrometer if running
        if hasattr(self, 'spectrometer_tab'):
            try:
                self.spectrometer_tab.stop_spectrometer()
                logger.info("Spectrometer stopped")
            except Exception as e:
                logger.error(f"Error stopping spectrometer: {e}")
        
        # Stop camera if running
        if hasattr(self, 'camera_tab'):
            try:
                self.camera_tab.stop_camera()
                logger.info("Camera stopped")
            except Exception as e:
                logger.error(f"Error stopping camera: {e}")
        
        # Call closeEvent on all tabs to clean up resources
        if hasattr(self, 'spectrometer_tab'):
            self.spectrometer_tab.closeEvent(event)
        if hasattr(self, 'camera_tab'):
            self.camera_tab.closeEvent(event)
        
        super().closeEvent(event)


# ---------------------------------------------------------------------------
# Background worker: connection check + initial mode switch
# ---------------------------------------------------------------------------

class _StartupWorker(QThread):
    """
    Runs two blocking network calls off the main thread so the UI stays
    responsive during startup:
      1. check_switcher_connection()
      2. switch_to_<mode>_mode() for the currently selected tab
    Results are emitted as Qt signals so slots run safely in the GUI thread.
    """

    connection_result = pyqtSignal(bool, str)
    mode_result = pyqtSignal(bool, str)

    def __init__(self, current_tab: int, parent=None):
        super().__init__(parent)
        self._current_tab = current_tab

    def run(self):
        # 1 — connection check
        try:
            success, message = check_switcher_connection()
        except Exception as e:
            success, message = False, str(e)
        self.connection_result.emit(success, message)

        # 2 — initial mode switch
        try:
            if self._current_tab == 0:
                ok, msg = switch_to_spectrometer_mode()
            elif self._current_tab == 1:
                ok, msg = switch_to_camera_mode()
            elif self._current_tab == 2:
                ok, msg = switch_to_Acquisition_mode()
            else:
                ok, msg = True, ""
        except Exception as e:
            ok, msg = False, str(e)
        self.mode_result.emit(ok, msg)
