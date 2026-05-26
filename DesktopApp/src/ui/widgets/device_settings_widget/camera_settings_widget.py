"""
Camera Settings Widget
Widget for configuring camera parameters (resolution, exposure, gain, white balance).
"""

import logging
from typing import Dict, Any, List

from PyQt5.QtCore import QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QCheckBox, QComboBox, QDoubleSpinBox, QGridLayout,
    QHBoxLayout, QLabel, QLineEdit, QPushButton,
    QSpinBox, QVBoxLayout, QWidget
)

from config.api_config import API_BASE_URL, ENDPOINTS
from core.constants.camera_constants import (
    ANALOGUE_GAIN_RANGE, BLUE_GAIN_RANGE, DEFAULT_ANALOGUE_GAIN, DEFAULT_BLUE_GAIN,
    DEFAULT_EXPOSURE_TIME, DEFAULT_EXPOSURE_VALUE, DEFAULT_RED_GAIN,
    DEFAULT_RESOLUTION_PHOTO, DEFAULT_RESOLUTION_VIDEO, EXPOSURE_TIME_RANGE,
    EXPOSURE_VALUE_RANGE, RED_GAIN_RANGE, THREAD_TIMEOUT_MS,
)
from core.constants.ui_strings import SettingsWidgetStrings
from .api_client_thread import APIClientThread
from .settings_slot_dialog import SettingsSlotDialog

logger = logging.getLogger(__name__)


