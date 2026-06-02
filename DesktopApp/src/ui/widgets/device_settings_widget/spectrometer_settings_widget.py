"""
Spectrometer Settings Widget
Widget for configuring spectrometer parameters (integral time, dark spectrum, overillumination threshold).
Supports both basic and advanced settings with FastAPI integration.
"""

import logging
from typing import List

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget,
    QHBoxLayout, QCheckBox, QLineEdit,
    QGridLayout
)

from core.constants.ui_strings import SettingsWidgetStrings
from .api_client_thread import APIClientThread
from config.api_config import ENDPOINTS

logger = logging.getLogger(__name__)


class SpectrometerSettingsWidget(QWidget):
    """Widget for spectrometer settings configuration."""

    integral_time_changed = pyqtSignal(int)
    set_dark_requested = pyqtSignal()
    clear_dark_requested = pyqtSignal()
    load_dark_requested = pyqtSignal()  # No filepath - API loads from standard location
    settings_changed = pyqtSignal(dict)  # settings dict

    def __init__(self, interface_text=None, spectrometer_service=None):
        super().__init__()
        self.interface_text = interface_text
        self.spectrometer_service = spectrometer_service
        self.current_settings = {}
        self.active_threads: List[QThread] = []
        self._build_ui()

        # Connect service signals if available
        if self.spectrometer_service:
            self.spectrometer_service.settings_updated.connect(self._on_settings_updated)
            self.spectrometer_service.error_occurred.connect(self._on_error)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        settings_layout = QGridLayout()
        settings_layout.setContentsMargins(5, 5, 5, 5)
        settings_layout.setHorizontalSpacing(10)
        settings_layout.setVerticalSpacing(8)

        # Settings Name
        settings_name_label = QLabel(
            self.interface_text.settings_name() if self.interface_text else SettingsWidgetStrings.SETTINGS_NAME
        )
        settings_name_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(settings_name_label, 0, 0, 1, 2)

        self.settings_name = QLineEdit()
        self.settings_name.setPlaceholderText("Enter settings name...")
        settings_layout.addWidget(self.settings_name, 1, 0, 1, 2)

        # Integral time
        it_label = QLabel(
            self.interface_text.integral_time() if self.interface_text else SettingsWidgetStrings.INTEGRAL_TIME
        )
        it_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(it_label, 2, 0)

        self.integral_time_input = QSpinBox()
        self.integral_time_input.setRange(1, 99999)
        self.integral_time_input.setValue(100)
        self.integral_time_input.setSuffix(" ms")
        self.integral_time_input.valueChanged.connect(self._on_integral_time_changed)
        settings_layout.addWidget(self.integral_time_input, 3, 0, 1, 2)

        # Auto dark correction
        self.auto_dark_checkbox = QCheckBox(
            self.interface_text.auto_dark_correction() if self.interface_text else SettingsWidgetStrings.AUTO_DARK_CORRECTION
        )
        self.auto_dark_checkbox.setChecked(True)
        self.auto_dark_checkbox.stateChanged.connect(self._on_settings_changed)
        settings_layout.addWidget(self.auto_dark_checkbox, 4, 0, 1, 2)

        # Overillumination threshold
        oi_label = QLabel(
            self.interface_text.overillumination_threshold() if self.interface_text else SettingsWidgetStrings.OVERILLUMINATION_THRESHOLD
        )
        oi_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(oi_label, 5, 0)

        self.overillumination_input = QSpinBox()
        self.overillumination_input.setRange(0, 65535)
        self.overillumination_input.setValue(65535)
        settings_layout.addWidget(self.overillumination_input, 6, 0, 1, 2)

        # Dark Spectrum section
        dark_label = QLabel(
            self.interface_text.dark_spectrum() if self.interface_text else SettingsWidgetStrings.DARK_SPECTRUM_STATUS
        )
        dark_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(dark_label, 7, 0, 1, 2)

        self.dark_status_label = QLabel(SettingsWidgetStrings.NO_DARK_SPECTRUM)
        self.dark_status_label.setStyleSheet("color: gray;")
        settings_layout.addWidget(self.dark_status_label, 8, 0, 1, 2)

        # Dark spectrum buttons
        dark_buttons_layout = QHBoxLayout()

        self.set_dark_button = QPushButton(
            self.interface_text.set_dark_spectrum() if self.interface_text else SettingsWidgetStrings.CAPTURE_DARK
        )
        self.set_dark_button.clicked.connect(self._on_capture_dark)
        dark_buttons_layout.addWidget(self.set_dark_button)

        self.clear_dark_button = QPushButton(
            self.interface_text.clear_dark_spectrum() if self.interface_text else SettingsWidgetStrings.CLEAR_DARK
        )
        self.clear_dark_button.clicked.connect(self._on_clear_dark)
        dark_buttons_layout.addWidget(self.clear_dark_button)

        self.load_dark_button = QPushButton(
            self.interface_text.load_dark() if self.interface_text else SettingsWidgetStrings.LOAD_DARK
        )
        self.load_dark_button.clicked.connect(self._on_load_dark)
        dark_buttons_layout.addWidget(self.load_dark_button)

        settings_layout.addLayout(dark_buttons_layout, 9, 0, 1, 2)

        layout.addLayout(settings_layout)

        # Buttons row - same style as camera (Apply, Load, Save)
        button_row_layout = QHBoxLayout()

        self.btn_apply = QPushButton(
            self.interface_text.apply() if self.interface_text else SettingsWidgetStrings.APPLY
        )
        self.btn_apply.setToolTip("Apply current settings to spectrometer immediately")
        button_row_layout.addWidget(self.btn_apply)

        self.btn_reload = QPushButton(
            self.interface_text.reload() if self.interface_text else SettingsWidgetStrings.RELOAD
        )
        self.btn_reload.setToolTip("Reload settings from server")
        button_row_layout.addWidget(self.btn_reload)

        self.btn_save = QPushButton(
            self.interface_text.save() if self.interface_text else SettingsWidgetStrings.SAVE
        )
        self.btn_save.setToolTip("Save current settings to server database")
        button_row_layout.addWidget(self.btn_save)

        button_row_layout.addStretch()

        layout.addLayout(button_row_layout)

        # Status label (same style as camera)
        self.status_label = QLabel(SettingsWidgetStrings.READY)
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        self.status_label.setWordWrap(True)
        self.status_label.setMaximumWidth(300)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Connect buttons
        self.btn_apply.clicked.connect(self._apply_settings)
        self.btn_reload.clicked.connect(self._reload_settings_async)
        self.btn_save.clicked.connect(self._save_settings_async)

        # Load initial settings
        self._load_initial_settings()

    def _on_integral_time_changed(self, value):
        """Handle integral time change."""
        self.integral_time_changed.emit(value)
        self.current_settings['IntegralTime'] = value
        self._on_settings_changed()

    def _on_settings_changed(self):
        """Handle any settings change."""
        self.current_settings.update({
            'SettingsName': self.settings_name.text(),
            'IntegralTime': self.integral_time_input.value(),
            'AutoDarkCorrection': self.auto_dark_checkbox.isChecked(),
            'OverilluminationThreshold': self.overillumination_input.value()
        })
        self.settings_changed.emit(self.current_settings.copy())

    def _on_settings_updated(self, settings):
        """Handle settings update from service."""
        self.current_settings = settings.copy()
        self._update_ui_from_settings()
        logger.info("Settings updated from service")

    def _on_error(self, error_msg):
        """Handle error from service."""
        self.status_label.setText(f"Error: {error_msg}")
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def _on_capture_dark(self):
        """Handle capture dark spectrum button."""
        self.set_dark_requested.emit()
        self.status_label.setText("Capturing dark spectrum...")
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")

    def _on_clear_dark(self):
        """Handle clear dark spectrum button."""
        self.clear_dark_requested.emit()
        self.current_settings['UseDarkSpectrum'] = False
        self._update_dark_status()
        self.status_label.setText("Dark spectrum cleared")
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")

    def _on_load_dark(self):
        """Handle load dark spectrum button - API loads from standard location."""
        self.load_dark_requested.emit()
        self.status_label.setText("Loading dark spectrum...")
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")

    def _cleanup_thread(self, thread: QThread) -> None:
        """Remove thread from active threads list."""
        if thread in self.active_threads:
            self.active_threads.remove(thread)

    def _apply_settings(self):
        """Apply settings to spectrometer via API."""
        self.status_label.setText(SettingsWidgetStrings.APPLYING_SETTINGS)
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")

        # Emit integral time changed to apply immediately
        self.integral_time_changed.emit(self.integral_time_input.value())

        self.status_label.setText("Settings applied to spectrometer")
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")

    def _reload_settings_async(self):
        """Reload settings from server asynchronously."""
        self.status_label.setText(SettingsWidgetStrings.LOADING_SETTINGS)
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")

        thread = APIClientThread('GET', ENDPOINTS["spectrometer_settings"])
        thread.response_received.connect(self._on_settings_loaded)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        self.active_threads.append(thread)
        thread.start()

    def _on_settings_loaded(self, success: bool, message: str, data: dict):
        """Handle settings loaded from server."""
        if success and data:
            self.current_settings = data
            self._update_ui_from_settings()
            self.status_label.setText(SettingsWidgetStrings.SETTINGS_LOADED)
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            logger.info("Settings loaded from server")
        else:
            self.status_label.setText(SettingsWidgetStrings.FAILED_TO_LOAD)
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def _save_settings_async(self):
        """Save settings to server asynchronously."""
        self.status_label.setText(SettingsWidgetStrings.SAVING_SETTINGS)
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")

        self._on_settings_changed()  # Update current_settings dict

        thread = APIClientThread('POST', ENDPOINTS["spectrometer_settings"], self.current_settings)
        thread.response_received.connect(self._on_settings_saved)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        self.active_threads.append(thread)
        thread.start()

    def _on_settings_saved(self, success: bool, message: str, data: dict):
        """Handle settings saved to server."""
        if success:
            self.status_label.setText(SettingsWidgetStrings.SETTINGS_SAVED)
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            # Notify service to reload settings
            if self.spectrometer_service:
                self.spectrometer_service.settings_updated.emit(self.current_settings)
        else:
            self.status_label.setText(f"{SettingsWidgetStrings.FAILED_TO_SAVE}: {message}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def _load_initial_settings(self):
        """Load initial settings from service."""
        if self.spectrometer_service:
            settings = self.spectrometer_service.get_spectrometer_settings()
            if settings:
                self.current_settings = settings
                self._update_ui_from_settings()
            else:
                # Use defaults if no settings available
                self.current_settings = {
                    'SettingsName': 'Default',
                    'IntegralTime': 100,
                    'AutoDarkCorrection': True,
                    'OverilluminationThreshold': 65535,
                    'UseDarkSpectrum': False
                }
                self._update_ui_from_settings()

    def _update_ui_from_settings(self):
        """Update UI controls from current settings."""
        if 'SettingsName' in self.current_settings:
            self.settings_name.setText(self.current_settings['SettingsName'])

        if 'IntegralTime' in self.current_settings:
            self.integral_time_input.setValue(self.current_settings['IntegralTime'])

        if 'AutoDarkCorrection' in self.current_settings:
            self.auto_dark_checkbox.setChecked(self.current_settings['AutoDarkCorrection'])

        if 'OverilluminationThreshold' in self.current_settings:
            self.overillumination_input.setValue(self.current_settings['OverilluminationThreshold'])

        self._update_dark_status()

    def _update_dark_status(self):
        """Update dark spectrum status label."""
        use_dark = self.current_settings.get('UseDarkSpectrum', False)
        if use_dark:
            self.dark_status_label.setText(SettingsWidgetStrings.DARK_SPECTRUM_LOADED)
            self.dark_status_label.setStyleSheet("color: green;")
        else:
            self.dark_status_label.setText(SettingsWidgetStrings.NO_DARK_SPECTRUM)
            self.dark_status_label.setStyleSheet("color: gray;")

    def closeEvent(self, event):
        """Clean up threads on close."""
        for thread in self.active_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait(1000)
        self.active_threads.clear()
        super().closeEvent(event)
