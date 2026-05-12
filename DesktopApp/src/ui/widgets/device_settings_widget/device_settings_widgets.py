"""
Device Settings Widgets
Provides widgets for managing camera, spectrometer, and positioner settings.
"""

import json
import logging
import os
from typing import Dict, Any, List, Optional, Tuple

import requests
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDialog, QDialogButtonBox, QDoubleSpinBox, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QListWidget, QListWidgetItem, QPushButton,
    QProgressBar, QSpinBox, QStackedWidget, QVBoxLayout, QWidget
)

from config.api_config import API_BASE_URL, ENDPOINTS, TIMEOUT_SECONDS
from core.constants.camera_constants import (
    ANALOGUE_GAIN_RANGE, BLUE_GAIN_RANGE, DEFAULT_ANALOGUE_GAIN, DEFAULT_BLUE_GAIN,
    DEFAULT_EXPOSURE_TIME, DEFAULT_EXPOSURE_VALUE, DEFAULT_RED_GAIN,
    DEFAULT_RESOLUTION_PHOTO, DEFAULT_RESOLUTION_VIDEO, EXPOSURE_TIME_RANGE,
    EXPOSURE_VALUE_RANGE, MAX_CAMERA_SLOTS, RED_GAIN_RANGE, THREAD_TIMEOUT_MS
)
from core.constants.ui_strings import (
    DialogStrings, SettingsWidgetStrings, StatusMessages
)
from utils.error_handler import handle_api_error, validate_slot_id
from .positioner_settings_widget import PositionerSettingsWidget

logger = logging.getLogger(__name__)