class CameraSettingsWidget(QWidget):
    """Widget for camera settings configuration."""

    slot_changed = pyqtSignal(int)
    settings_updated = pyqtSignal()

    def __init__(self, interface_text=None, theme_manager=None):
        super().__init__()
        self.interface_text = interface_text
        self._theme_manager = theme_manager
        self.api_base_url = API_BASE_URL
        self.current_settings: Dict[str, Any] = {}
        self.active_threads: List[QThread] = []
        self.current_slot_id = 0
        self._build_ui()
        self.load_settings_from_slot(0)

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

        # Photo Resolution
        photo_res_label = QLabel(
            self.interface_text.photo_resolution() if self.interface_text else SettingsWidgetStrings.PHOTO_RESOLUTION
        )
        photo_res_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(photo_res_label, 2, 0, 1, 2)

        self.photo_resolution_combo = QComboBox()
        self.photo_resolution_combo.addItems([
            '640x480 (4:3)', '800x600 (4:3)', '1024x768 (4:3)',
            '1280x720 (16:9)', '1296x972 (4:3)', '1640x1232 (4:3)',
            '1920x1080 (16:9)', '2304x1296 (16:9)', '2592x1944 (4:3)',
            '3280x2464 (4:3)', '4608x2592 (16:9)',
        ])
        self.photo_resolution_combo.setCurrentText(f'{DEFAULT_RESOLUTION_PHOTO} (4:3)')
        settings_layout.addWidget(self.photo_resolution_combo, 3, 0, 1, 2)

        # Video Resolution
        video_res_label = QLabel(
            self.interface_text.video_resolution() if self.interface_text else SettingsWidgetStrings.VIDEO_RESOLUTION
        )
        video_res_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(video_res_label, 4, 0, 1, 2)

        self.video_resolution_combo = QComboBox()
        self.video_resolution_combo.addItems([
            '640x480 (4:3)', '800x600 (4:3)', '1024x768 (4:3)',
            '1280x720 (16:9)', '1296x972 (4:3)', '1640x1232 (4:3)',
            '1920x1080 (16:9)',
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
        self.exp_time_label = QLabel(
            self.interface_text.exposure_time() if self.interface_text else SettingsWidgetStrings.EXPOSURE_TIME
        )
        self.exp_time_label.setStyleSheet("QLabel { font-weight: bold; }")
        self.exp_time_range_label = QLabel(f"({EXPOSURE_TIME_RANGE[0]} - {EXPOSURE_TIME_RANGE[1]} μs)")
        self.exp_time_range_label.setStyleSheet("QLabel { font-size: 10px; color: gray; }")
        settings_layout.addWidget(self.exp_time_label, 8, 0)
        settings_layout.addWidget(self.exp_time_range_label, 8, 1)

        self.exp_time = QSpinBox()
        self.exp_time.setRange(0, 2147483647)
        self.exp_time.setValue(DEFAULT_EXPOSURE_TIME)
        self.exp_time.setSuffix(" μs")
        settings_layout.addWidget(self.exp_time, 9, 0, 1, 2)

        # Analogue Gain
        self.gain_label = QLabel(
            self.interface_text.analogue_gain() if self.interface_text else SettingsWidgetStrings.ANALOGUE_GAIN
        )
        self.gain_label.setStyleSheet("QLabel { font-weight: bold; }")
        self.gain_range_label = QLabel(f"({ANALOGUE_GAIN_RANGE[0]} - {ANALOGUE_GAIN_RANGE[1]})")
        self.gain_range_label.setStyleSheet("QLabel { font-size: 10px; color: gray; }")
        settings_layout.addWidget(self.gain_label, 10, 0)
        settings_layout.addWidget(self.gain_range_label, 10, 1)

        self.gain = QDoubleSpinBox()
        self.gain.setRange(-1e9, 1e9)
        self.gain.setValue(DEFAULT_ANALOGUE_GAIN)
        self.gain.setDecimals(2)
        settings_layout.addWidget(self.gain, 11, 0, 1, 2)

        # Exposure Value
        self.exp_value_label = QLabel(
            self.interface_text.exposure_value() if self.interface_text else SettingsWidgetStrings.EXPOSURE_VALUE
        )
        self.exp_value_label.setStyleSheet("QLabel { font-weight: bold; }")
        self.exp_value_range_label = QLabel(f"({EXPOSURE_VALUE_RANGE[0]} - {EXPOSURE_VALUE_RANGE[1]})")
        self.exp_value_range_label.setStyleSheet("QLabel { font-size: 10px; color: gray; }")
        settings_layout.addWidget(self.exp_value_label, 12, 0)
        settings_layout.addWidget(self.exp_value_range_label, 12, 1)

        self.exp_value = QDoubleSpinBox()
        self.exp_value.setRange(-1e9, 1e9)
        self.exp_value.setValue(DEFAULT_EXPOSURE_VALUE)
        self.exp_value.setDecimals(2)
        settings_layout.addWidget(self.exp_value, 13, 0, 1, 2)

        # Red Gain
        self.red_gain_label = QLabel(
            self.interface_text.red_gain() if self.interface_text else SettingsWidgetStrings.RED_GAIN
        )
        self.red_gain_label.setStyleSheet("QLabel { font-weight: bold; }")
        self.red_gain_range_label = QLabel(f"({RED_GAIN_RANGE[0]} - {RED_GAIN_RANGE[1]})")
        self.red_gain_range_label.setStyleSheet("QLabel { font-size: 10px; color: gray; }")
        settings_layout.addWidget(self.red_gain_label, 14, 0)
        settings_layout.addWidget(self.red_gain_range_label, 14, 1)

        self.red_gain = QDoubleSpinBox()
        self.red_gain.setRange(-1e9, 1e9)
        self.red_gain.setValue(DEFAULT_RED_GAIN)
        self.red_gain.setDecimals(2)
        settings_layout.addWidget(self.red_gain, 15, 0, 1, 2)

        # Blue Gain
        self.blue_gain_label = QLabel(
            self.interface_text.blue_gain() if self.interface_text else SettingsWidgetStrings.BLUE_GAIN
        )
        self.blue_gain_label.setStyleSheet("QLabel { font-weight: bold; }")
        self.blue_gain_range_label = QLabel(f"({BLUE_GAIN_RANGE[0]} - {BLUE_GAIN_RANGE[1]})")
        self.blue_gain_range_label.setStyleSheet("QLabel { font-size: 10px; color: gray; }")
        settings_layout.addWidget(self.blue_gain_label, 16, 0)
        settings_layout.addWidget(self.blue_gain_range_label, 16, 1)

        self.blue_gain = QDoubleSpinBox()
        self.blue_gain.setRange(-1e9, 1e9)
        self.blue_gain.setValue(DEFAULT_RED_GAIN)
        self.blue_gain.setDecimals(2)
        settings_layout.addWidget(self.blue_gain, 17, 0, 1, 2)

        self.exp_time.editingFinished.connect(self._clamp_exp_time)
        self.gain.editingFinished.connect(self._clamp_gain)
        self.exp_value.editingFinished.connect(self._clamp_exp_value)
        self.red_gain.editingFinished.connect(self._clamp_red_gain)
        self.blue_gain.editingFinished.connect(self._clamp_blue_gain)

        layout.addLayout(settings_layout)

        # Buttons
        button_row1_layout = QHBoxLayout()

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

        button_row1_layout.addWidget(self.btn_apply)
        button_row1_layout.addWidget(self.btn_load_slot)
        button_row1_layout.addWidget(self.btn_save_slot)
        button_row1_layout.addStretch()

        layout.addLayout(button_row1_layout)

        self.status_label = QLabel(SettingsWidgetStrings.READY)
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        self.status_label.setWordWrap(True)
        self.status_label.setMaximumWidth(300)
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.btn_load_slot.clicked.connect(self.show_slot_selection_dialog)
        self.btn_save_slot.clicked.connect(self.save_to_slot_dialog)
        self.btn_apply.clicked.connect(self.apply_settings)

        self.chk_ae.toggled.connect(self._update_control_states)
        self.chk_awb.toggled.connect(self._update_control_states)
        self._update_control_states()

    def _update_control_states(self):
        """Enable/disable controls based on auto exposure and white balance settings."""
        ae_enabled = self.chk_ae.isChecked()
        awb_enabled = self.chk_awb.isChecked()
        self.exp_time.setEnabled(not ae_enabled)
        self.gain.setEnabled(not ae_enabled)
        self.exp_value.setEnabled(ae_enabled)
        self.red_gain.setEnabled(not awb_enabled)
        self.blue_gain.setEnabled(not awb_enabled)
        self._set_manual_control_visual_state([self.exp_time_label, self.exp_time_range_label], not ae_enabled)
        self._set_manual_control_visual_state([self.gain_label, self.gain_range_label], not ae_enabled)
        self._set_manual_control_visual_state([self.exp_value_label, self.exp_value_range_label], ae_enabled)
        self._set_manual_control_visual_state([self.red_gain_label, self.red_gain_range_label], not awb_enabled)
        self._set_manual_control_visual_state([self.blue_gain_label, self.blue_gain_range_label], not awb_enabled)

    def _set_manual_control_visual_state(self, labels, enabled):
        if enabled:
            is_dark = self._theme_manager.is_dark if self._theme_manager is not None else False
            main_color = "#f0f0f0" if is_dark else "#1a1a1a"
            range_color = "gray"
        else:
            main_color = "#777"
            range_color = "#777"
        if labels:
            labels[0].setStyleSheet(f"QLabel {{ color: {main_color}; font-weight: bold; }}")
        if len(labels) > 1:
            labels[1].setStyleSheet(f"QLabel {{ font-size: 10px; color: {range_color}; }}")

    def _clamp_value(self, value, min_val, max_val, default_val, value_type=float):
        """Clamp value to valid range."""
        try:
            converted = value_type(value)
            return max(min_val, min(max_val, converted))
        except (ValueError, TypeError):
            return default_val

    def _clamp_exp_time(self):
        raw = self.exp_time.lineEdit().text().replace(" μs", "").strip()
        try:
            value = int(raw)
        except (ValueError, TypeError):
            value = self.exp_time.value()
        clamped = self._clamp_value(value, EXPOSURE_TIME_RANGE[0], EXPOSURE_TIME_RANGE[1], DEFAULT_EXPOSURE_TIME, int)
        if value != clamped:
            self.exp_time.setValue(clamped)

    def _clamp_gain(self):
        raw = self.gain.lineEdit().text().strip()
        try:
            value = float(raw)
        except (ValueError, TypeError):
            value = self.gain.value()
        clamped = self._clamp_value(value, ANALOGUE_GAIN_RANGE[0], ANALOGUE_GAIN_RANGE[1], DEFAULT_ANALOGUE_GAIN, float)
        if value != clamped:
            self.gain.setValue(clamped)

    def _clamp_exp_value(self):
        raw = self.exp_value.lineEdit().text().strip()
        try:
            value = float(raw)
        except (ValueError, TypeError):
            value = self.exp_value.value()
        clamped = self._clamp_value(value, EXPOSURE_VALUE_RANGE[0], EXPOSURE_VALUE_RANGE[1], DEFAULT_EXPOSURE_VALUE, float)
        if value != clamped:
            self.exp_value.setValue(clamped)

    def _clamp_red_gain(self):
        raw = self.red_gain.lineEdit().text().strip()
        try:
            value = float(raw)
        except (ValueError, TypeError):
            value = self.red_gain.value()
        clamped = self._clamp_value(value, RED_GAIN_RANGE[0], RED_GAIN_RANGE[1], DEFAULT_RED_GAIN, float)
        if value != clamped:
            self.red_gain.setValue(clamped)

    def _clamp_blue_gain(self):
        raw = self.blue_gain.lineEdit().text().strip()
        try:
            value = float(raw)
        except (ValueError, TypeError):
            value = self.blue_gain.value()
        clamped = self._clamp_value(value, BLUE_GAIN_RANGE[0], BLUE_GAIN_RANGE[1], DEFAULT_BLUE_GAIN, float)
        if value != clamped:
            self.blue_gain.setValue(clamped)

    def _update_ui_from_settings(self, settings):
        """Update UI controls from settings dictionary."""
        try:
            self.settings_name.setText(settings.get('SettingsName', 'Basic'))

            photo_res = settings.get('PhotoResolution', DEFAULT_RESOLUTION_PHOTO)
            index = self.photo_resolution_combo.findText(photo_res)
            if index < 0:
                for i in range(self.photo_resolution_combo.count()):
                    if self.photo_resolution_combo.itemText(i).startswith(photo_res):
                        index = i
                        break
            if index >= 0:
                self.photo_resolution_combo.setCurrentIndex(index)

            video_res = settings.get('VideoResolution', DEFAULT_RESOLUTION_VIDEO)
            index = self.video_resolution_combo.findText(video_res)
            if index < 0:
                for i in range(self.video_resolution_combo.count()):
                    if self.video_resolution_combo.itemText(i).startswith(video_res):
                        index = i
                        break
            if index >= 0:
                self.video_resolution_combo.setCurrentIndex(index)

            self.chk_ae.setChecked(bool(settings.get('AeEnable', True)))
            self.chk_awb.setChecked(bool(settings.get('AwbEnable', True)))

            self.exp_time.setValue(self._clamp_value(
                settings.get('ExposureTime', DEFAULT_EXPOSURE_TIME),
                EXPOSURE_TIME_RANGE[0], EXPOSURE_TIME_RANGE[1], DEFAULT_EXPOSURE_TIME, int))
            self.gain.setValue(self._clamp_value(
                settings.get('AnalogueGain', DEFAULT_ANALOGUE_GAIN),
                ANALOGUE_GAIN_RANGE[0], ANALOGUE_GAIN_RANGE[1], DEFAULT_ANALOGUE_GAIN, float))
            self.exp_value.setValue(self._clamp_value(
                settings.get('ExposureValue', DEFAULT_EXPOSURE_VALUE),
                EXPOSURE_VALUE_RANGE[0], EXPOSURE_VALUE_RANGE[1], DEFAULT_EXPOSURE_VALUE, float))
            self.red_gain.setValue(self._clamp_value(
                settings.get('RedGain', DEFAULT_RED_GAIN),
                RED_GAIN_RANGE[0], RED_GAIN_RANGE[1], DEFAULT_RED_GAIN, float))
            self.blue_gain.setValue(self._clamp_value(
                settings.get('BlueGain', DEFAULT_BLUE_GAIN),
                BLUE_GAIN_RANGE[0], BLUE_GAIN_RANGE[1], DEFAULT_BLUE_GAIN, float))

            self._update_control_states()

        except Exception as e:
            logger.error(f"Error updating UI: {e}")
            self.status_label.setText(SettingsWidgetStrings.ERROR_UPDATING_UI.format(str(e)))
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def _cleanup_thread(self, thread: QThread) -> None:
        if thread in self.active_threads:
            self.active_threads.remove(thread)

    def closeEvent(self, event) -> None:
        for thread in self.active_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait(THREAD_TIMEOUT_MS)
        self.active_threads.clear()
        super().closeEvent(event)

    def apply_settings(self) -> None:
        """Apply current settings to the camera without saving to database."""
        self.status_label.setText(SettingsWidgetStrings.APPLYING_SETTINGS)
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        self._clamp_exp_time()
        self._clamp_gain()
        self._clamp_exp_value()
        self._clamp_red_gain()
        self._clamp_blue_gain()

        photo_res_text = self.photo_resolution_combo.currentText()
        photo_res = photo_res_text.split(' ')[0] if ' ' in photo_res_text else photo_res_text
        video_res_text = self.video_resolution_combo.currentText()
        video_res = video_res_text.split(' ')[0] if ' ' in video_res_text else video_res_text

        settings = {
            'SettingsName': str(self.settings_name.text()),
            'PhotoResolution': photo_res,
            'VideoResolution': video_res,
            'AeEnable': self.chk_ae.isChecked(),
            'AwbEnable': self.chk_awb.isChecked(),
            'ExposureTime': int(self.exp_time.value()),
            'AnalogueGain': float(self.gain.value()),
            'ExposureValue': float(self.exp_value.value()),
            'RedGain': float(self.red_gain.value()),
            'BlueGain': float(self.blue_gain.value()),
        }
        logger.info(f"Applying session settings to camera: {settings}")
        thread = APIClientThread('POST', ENDPOINTS["apply_camera"], settings)
        thread.response_received.connect(self._on_session_settings_applied)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        self.active_threads.append(thread)
        thread.start()

    def _on_session_settings_applied(self, success: bool, message: str, data: Dict[str, Any]) -> None:
        if success:
            self.status_label.setText(SettingsWidgetStrings.ALL_SETTINGS_APPLIED)
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
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
        """Load settings from a specific slot via API."""
        try:
            if slot_id == 0:
                api_url = ENDPOINTS["camera_settings_slot"].format(slot_id=slot_id)
                thread = APIClientThread('GET', api_url)
                thread.response_received.connect(lambda s, m, d:
                    self._on_slot_settings_loaded(s, m, d, slot_id))
                thread.finished.connect(lambda: self._cleanup_thread(thread))
                self.active_threads.append(thread)
                thread.start()
            else:
                self.status_label.setText(f"Loading slot {slot_id} to current session...")
                self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
                api_url = ENDPOINTS["load_camera_slot"].format(slot_id=slot_id)
                thread = APIClientThread('POST', api_url, {})
                thread.response_received.connect(lambda s, m, d:
                    self._on_slot_loaded_to_session(s, m, d, slot_id))
                thread.finished.connect(lambda: self._cleanup_thread(thread))
                self.active_threads.append(thread)
                thread.start()
        except Exception as e:
            self.status_label.setText(f"Error loading slot {slot_id}: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def _on_slot_settings_loaded(self, success, message, data, slot_id):
        try:
            if success and ('id' in data or (data.get('success') and 'data' in data)):
                settings = data if 'id' in data else data.get('data', {})
                self.current_slot_id = slot_id
                self.current_settings = settings
                self._update_ui_from_settings(settings)
                slot_name = settings.get('SettingsName', 'Current Session')
                self.status_label.setText(f"Loaded current session: {slot_name}")
                self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
                self.slot_changed.emit(slot_id)
            else:
                self.status_label.setText(f"API error loading session: {message}")
                self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
        except Exception as e:
            self.status_label.setText(f"Error processing session: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def _on_slot_loaded_to_session(self, success, message, data, source_slot_id):
        try:
            if success and data.get('success'):
                settings = data.get('data', {}).get('settings', {})
                self.current_slot_id = 0
                self.current_settings = settings
                self._update_ui_from_settings(settings)
                self.status_label.setText(
                    f"Loaded slot {source_slot_id} to current session, camera restarted")
                self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
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
        """Save current settings to a specific slot via API."""
        try:
            if slot_id == 0:
                self.status_label.setText("Slot 0 is current session - using Apply instead")
                self.apply_settings()
                return

            photo_res_text = self.photo_resolution_combo.currentText()
            photo_res = photo_res_text.split(' ')[0] if ' ' in photo_res_text else photo_res_text
            video_res_text = self.video_resolution_combo.currentText()
            video_res = video_res_text.split(' ')[0] if ' ' in video_res_text else video_res_text

            settings = {
                'SettingsName': str(self.settings_name.text() or f"Slot {slot_id}"),
                'PhotoResolution': photo_res,
                'VideoResolution': video_res,
                'AeEnable': self.chk_ae.isChecked(),
                'AwbEnable': self.chk_awb.isChecked(),
                'ExposureTime': int(self.exp_time.value()),
                'AnalogueGain': float(self.gain.value()),
                'ExposureValue': float(self.exp_value.value()),
                'RedGain': float(self.red_gain.value()),
                'BlueGain': float(self.blue_gain.value()),
            }
            thread = APIClientThread('POST', ENDPOINTS["save_camera_slot"].format(slot_id=slot_id), settings)
            thread.response_received.connect(lambda s, m, d:
                self._on_slot_saved(s, m, d, slot_id, settings))
            thread.finished.connect(lambda: self._cleanup_thread(thread))
            self.active_threads.append(thread)
            thread.start()
        except Exception as e:
            self.status_label.setText(f"Error saving to slot {slot_id}: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def _on_slot_saved(self, success, message, data, slot_id, settings):
        if success:
            self.current_slot_id = slot_id
            slot_name = data.get('data', {}).get('settings', {}).get('SettingsName', f"Slot {slot_id}")
            self.status_label.setText(f"Saved to slot {slot_id}: {slot_name} (camera not affected)")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            self.status_label.setText(f"Failed to save settings to slot {slot_id}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
