import requests
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, 
    QLabel, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, 
    QGridLayout
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont


class APIClientThread(QThread):
    """Thread for making API calls to avoid blocking the UI."""
    response_received = pyqtSignal(bool, str, dict)
    
    def __init__(self, method, url, data=None):
        super().__init__()
        self.method = method.upper()
        self.url = url
        self.data = data
    
    def run(self):
        try:
            if self.method == 'GET':
                response = requests.get(self.url, timeout=5)
            elif self.method == 'POST':
                response = requests.post(self.url, json=self.data, timeout=5)
            else:
                self.response_received.emit(False, f"Unsupported method: {self.method}", {})
                return
            
            if response.status_code == 200:
                self.response_received.emit(True, "Success", response.json())
            elif response.status_code == 422:
                # FastAPI validation error
                error_data = response.json()
                detail = error_data.get('detail', [])
                if isinstance(detail, list) and detail:
                    error_msg = f"Validation error: {detail[0].get('msg', 'Unknown validation error')}"
                else:
                    error_msg = f"Validation error: {error_data.get('detail', 'Unknown error')}"
                self.response_received.emit(False, error_msg, {})
            else:
                # Try to parse FastAPI error response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', f"HTTP {response.status_code}: {response.text}")
                except (ValueError, json.JSONDecodeError):
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                self.response_received.emit(False, error_msg, {})
                
        except requests.exceptions.RequestException as e:
            self.response_received.emit(False, f"Network error: {str(e)}", {})
        except Exception as e:
            self.response_received.emit(False, f"Error: {str(e)}", {})


