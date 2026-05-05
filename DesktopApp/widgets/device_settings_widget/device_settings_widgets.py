import requests
import json
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTabWidget, QGroupBox, 
    QLabel, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, 
    QGridLayout, QComboBox, QLineEdit, QDialog, QDialogButtonBox,
    QListWidget, QListWidgetItem
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont


class SettingsSlotDialog(QDialog):
    """Dialog for selecting and managing camera settings slots (0-9)."""
    
    slot_selected = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Camera Settings Slots")
        self.setModal(True)
        self.resize(400, 300)
        self.slots_data = {}
        self._build_ui()
        self._load_slots()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel("Select a settings slot to load:")
        title.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; }")
        layout.addWidget(title)
        
        # Slots list
        self.slots_list = QListWidget()
        self.slots_list.itemDoubleClicked.connect(self._on_slot_selected)
        layout.addWidget(self.slots_list)
        
        # Buttons
        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_ok_clicked)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)
    
    def _load_slots(self):
        """Load all settings slots from database."""
        try:
            import sys
            import os
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'RaspberryPi', 'services')
            if db_path not in sys.path:
                sys.path.insert(0, db_path)
            
            from database_service import db_service
            self.slots_data = db_service.get_all_camera_settings_slots()
            
            # Populate list widget
            self.slots_list.clear()
            for slot_id, settings in self.slots_data.items():
                name = settings.get('SettingsName', f"Slot {slot_id}")
                resolution = settings.get('Resolution', '1920x1080')
                
                if slot_id == 0:
                    display_text = f"Slot {slot_id} - {name} (Basic) - {resolution}"
                else:
                    display_text = f"Slot {slot_id} - {name} - {resolution}"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, slot_id)
                self.slots_list.addItem(item)
                
        except Exception as e:
            # Fallback: create empty slots
            self.slots_list.clear()
            for slot_id in range(10):
                name = "Basic" if slot_id == 0 else f"Custom {slot_id}"
                display_text = f"Slot {slot_id} - {name} - 1920x1080"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, slot_id)
                self.slots_list.addItem(item)
    
    def _on_slot_selected(self, item):
        """Handle slot selection."""
        slot_id = item.data(Qt.UserRole)
        self.slot_selected.emit(slot_id)
        self.accept()
    
    def _on_ok_clicked(self):
        """Handle OK button click."""
        current_item = self.slots_list.currentItem()
        if current_item:
            slot_id = current_item.data(Qt.UserRole)
            self.slot_selected.emit(slot_id)
            self.accept()
    
    def get_selected_slot(self):
        """Get the selected slot ID."""
        current_item = self.slots_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None


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
    
    # Signal emitted when settings slot is changed
    slot_changed = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.api_base_url = "http://localhost:8000/api"
        self.current_settings = {}
        self.active_threads = []  # Track active threads
        self.current_slot_id = 0  # Track current settings slot
        self._build_ui()
        # Load default settings from slot 0 on startup
        self.load_settings_from_slot(0)
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Camera settings group
        settings_group = QGroupBox("Camera Parameters")
        settings_layout = QGridLayout(settings_group)
        
        # Settings Name
        self.settings_name = QLineEdit()
        self.settings_name.setPlaceholderText("Enter settings name...")
        settings_layout.addWidget(QLabel("Settings Name:"), 0, 0)
        settings_layout.addWidget(self.settings_name, 0, 1)
        
        # Resolution
        self.resolution_combo = QComboBox()
        self.resolution_combo.addItems([
            '640x480 (4:3)',      # VGA
            '800x600 (4:3)',      # SVGA  
            '1024x768 (4:3)',     # XGA
            '1280x720 (16:9)',    # 720p HD
            '1296x972 (4:3)',     # 4:3 mid-resolution
            '1640x1232 (4:3)',    # 4:3 aspect ratio
            '1920x1080 (16:9)',   # 1080p FHD
            '2304x1296 (16:9)',   # 16:9 aspect ratio
            '2592x1944 (4:3)',    # High 4:3 resolution
            '3280x2464 (4:3)',    # Full 8MP resolution
            '4608x2592 (16:9)',   # Full 12MP resolution
        ])
        self.resolution_combo.setCurrentText('1920x1080 (16:9)')
        settings_layout.addWidget(QLabel("Resolution:"), 1, 0)
        settings_layout.addWidget(self.resolution_combo, 1, 1)
        
        # Auto Exposure
        self.chk_ae = QCheckBox("Auto Exposure")
        self.chk_ae.setChecked(True)
        settings_layout.addWidget(QLabel("Auto Exposure:"), 2, 0)
        settings_layout.addWidget(self.chk_ae, 2, 1)
        
        # Auto White Balance
        self.chk_awb = QCheckBox("Auto White Balance")
        self.chk_awb.setChecked(True)
        settings_layout.addWidget(QLabel("Auto WB:"), 3, 0)
        settings_layout.addWidget(self.chk_awb, 3, 1)
        
        # Exposure Time
        self.exp_time = QSpinBox()
        self.exp_time.setRange(100, 3000000)
        self.exp_time.setValue(10000)
        self.exp_time.setSuffix(" μs")
        settings_layout.addWidget(QLabel("Exposure Time:"), 4, 0)
        settings_layout.addWidget(self.exp_time, 4, 1)
        
        # Analogue Gain
        self.gain = QDoubleSpinBox()
        self.gain.setRange(0.0, 32.0)
        self.gain.setValue(1.0)
        self.gain.setDecimals(2)
        settings_layout.addWidget(QLabel("Analogue Gain:"), 5, 0)
        settings_layout.addWidget(self.gain, 5, 1)
        
        # Exposure Value
        self.exp_value = QDoubleSpinBox()
        self.exp_value.setRange(-10.0, 10.0)
        self.exp_value.setValue(0.0)
        self.exp_value.setDecimals(2)
        settings_layout.addWidget(QLabel("Exposure Value:"), 6, 0)
        settings_layout.addWidget(self.exp_value, 6, 1)
        
        # Red Gain
        self.red_gain = QDoubleSpinBox()
        self.red_gain.setRange(0.0, 8.0)
        self.red_gain.setValue(1.0)
        self.red_gain.setDecimals(2)
        settings_layout.addWidget(QLabel("Red Gain:"), 7, 0)
        settings_layout.addWidget(self.red_gain, 7, 1)
        
        # Blue Gain
        self.blue_gain = QDoubleSpinBox()
        self.blue_gain.setRange(0.0, 8.0)
        self.blue_gain.setValue(1.0)
        self.blue_gain.setDecimals(2)
        settings_layout.addWidget(QLabel("Blue Gain:"), 8, 0)
        settings_layout.addWidget(self.blue_gain, 8, 1)
        
        layout.addWidget(settings_group)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton("Refresh")
        self.btn_load_slot = QPushButton("Load Slot")
        self.btn_save_slot = QPushButton("Save to Slot")
        self.btn_apply = QPushButton("Apply Changes")
        
        button_layout.addWidget(self.btn_refresh)
        button_layout.addWidget(self.btn_load_slot)
        button_layout.addWidget(self.btn_save_slot)
        button_layout.addStretch()
        button_layout.addWidget(self.btn_apply)
        
        layout.addLayout(button_layout)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        self.status_label.setWordWrap(True)
        self.status_label.setMaximumWidth(300)  # Prevent screen stretching
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Connect signals
        self.btn_refresh.clicked.connect(self.load_settings)
        self.btn_load_slot.clicked.connect(self.show_slot_selection_dialog)
        self.btn_save_slot.clicked.connect(self.save_to_slot_dialog)
        self.btn_apply.clicked.connect(self.apply_settings)
        
        # Enable/disable controls based on auto settings
        self.chk_ae.toggled.connect(self._update_control_states)
        self.chk_awb.toggled.connect(self._update_control_states)
        
        # Initialize control states based on default checkbox values
        self._update_control_states()
    
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
    
    def _update_ui_from_settings(self, settings):
        """Update UI controls from settings dictionary."""
        try:
            # Update settings name and resolution
            self.settings_name.setText(settings.get('SettingsName', 'Basic'))
            resolution = settings.get('Resolution', '1920x1080')
            
            # Try to find exact match first (with aspect ratio)
            index = self.resolution_combo.findText(resolution)
            if index < 0:
                # If not found, try to find by resolution part only
                for i in range(self.resolution_combo.count()):
                    text = self.resolution_combo.itemText(i)
                    if text.startswith(resolution):
                        index = i
                        break
            
            if index >= 0:
                self.resolution_combo.setCurrentIndex(index)
            
            # Update checkbox states
            self.chk_ae.setChecked(bool(settings.get('AeEnable', True)))
            self.chk_awb.setChecked(bool(settings.get('AwbEnable', True)))
            
            # Update numeric values
            self.exp_time.setValue(int(settings.get('ExposureTime', 10000)))
            self.gain.setValue(float(settings.get('AnalogueGain', 1.0)))
            self.exp_value.setValue(float(settings.get('ExposureValue', 0.0)))
            self.red_gain.setValue(float(settings.get('RedGain', 1.0)))
            self.blue_gain.setValue(float(settings.get('BlueGain', 1.0)))
            
            # Update control states (this will enable/disable appropriate controls)
            self._update_control_states()
            
        except Exception as e:
            self.status_label.setText(f"Error updating UI: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def load_settings(self):
        """Load current camera settings from API or database fallback."""
        self.status_label.setText("Loading settings...")
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        
        # Try API first, then fallback to database
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
            self._update_ui_from_settings(settings)
            
            self.status_label.setText("Settings loaded successfully")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            # API failed, try database fallback
            self._load_settings_from_database()
    
    def _load_settings_from_database(self):
        """Load settings directly from database as fallback."""
        try:
            import sys
            import os
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'RaspberryPi', 'services')
            if db_path not in sys.path:
                sys.path.insert(0, db_path)
            
            from database_service import db_service
            settings = db_service.get_camera_settings()
            
            if settings:
                self.current_settings = settings
                self._update_ui_from_settings(settings)
                self.status_label.setText("Settings loaded from database (API offline)")
                self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
            else:
                self.status_label.setText("No settings found in database")
                self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
                
        except Exception as e:
            self.status_label.setText(f"Failed to load from database: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def apply_settings(self):
        """Apply current settings to the database."""
        self.status_label.setText("Applying settings...")
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        
        # Extract resolution from display text (remove aspect ratio)
        resolution_text = self.resolution_combo.currentText()
        resolution = resolution_text.split(' ')[0] if ' ' in resolution_text else resolution_text
        
        # Collect all settings
        settings_to_update = [
            ("CameraSettings", "SettingsName", self.settings_name.text()),
            ("CameraSettings", "Resolution", resolution),
            ("CameraSettings", "AeEnable", str(int(self.chk_ae.isChecked()))),
            ("CameraSettings", "AwbEnable", str(int(self.chk_awb.isChecked()))),
            ("CameraSettings", "ExposureTime", str(int(self.exp_time.value()))),
            ("CameraSettings", "AnalogueGain", str(float(self.gain.value()))),
            ("CameraSettings", "ExposureValue", str(float(self.exp_value.value()))),
            ("CameraSettings", "RedGain", str(float(self.red_gain.value()))),
            ("CameraSettings", "BlueGain", str(float(self.blue_gain.value()))),
        ]
        
        # Try API first, then fallback to database
        self._apply_settings_with_fallback(settings_to_update, 0)
    
    def _apply_settings_with_fallback(self, settings_list, index):
        """Apply settings with API fallback to database."""
        if index >= len(settings_list):
            self.status_label.setText("All settings applied successfully")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            # Emit signal that settings were updated
            try:
                # Try to find the DeviceSettingsWidget parent
                parent = self.parent()
                while parent and not hasattr(parent, 'settings_updated'):
                    parent = parent.parent()
                
                if parent and hasattr(parent, 'settings_updated'):
                    parent.settings_updated.emit()
                else:
                    pass  # Could not find parent with signal
            except Exception:
                pass  # Error emitting signal
            return
        
        table_name, parameter, value = settings_list[index]
        
        # Try API first
        thread = APIClientThread('POST', f"{self.api_base_url}/settings/update", {
            'table_name': table_name,
            'parameter': parameter,
            'value': value
        })
        
        # Store remaining settings for next call
        thread.remaining_settings = settings_list
        thread.next_index = index + 1
        
        thread.response_received.connect(lambda success, message, data: 
            self._on_setting_applied_with_fallback(success, message, data, thread))
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        self.active_threads.append(thread)
        thread.start()
    
    def _on_setting_applied_with_fallback(self, success, message, data, thread):
        """Handle individual setting application response with fallback."""
        if success:
            # Continue with next setting
            self._apply_settings_with_fallback(thread.remaining_settings, thread.next_index)
        else:
            # API failed, try database fallback for this setting
            table_name, parameter, value = thread.remaining_settings[thread.next_index - 1]
            self._apply_setting_to_database(table_name, parameter, value, thread.remaining_settings, thread.next_index)
    
    def _apply_setting_to_database(self, table_name, parameter, value, settings_list, index):
        """Apply setting directly to database."""
        try:
            import sys
            import os
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'RaspberryPi', 'services')
            if db_path not in sys.path:
                sys.path.insert(0, db_path)
            
            from database_service import db_service
            success, message = db_service.update_parameter(table_name, parameter, value)
            
            # Database update successful
            
            if success:
                # Continue with next setting
                self._apply_settings_with_fallback(settings_list, index)
            else:
                self.status_label.setText(f"Failed to apply {parameter}: {message}")
                self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
                
        except Exception as e:
            self.status_label.setText(f"Database error for {parameter}: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def _apply_settings_sequentially(self, settings_list, index):
        """Apply settings one by one to avoid overwhelming the API."""
        if index >= len(settings_list):
            self.status_label.setText("All settings applied successfully")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            # Emit signal that settings were updated
            try:
                # Try to find the DeviceSettingsWidget parent
                parent = self.parent()
                while parent and not hasattr(parent, 'settings_updated'):
                    parent = parent.parent()
                
                if parent and hasattr(parent, 'settings_updated'):
                    parent.settings_updated.emit()
                else:
                    pass  # Could not find parent with signal
            except Exception:
                pass  # Error emitting signal
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
    
    def show_slot_selection_dialog(self):
        """Show dialog for selecting a settings slot to load."""
        try:
            dialog = SettingsSlotDialog(self)
            dialog.slot_selected.connect(self.load_settings_from_slot)
            dialog.exec_()
        except Exception as e:
            self.status_label.setText(f"Error opening slot dialog: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def load_settings_from_slot(self, slot_id):
        """Load settings from a specific slot."""
        try:
            import sys
            import os
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'RaspberryPi', 'services')
            if db_path not in sys.path:
                sys.path.insert(0, db_path)
            
            from database_service import db_service
            settings = db_service.get_camera_settings_by_slot(slot_id)
            
            self.current_slot_id = slot_id
            self.current_settings = settings
            self._update_ui_from_settings(settings)
            
            slot_name = settings.get('SettingsName', f"Slot {slot_id}")
            self.status_label.setText(f"Loaded settings from: {slot_name}")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            
            # Emit signal that slot has changed
            self.slot_changed.emit(slot_id)
            
        except Exception as e:
            self.status_label.setText(f"Error loading slot {slot_id}: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def save_to_slot_dialog(self):
        """Show dialog for selecting a slot to save current settings."""
        try:
            dialog = SettingsSlotDialog(self)
            dialog.setWindowTitle("Save to Settings Slot")
            dialog.slot_selected.connect(self.save_current_settings_to_slot)
            dialog.exec_()
        except Exception as e:
            self.status_label.setText(f"Error opening save dialog: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def save_current_settings_to_slot(self, slot_id):
        """Save current settings to a specific slot."""
        try:
            import sys
            import os
            db_path = os.path.join(os.path.dirname(__file__), '..', '..', '..', 'RaspberryPi', 'services')
            if db_path not in sys.path:
                sys.path.insert(0, db_path)
            
            from database_service import db_service
            
            # Extract resolution from display text (remove aspect ratio)
            resolution_text = self.resolution_combo.currentText()
            resolution = resolution_text.split(' ')[0] if ' ' in resolution_text else resolution_text
            
            # Collect current settings
            settings = {
                'SettingsName': self.settings_name.text() or f"Slot {slot_id}",
                'Resolution': resolution,
                'AeEnable': self.chk_ae.isChecked(),
                'AwbEnable': self.chk_awb.isChecked(),
                'ExposureTime': self.exp_time.value(),
                'AnalogueGain': self.gain.value(),
                'ExposureValue': self.exp_value.value(),
                'RedGain': self.red_gain.value(),
                'BlueGain': self.blue_gain.value()
            }
            
            success, message = db_service.save_camera_settings_to_slot(slot_id, settings)
            
            if success:
                self.current_slot_id = slot_id
                slot_name = settings['SettingsName']
                self.status_label.setText(f"Settings saved to slot {slot_id}: {slot_name}")
                self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            else:
                self.status_label.setText(f"Error saving to slot {slot_id}: {message}")
                self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
                
        except Exception as e:
            self.status_label.setText(f"Error saving to slot {slot_id}: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")


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
    
    # Signal emitted when settings are updated
    settings_updated = pyqtSignal()
    
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