"""
Spectrometer Settings Widget
Widget for configuring spectrometer parameters (integral time, dark spectrum, overillumination threshold).
Supports both basic and advanced settings with FastAPI integration.
"""

import logging
from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget, 
    QHBoxLayout, QCheckBox, QGroupBox, QLineEdit, QFileDialog,
    QMessageBox, QProgressBar
)

logger = logging.getLogger(__name__)


class SpectrometerSettingsWidget(QWidget):
    """Widget for spectrometer settings configuration."""

    integral_time_changed = pyqtSignal(int)
    set_dark_requested = pyqtSignal()
    clear_dark_requested = pyqtSignal()
    load_dark_requested = pyqtSignal(str)  # filepath
    settings_changed = pyqtSignal(dict)  # settings dict

    def __init__(self, interface_text=None, spectrometer_service=None):
        super().__init__()
        self.interface_text = interface_text
        self.spectrometer_service = spectrometer_service
        self.current_settings = {}
        self._build_ui()
        
        # Connect service signals if available
        if self.spectrometer_service:
            self.spectrometer_service.settings_updated.connect(self._on_settings_updated)
            self.spectrometer_service.error_occurred.connect(self._on_error)

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Connection status
        self.connection_label = QLabel(
            self.interface_text.status_disconnected() if self.interface_text else "Status: Disconnected"
        )
        self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        self.connection_label.setWordWrap(True)
        layout.addWidget(self.connection_label)

        # Basic Settings Group
        basic_group = QGroupBox("Basic Settings")
        basic_layout = QVBoxLayout(basic_group)
        
        # Integral time
        it_label = QLabel(
            self.interface_text.integral_time() if self.interface_text else "Integral Time (ms):"
        )
        it_label.setStyleSheet("QLabel { font-weight: bold; }")
        it_label.setWordWrap(True)
        basic_layout.addWidget(it_label)

        self.integral_time_input = QSpinBox()
        self.integral_time_input.setRange(1, 99999)
        self.integral_time_input.setValue(100)
        self.integral_time_input.setButtonSymbols(QSpinBox.NoButtons)
        self.integral_time_input.valueChanged.connect(self._on_integral_time_changed)
        basic_layout.addWidget(self.integral_time_input)
        
        layout.addWidget(basic_group)
        
        # Dark Spectrum Group
        dark_group = QGroupBox("Dark Spectrum")
        dark_layout = QVBoxLayout(dark_group)
        
        # Dark spectrum status
        self.dark_status_label = QLabel("No dark spectrum loaded")
        self.dark_status_label.setStyleSheet("color: gray;")
        dark_layout.addWidget(self.dark_status_label)
        
        # Dark spectrum buttons
        dark_buttons_layout = QHBoxLayout()
        
        self.set_dark_button = QPushButton(
            self.interface_text.set_dark_spectrum() if self.interface_text else "Capture Dark"
        )
        self.set_dark_button.clicked.connect(self.set_dark_requested.emit)
        dark_buttons_layout.addWidget(self.set_dark_button)

        self.clear_dark_button = QPushButton(
            self.interface_text.clear_dark_spectrum() if self.interface_text else "Clear Dark"
        )
        self.clear_dark_button.clicked.connect(self.clear_dark_requested.emit)
        dark_buttons_layout.addWidget(self.clear_dark_button)
        
        dark_layout.addLayout(dark_buttons_layout)
        
        # Load dark spectrum from file
        load_layout = QHBoxLayout()
        self.dark_path_input = QLineEdit()
        self.dark_path_input.setPlaceholderText("Path to dark spectrum file...")
        self.dark_path_input.setReadOnly(True)
        load_layout.addWidget(self.dark_path_input)
        
        self.browse_dark_button = QPushButton("Browse")
        self.browse_dark_button.clicked.connect(self._browse_dark_file)
        load_layout.addWidget(self.browse_dark_button)
        
        self.load_dark_button = QPushButton("Load")
        self.load_dark_button.clicked.connect(self._load_dark_spectrum)
        load_layout.addWidget(self.load_dark_button)
        
        dark_layout.addLayout(load_layout)
        
        layout.addWidget(dark_group)
        
        # Advanced Settings Group
        advanced_group = QGroupBox("Advanced Settings")
        advanced_layout = QVBoxLayout(advanced_group)
        
        # Auto dark correction
        self.auto_dark_checkbox = QCheckBox("Auto Dark Correction")
        self.auto_dark_checkbox.setChecked(True)
        self.auto_dark_checkbox.stateChanged.connect(self._on_settings_changed)
        advanced_layout.addWidget(self.auto_dark_checkbox)
        
        # Overillumination threshold
        oi_label = QLabel("Overillumination Threshold:")
        oi_label.setStyleSheet("QLabel { font-weight: bold; }")
        advanced_layout.addWidget(oi_label)
        
        self.overillumination_input = QSpinBox()
        self.overillumination_input.setRange(0, 65535)
        self.overillumination_input.setValue(65535)
        self.overillumination_input.setButtonSymbols(QSpinBox.NoButtons)
        self.overillumination_input.valueChanged.connect(self._on_settings_changed)
        advanced_layout.addWidget(self.overillumination_input)
        
        layout.addWidget(advanced_group)
        
        # Settings management
        settings_layout = QHBoxLayout()
        
        self.reload_settings_button = QPushButton("Reload Settings")
        self.reload_settings_button.clicked.connect(self._reload_settings)
        settings_layout.addWidget(self.reload_settings_button)
        
        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(self._save_settings)
        settings_layout.addWidget(self.save_settings_button)
        
        layout.addLayout(settings_layout)
        
        # Progress bar for operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)
        
        layout.addStretch()
        
        # Load initial settings
        self._load_initial_settings()

    def set_connection_status(self, connected: bool):
        """Update connection status label."""
        if connected:
            status_text = self.interface_text.status_connected() if self.interface_text else "Status: Connected"
            self.connection_label.setText(status_text)
            self.connection_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            status_text = self.interface_text.status_disconnected() if self.interface_text else "Status: Disconnected"
            self.connection_label.setText(status_text)
            self.connection_label.setStyleSheet("color: red; font-weight: bold;")
    
    def _on_integral_time_changed(self, value):
        """Handle integral time change."""
        self.integral_time_changed.emit(value)
        self.current_settings['IntegralTime'] = value
        self._on_settings_changed()
    
    def _on_settings_changed(self):
        """Handle any settings change."""
        # Update current settings dict
        self.current_settings.update({
            'IntegralTime': self.integral_time_input.value(),
            'AutoDarkCorrection': self.auto_dark_checkbox.isChecked(),
            'OverilluminationThreshold': self.overillumination_input.value()
        })
        
        # Emit signal for real-time updates
        self.settings_changed.emit(self.current_settings.copy())
    
    def _on_settings_updated(self, settings):
        """Handle settings update from service."""
        self.current_settings = settings.copy()
        self._update_ui_from_settings()
        logger.info("Settings updated from service")
    
    def _on_error(self, error_msg):
        """Handle error from service."""
        QMessageBox.warning(self, "Error", error_msg)
    
    def _browse_dark_file(self):
        """Browse for dark spectrum file."""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Select Dark Spectrum File",
            "",
            "NumPy Files (*.npy);;Text Files (*.txt *.csv);;All Files (*)"
        )
        if file_path:
            self.dark_path_input.setText(file_path)
    
    def _load_dark_spectrum(self):
        """Load dark spectrum from file."""
        file_path = self.dark_path_input.text().strip()
        if not file_path:
            QMessageBox.warning(self, "Warning", "Please select a dark spectrum file")
            return
        
        self.progress_bar.setVisible(True)
        self.progress_bar.setRange(0, 0)  # Indeterminate progress
        
        if self.spectrometer_service:
            success = self.spectrometer_service.load_dark_spectrum_file(file_path)
            if success:
                self.current_settings['DarkSpectrumPath'] = file_path
                self._update_dark_status()
                QMessageBox.information(self, "Success", "Dark spectrum loaded successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to load dark spectrum")
        
        self.progress_bar.setVisible(False)
    
    def _reload_settings(self):
        """Reload settings from server."""
        if self.spectrometer_service:
            settings = self.spectrometer_service.get_spectrometer_settings()
            if settings:
                self.current_settings = settings
                self._update_ui_from_settings()
                logger.info("Settings reloaded from server")
            else:
                QMessageBox.warning(self, "Warning", "Failed to reload settings")
    
    def _save_settings(self):
        """Save current settings to server."""
        if self.spectrometer_service:
            self.progress_bar.setVisible(True)
            self.progress_bar.setRange(0, 0)
            
            success = self.spectrometer_service.update_spectrometer_settings(self.current_settings)
            if success:
                QMessageBox.information(self, "Success", "Settings saved successfully")
            else:
                QMessageBox.warning(self, "Error", "Failed to save settings")
            
            self.progress_bar.setVisible(False)
    
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
                    'IntegralTime': 100,
                    'AutoDarkCorrection': True,
                    'OverilluminationThreshold': 65535,
                    'DarkSpectrumPath': ''
                }
    
    def _update_ui_from_settings(self):
        """Update UI controls from current settings."""
        if 'IntegralTime' in self.current_settings:
            self.integral_time_input.setValue(self.current_settings['IntegralTime'])
        
        if 'AutoDarkCorrection' in self.current_settings:
            self.auto_dark_checkbox.setChecked(self.current_settings['AutoDarkCorrection'])
        
        if 'OverilluminationThreshold' in self.current_settings:
            self.overillumination_input.setValue(self.current_settings['OverilluminationThreshold'])
        
        if 'DarkSpectrumPath' in self.current_settings:
            self.dark_path_input.setText(self.current_settings['DarkSpectrumPath'])
        
        self._update_dark_status()
    
    def _update_dark_status(self):
        """Update dark spectrum status label."""
        if self.current_settings.get('DarkSpectrumPath'):
            self.dark_status_label.setText(f"Dark spectrum loaded: {self.current_settings['DarkSpectrumPath']}")
            self.dark_status_label.setStyleSheet("color: green;")
        else:
            self.dark_status_label.setText("No dark spectrum loaded")
            self.dark_status_label.setStyleSheet("color: gray;")