class CameraSettingsWidget(QWidget):
    """Widget for camera settings configuration."""
    
    def __init__(self):
        super().__init__()
        self.api_base_url = "http://localhost:8000/api"
        self.current_settings = {}
        self.active_threads = []  # Track active threads
        self._build_ui()
        # Don't auto-load settings to avoid threading issues on startup
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Camera settings group
        settings_group = QGroupBox("Camera Parameters")
        settings_layout = QGridLayout(settings_group)
        
        # Auto Exposure
        self.chk_ae = QCheckBox("Auto Exposure")
        self.chk_ae.setChecked(True)
        settings_layout.addWidget(QLabel("Auto Exposure:"), 0, 0)
        settings_layout.addWidget(self.chk_ae, 0, 1)
        
        # Auto White Balance
        self.chk_awb = QCheckBox("Auto White Balance")
        self.chk_awb.setChecked(True)
        settings_layout.addWidget(QLabel("Auto WB:"), 1, 0)
        settings_layout.addWidget(self.chk_awb, 1, 1)
        
        # Exposure Time
        self.exp_time = QSpinBox()
        self.exp_time.setRange(100, 3000000)
        self.exp_time.setValue(10000)
        self.exp_time.setSuffix(" μs")
        settings_layout.addWidget(QLabel("Exposure Time:"), 2, 0)
        settings_layout.addWidget(self.exp_time, 2, 1)
        
        # Analogue Gain
        self.gain = QDoubleSpinBox()
        self.gain.setRange(0.0, 32.0)
        self.gain.setValue(1.0)
        self.gain.setDecimals(2)
        settings_layout.addWidget(QLabel("Analogue Gain:"), 3, 0)
        settings_layout.addWidget(self.gain, 3, 1)
        
        # Exposure Value
        self.exp_value = QDoubleSpinBox()
        self.exp_value.setRange(-10.0, 10.0)
        self.exp_value.setValue(0.0)
        self.exp_value.setDecimals(2)
        settings_layout.addWidget(QLabel("Exposure Value:"), 4, 0)
        settings_layout.addWidget(self.exp_value, 4, 1)
        
        # Red Gain
        self.red_gain = QDoubleSpinBox()
        self.red_gain.setRange(0.0, 8.0)
        self.red_gain.setValue(1.0)
        self.red_gain.setDecimals(2)
        settings_layout.addWidget(QLabel("Red Gain:"), 5, 0)
        settings_layout.addWidget(self.red_gain, 5, 1)
        
        # Blue Gain
        self.blue_gain = QDoubleSpinBox()
        self.blue_gain.setRange(0.0, 8.0)
        self.blue_gain.setValue(1.0)
        self.blue_gain.setDecimals(2)
        settings_layout.addWidget(QLabel("Blue Gain:"), 6, 0)
        settings_layout.addWidget(self.blue_gain, 6, 1)
        
        layout.addWidget(settings_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_apply = QPushButton("Apply Changes")
        self.btn_reset = QPushButton("Reset to Defaults")
        
        button_layout.addWidget(self.btn_refresh)
        button_layout.addWidget(self.btn_reset)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_apply)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Connect signals
        self.btn_refresh.clicked.connect(self.load_settings)
        self.btn_apply.clicked.connect(self.apply_settings)
        self.btn_reset.clicked.connect(self.reset_to_defaults)
        
        # Enable/disable controls based on auto settings
        self.chk_ae.toggled.connect(self._update_control_states)
        self.chk_awb.toggled.connect(self._update_control_states)
    
    def _update_control_states(self):
        """Enable/disable controls based on auto exposure and white balance settings."""
        ae_enabled = self.chk_ae.isChecked()
        awb_enabled = self.chk_awb.isChecked()
        
        # When auto exposure is enabled, disable manual exposure controls
        self.exp_time.setEnabled(not ae_enabled)
        self.gain.setEnabled(not ae_enabled)
        self.exp_value.setEnabled(ae_enabled)
        
        # When auto white balance is enabled, disable manual gain controls
        self.red_gain.setEnabled(not awb_enabled)
        self.blue_gain.setEnabled(not awb_enabled)
    
    def load_settings(self):
        """Load current camera settings from API."""
        self.status_label.setText("Loading settings...")
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        
        thread = APIClientThread('GET', f"{self.api_base_url}/settings/camera")
        thread.response_received.connect(self._on_settings_loaded)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        self.active_threads.append(thread)
        thread.start()
    
    def _cleanup_thread(self, thread):
        """Remove thread from active threads list when finished."""
        if thread in self.active_threads:
            self.active_threads.remove(thread)
    
    def closeEvent(self, event):
        """Clean up active threads when widget is destroyed."""
        # Terminate all active threads
        for thread in self.active_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait(1000)  # Wait up to 1 second for thread to finish
        self.active_threads.clear()
        super().closeEvent(event)
    
    def _on_settings_loaded(self, success, message, data):
        """Handle settings load response."""
        if success and (data.get('success') or 'id' in data):  # FastAPI returns direct object for camera settings
            # Handle both formats: FastAPI direct response and wrapped response
            if 'id' in data:
                # Direct FastAPI response
                settings = data
            else:
                # Wrapped response format
                settings = data.get('data', {})
            
            self.current_settings = settings
            
            # Update UI with loaded settings
            self.chk_ae.setChecked(bool(settings.get('AeEnable', True)))
            self.chk_awb.setChecked(bool(settings.get('AwbEnable', True)))
            self.exp_time.setValue(int(settings.get('ExposureTime', 10000)))
            self.gain.setValue(float(settings.get('AnalogueGain', 1.0)))
            self.exp_value.setValue(float(settings.get('ExposureValue', 0.0)))
            self.red_gain.setValue(float(settings.get('RedGain', 1.0)))
            self.blue_gain.setValue(float(settings.get('BlueGain', 1.0)))
            
            self._update_control_states()
            
            self.status_label.setText("Settings loaded successfully")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            self.status_label.setText(f"Failed to load settings: {message}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def apply_settings(self):
        """Apply current settings to the database."""
        self.status_label.setText("Applying settings...")
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        
        # Collect all settings
        settings_to_update = [
            ("CameraSettings", "AeEnable", str(int(self.chk_ae.isChecked()))),
            ("CameraSettings", "AwbEnable", str(int(self.chk_awb.isChecked()))),
            ("CameraSettings", "ExposureTime", str(self.exp_time.value())),
            ("CameraSettings", "AnalogueGain", str(self.gain.value())),
            ("CameraSettings", "ExposureValue", str(self.exp_value.value())),
            ("CameraSettings", "RedGain", str(self.red_gain.value())),
            ("CameraSettings", "BlueGain", str(self.blue_gain.value())),
        ]
        
        # Apply settings sequentially
        self._apply_settings_sequentially(settings_to_update, 0)
    
    def _apply_settings_sequentially(self, settings_list, index):
        """Apply settings one by one to avoid overwhelming the API."""
        if index >= len(settings_list):
            self.status_label.setText("All settings applied successfully")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            return
        
        table_name, parameter, value = settings_list[index]
        
        thread = APIClientThread('POST', f"{self.api_base_url}/settings/update", {
            'table_name': table_name,
            'parameter': parameter,
            'value': value
        })
        
        # Store remaining settings for next call
        thread.remaining_settings = settings_list
        thread.next_index = index + 1
        
        thread.response_received.connect(lambda success, message, data: 
            self._on_setting_applied(success, message, data, thread))
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        self.active_threads.append(thread)
        thread.start()
    
    def _on_setting_applied(self, success, message, data, thread):
        """Handle individual setting application response."""
        if success:
            # Continue with next setting
            self._apply_settings_sequentially(thread.remaining_settings, thread.next_index)
        else:
            self.status_label.setText(f"Failed to apply setting: {message}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def reset_to_defaults(self):
        """Reset all settings to default values."""
        self.chk_ae.setChecked(True)
        self.chk_awb.setChecked(True)
        self.exp_time.setValue(10000)
        self.gain.setValue(1.0)
        self.exp_value.setValue(0.0)
        self.red_gain.setValue(1.0)
        self.blue_gain.setValue(1.0)
        
        self._update_control_states()
        self.status_label.setText("Reset to default values")
        self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")


class SpectrometerSettingsWidget(QWidget):
    """Widget for spectrometer settings configuration."""
    
    def __init__(self):
        super().__init__()
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Placeholder for spectrometer settings
        placeholder = QLabel("Spectrometer settings will be implemented here")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("QLabel { color: gray; font-size: 14px; }")
        
        layout.addWidget(placeholder)
        layout.addStretch()


class FileSettingsWidget(QWidget):
    """Widget for file saving settings configuration."""
    
    def __init__(self):
        super().__init__()
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Placeholder for file settings
        placeholder = QLabel("File saving settings will be implemented here")
        placeholder.setAlignment(Qt.AlignCenter)
        placeholder.setStyleSheet("QLabel { color: gray; font-size: 14px; }")
        
        layout.addWidget(placeholder)
        layout.addStretch()


class DeviceSettingsWidget(QWidget):
    """Main device settings widget with tabbed interface."""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Create tab widget
        self.tab_widget = QTabWidget()
        
        # Add tabs
        self.camera_tab = CameraSettingsWidget()
        self.spectrometer_tab = SpectrometerSettingsWidget()
        self.file_tab = FileSettingsWidget()
        
        self.tab_widget.addTab(self.camera_tab, "Camera")
        self.tab_widget.addTab(self.spectrometer_tab, "Spectrometer")
        self.tab_widget.addTab(self.file_tab, "File Settings")
        
        layout.addWidget(self.tab_widget)
        
        # Set font for better readability
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)