class SettingsSlotDialog(QDialog):
    """Dialog for selecting and managing camera settings slots (0-9)."""
    
    slot_selected = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle(DialogStrings.CAMERA_SETTINGS_SLOTS)
        self.setModal(True)
        self.resize(800, 900) 
        self.slots_data = {}
        self.api_base_url = API_BASE_URL
        self.active_threads = []
        self._build_ui()
    
    def showEvent(self, event):
        """Override showEvent to reload slots data each time dialog is shown."""
        super().showEvent(event)
        self._load_slots()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Title
        title = QLabel(DialogStrings.SELECT_SETTINGS_SLOT)
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
    
    def _load_slots(self) -> None:
        """Load all settings slots from API."""
        try:
            # Load slots from API
            api_url = ENDPOINTS["camera_settings_slots"]
            thread = APIClientThread('GET', api_url)
            thread.response_received.connect(self._on_slots_loaded)
            thread.finished.connect(lambda: self._cleanup_thread(thread))
            self.active_threads.append(thread)
            thread.start()
                
        except Exception as e:
            logger.error(f"Error loading slots from API: {e}")
            # Fallback: create empty slots
            self._create_fallback_slots()
    
    def _on_slots_loaded(self, success, message, data):
        """Handle slots loaded response from API."""
        try:
            if success and data.get('success') and 'data' in data:
                self.slots_data = data['data']
                
                # Clear list and start loading individual slot details
                self.slots_list.clear()
                self._load_individual_slot_details(0)
            else:
                print(f"API error loading slots: {message}")
                # Fallback to empty slots
                self._create_fallback_slots()
                
        except Exception as e:
            print(f"Error processing slots data: {e}")
            self._create_fallback_slots()
    
    def _load_individual_slot_details(self, slot_id):
        """Load details for a specific slot via API."""
        if slot_id > 9:
            # All slots loaded
            return
        
        try:
            api_url = ENDPOINTS["camera_settings_slot"].format(slot_id=slot_id)
            thread = APIClientThread('GET', api_url)
            thread.response_received.connect(lambda success, message, data: 
                self._on_slot_details_loaded(success, message, data, slot_id))
            thread.finished.connect(lambda: self._cleanup_thread(thread))
            self.active_threads.append(thread)
            thread.start()
        except Exception as e:
            print(f"Error loading slot {slot_id} details: {e}")
            # Continue with next slot
            self._load_individual_slot_details(slot_id + 1)
    
    def _on_slot_details_loaded(self, success, message, data, slot_id):
        """Handle individual slot details loaded from API."""
        try:
            if success and 'id' in data:
                # Real slot data from API
                settings = data
                name = settings.get('SettingsName', f"Slot {slot_id}")
                photo_resolution = settings.get('PhotoResolution', '3280x2464')
                video_resolution = settings.get('VideoResolution', '1920x1080')
                exposure_time = settings.get('ExposureTime', 10000)
                ae_enable = settings.get('AeEnable', True)
                
                # Create display text with real parameters
                if slot_id == 0:
                    display_text = f"Slot {slot_id} - {name} (Basic)\n  Photo: {photo_resolution} | Video: {video_resolution}\n  Exposure: {exposure_time}μs | Auto-Exp: {'On' if ae_enable else 'Off'}"
                else:
                    display_text = f"Slot {slot_id} - {name}\n  Photo: {photo_resolution} | Video: {video_resolution}\n  Exposure: {exposure_time}μs | Auto-Exp: {'On' if ae_enable else 'Off'}"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, slot_id)
                self.slots_list.addItem(item)
            else:
                # Slot doesn't exist or API error, use defaults
                name = "Basic" if slot_id == 0 else f"Custom {slot_id}"
                if slot_id == 0:
                    display_text = f"Slot {slot_id} - {name} (Basic)\n  Photo: 3280x2464 | Video: 1920x1080\n  Default settings"
                else:
                    display_text = f"Slot {slot_id} - {name}\n  Photo: 3280x2464 | Video: 1920x1080\n  Empty slot"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, slot_id)
                self.slots_list.addItem(item)
            
            # Add separator after each slot except the last one
            if slot_id < 9:
                self._add_separator_after_current_item()
            
            # Continue with next slot
            self._load_individual_slot_details(slot_id + 1)
            
        except Exception as e:
            print(f"Error processing slot {slot_id} details: {e}")
            # Continue with next slot
            self._load_individual_slot_details(slot_id + 1)
    
    def _add_separator_after_current_item(self):
        """Add separator after the current last item in the list."""
        separator = QListWidgetItem("")
        separator.setFlags(Qt.NoItemFlags)  # Make it non-selectable
        separator.setSizeHint(separator.sizeHint().expandedTo(separator.sizeHint() + 
                       separator.sizeHint().expandedTo(separator.sizeHint())))
        # Create a visual separator using a line character
        separator.setText("─" * 40)  # Horizontal line
        separator.setForeground(separator.foreground().color().lighter(150))  # Make it lighter
        self.slots_list.addItem(separator)
    
    def _create_fallback_slots(self) -> None:
        """Create fallback slots when API fails."""
        self.slots_list.clear()
        for slot_id in range(MAX_CAMERA_SLOTS):
            name = "Basic" if slot_id == 0 else f"Custom {slot_id}"
            display_text = f"Slot {slot_id} - {name}\n  Photo: {DEFAULT_RESOLUTION_PHOTO} | Video: {DEFAULT_RESOLUTION_VIDEO}"
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, slot_id)
            self.slots_list.addItem(item)
            
            # Add visual separator after each item except the last one
            if slot_id < MAX_CAMERA_SLOTS - 1:
                self._add_separator_after_current_item()
    
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
    
    def _cleanup_thread(self, thread):
        """Remove thread from active threads list when finished."""
        if hasattr(self, 'active_threads') and thread in self.active_threads:
            self.active_threads.remove(thread)


