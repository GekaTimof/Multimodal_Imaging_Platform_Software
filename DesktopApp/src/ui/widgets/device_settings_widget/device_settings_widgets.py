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
    """Dialog for selecting and managing camera settings slots (0-10).

    Slot 0: Current Session (runtime settings applied to camera)
    Slots 1-10: Saved presets (persistent storage)
    """
    
    slot_selected = pyqtSignal(int)
    
    def __init__(self, parent=None, exclude_slot_0=False):
        super().__init__(parent)
        self.setWindowTitle(DialogStrings.CAMERA_SETTINGS_SLOTS)
        self.setModal(True)
        self.resize(800, 900) 
        self.slots_data = {}
        self.api_base_url = API_BASE_URL
        self.active_threads = []
        self.exclude_slot_0 = exclude_slot_0
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
        # Skip slot 0 if excluded
        if slot_id == 0 and self.exclude_slot_0:
            self._load_individual_slot_details(slot_id + 1)
            return
        
        if slot_id >= MAX_CAMERA_SLOTS:
            # All slots loaded (0-10)
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
                photo_resolution = settings.get('PhotoResolution', DEFAULT_RESOLUTION_PHOTO)
                video_resolution = settings.get('VideoResolution', DEFAULT_RESOLUTION_VIDEO)
                exposure_time = settings.get('ExposureTime', DEFAULT_EXPOSURE_TIME)
                ae_enable = settings.get('AeEnable', True)

                # Create display text with real parameters
                if slot_id == 0:
                    display_text = f"[CURRENT SESSION] {name}\n  Photo: {photo_resolution} | Video: {video_resolution}\n  Exposure: {exposure_time}μs | Auto-Exp: {'On' if ae_enable else 'Off'}"
                else:
                    display_text = f"Slot {slot_id} - {name}\n  Photo: {photo_resolution} | Video: {video_resolution}\n  Exposure: {exposure_time}μs | Auto-Exp: {'On' if ae_enable else 'Off'}"
                
                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, slot_id)
                self.slots_list.addItem(item)
            else:
                # Slot doesn't exist or API error, use defaults
                # Skip slot 0 if excluded
                if slot_id == 0 and self.exclude_slot_0:
                    pass
                elif slot_id == 0:
                    name = "Current Session"
                    display_text = f"[CURRENT SESSION] {name}\n  Photo: {DEFAULT_RESOLUTION_PHOTO} | Video: {DEFAULT_RESOLUTION_VIDEO}\n  Active camera settings"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, slot_id)
                    self.slots_list.addItem(item)
                else:
                    name = f"Slot {slot_id}"
                    display_text = f"Slot {slot_id} - {name}\n  Photo: {DEFAULT_RESOLUTION_PHOTO} | Video: {DEFAULT_RESOLUTION_VIDEO}\n  Empty slot"
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, slot_id)
                    self.slots_list.addItem(item)
            
            # Add separator after each slot except the last one
            # Last slot is 9 when showing 0-9, or 10 when showing 1-10 (exclude_slot_0)
            last_slot = 10 if self.exclude_slot_0 else 9
            if slot_id < last_slot:
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
        start_slot = 1 if self.exclude_slot_0 else 0
        for slot_id in range(start_slot, MAX_CAMERA_SLOTS):
            name = f"Slot {slot_id}"
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
            '1280x720 (16:9)',    # 720p HD
            '1296x972 (4:3)',     # 4:3 mid-resolution
            '1640x1232 (4:3)',    # 4:3 aspect ratio
            '1920x1080 (16:9)',   # 1080p FHD
            '2304x1296 (16:9)',   # 16:9 aspect ratio
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
        exp_time_label = QLabel(
            self.interface_text.exposure_time() if self.interface_text else SettingsWidgetStrings.EXPOSURE_TIME
        )
        exp_time_label.setStyleSheet("QLabel { font-weight: bold; }")
        exp_time_range_label = QLabel(f"({EXPOSURE_TIME_RANGE[0]} - {EXPOSURE_TIME_RANGE[1]} μs)")
        exp_time_range_label.setStyleSheet("QLabel { font-size: 10px; color: gray; }")
        settings_layout.addWidget(exp_time_label, 8, 0)
        settings_layout.addWidget(exp_time_range_label, 8, 1)
        
        self.exp_time = QSpinBox()
        self.exp_time.setRange(0, 2147483647)  # Remove Qt auto-limit, we handle clamping manually
        self.exp_time.setValue(DEFAULT_EXPOSURE_TIME)
        self.exp_time.setSuffix(" μs")
        settings_layout.addWidget(self.exp_time, 9, 0, 1, 2)
        
        # Analogue Gain
        gain_label = QLabel(
            self.interface_text.analogue_gain() if self.interface_text else SettingsWidgetStrings.ANALOGUE_GAIN
        )
        gain_label.setStyleSheet("QLabel { font-weight: bold; }")
        gain_range_label = QLabel(f"({ANALOGUE_GAIN_RANGE[0]} - {ANALOGUE_GAIN_RANGE[1]})")
        gain_range_label.setStyleSheet("QLabel { font-size: 10px; color: gray; }")
        settings_layout.addWidget(gain_label, 10, 0)
        settings_layout.addWidget(gain_range_label, 10, 1)
        
        self.gain = QDoubleSpinBox()
        self.gain.setRange(-1e9, 1e9)  # Remove Qt auto-limit, we handle clamping manually
        self.gain.setValue(DEFAULT_ANALOGUE_GAIN)
        self.gain.setDecimals(2)
        settings_layout.addWidget(self.gain, 11, 0, 1, 2)
        
        # Exposure Value
        exp_value_label = QLabel(
            self.interface_text.exposure_value() if self.interface_text else SettingsWidgetStrings.EXPOSURE_VALUE
        )
        exp_value_label.setStyleSheet("QLabel { font-weight: bold; }")
        exp_value_range_label = QLabel(f"({EXPOSURE_VALUE_RANGE[0]} - {EXPOSURE_VALUE_RANGE[1]})")
        exp_value_range_label.setStyleSheet("QLabel { font-size: 10px; color: gray; }")
        settings_layout.addWidget(exp_value_label, 12, 0)
        settings_layout.addWidget(exp_value_range_label, 12, 1)
        
        self.exp_value = QDoubleSpinBox()
        self.exp_value.setRange(-1e9, 1e9)  # Remove Qt auto-limit, we handle clamping manually
        self.exp_value.setValue(DEFAULT_EXPOSURE_VALUE)
        self.exp_value.setDecimals(2)
        settings_layout.addWidget(self.exp_value, 13, 0, 1, 2)
        
        # Red Gain
        red_gain_label = QLabel(
            self.interface_text.red_gain() if self.interface_text else SettingsWidgetStrings.RED_GAIN
        )
        red_gain_label.setStyleSheet("QLabel { font-weight: bold; }")
        red_gain_range_label = QLabel(f"({RED_GAIN_RANGE[0]} - {RED_GAIN_RANGE[1]})")
        red_gain_range_label.setStyleSheet("QLabel { font-size: 10px; color: gray; }")
        settings_layout.addWidget(red_gain_label, 14, 0)
        settings_layout.addWidget(red_gain_range_label, 14, 1)
        
        self.red_gain = QDoubleSpinBox()
        self.red_gain.setRange(-1e9, 1e9)  # Remove Qt auto-limit, we handle clamping manually
        self.red_gain.setValue(DEFAULT_RED_GAIN)
        self.red_gain.setDecimals(2)
        settings_layout.addWidget(self.red_gain, 15, 0, 1, 2)
        
        # Blue Gain
        blue_gain_label = QLabel(
            self.interface_text.blue_gain() if self.interface_text else SettingsWidgetStrings.BLUE_GAIN
        )
        blue_gain_label.setStyleSheet("QLabel { font-weight: bold; }")
        blue_gain_range_label = QLabel(f"({BLUE_GAIN_RANGE[0]} - {BLUE_GAIN_RANGE[1]})")
        blue_gain_range_label.setStyleSheet("QLabel { font-size: 10px; color: gray; }")
        settings_layout.addWidget(blue_gain_label, 16, 0)
        settings_layout.addWidget(blue_gain_range_label, 16, 1)
        
        self.blue_gain = QDoubleSpinBox()
        self.blue_gain.setRange(-1e9, 1e9)  # Remove Qt auto-limit, we handle clamping manually
        self.blue_gain.setValue(DEFAULT_BLUE_GAIN)
        self.blue_gain.setDecimals(2)
        settings_layout.addWidget(self.blue_gain, 17, 0, 1, 2)
        
        # Connect editingFinished to clamp values when user leaves the field
        self.exp_time.editingFinished.connect(self._clamp_exp_time)
        self.gain.editingFinished.connect(self._clamp_gain)
        self.exp_value.editingFinished.connect(self._clamp_exp_value)
        self.red_gain.editingFinished.connect(self._clamp_red_gain)
        self.blue_gain.editingFinished.connect(self._clamp_blue_gain)
        
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
        self.btn_apply.setToolTip(
            "Apply current settings to camera immediately. "
            "Restarts camera stream. Settings are NOT saved to database."
        )
        self.btn_save_slot.setToolTip(
            "Save current settings to a database slot. "
            "Does NOT affect the running camera. Use Apply to update camera."
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
    
    def _clamp_exp_time(self):
        """Clamp exposure time to valid range when editing finished."""
        # Get raw text from lineEdit before Qt processes it
        raw_text = self.exp_time.lineEdit().text().replace(" μs", "").strip()
        try:
            value = int(raw_text)
        except (ValueError, TypeError):
            value = self.exp_time.value()
        clamped = self._clamp_value(value, EXPOSURE_TIME_RANGE[0], EXPOSURE_TIME_RANGE[1], DEFAULT_EXPOSURE_TIME, int)
        if value != clamped:
            self.exp_time.setValue(clamped)
    
    def _clamp_gain(self):
        """Clamp analogue gain to valid range when editing finished."""
        raw_text = self.gain.lineEdit().text().strip()
        try:
            value = float(raw_text)
        except (ValueError, TypeError):
            value = self.gain.value()
        clamped = self._clamp_value(value, ANALOGUE_GAIN_RANGE[0], ANALOGUE_GAIN_RANGE[1], DEFAULT_ANALOGUE_GAIN, float)
        if value != clamped:
            self.gain.setValue(clamped)
    
    def _clamp_exp_value(self):
        """Clamp exposure value to valid range when editing finished."""
        raw_text = self.exp_value.lineEdit().text().strip()
        try:
            value = float(raw_text)
        except (ValueError, TypeError):
            value = self.exp_value.value()
        clamped = self._clamp_value(value, EXPOSURE_VALUE_RANGE[0], EXPOSURE_VALUE_RANGE[1], DEFAULT_EXPOSURE_VALUE, float)
        if value != clamped:
            self.exp_value.setValue(clamped)
    
    def _clamp_red_gain(self):
        """Clamp red gain to valid range when editing finished."""
        raw_text = self.red_gain.lineEdit().text().strip()
        try:
            value = float(raw_text)
        except (ValueError, TypeError):
            value = self.red_gain.value()
        clamped = self._clamp_value(value, RED_GAIN_RANGE[0], RED_GAIN_RANGE[1], DEFAULT_RED_GAIN, float)
        if value != clamped:
            self.red_gain.setValue(clamped)
    
    def _clamp_blue_gain(self):
        """Clamp blue gain to valid range when editing finished."""
        raw_text = self.blue_gain.lineEdit().text().strip()
        try:
            value = float(raw_text)
        except (ValueError, TypeError):
            value = self.blue_gain.value()
        clamped = self._clamp_value(value, BLUE_GAIN_RANGE[0], BLUE_GAIN_RANGE[1], DEFAULT_BLUE_GAIN, float)
        if value != clamped:
            self.blue_gain.setValue(clamped)
    
    def _clamp_value(self, value, min_val, max_val, default_val, value_type=float):
        """Clamp value to valid range. If value is outside range, return clamped value.
        
        Args:
            value: The value to clamp
            min_val: Minimum allowed value
            max_val: Maximum allowed value
            default_val: Default value if conversion fails
            value_type: Type to convert to (int or float)
            
        Returns:
            Clamped value within [min_val, max_val]
        """
        try:
            converted = value_type(value)
            if converted < min_val:
                return min_val
            elif converted > max_val:
                return max_val
            return converted
        except (ValueError, TypeError):
            return default_val
    
    def _update_ui_from_settings(self, settings):
        """Update UI controls from settings dictionary."""
        try:
            # Update settings name and resolutions
            self.settings_name.setText(settings.get('SettingsName', 'Basic'))
            
            # Update photo resolution
            photo_resolution = settings.get('PhotoResolution', DEFAULT_RESOLUTION_PHOTO)
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
            
            # Update numeric values with clamping to valid ranges
            exp_time_val = self._clamp_value(
                settings.get('ExposureTime', DEFAULT_EXPOSURE_TIME),
                EXPOSURE_TIME_RANGE[0], EXPOSURE_TIME_RANGE[1],
                DEFAULT_EXPOSURE_TIME, int
            )
            self.exp_time.setValue(exp_time_val)
            
            gain_val = self._clamp_value(
                settings.get('AnalogueGain', DEFAULT_ANALOGUE_GAIN),
                ANALOGUE_GAIN_RANGE[0], ANALOGUE_GAIN_RANGE[1],
                DEFAULT_ANALOGUE_GAIN, float
            )
            self.gain.setValue(gain_val)
            
            exp_value_val = self._clamp_value(
                settings.get('ExposureValue', DEFAULT_EXPOSURE_VALUE),
                EXPOSURE_VALUE_RANGE[0], EXPOSURE_VALUE_RANGE[1],
                DEFAULT_EXPOSURE_VALUE, float
            )
            self.exp_value.setValue(exp_value_val)
            
            red_gain_val = self._clamp_value(
                settings.get('RedGain', DEFAULT_RED_GAIN),
                RED_GAIN_RANGE[0], RED_GAIN_RANGE[1],
                DEFAULT_RED_GAIN, float
            )
            self.red_gain.setValue(red_gain_val)
            
            blue_gain_val = self._clamp_value(
                settings.get('BlueGain', DEFAULT_BLUE_GAIN),
                BLUE_GAIN_RANGE[0], BLUE_GAIN_RANGE[1],
                DEFAULT_BLUE_GAIN, float
            )
            self.blue_gain.setValue(blue_gain_val)
            
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
        """Apply current settings to the camera without saving to database.

        This updates the camera's operational parameters and restarts the
        camera stream to apply changes immediately. Settings are NOT saved
        to any database slot - use save_to_slot_dialog() to persist settings.
        """
        self.status_label.setText(SettingsWidgetStrings.APPLYING_SETTINGS)
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")

        # Ensure all numeric values are clamped before applying
        self._clamp_exp_time()
        self._clamp_gain()
        self._clamp_exp_value()
        self._clamp_red_gain()
        self._clamp_blue_gain()

        # Extract resolution from display text (remove aspect ratio)
        photo_resolution_text = self.photo_resolution_combo.currentText()
        photo_resolution = photo_resolution_text.split(' ')[0] if ' ' in photo_resolution_text else photo_resolution_text

        video_resolution_text = self.video_resolution_combo.currentText()
        video_resolution = video_resolution_text.split(' ')[0] if ' ' in video_resolution_text else video_resolution_text

        # Collect all settings into a dictionary for the new API
        settings = {
            'SettingsName': str(self.settings_name.text()),
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

        # Log settings for debugging
        logger.info(f"Applying session settings to camera: {settings}")

        # Apply settings via new API endpoint (no database save)
        self._apply_session_settings_via_api(settings)
    
    def _apply_session_settings_via_api(self, settings: Dict[str, Any]) -> None:
        """Apply session settings via API without saving to database.

        Args:
            settings: Dictionary containing camera settings to apply
        """
        try:
            thread = APIClientThread('POST', ENDPOINTS["apply_camera"], settings)
            thread.response_received.connect(self._on_session_settings_applied)
            thread.finished.connect(lambda: self._cleanup_thread(thread))
            self.active_threads.append(thread)
            thread.start()
        except Exception as e:
            logger.error(f"Error applying session settings: {e}")
            self.status_label.setText(f"Error applying settings: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def _on_session_settings_applied(self, success: bool, message: str, data: Dict[str, Any]) -> None:
        """Handle session settings application response."""
        if success:
            self.status_label.setText(SettingsWidgetStrings.ALL_SETTINGS_APPLIED)
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            # Emit signal that settings were updated (camera will be restarted)
            self.settings_updated.emit()
        else:
            logger.error(f"Failed to apply session settings: {message}")
            self.status_label.setText(f"Failed to apply: {message}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def show_slot_selection_dialog(self):
        """Show dialog for selecting a settings slot to load."""
        try:
            dialog = SettingsSlotDialog(self, exclude_slot_0=True)
            dialog.slot_selected.connect(self.load_settings_from_slot)
            dialog.exec_()
        except Exception as e:
            self.status_label.setText(f"Error opening slot dialog: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def load_settings_from_slot(self, slot_id):
        """Load settings from a specific slot via API.

        Slot 0: Just reads current session settings from slot 0.
        Slots 1-10: Copies settings from the slot to current session (slot 0)
                   and restarts the camera to apply settings.
        """
        try:
            if slot_id == 0:
                # For slot 0, just read current session settings
                api_url = ENDPOINTS["camera_settings_slot"].format(slot_id=slot_id)
                thread = APIClientThread('GET', api_url)
                thread.response_received.connect(lambda success, message, data:
                    self._on_slot_settings_loaded(success, message, data, slot_id))
                thread.finished.connect(lambda: self._cleanup_thread(thread))
                self.active_threads.append(thread)
                thread.start()
            else:
                # For slots 1-10, use load-slot endpoint which:
                # 1. Copies settings from slot N to slot 0 (session)
                # 2. Restarts camera with new settings
                self.status_label.setText(f"Loading slot {slot_id} to current session...")
                self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")

                api_url = ENDPOINTS["load_camera_slot"].format(slot_id=slot_id)
                thread = APIClientThread('POST', api_url, {})
                thread.response_received.connect(lambda success, message, data:
                    self._on_slot_loaded_to_session(success, message, data, slot_id))
                thread.finished.connect(lambda: self._cleanup_thread(thread))
                self.active_threads.append(thread)
                thread.start()

        except Exception as e:
            self.status_label.setText(f"Error loading slot {slot_id}: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def _on_slot_settings_loaded(self, success, message, data, slot_id):
        """Handle slot 0 settings loaded from API (current session)."""
        try:
            if success and 'id' in data:
                # FastAPI direct response for slot settings
                settings = data

                self.current_slot_id = slot_id
                self.current_settings = settings
                self._update_ui_from_settings(settings)

                slot_name = settings.get('SettingsName', 'Current Session')
                self.status_label.setText(f"Loaded current session: {slot_name}")
                self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")

                # Emit signal that slot has changed
                self.slot_changed.emit(slot_id)
            elif success and data.get('success') and 'data' in data:
                # Wrapped response format (fallback)
                settings = data.get('data', {})

                self.current_slot_id = slot_id
                self.current_settings = settings
                self._update_ui_from_settings(settings)

                slot_name = settings.get('SettingsName', 'Current Session')
                self.status_label.setText(f"Loaded current session: {slot_name}")
                self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")

                # Emit signal that slot has changed
                self.slot_changed.emit(slot_id)
            else:
                self.status_label.setText(f"API error loading session: {message}")
                self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

        except Exception as e:
            self.status_label.setText(f"Error processing session: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def _on_slot_loaded_to_session(self, success, message, data, source_slot_id):
        """Handle slot loaded to current session and applied to camera."""
        try:
            if success and data.get('success'):
                # Settings copied from slot N to slot 0 and camera restarted
                settings = data.get('data', {}).get('settings', {})

                self.current_slot_id = 0  # Now we're using session (slot 0)
                self.current_settings = settings
                self._update_ui_from_settings(settings)

                slot_name = settings.get('SettingsName', f"Slot {source_slot_id}")
                self.status_label.setText(
                    f"Loaded slot {source_slot_id} to current session, camera restarted"
                )
                self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")

                # Emit signal that settings were updated (camera restarted)
                self.settings_updated.emit()
                self.slot_changed.emit(0)
            else:
                self.status_label.setText(f"Failed to load slot {source_slot_id}: {message}")
                self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

        except Exception as e:
            self.status_label.setText(f"Error loading slot {source_slot_id}: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def save_to_slot_dialog(self):
        """Show dialog for selecting a slot to save current settings."""
        try:
            dialog = SettingsSlotDialog(self, exclude_slot_0=True)
            dialog.setWindowTitle("Save to Settings Slot")
            dialog.slot_selected.connect(self.save_current_settings_to_slot)
            dialog.exec_()
        except Exception as e:
            self.status_label.setText(f"Error opening save dialog: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def save_current_settings_to_slot(self, slot_id):
        """Save current settings to a specific slot via API.

        Note: Slot 0 is the current session. Saving to slot 0 will apply
        settings to the camera (same as Apply button). Use slots 1-10
        for persistent storage.
        """
        try:
            # If slot 0 selected, treat as apply operation
            if slot_id == 0:
                self.status_label.setText("Slot 0 is current session - using Apply instead")
                self.apply_settings()
                return

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
            self.status_label.setText(f"Saved to slot {slot_id}: {slot_name} (camera not affected)")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            # Note: Save does NOT restart camera - only Apply does that
        else:
            # If new API fails, try the old method (update current settings)
            self.status_label.setText(f"New API failed, trying fallback: {message}")
            self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
            self._save_slot_settings_fallback(settings, slot_id)
    
    def _save_slot_settings_fallback(self, settings, slot_id):
        """Fallback: re-attempt save to the correct slot via direct POST."""
        try:
            self.status_label.setText(f"Retrying save to slot {slot_id}...")
            self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
            self._save_slot_settings_via_api(settings, slot_id)
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

    integral_time_changed = pyqtSignal(int)
    set_dark_requested = pyqtSignal()
    clear_dark_requested = pyqtSignal()

    def __init__(self, interface_text=None):
        super().__init__()
        self.interface_text = interface_text
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # --- Connection status ---
        self.connection_label = QLabel(self.interface_text.status_disconnected() if self.interface_text else "Status: Disconnected")
        self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        self.connection_label.setWordWrap(True)
        layout.addWidget(self.connection_label)

        # --- Integral time ---
        it_label = QLabel(self.interface_text.integral_time() if self.interface_text else "Integral Time (ms):")
        it_label.setStyleSheet("QLabel { font-weight: bold; }")
        it_label.setWordWrap(True)
        layout.addWidget(it_label)

        self.integral_time_input = QSpinBox()
        self.integral_time_input.setRange(1, 10000)
        self.integral_time_input.setValue(100)
        self.integral_time_input.setButtonSymbols(QSpinBox.NoButtons)
        self.integral_time_input.valueChanged.connect(self.integral_time_changed.emit)
        layout.addWidget(self.integral_time_input)

        # --- Dark spectrum ---
        dark_label = QLabel("Dark Spectrum:")
        dark_label.setStyleSheet("QLabel { font-weight: bold; }")
        layout.addWidget(dark_label)

        self.set_dark_button = QPushButton(self.interface_text.set_dark_spectrum() if self.interface_text else "Set Dark Spectrum")
        self.set_dark_button.clicked.connect(self.set_dark_requested.emit)
        layout.addWidget(self.set_dark_button)

        self.clear_dark_button = QPushButton(self.interface_text.clear_dark_spectrum() if self.interface_text else "Clear Dark Spectrum")
        self.clear_dark_button.clicked.connect(self.clear_dark_requested.emit)
        layout.addWidget(self.clear_dark_button)

        layout.addStretch()

    def set_connection_status(self, connected: bool):
        """Update connection status label."""
        if connected:
            self.connection_label.setText("Status: Connected")
            self.connection_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connection_label.setText("Status: Disconnected")
            self.connection_label.setStyleSheet("color: red; font-weight: bold;")


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
        from services.directory_control import get_home_directory, is_path_inside
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        home_dir = get_home_directory()
        options = QFileDialog.Option.DontUseNativeDialog
        options |= QFileDialog.Option.ReadOnly
        
        current_directory = self.photo_dir_label.text() if os.path.isdir(self.photo_dir_label.text()) else home_dir
        
        directory = QFileDialog.getExistingDirectory(self, 
            self.interface_text.select_save_directory() if self.interface_text else "Select Save Directory",
            current_directory, options)
        if directory:
            if not is_path_inside(directory, home_dir):
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
        from services.directory_control import get_home_directory, is_path_inside
        from PyQt5.QtWidgets import QFileDialog, QMessageBox
        
        home_dir = get_home_directory()
        options = QFileDialog.Option.DontUseNativeDialog
        options |= QFileDialog.Option.ReadOnly
        
        current_directory = self.spectrum_dir_label.text() if os.path.isdir(self.spectrum_dir_label.text()) else home_dir
        
        directory = QFileDialog.getExistingDirectory(self, 
            self.interface_text.select_save_directory() if self.interface_text else "Select Save Directory",
            current_directory, options)
        if directory:
            if not is_path_inside(directory, home_dir):
                QMessageBox.warning(self, 
                    self.interface_text.warning_title() if self.interface_text else "Warning",
                    self.interface_text.warning_select_out_of_home() if self.interface_text else "Please select a directory within your home folder.")
                return
            
            self.spectrum_dir_label.setText(directory)
            self._save_spectrum_directory(directory)
            self.status_label.setText(f"Spectrum directory set: {directory}")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
    
    def _save_spectrum_directory(self, directory):
        """Save spectrum directory to path manager."""
        try:
            from config import path_manager
            path_manager.set_save_directory('spectrum', directory)
        except Exception as e:
            self.status_label.setText(f"Error saving directory: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def _save_photo_directory(self, directory):
        """Save photo directory to path manager."""
        try:
            from config import path_manager
            path_manager.set_save_directory('photo', directory)
            self.status_label.setText(f"Photo directory saved: {directory}")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        except Exception as e:
            self.status_label.setText(f"Error saving directory: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def _load_settings(self):
        """Load file settings from path manager."""
        try:
            from config import path_manager
            # Load photo directory
            photo_dir = path_manager.get_save_directory('photo')
            if photo_dir:
                self.photo_dir_label.setText(photo_dir)
            
            # Load spectrum directory
            spectrum_dir = path_manager.get_save_directory('spectrum')
            if spectrum_dir:
                self.spectrum_dir_label.setText(spectrum_dir)
                
        except Exception as e:
            print(f"Error loading file settings: {e}")
    
    def get_photo_save_directory(self):
        """Get current photo save directory."""
        dir_text = self.photo_dir_label.text()
        return dir_text if os.path.isdir(dir_text) else None

    def get_spectrum_save_directory(self):
        """Get current spectrum save directory."""
        dir_text = self.spectrum_dir_label.text()
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