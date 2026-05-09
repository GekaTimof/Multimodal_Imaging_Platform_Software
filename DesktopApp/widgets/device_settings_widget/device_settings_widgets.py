import requests
import json
import os
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QSpinBox, QDoubleSpinBox, QCheckBox, QPushButton, 
    QGridLayout, QComboBox, QLineEdit, QDialog, QDialogButtonBox,
    QListWidget, QListWidgetItem, QStackedWidget, QProgressBar
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
        self.resize(800, 900) 
        self.slots_data = {}
        self.api_base_url = "http://10.43.70.189:8000/api"
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
        """Load all settings slots from API."""
        try:
            # Load slots from API
            api_url = f"{self.api_base_url}/settings/CameraSettings"
            thread = APIClientThread('GET', api_url)
            thread.response_received.connect(self._on_slots_loaded)
            thread.finished.connect(lambda: self._cleanup_thread(thread))
            self.active_threads.append(thread)
            thread.start()
                
        except Exception as e:
            print(f"Error loading slots from API: {e}")
            # Fallback: create empty slots
            self.slots_list.clear()
            for slot_id in range(10):
                name = "Basic" if slot_id == 0 else f"Custom {slot_id}"
                display_text = f"Slot {slot_id} - {name}\n  Photo: 3280x2464 | Video: 1920x1080"
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, slot_id)
                self.slots_list.addItem(item)
                
                # Add visual separator after each item except the last one
                if slot_id < 9:
                    separator = QListWidgetItem("")
                    separator.setFlags(Qt.NoItemFlags)  # Make it non-selectable
                    separator.setSizeHint(separator.sizeHint().expandedTo(separator.sizeHint() + 
                                   separator.sizeHint().expandedTo(separator.sizeHint())))
                    # Create a visual separator using a line character
                    separator.setText("─" * 40)  # Horizontal line
                    separator.setForeground(separator.foreground().color().lighter(150))  # Make it lighter
                    self.slots_list.addItem(separator)
    
    def _on_slots_loaded(self, success, message, data):
        """Handle slots loaded response from API."""
        try:
            if success and data.get('success') and 'data' in data:
                self.slots_data = data['data']
                
                # Populate list widget
                self.slots_list.clear()
                
                # Create slots 0-9 with data from API or defaults
                for slot_id in range(10):
                    if slot_id in self.slots_data:
                        settings = self.slots_data[slot_id]
                        name = settings.get('SettingsName', f"Slot {slot_id}")
                        photo_resolution = settings.get('PhotoResolution', '3280x2464')
                        video_resolution = settings.get('VideoResolution', '1920x1080')
                    else:
                        # Default slot data
                        name = "Basic" if slot_id == 0 else f"Custom {slot_id}"
                        photo_resolution = "3280x2464"
                        video_resolution = "1920x1080"
                    
                    if slot_id == 0:
                        display_text = f"Slot {slot_id} - {name} (Basic)\n  Photo: {photo_resolution} | Video: {video_resolution}"
                    else:
                        display_text = f"Slot {slot_id} - {name}\n  Photo: {photo_resolution} | Video: {video_resolution}"
                    
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, slot_id)
                    self.slots_list.addItem(item)
                    
                    # Add visual separator after each item except the last one
                    if slot_id < 9:
                        separator = QListWidgetItem("")
                        separator.setFlags(Qt.NoItemFlags)  # Make it non-selectable
                        separator.setSizeHint(separator.sizeHint().expandedTo(separator.sizeHint() + 
                                       separator.sizeHint().expandedTo(separator.sizeHint())))
                        # Create a visual separator using a line character
                        separator.setText("─" * 40)  # Horizontal line
                        separator.setForeground(separator.foreground().color().lighter(150))  # Make it lighter
                        self.slots_list.addItem(separator)
            else:
                print(f"API error loading slots: {message}")
                # Fallback to empty slots
                self._create_fallback_slots()
                
        except Exception as e:
            print(f"Error processing slots data: {e}")
            self._create_fallback_slots()
    
    def _create_fallback_slots(self):
        """Create fallback slots when API fails."""
        self.slots_list.clear()
        for slot_id in range(10):
            name = "Basic" if slot_id == 0 else f"Custom {slot_id}"
            display_text = f"Slot {slot_id} - {name}\n  Photo: 3280x2464 | Video: 1920x1080"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, slot_id)
            self.slots_list.addItem(item)
            
            # Add visual separator after each item except the last one
            if slot_id < 9:
                separator = QListWidgetItem("")
                separator.setFlags(Qt.NoItemFlags)  # Make it non-selectable
                separator.setSizeHint(separator.sizeHint().expandedTo(separator.sizeHint() + 
                               separator.sizeHint().expandedTo(separator.sizeHint())))
                # Create a visual separator using a line character
                separator.setText("─" * 40)  # Horizontal line
                separator.setForeground(separator.foreground().color().lighter(150))  # Make it lighter
                self.slots_list.addItem(separator)
    
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
    
    # Signal emitted when settings are updated
    settings_updated = pyqtSignal()
    
    def __init__(self, interface_text=None):
        super().__init__()
        self.interface_text = interface_text
        self.api_base_url = "http://10.43.70.189:8000/api"
        self.current_settings = {}
        self.active_threads = []  # Track active threads
        self.current_slot_id = 0  # Track current settings slot
        self._build_ui()
        # Load default settings from slot 0 on startup
        self.load_settings_from_slot(0)
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Camera settings layout (no group box)
        settings_layout = QGridLayout()
        
        # Settings Name
        settings_name_label = QLabel(self.interface_text.settings_name() if self.interface_text else "Settings Name:")
        settings_name_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(settings_name_label, 0, 0, 1, 2)
        
        self.settings_name = QLineEdit()
        self.settings_name.setPlaceholderText("Enter settings name...")
        settings_layout.addWidget(self.settings_name, 1, 0, 1, 2)
        
        # Photo Resolution
        photo_resolution_label = QLabel(self.interface_text.photo_resolution() if self.interface_text else "Photo Resolution:")
        photo_resolution_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(photo_resolution_label, 2, 0, 1, 2)
        
        self.photo_resolution_combo = QComboBox()
        self.photo_resolution_combo.addItems([
            '640x480 (4:3)',      # VGA
            '800x600 (4:3)',      # SVGA  
            '1024x768 (4:3)',     # XGA
            '1296x972 (4:3)',     # 4:3 mid-resolution
            '1640x1232 (4:3)',    # 4:3 aspect ratio
            '1920x1080 (16:9)',   # 1080p FHD
            '2592x1944 (4:3)',    # High 4:3 resolution
            '3280x2464 (4:3)',    # Full 8MP resolution
            '4608x2592 (16:9)',   # Full 12MP resolution
        ])
        self.photo_resolution_combo.setCurrentText('3280x2464 (4:3)')
        settings_layout.addWidget(self.photo_resolution_combo, 3, 0, 1, 2)
        
        # Video Resolution
        video_resolution_label = QLabel(self.interface_text.video_resolution() if self.interface_text else "Video Resolution:")
        video_resolution_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(video_resolution_label, 4, 0, 1, 2)
        
        self.video_resolution_combo = QComboBox()
        self.video_resolution_combo.addItems([
            '640x480 (4:3)',      # VGA
            '800x600 (4:3)',      # SVGA  
            '1024x768 (4:3)',     # XGA
            '1280x720 (16:9)',    # 720p HD
            '1296x972 (4:3)',     # 4:3 mid-resolution
            '1640x1232 (4:3)',    # 4:3 aspect ratio
            '1920x1080 (16:9)',   # 1080p FHD
            '2304x1296 (16:9)',   # 16:9 aspect ratio
            '2592x1944 (4:3)',    # High 4:3 resolution
        ])
        self.video_resolution_combo.setCurrentText('1920x1080 (16:9)')
        settings_layout.addWidget(self.video_resolution_combo, 5, 0, 1, 2)
        
        # Auto Exposure
        self.chk_ae = QCheckBox(self.interface_text.auto_exposure() if self.interface_text else "Auto Exposure")
        self.chk_ae.setChecked(True)
        settings_layout.addWidget(self.chk_ae, 6, 0, 1, 2)
        
        # Auto White Balance
        self.chk_awb = QCheckBox(self.interface_text.auto_white_balance() if self.interface_text else "Auto White Balance")
        self.chk_awb.setChecked(True)
        settings_layout.addWidget(self.chk_awb, 7, 0, 1, 2)
        
        # Exposure Time
        self.exp_time = QSpinBox()
        self.exp_time.setRange(100, 3000000)
        self.exp_time.setValue(10000)
        self.exp_time.setSuffix(" μs")
        settings_layout.addWidget(self.exp_time, 8, 0, 1, 2)
        
        # Analogue Gain
        self.gain = QDoubleSpinBox()
        self.gain.setRange(0.0, 32.0)
        self.gain.setValue(1.0)
        self.gain.setDecimals(2)
        settings_layout.addWidget(self.gain, 9, 0, 1, 2)
        
        # Exposure Value
        self.exp_value = QDoubleSpinBox()
        self.exp_value.setRange(-10.0, 10.0)
        self.exp_value.setValue(0.0)
        self.exp_value.setDecimals(2)
        settings_layout.addWidget(self.exp_value, 10, 0, 1, 2)
        
        # Red Gain
        self.red_gain = QDoubleSpinBox()
        self.red_gain.setRange(0.0, 8.0)
        self.red_gain.setValue(1.0)
        self.red_gain.setDecimals(2)
        settings_layout.addWidget(self.red_gain, 11, 0, 1, 2)
        
        # Blue Gain
        self.blue_gain = QDoubleSpinBox()
        self.blue_gain.setRange(0.0, 8.0)
        self.blue_gain.setValue(1.0)
        self.blue_gain.setDecimals(2)
        settings_layout.addWidget(self.blue_gain, 12, 0, 1, 2)
        
        layout.addLayout(settings_layout)
        
        # Buttons
        button_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton(self.interface_text.refresh() if self.interface_text else "Refresh")
        self.btn_load_slot = QPushButton(self.interface_text.load() if self.interface_text else "Load")
        self.btn_save_slot = QPushButton(self.interface_text.save() if self.interface_text else "Save")
        self.btn_apply = QPushButton(self.interface_text.apply() if self.interface_text else "Apply")
        
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
            # Update settings name and resolutions
            self.settings_name.setText(settings.get('SettingsName', 'Basic'))
            
            # Update photo resolution
            photo_resolution = settings.get('PhotoResolution', '3280x2464')
            index = self.photo_resolution_combo.findText(photo_resolution)
            if index < 0:
                for i in range(self.photo_resolution_combo.count()):
                    text = self.photo_resolution_combo.itemText(i)
                    if text.startswith(photo_resolution):
                        index = i
                        break
            if index >= 0:
                self.photo_resolution_combo.setCurrentIndex(index)
            
            # Update video resolution
            video_resolution = settings.get('VideoResolution', '1920x1080')
            index = self.video_resolution_combo.findText(video_resolution)
            if index < 0:
                for i in range(self.video_resolution_combo.count()):
                    text = self.video_resolution_combo.itemText(i)
                    if text.startswith(video_resolution):
                        index = i
                        break
            if index >= 0:
                self.video_resolution_combo.setCurrentIndex(index)
            
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
    
    def _load_settings_from_api_fallback(self):
        """Load settings from API fallback when main API call fails."""
        try:
            # Try API again with different approach
            api_url = f"{self.api_base_url}/settings/camera"
            thread = APIClientThread('GET', api_url)
            thread.response_received.connect(self._on_settings_loaded)
            thread.finished.connect(lambda: self._cleanup_thread(thread))
            self.active_threads.append(thread)
            thread.start()
                
        except Exception as e:
            self.status_label.setText(f"Failed to load from API: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def apply_settings(self):
        """Apply current settings to the database."""
        self.status_label.setText("Applying settings...")
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        
        # Extract resolution from display text (remove aspect ratio)
        photo_resolution_text = self.photo_resolution_combo.currentText()
        photo_resolution = photo_resolution_text.split(' ')[0] if ' ' in photo_resolution_text else photo_resolution_text
        
        video_resolution_text = self.video_resolution_combo.currentText()
        video_resolution = video_resolution_text.split(' ')[0] if ' ' in video_resolution_text else video_resolution_text
        
        # Collect all settings
        settings_to_update = [
            ("CameraSettings", "SettingsName", self.settings_name.text()),
            ("CameraSettings", "PhotoResolution", photo_resolution),
            ("CameraSettings", "VideoResolution", video_resolution),
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
        """Apply settings with API only (no fallback to local DB)."""
        if index >= len(settings_list):
            self.status_label.setText("All settings applied successfully")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            # Emit signal that settings were updated
            self.settings_updated.emit()
            return
        
        table_name, parameter, value = settings_list[index]
        
        # Apply via API only
        self._apply_setting_via_api(table_name, parameter, value, settings_list, index)
    
    def _apply_setting_via_api(self, table_name, parameter, value, settings_list, index):
        """Apply setting via API."""
        try:
            thread = APIClientThread('POST', f"{self.api_base_url}/settings/update", {
                'table_name': table_name,
                'parameter': parameter,
                'value': value
            })
            
            # Store remaining settings for next call
            thread.remaining_settings = settings_list
            thread.next_index = index
            
            thread.response_received.connect(lambda success, message, data: 
                self._on_setting_applied_via_api(success, message, data, thread))
            thread.finished.connect(lambda: self._cleanup_thread(thread))
            self.active_threads.append(thread)
            thread.start()
                
        except Exception as e:
            self.status_label.setText(f"API error for {parameter}: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def _on_setting_applied_via_api(self, success, message, data, thread):
        """Handle individual setting application response via API."""
        if success:
            # Continue with next setting
            self._apply_settings_with_fallback(thread.remaining_settings, thread.next_index)
        else:
            self.status_label.setText(f"Failed to apply setting: {message}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def _apply_settings_sequentially(self, settings_list, index):
        """Apply settings one by one to avoid overwhelming the API."""
        if index >= len(settings_list):
            self.status_label.setText("All settings applied successfully")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            # Emit signal that settings were updated
            self.settings_updated.emit()
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
        """Load settings from a specific slot via API."""
        try:
            # Load settings from API for current slot
            api_url = f"{self.api_base_url}/settings/camera"
            thread = APIClientThread('GET', api_url)
            thread.response_received.connect(lambda success, message, data: 
                self._on_slot_settings_loaded(success, message, data, slot_id))
            thread.finished.connect(lambda: self._cleanup_thread(thread))
            self.active_threads.append(thread)
            thread.start()
            
        except Exception as e:
            self.status_label.setText(f"Error loading slot {slot_id}: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def _on_slot_settings_loaded(self, success, message, data, slot_id):
        """Handle slot settings loaded from API."""
        try:
            if success and (data.get('success') or 'id' in data):
                # Handle both formats: FastAPI direct response and wrapped response
                if 'id' in data:
                    # Direct FastAPI response
                    settings = data
                else:
                    # Wrapped response format
                    settings = data.get('data', {})
                
                self.current_slot_id = slot_id
                self.current_settings = settings
                self._update_ui_from_settings(settings)
                
                slot_name = settings.get('SettingsName', f"Slot {slot_id}")
                self.status_label.setText(f"Loaded settings from API: {slot_name}")
                self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
                
                # Emit signal that slot has changed
                self.slot_changed.emit(slot_id)
            else:
                self.status_label.setText(f"API error loading slot {slot_id}: {message}")
                self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
                
        except Exception as e:
            self.status_label.setText(f"Error processing slot {slot_id}: {str(e)}")
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
        """Save current settings to a specific slot via API."""
        try:
            # Extract resolution from display text (remove aspect ratio)
            photo_resolution_text = self.photo_resolution_combo.currentText()
            photo_resolution = photo_resolution_text.split(' ')[0] if ' ' in photo_resolution_text else photo_resolution_text
            
            video_resolution_text = self.video_resolution_combo.currentText()
            video_resolution = video_resolution_text.split(' ')[0] if ' ' in video_resolution_text else video_resolution_text
            
            # Collect current settings
            settings = {
                'SettingsName': self.settings_name.text() or f"Slot {slot_id}",
                'PhotoResolution': photo_resolution,
                'VideoResolution': video_resolution,
                'AeEnable': self.chk_ae.isChecked(),
                'AwbEnable': self.chk_awb.isChecked(),
                'ExposureTime': self.exp_time.value(),
                'AnalogueGain': self.gain.value(),
                'ExposureValue': self.exp_value.value(),
                'RedGain': self.red_gain.value(),
                'BlueGain': self.blue_gain.value()
            }
            
            # Save each setting via API
            settings_to_save = [
                ("CameraSettings", f"Slot{slot_id}Name", settings['SettingsName']),
                ("CameraSettings", f"Slot{slot_id}PhotoResolution", settings['PhotoResolution']),
                ("CameraSettings", f"Slot{slot_id}VideoResolution", settings['VideoResolution']),
                ("CameraSettings", f"Slot{slot_id}AeEnable", str(int(settings['AeEnable']))),
                ("CameraSettings", f"Slot{slot_id}AwbEnable", str(int(settings['AwbEnable']))),
                ("CameraSettings", f"Slot{slot_id}ExposureTime", str(settings['ExposureTime'])),
                ("CameraSettings", f"Slot{slot_id}AnalogueGain", str(settings['AnalogueGain'])),
                ("CameraSettings", f"Slot{slot_id}ExposureValue", str(settings['ExposureValue'])),
                ("CameraSettings", f"Slot{slot_id}RedGain", str(settings['RedGain'])),
                ("CameraSettings", f"Slot{slot_id}BlueGain", str(settings['BlueGain']))
            ]
            
            self._save_slot_settings_via_api(settings_to_save, 0, slot_id, settings['SettingsName'])
                
        except Exception as e:
            self.status_label.setText(f"Error saving to slot {slot_id}: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def _save_slot_settings_via_api(self, settings_list, index, slot_id, slot_name):
        """Save slot settings via API one by one."""
        if index >= len(settings_list):
            self.current_slot_id = slot_id
            self.status_label.setText(f"Settings saved to slot {slot_id}: {slot_name}")
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
        thread.slot_id = slot_id
        thread.slot_name = slot_name
        
        thread.response_received.connect(lambda success, message, data: 
            self._on_slot_setting_saved(success, message, data, thread))
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        self.active_threads.append(thread)
        thread.start()
    
    def _on_slot_setting_saved(self, success, message, data, thread):
        """Handle individual slot setting save response."""
        if success:
            # Continue with next setting
            self._save_slot_settings_via_api(thread.remaining_settings, thread.next_index, thread.slot_id, thread.slot_name)
        else:
            self.status_label.setText(f"Error saving setting: {message}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")


class SpectrometerSettingsWidget(QWidget):
    """Widget for spectrometer settings configuration."""
    
    def __init__(self, interface_text=None):
        super().__init__()
        self.interface_text = interface_text
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
    
    # Signal emitted when file settings are updated
    settings_updated = pyqtSignal()
    
    def __init__(self, interface_text=None):
        super().__init__()
        self.interface_text = interface_text
        self._build_ui()
        self._load_settings()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Photo save directory
        photo_dir_label = QLabel(self.interface_text.photo_save_directory() if self.interface_text else "Photo Save Directory:")
        photo_dir_label.setStyleSheet("QLabel { font-weight: bold; }")
        layout.addWidget(photo_dir_label)
        
        photo_dir_layout = QHBoxLayout()
        self.photo_dir_label = QLabel(self.interface_text.no_folder_selected() if self.interface_text else "No folder selected")
        self.photo_dir_label.setWordWrap(True)
        self.photo_dir_button = QPushButton(self.interface_text.select() if self.interface_text else "Select")
        
        photo_dir_layout.addWidget(self.photo_dir_label, 1)
        photo_dir_layout.addWidget(self.photo_dir_button)
        layout.addLayout(photo_dir_layout)
        
        # Spectrum save directory (placeholder for future)
        spectrum_dir_label = QLabel(self.interface_text.spectrum_save_directory() if self.interface_text else "Spectrum Save Directory:")
        spectrum_dir_label.setStyleSheet("QLabel { font-weight: bold; }")
        layout.addWidget(spectrum_dir_label)
        
        spectrum_dir_layout = QHBoxLayout()
        self.spectrum_dir_label = QLabel(self.interface_text.no_folder_selected() if self.interface_text else "No folder selected")
        self.spectrum_dir_label.setWordWrap(True)
        self.spectrum_dir_button = QPushButton(self.interface_text.select() if self.interface_text else "Select")
        
        spectrum_dir_layout.addWidget(self.spectrum_dir_label, 1)
        spectrum_dir_layout.addWidget(self.spectrum_dir_button)
        layout.addLayout(spectrum_dir_layout)
        
        # Progress bar for file operations
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)  # Hidden by default
        layout.addWidget(self.progress_bar)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        layout.addStretch()
        
        # Connect signals
        self.photo_dir_button.clicked.connect(self._select_photo_directory)
        self.spectrum_dir_button.clicked.connect(self._select_spectrum_directory)
    
    def _select_photo_directory(self):
        """Select photo save directory."""
        from DesktopApp.services.directory_control import get_home_directory
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        home_dir = get_home_directory()
        options = QFileDialog.Option.DontUseNativeDialog
        options |= QFileDialog.Option.ReadOnly
        
        current_directory = self.photo_dir_label.text() if os.path.isdir(self.photo_dir_label.text()) else home_dir
        
        directory = QFileDialog.getExistingDirectory(self, 
            self.interface_text.select_save_directory() if self.interface_text else "Select Save Directory",
            current_directory, options)
        if directory:
            if not directory.startswith(home_dir):
                QMessageBox.warning(self, 
                    self.interface_text.warning_title() if self.interface_text else "Warning",
                    self.interface_text.warning_select_out_of_home() if self.interface_text else "Please select a directory within your home folder.")
                return
            
            self.photo_dir_label.setText(directory)
            self._save_photo_directory(directory)
            self.settings_updated.emit()
    
    def _update_progress(self, value, maximum=100):
        """Update progress bar with current value and maximum."""
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
        if value >= maximum:
            # Hide progress bar when complete
            self.progress_bar.setVisible(False)
        elif not self.progress_bar.isVisible():
            # Show progress bar when operation starts
            self.progress_bar.setVisible(True)
    
    def _select_spectrum_directory(self):
        """Select spectrum save directory (placeholder for future implementation)."""
        from DesktopApp.services.directory_control import get_home_directory
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        home_dir = get_home_directory()
        options = QFileDialog.Option.DontUseNativeDialog
        options |= QFileDialog.Option.ReadOnly
        
        current_directory = self.spectrum_dir_label.text() if os.path.isdir(self.spectrum_dir_label.text()) else home_dir
        
        directory = QFileDialog.getExistingDirectory(self, 
            self.interface_text.select_save_directory() if self.interface_text else "Select Save Directory",
            current_directory, options)
        if directory:
            if not directory.startswith(home_dir):
                QMessageBox.warning(self, 
                    self.interface_text.warning_title() if self.interface_text else "Warning",
                    self.interface_text.warning_select_out_of_home() if self.interface_text else "Please select a directory within your home folder.")
                return
            
            self.spectrum_dir_label.setText(directory)
            self.status_label.setText(f"Spectrum directory set: {directory}")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
    
    def _save_photo_directory(self, directory):
        """Save photo directory to path manager."""
        try:
            from DesktopApp.config import path_manager
            path_manager.set_save_directory('photo', directory)
            self.status_label.setText(f"Photo directory saved: {directory}")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        except Exception as e:
            self.status_label.setText(f"Error saving directory: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def _load_settings(self):
        """Load file settings from path manager."""
        try:
            from DesktopApp.config import path_manager
            # Load photo directory
            photo_dir = path_manager.get_save_directory('photo')
            if photo_dir:
                self.photo_dir_label.setText(photo_dir)
            
            # Load spectrum directory (placeholder for future)
            # spectrum_dir = path_manager.get_save_directory('spectrum')
            # if spectrum_dir:
            #     self.spectrum_dir_label.setText(spectrum_dir)
                
        except Exception as e:
            print(f"Error loading file settings: {e}")
    
    def get_photo_save_directory(self):
        """Get current photo save directory."""
        dir_text = self.photo_dir_label.text()
        return dir_text if os.path.isdir(dir_text) else None


class DeviceSettingsWidget(QWidget):
    """Main device settings widget with dropdown selector."""
    
    # Signal emitted when settings are updated
    settings_updated = pyqtSignal()
    
    def __init__(self, interface_text=None, parent=None):
        super().__init__(parent)
        self.interface_text = interface_text
        self._build_ui()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Create dropdown for settings type selection
        self.settings_type_combo = QComboBox()
        if self.interface_text:
            self.settings_type_combo.addItems([
                self.interface_text.camera(),
                self.interface_text.spectrometer(),
                self.interface_text.file_settings()
            ])
        else:
            self.settings_type_combo.addItems(["Camera", "Spectrometer", "File Settings"])
        self.settings_type_combo.currentTextChanged.connect(self._on_settings_type_changed)
        self.settings_type_combo.setMaximumWidth(200)  # Limit width for better layout
        layout.addWidget(self.settings_type_combo)
        
        # Create stacked widget for different settings
        self.stacked_widget = QStackedWidget()
        
        # Add settings widgets
        self.camera_tab = CameraSettingsWidget(self.interface_text)
        self.spectrometer_tab = SpectrometerSettingsWidget(self.interface_text)
        self.file_tab = FileSettingsWidget(self.interface_text)
        
        self.stacked_widget.addWidget(self.camera_tab)
        self.stacked_widget.addWidget(self.spectrometer_tab)
        self.stacked_widget.addWidget(self.file_tab)
        
        layout.addWidget(self.stacked_widget)
        
        # Set font for better readability
        font = QFont()
        font.setPointSize(10)
        self.setFont(font)
        
        # Connect camera settings signals
        self.camera_tab.settings_updated.connect(self.settings_updated.emit)
        self.camera_tab.slot_changed.connect(self._on_slot_changed)
    
    def _on_settings_type_changed(self, text):
        """Handle settings type dropdown change."""
        if text == "Camera":
            self.stacked_widget.setCurrentWidget(self.camera_tab)
        elif text == "Spectrometer":
            self.stacked_widget.setCurrentWidget(self.spectrometer_tab)
        elif text == "File Settings":
            self.stacked_widget.setCurrentWidget(self.file_tab)
    
    def _on_slot_changed(self, slot_id):
        """Forward slot changed signal."""
        # This will be handled by parent widget
        pass