class APIClientThread(QThread):
    """Thread for making API calls to avoid blocking the UI."""
    response_received = pyqtSignal(bool, str, dict)
    
    def __init__(self, method: str, url: str, data: Optional[Dict[str, Any]] = None):
        super().__init__()
        self.method = method.upper()
        self.url = url
        self.data = data
    
    def run(self) -> None:
        """Execute the API request."""
        try:
            headers = {'Content-Type': 'application/json'}
            
            if self.method == 'GET':
                response = requests.get(self.url, timeout=TIMEOUT_SECONDS)
            elif self.method == 'POST':
                response = requests.post(self.url, json=self.data, headers=headers, timeout=TIMEOUT_SECONDS)
            else:
                logger.error(f"Unsupported method: {self.method}")
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
                logger.warning(f"API validation error: {error_msg}")
                self.response_received.emit(False, error_msg, {})
            else:
                # Try to parse FastAPI error response
                try:
                    error_data = response.json()
                    error_msg = error_data.get('detail', f"HTTP {response.status_code}: {response.text}")
                except (ValueError, json.JSONDecodeError):
                    error_msg = f"HTTP {response.status_code}: {response.text}"
                logger.error(f"API error: {error_msg}")
                self.response_received.emit(False, error_msg, {})
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error: {e}")
            self.response_received.emit(False, f"Network error: {str(e)}", {})
        except Exception as e:
            logger.error(f"Unexpected error in API request: {e}")
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
        self.api_base_url = API_BASE_URL
        self.current_settings: Dict[str, Any] = {}
        self.active_threads: List[QThread] = []  # Track active threads
        self.current_slot_id = 0  # Track current settings slot
        self._build_ui()
        # Load default settings from slot 0 on startup
        self.load_settings_from_slot(0)
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        
        # Set margins and spacing for better layout
        layout.setContentsMargins(10, 10, 10, 10)  # Add padding around the widget
        layout.setSpacing(10)  # Add spacing between elements
        
        # Camera settings layout (no group box)
        settings_layout = QGridLayout()
        settings_layout.setContentsMargins(5, 5, 5, 5)  # Add padding inside settings grid
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
        
        # Photo Resolution
        photo_resolution_label = QLabel(
            self.interface_text.photo_resolution() if self.interface_text else SettingsWidgetStrings.PHOTO_RESOLUTION
        )
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
        self.photo_resolution_combo.setCurrentText(f'{DEFAULT_RESOLUTION_PHOTO} (4:3)')
        settings_layout.addWidget(self.photo_resolution_combo, 3, 0, 1, 2)
        
        # Video Resolution
        video_resolution_label = QLabel(
            self.interface_text.video_resolution() if self.interface_text else SettingsWidgetStrings.VIDEO_RESOLUTION
        )
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
        self.video_resolution_combo.setCurrentText(f'{DEFAULT_RESOLUTION_VIDEO} (16:9)')
        settings_layout.addWidget(self.video_resolution_combo, 5, 0, 1, 2)
        
        # Auto Exposure
        self.chk_ae = QCheckBox(
            self.interface_text.auto_exposure() if self.interface_text else SettingsWidgetStrings.AUTO_EXPOSURE
        )
        self.chk_ae.setChecked(True)
        settings_layout.addWidget(self.chk_ae, 6, 0, 1, 2)
        
        # Auto White Balance
        self.chk_awb = QCheckBox(
            self.interface_text.auto_white_balance() if self.interface_text else SettingsWidgetStrings.AUTO_WHITE_BALANCE
        )
        self.chk_awb.setChecked(True)
        settings_layout.addWidget(self.chk_awb, 7, 0, 1, 2)
        
        # Exposure Time
        self.exp_time = QSpinBox()
        self.exp_time.setRange(*EXPOSURE_TIME_RANGE)
        self.exp_time.setValue(DEFAULT_EXPOSURE_TIME)
        self.exp_time.setSuffix(" μs")
        settings_layout.addWidget(self.exp_time, 8, 0, 1, 2)
        
        # Analogue Gain
        self.gain = QDoubleSpinBox()
        self.gain.setRange(*ANALOGUE_GAIN_RANGE)
        self.gain.setValue(DEFAULT_ANALOGUE_GAIN)
        self.gain.setDecimals(2)
        settings_layout.addWidget(self.gain, 9, 0, 1, 2)
        
        # Exposure Value
        self.exp_value = QDoubleSpinBox()
        self.exp_value.setRange(*EXPOSURE_VALUE_RANGE)
        self.exp_value.setValue(DEFAULT_EXPOSURE_VALUE)
        self.exp_value.setDecimals(2)
        settings_layout.addWidget(self.exp_value, 10, 0, 1, 2)
        
        # Red Gain
        self.red_gain = QDoubleSpinBox()
        self.red_gain.setRange(*RED_GAIN_RANGE)
        self.red_gain.setValue(DEFAULT_RED_GAIN)
        self.red_gain.setDecimals(2)
        settings_layout.addWidget(self.red_gain, 11, 0, 1, 2)
        
        # Blue Gain
        self.blue_gain = QDoubleSpinBox()
        self.blue_gain.setRange(*BLUE_GAIN_RANGE)
        self.blue_gain.setValue(DEFAULT_BLUE_GAIN)
        self.blue_gain.setDecimals(2)
        settings_layout.addWidget(self.blue_gain, 12, 0, 1, 2)
        
        layout.addLayout(settings_layout)
        
        # Buttons - organize in rows with max 3 buttons per row
        button_row1_layout = QHBoxLayout()
        button_row2_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton(
            self.interface_text.refresh() if self.interface_text else SettingsWidgetStrings.REFRESH
        )
        self.btn_load_slot = QPushButton(
            self.interface_text.load() if self.interface_text else SettingsWidgetStrings.LOAD
        )
        self.btn_save_slot = QPushButton(
            self.interface_text.save() if self.interface_text else SettingsWidgetStrings.SAVE
        )
        self.btn_apply = QPushButton(
            self.interface_text.apply() if self.interface_text else SettingsWidgetStrings.APPLY
        )
        
        # First row: Refresh, Load, Save (3 buttons)
        button_row1_layout.addWidget(self.btn_refresh)
        button_row1_layout.addWidget(self.btn_load_slot)
        button_row1_layout.addWidget(self.btn_save_slot)
        button_row1_layout.addStretch()  # Push buttons to left
        
        # Second row: Apply (1 button)
        button_row2_layout.addWidget(self.btn_apply)
        button_row2_layout.addStretch()  # Push button to left
        
        layout.addLayout(button_row1_layout)
        layout.addLayout(button_row2_layout)
        
        # Status label
        self.status_label = QLabel(SettingsWidgetStrings.READY)
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
            video_resolution = settings.get('VideoResolution', DEFAULT_RESOLUTION_VIDEO)
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
            self.exp_time.setValue(int(settings.get('ExposureTime', DEFAULT_EXPOSURE_TIME)))
            self.gain.setValue(float(settings.get('AnalogueGain', DEFAULT_ANALOGUE_GAIN)))
            self.exp_value.setValue(float(settings.get('ExposureValue', DEFAULT_EXPOSURE_VALUE)))
            self.red_gain.setValue(float(settings.get('RedGain', DEFAULT_RED_GAIN)))
            self.blue_gain.setValue(float(settings.get('BlueGain', DEFAULT_BLUE_GAIN)))
            
            # Update control states (this will enable/disable appropriate controls)
            self._update_control_states()
            
        except Exception as e:
            logger.error(f"Error updating UI: {e}")
            self.status_label.setText(SettingsWidgetStrings.ERROR_UPDATING_UI.format(str(e)))
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def load_settings(self) -> None:
        """Load current camera settings from API."""
        self.status_label.setText(SettingsWidgetStrings.LOADING_SETTINGS)
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        
        # Try API
        thread = APIClientThread('GET', ENDPOINTS["camera_settings"])
        thread.response_received.connect(self._on_settings_loaded)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        self.active_threads.append(thread)
        thread.start()
    
    def _cleanup_thread(self, thread: QThread) -> None:
        """Remove thread from active threads list when finished."""
        if thread in self.active_threads:
            self.active_threads.remove(thread)
    
    def closeEvent(self, event) -> None:
        """Clean up active threads when widget is destroyed."""
        # Terminate all active threads
        for thread in self.active_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait(THREAD_TIMEOUT_MS)  # Wait up to timeout for thread to finish
        self.active_threads.clear()
        super().closeEvent(event)
    
    def _on_settings_loaded(self, success: bool, message: str, data: Dict[str, Any]) -> None:
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
            
            # Settings loaded successfully - user can manually apply if needed
            self.status_label.setText(SettingsWidgetStrings.SETTINGS_LOADED)
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            # API failed, show error
            logger.error(f"Failed to load settings: {message}")
            self.status_label.setText(SettingsWidgetStrings.FAILED_TO_LOAD)
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
        
    def apply_settings(self) -> None:
        """Apply current settings to the API."""
        self.status_label.setText(SettingsWidgetStrings.APPLYING_SETTINGS)
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        
        # Extract resolution from display text (remove aspect ratio)
        photo_resolution_text = self.photo_resolution_combo.currentText()
        photo_resolution = photo_resolution_text.split(' ')[0] if ' ' in photo_resolution_text else photo_resolution_text
        
        video_resolution_text = self.video_resolution_combo.currentText()
        video_resolution = video_resolution_text.split(' ')[0] if ' ' in video_resolution_text else video_resolution_text
        
        # Collect all settings
        settings_to_update = [
            ("CameraSettings", "SettingsName", str(self.settings_name.text())),
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
        
        # Log settings for debugging
        logger.info(f"Applying settings: {settings_to_update}")
        
        # Apply settings via API
        self._apply_settings_with_fallback(settings_to_update, 0)
    
    def _apply_settings_with_fallback(self, settings_list, index):
        """Apply settings sequentially (one at a time)."""
        if index >= len(settings_list):
            self.status_label.setText("All settings applied successfully")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            # Emit signal that settings were updated
            self.settings_updated.emit()
            return
        
        table_name, parameter, value = settings_list[index]
        
        # Apply via API only - but wait for response before continuing
        self._apply_settings_sequentially(settings_list, index)
    
    def _apply_setting_via_api(self, table_name, parameter, value, settings_list, index):
        """Apply setting via API."""
        try:
            logger.info(f"Applying {parameter}={value} to {table_name}")
            
            # Add small delay to prevent overwhelming the API
            import time
            if index > 0:  # Don't delay first request
                time.sleep(0.1)  # 100ms delay between requests
            
            thread = APIClientThread('POST', ENDPOINTS['update_parameter'], {
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
            logger.error(f"API error for {parameter}: {e}")
            self.status_label.setText(f"API error for {parameter}: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def _on_setting_applied_via_api(self, success, message, data, thread):
        """Handle individual setting application response via API."""
        if success:
            logger.info("Successfully applied setting, continuing with next one")
            # Continue with next setting (increment index)
            self._apply_settings_with_fallback(thread.remaining_settings, thread.next_index + 1)
        else:
            logger.error(f"Failed to apply setting: {message}")
            self.status_label.setText(f"Failed to apply setting: {message}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def _apply_settings_sequentially(self, settings_list, index):
        """Apply settings one by one to avoid overwhelming API."""
        if index >= len(settings_list):
            self.status_label.setText("All settings applied successfully")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            # Emit signal that settings were updated
            self.settings_updated.emit()
            return
        
        table_name, parameter, value = settings_list[index]
        
        # Add small delay to prevent overwhelming the API
        import time
        if index > 0:  # Don't delay first request
            time.sleep(0.1)  # 100ms delay between requests
        
        thread = APIClientThread('POST', ENDPOINTS['update_parameter'], {
            'table_name': table_name,
            'parameter': parameter,
            'value': value
        })
        
        # Store remaining settings for next call
        thread.remaining_settings = settings_list
        thread.next_index = index + 1
        
        thread.response_received.connect(lambda success, message, data: 
            self._on_setting_applied_sequentially(success, message, data, thread))
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        self.active_threads.append(thread)
        thread.start()
    
    def _on_setting_applied_sequentially(self, success, message, data, thread):
        """Handle individual setting application response in sequential mode."""
        if success:
            logger.info("Successfully applied setting, continuing with next one")
            # Continue with next setting (increment index)
            self._apply_settings_sequentially(thread.remaining_settings, thread.next_index)
        else:
            logger.error(f"Failed to apply setting: {message}")
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
            # Load settings from API for specific slot
            api_url = ENDPOINTS["camera_settings_slot"].format(slot_id=slot_id)
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
            if success and 'id' in data:
                # FastAPI direct response for slot settings
                settings = data
                
                self.current_slot_id = slot_id
                self.current_settings = settings
                self._update_ui_from_settings(settings)
                
                slot_name = settings.get('SettingsName', f"Slot {slot_id}")
                self.status_label.setText(f"Loaded settings from slot {slot_id}: {slot_name}")
                self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
                
                # Emit signal that slot has changed
                self.slot_changed.emit(slot_id)
            elif success and data.get('success') and 'data' in data:
                # Wrapped response format (fallback)
                settings = data.get('data', {})
                
                self.current_slot_id = slot_id
                self.current_settings = settings
                self._update_ui_from_settings(settings)
                
                slot_name = settings.get('SettingsName', f"Slot {slot_id}")
                self.status_label.setText(f"Loaded settings from slot {slot_id}: {slot_name}")
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
                'SettingsName': str(self.settings_name.text() or f"Slot {slot_id}"),
                'PhotoResolution': photo_resolution,
                'VideoResolution': video_resolution,
                'AeEnable': self.chk_ae.isChecked(),
                'AwbEnable': self.chk_awb.isChecked(),
                'ExposureTime': int(self.exp_time.value()),
                'AnalogueGain': float(self.gain.value()),
                'ExposureValue': float(self.exp_value.value()),
                'RedGain': float(self.red_gain.value()),
                'BlueGain': float(self.blue_gain.value())
            }
            
            # Save all settings at once via new API endpoint
            self._save_slot_settings_via_api(settings, slot_id)
                
        except Exception as e:
            self.status_label.setText(f"Error saving to slot {slot_id}: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def _save_slot_settings_via_api(self, settings, slot_id):
        """Save slot settings via new API endpoint with fallback."""
        try:
            thread = APIClientThread('POST', ENDPOINTS["save_camera_slot"].format(slot_id=slot_id), settings)
            
            thread.response_received.connect(lambda success, message, data: 
                self._on_slot_settings_saved_via_new_api(success, message, data, slot_id, settings))
            thread.finished.connect(lambda: self._cleanup_thread(thread))
            self.active_threads.append(thread)
            thread.start()
                
        except Exception as e:
            self.status_label.setText(f"API error saving to slot {slot_id}: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def _on_slot_settings_saved_via_new_api(self, success, message, data, slot_id, settings):
        """Handle slot settings save response from new API endpoint."""
        if success:
            self.current_slot_id = slot_id
            slot_name = data.get('data', {}).get('settings', {}).get('SettingsName', f"Slot {slot_id}")
            self.status_label.setText(f"Settings saved to slot {slot_id}: {slot_name}")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            # If new API fails, try the old method (update current settings)
            self.status_label.setText(f"New API failed, trying fallback: {message}")
            self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
            self._save_slot_settings_fallback(settings, slot_id)
    
    def _save_slot_settings_fallback(self, settings, slot_id):
        """Fallback method: save settings by updating current settings."""
        try:
            # Update current settings (not slot-specific)
            settings_to_update = [
                ("CameraSettings", "SettingsName", str(settings.get('SettingsName', f"Slot {slot_id}"))),
                ("CameraSettings", "PhotoResolution", settings.get('PhotoResolution', '3280x2464')),
                ("CameraSettings", "VideoResolution", settings.get('VideoResolution', '1920x1080')),
                ("CameraSettings", "AeEnable", str(int(settings.get('AeEnable', True)))),
                ("CameraSettings", "AwbEnable", str(int(settings.get('AwbEnable', True)))),
                ("CameraSettings", "ExposureTime", str(int(settings.get('ExposureTime', 10000)))),
                ("CameraSettings", "AnalogueGain", str(float(settings.get('AnalogueGain', 1.0)))),
                ("CameraSettings", "ExposureValue", str(float(settings.get('ExposureValue', 0.0)))),
                ("CameraSettings", "RedGain", str(float(settings.get('RedGain', 1.0)))),
                ("CameraSettings", "BlueGain", str(float(settings.get('BlueGain', 1.0))))
            ]
            
            self._apply_settings_with_fallback(settings_to_update, 0)
            
        except Exception as e:
            self.status_label.setText(f"Fallback save failed: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
        
    def _on_slot_settings_saved(self, success, message, data, slot_id):
        """Handle slot settings save response (legacy method)."""
        if success:
            self.current_slot_id = slot_id
            slot_name = data.get('data', {}).get('settings', {}).get('SettingsName', f"Slot {slot_id}")
            self.status_label.setText(f"Settings saved to slot {slot_id}: {slot_name}")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            self.status_label.setText(f"Error saving to slot {slot_id}: {message}")
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
        
        # Set margins and spacing for better layout
        layout.setContentsMargins(10, 10, 10, 10)  # Add padding around the widget
        layout.setSpacing(10)  # Add spacing between elements
        
        # Photo save directory
        photo_dir_label = QLabel(self.interface_text.photo_save_directory() if self.interface_text else "Photo Save Directory:")
        photo_dir_label.setStyleSheet("QLabel { font-weight: bold; }")
        photo_dir_label.setWordWrap(True)
        layout.addWidget(photo_dir_label)
        
        photo_dir_layout = QHBoxLayout()
        photo_dir_layout.setSpacing(10)  # Add spacing between label and button
        self.photo_dir_label = QLabel(self.interface_text.no_folder_selected() if self.interface_text else "No folder selected")
        self.photo_dir_label.setWordWrap(True)
        self.photo_dir_label.setMaximumWidth(250)  # Prevent label from stretching too wide
        self.photo_dir_button = QPushButton(self.interface_text.select() if self.interface_text else "Select")
        self.photo_dir_button.setMaximumWidth(80)  # Limit button width
        
        photo_dir_layout.addWidget(self.photo_dir_label, 1)
        photo_dir_layout.addWidget(self.photo_dir_button)
        layout.addLayout(photo_dir_layout)
        
        # Spectrum save directory (placeholder for future)
        spectrum_dir_label = QLabel(self.interface_text.spectrum_save_directory() if self.interface_text else "Spectrum Save Directory:")
        spectrum_dir_label.setStyleSheet("QLabel { font-weight: bold; }")
        spectrum_dir_label.setWordWrap(True)
        layout.addWidget(spectrum_dir_label)
        
        spectrum_dir_layout = QHBoxLayout()
        spectrum_dir_layout.setSpacing(10)  # Add spacing between label and button
        self.spectrum_dir_label = QLabel(self.interface_text.no_folder_selected() if self.interface_text else "No folder selected")
        self.spectrum_dir_label.setWordWrap(True)
        self.spectrum_dir_label.setMaximumWidth(250)  # Prevent label from stretching too wide
        self.spectrum_dir_button = QPushButton(self.interface_text.select() if self.interface_text else "Select")
        self.spectrum_dir_button.setMaximumWidth(80)  # Limit button width
        
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
        
        # Set margins and spacing for better layout
        layout.setContentsMargins(10, 10, 10, 10)  # Add padding around the widget
        layout.setSpacing(10)  # Add spacing between elements
        
        # Create dropdown for settings type selection
        self.settings_type_combo = QComboBox()
        if self.interface_text:
            self.settings_type_combo.addItems([
                self.interface_text.camera(),
                self.interface_text.spectrometer(),
                self.interface_text.positioner() if hasattr(self.interface_text, 'positioner') else "Positioner",
                self.interface_text.file_settings()
            ])
        else:
            self.settings_type_combo.addItems(["Camera", "Spectrometer", "Positioner", "File Settings"])
        self.settings_type_combo.currentTextChanged.connect(self._on_settings_type_changed)
        self.settings_type_combo.setMaximumWidth(200)  # Limit width for better layout
        layout.addWidget(self.settings_type_combo)
        
        # Create stacked widget for different settings
        self.stacked_widget = QStackedWidget()
        
        # Add settings widgets
        self.camera_tab = CameraSettingsWidget(self.interface_text)
        self.spectrometer_tab = SpectrometerSettingsWidget(self.interface_text)
        self.positioner_tab = PositionerSettingsWidget(self.interface_text)
        self.file_tab = FileSettingsWidget(self.interface_text)
        
        self.stacked_widget.addWidget(self.camera_tab)
        self.stacked_widget.addWidget(self.spectrometer_tab)
        self.stacked_widget.addWidget(self.positioner_tab)
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
        # Handle localized text comparison
        if self.interface_text:
            camera_text = self.interface_text.camera()
            spectrometer_text = self.interface_text.spectrometer()
            positioner_text = self.interface_text.positioner()
            file_settings_text = self.interface_text.file_settings()
        else:
            camera_text = "Camera"
            spectrometer_text = "Spectrometer"
            positioner_text = "Positioner"
            file_settings_text = "File Settings"
        
        if text == camera_text:
            self.stacked_widget.setCurrentWidget(self.camera_tab)
            # Call refresh when switching to camera settings
            self.camera_tab.load_settings()
        elif text == spectrometer_text:
            self.stacked_widget.setCurrentWidget(self.spectrometer_tab)
            # Placeholder for spectrometer refresh (will be implemented later)
            self._spectrometer_refresh_placeholder()
        elif text == positioner_text:
            self.stacked_widget.setCurrentWidget(self.positioner_tab)
            # Load positioner settings when switching
            self.positioner_tab.load_settings()
        elif text == file_settings_text:
            self.stacked_widget.setCurrentWidget(self.file_tab)
    
    def _on_slot_changed(self, slot_id):
        """Forward slot changed signal."""
        # This will be handled by parent widget
        pass
    
    def _spectrometer_refresh_placeholder(self):
        """Placeholder method for spectrometer refresh functionality."""
        # This will be implemented when spectrometer settings are fully developed
        print("Spectrometer refresh called - placeholder implementation")
    
    def switch_to_settings(self, settings_type):
        """
        Switch to specific settings type and trigger appropriate actions.
        
        Args:
            settings_type (str): Type of settings to switch to ('Camera', 'Spectrometer', 'Positioner', 'File Settings')
        """
        # Find the index of the requested settings type
        index = self.settings_type_combo.findText(settings_type)
        if index >= 0:
            current_index = self.settings_type_combo.currentIndex()
            if current_index != index:
                # Only switch if different from current
                self.settings_type_combo.setCurrentIndex(index)
                print(f"Switched to settings: {settings_type}")
            else:
                # Already on correct settings, but still trigger refresh for camera
                if settings_type == self.interface_text.camera() if self.interface_text else "Camera":
                    print("Already on camera settings, triggering refresh anyway")
                    self.camera_tab.load_settings()
        else:
            print(f"Settings type '{settings_type}' not found")