"""
Positioner Settings Widget
Widget for configuring positioner device parameters for Acquisition analysis mode.

This widget provides controls for:
- Connection management (connect / disconnect)
- Position coordinates (X, Y, Z)
- Movement speed & acceleration
- Go Home / Move To / Emergency Stop
- Axis calibration (per-axis and all-at-once)
- Live status display from the GRBL controller
"""

import logging

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton,
    QGridLayout,
)
from PyQt5.QtCore import pyqtSignal

from config.api_config import ENDPOINTS
from core.constants.camera_constants import THREAD_TIMEOUT_MS
from ui.ui_utils import get_relative_margin
from .api_client_thread import APIClientThread

logger = logging.getLogger(__name__)

# Positioner moves / calibration can take several minutes
_POSITIONER_TIMEOUT = 600.0


def _t(interface_text, method_name: str, fallback: str) -> str:
    """Safely get localised text with a fallback."""
    if interface_text is None:
        return fallback
    fn = getattr(interface_text, method_name, None)
    return fn() if fn else fallback


class PositionerSettingsWidget(QWidget):
    """Widget for positioner settings configuration."""

    # Signal emitted when settings are updated
    settings_updated = pyqtSignal()

    def __init__(self, interface_text=None):
        super().__init__()
        self.interface_text = interface_text
        self.current_settings = {}
        self._active_threads: list = []
        self._build_ui()
        # Load saved settings on startup (does not require connection)
        self.load_settings()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            get_relative_margin(0.9), get_relative_margin(0.9),
            get_relative_margin(0.9), get_relative_margin(0.9),
        )
        layout.setSpacing(get_relative_margin(0.9))

        # ---- Connection row ----
        conn_row = QHBoxLayout()
        self.btn_connect = QPushButton(_t(self.interface_text, 'connect_positioner', 'Connect'))
        self.btn_stop = QPushButton(_t(self.interface_text, 'stop_positioner', 'Stop'))
        self.btn_stop.setStyleSheet("QPushButton { color: red; font-weight: bold; }")
        self.btn_status = QPushButton(_t(self.interface_text, 'positioner_status', 'Status'))
        conn_row.addWidget(self.btn_connect)
        conn_row.addWidget(self.btn_stop)
        conn_row.addWidget(self.btn_status)
        conn_row.addStretch()
        layout.addLayout(conn_row)

        # ---- Position / speed fields ----
        settings_layout = QGridLayout()
        settings_layout.setContentsMargins(
            get_relative_margin(0.5), get_relative_margin(0.5),
            get_relative_margin(0.5), get_relative_margin(0.5),
        )
        settings_layout.setHorizontalSpacing(get_relative_margin(0.9))
        settings_layout.setVerticalSpacing(get_relative_margin(0.7))

        row = 0

        # X Position
        x_label = QLabel(_t(self.interface_text, 'x_position', 'X Position (mm):'))
        x_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(x_label, row, 0, 1, 2)
        row += 1
        self.x_position = QDoubleSpinBox()
        self.x_position.setRange(-5000.0, 15000.0)
        self.x_position.setValue(0.0)
        self.x_position.setDecimals(2)
        settings_layout.addWidget(self.x_position, row, 0, 1, 2)
        row += 1

        # Y Position
        y_label = QLabel(_t(self.interface_text, 'y_position', 'Y Position (mm):'))
        y_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(y_label, row, 0, 1, 2)
        row += 1
        self.y_position = QDoubleSpinBox()
        self.y_position.setRange(-5000.0, 15000.0)
        self.y_position.setValue(0.0)
        self.y_position.setDecimals(2)
        settings_layout.addWidget(self.y_position, row, 0, 1, 2)
        row += 1

        # Z Position
        z_label = QLabel(_t(self.interface_text, 'z_position', 'Z Position (mm):'))
        z_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(z_label, row, 0, 1, 2)
        row += 1
        self.z_position = QDoubleSpinBox()
        self.z_position.setRange(-5000.0, 15000.0)
        self.z_position.setValue(0.0)
        self.z_position.setDecimals(2)
        settings_layout.addWidget(self.z_position, row, 0, 1, 2)
        row += 1

        # Movement Speed
        speed_label = QLabel(_t(self.interface_text, 'speed', 'Speed (mm/s):'))
        speed_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(speed_label, row, 0, 1, 2)
        row += 1
        self.movement_speed = QDoubleSpinBox()
        self.movement_speed.setRange(0.1, 100.0)
        self.movement_speed.setValue(10.0)
        self.movement_speed.setDecimals(1)
        settings_layout.addWidget(self.movement_speed, row, 0, 1, 2)
        row += 1

        # Acceleration
        accel_label = QLabel(_t(self.interface_text, 'acceleration', 'Acceleration (mm/s²):'))
        accel_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(accel_label, row, 0, 1, 2)
        row += 1
        self.acceleration = QDoubleSpinBox()
        self.acceleration.setRange(0.1, 1000.0)
        self.acceleration.setValue(100.0)
        self.acceleration.setDecimals(1)
        settings_layout.addWidget(self.acceleration, row, 0, 1, 2)
        row += 1

        layout.addLayout(settings_layout)

        # ---- Motion buttons ----
        motion_row = QHBoxLayout()
        self.btn_refresh = QPushButton(_t(self.interface_text, 'refresh', 'Refresh'))
        self.btn_home = QPushButton(_t(self.interface_text, 'go_home', 'Go Home'))
        self.btn_move_to = QPushButton(_t(self.interface_text, 'move_to', 'Move To'))
        self.btn_apply = QPushButton(_t(self.interface_text, 'apply', 'Apply'))
        motion_row.addWidget(self.btn_refresh)
        motion_row.addWidget(self.btn_home)
        motion_row.addWidget(self.btn_move_to)
        motion_row.addWidget(self.btn_apply)
        motion_row.addStretch()
        layout.addLayout(motion_row)

        # ---- Calibration buttons ----
        cal_row = QHBoxLayout()
        self.btn_cal_x = QPushButton(_t(self.interface_text, 'calibrate_axis', 'Cal {axis}').format(axis='X'))
        self.btn_cal_y = QPushButton(_t(self.interface_text, 'calibrate_axis', 'Cal {axis}').format(axis='Y'))
        self.btn_cal_z = QPushButton(_t(self.interface_text, 'calibrate_axis', 'Cal {axis}').format(axis='Z'))
        self.btn_cal_all = QPushButton(_t(self.interface_text, 'calibrate_all', 'Calibrate All'))
        cal_row.addWidget(self.btn_cal_x)
        cal_row.addWidget(self.btn_cal_y)
        cal_row.addWidget(self.btn_cal_z)
        cal_row.addWidget(self.btn_cal_all)
        cal_row.addStretch()
        layout.addLayout(cal_row)

        # ---- Status label ----
        self.status_label = QLabel(_t(self.interface_text, 'ready', 'Ready'))
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # ---- Wire signals ----
        self.btn_connect.clicked.connect(self.connect_positioner)
        self.btn_stop.clicked.connect(self.stop_positioner)
        self.btn_status.clicked.connect(self.refresh_status)
        self.btn_refresh.clicked.connect(self.load_settings)
        self.btn_home.clicked.connect(self.go_home)
        self.btn_move_to.clicked.connect(self.move_to_position)
        self.btn_apply.clicked.connect(self.apply_settings)
        self.btn_cal_x.clicked.connect(lambda: self.calibrate_axis('x'))
        self.btn_cal_y.clicked.connect(lambda: self.calibrate_axis('y'))
        self.btn_cal_z.clicked.connect(lambda: self.calibrate_axis('z'))
        self.btn_cal_all.clicked.connect(self.calibrate_all)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _request(self, method: str, url: str, data, callback, timeout: float | None = None):
        thread = APIClientThread(method, url, data, timeout=timeout)
        thread.response_received.connect(callback)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        self._active_threads.append(thread)
        thread.start()

    def _set_status(self, text: str, colour: str = "green"):
        self.status_label.setText(text)
        self.status_label.setStyleSheet(f"QLabel {{ color: {colour}; font-weight: bold; }}")

    def _set_buttons_enabled(self, enabled: bool):
        """Disable motion / calibration buttons while a long operation runs."""
        for btn in (self.btn_home, self.btn_move_to, self.btn_apply,
                    self.btn_cal_x, self.btn_cal_y, self.btn_cal_z, self.btn_cal_all):
            btn.setEnabled(enabled)

    def _update_position_from_response(self, data: dict):
        """Update X/Y/Z spin boxes from API response data."""
        position = data.get('work_position') or data.get('position', {})
        if position:
            self.x_position.setValue(float(position.get('x', self.x_position.value())))
            self.y_position.setValue(float(position.get('y', self.y_position.value())))
            self.z_position.setValue(float(position.get('z', self.z_position.value())))

    # ------------------------------------------------------------------
    # Connection
    # ------------------------------------------------------------------

    def connect_positioner(self):
        self._set_status(_t(self.interface_text, 'positioner_connecting', 'Connecting positioner...'), 'blue')
        self._request('POST', ENDPOINTS['positioner_connect'], {}, self._on_connected)

    def _on_connected(self, success: bool, message: str, response: dict):
        if not success:
            self._set_status(_t(self.interface_text, 'positioner_connection_failed', 'Connection failed') + f': {message}', 'red')
            return
        data = response.get('data', {})
        self._update_position_from_response(data)
        self._set_status(_t(self.interface_text, 'positioner_connected', 'Positioner connected'))

    # ------------------------------------------------------------------
    # Emergency stop
    # ------------------------------------------------------------------

    def stop_positioner(self):
        self._request('POST', ENDPOINTS['positioner_stop'], {}, self._on_stopped)

    def _on_stopped(self, success: bool, message: str, response: dict):
        if not success:
            self._set_status(f"Stop: {message}", 'red')
            return
        self._set_status(_t(self.interface_text, 'positioner_stopped', 'Positioner stopped'), 'orange')

    # ------------------------------------------------------------------
    # Status
    # ------------------------------------------------------------------

    def refresh_status(self):
        self._set_status(_t(self.interface_text, 'loading_positioner_settings', 'Loading...'), 'blue')
        self._request('GET', ENDPOINTS['positioner_status'], None, self._on_status)

    def _on_status(self, success: bool, message: str, response: dict):
        if not success:
            self._set_status(message, 'red')
            return
        data = response.get('data', {})
        self._update_position_from_response(data)
        state = data.get('state', '?')
        connected = data.get('connected', False)
        calibration = data.get('calibration', {})
        cal_text = ', '.join(f"{a.upper()}" for a in calibration) if calibration else \
            _t(self.interface_text, 'positioner_not_calibrated', 'Not calibrated')
        colour = 'green' if connected else 'red'
        self._set_status(f"State: {state} | Cal: {cal_text}", colour)

    # ------------------------------------------------------------------
    # Settings load / apply
    # ------------------------------------------------------------------

    def load_settings(self):
        self._set_status(_t(self.interface_text, 'loading_positioner_settings', 'Loading positioner settings...'), 'blue')
        self._request('GET', ENDPOINTS['positioner_settings'], None, self._settings_loaded)

    def _settings_loaded(self, success: bool, message: str, response: dict):
        if not success:
            self._set_status(message, 'red')
            return
        self.current_settings = response
        self._update_ui_from_settings(response)
        self._set_status(_t(self.interface_text, 'positioner_settings_loaded', 'Positioner settings loaded'))

    def _update_ui_from_settings(self, settings: dict):
        try:
            self.x_position.setValue(float(settings.get('XPosition', 0.0)))
            self.y_position.setValue(float(settings.get('YPosition', 0.0)))
            self.z_position.setValue(float(settings.get('ZPosition', 0.0)))
            self.movement_speed.setValue(float(settings.get('MovementSpeed', 10.0)))
            self.acceleration.setValue(float(settings.get('Acceleration', 100.0)))
        except Exception as e:
            self._set_status(f"Error updating UI: {e}", 'red')

    def apply_settings(self):
        self._set_status(_t(self.interface_text, 'applying_positioner_settings', 'Applying positioner settings...'), 'blue')
        settings = {
            'SettingsName': self.current_settings.get('SettingsName', 'Basic'),
            'XPosition': self.x_position.value(),
            'YPosition': self.y_position.value(),
            'ZPosition': self.z_position.value(),
            'MovementSpeed': self.movement_speed.value(),
            'Acceleration': self.acceleration.value(),
        }
        self._request('POST', ENDPOINTS['positioner_settings'], settings, self._settings_applied)

    def _settings_applied(self, success: bool, message: str, response: dict):
        if not success:
            self._set_status(message, 'red')
            return
        self.current_settings = response.get('data', self.current_settings)
        self._set_status(_t(self.interface_text, 'positioner_settings_applied', 'Positioner settings applied'))
        self.settings_updated.emit()

    # ------------------------------------------------------------------
    # Motion: home / move
    # ------------------------------------------------------------------

    def go_home(self):
        self._set_status(_t(self.interface_text, 'moving_to_home', 'Moving to home position...'), 'blue')
        self._set_buttons_enabled(False)
        self._request('POST', ENDPOINTS['positioner_home'], {}, self._motion_completed, timeout=_POSITIONER_TIMEOUT)

    def move_to_position(self):
        self._set_status(_t(self.interface_text, 'moving_to_position', 'Moving to position...'), 'blue')
        self._set_buttons_enabled(False)
        self._request('POST', ENDPOINTS['positioner_move'], {
            'x': self.x_position.value(),
            'y': self.y_position.value(),
            'z': self.z_position.value(),
            'speed': self.movement_speed.value(),
        }, self._motion_completed, timeout=_POSITIONER_TIMEOUT)

    def _motion_completed(self, success: bool, message: str, response: dict):
        self._set_buttons_enabled(True)
        if not success:
            self._set_status(message, 'red')
            return
        data = response.get('data', {})
        self._update_position_from_response(data)
        self._set_status(response.get('message', 'Movement completed'))

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def calibrate_axis(self, axis: str):
        self._set_status(
            _t(self.interface_text, 'calibrating_positioner', 'Calibrating {axis}...').format(axis=axis.upper()),
            'blue',
        )
        self._set_buttons_enabled(False)
        url = ENDPOINTS['positioner_calibrate_axis'].format(axis=axis)
        self._request('POST', url, {}, self._on_calibration_done, timeout=_POSITIONER_TIMEOUT)

    def calibrate_all(self):
        self._set_status(_t(self.interface_text, 'calibrating_all', 'Calibrating all axes...'), 'blue')
        self._set_buttons_enabled(False)
        self._request('POST', ENDPOINTS['positioner_calibrate'], {}, self._on_calibration_done, timeout=_POSITIONER_TIMEOUT)

    def _on_calibration_done(self, success: bool, message: str, response: dict):
        self._set_buttons_enabled(True)
        if not success:
            self._set_status(message, 'red')
            return
        self._set_status(_t(self.interface_text, 'calibration_complete', 'Calibration complete'))

    # ------------------------------------------------------------------
    # Cleanup
    # ------------------------------------------------------------------

    def _cleanup_thread(self, thread):
        if thread in self._active_threads:
            self._active_threads.remove(thread)

    def closeEvent(self, event):
        for thread in self._active_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait(THREAD_TIMEOUT_MS)
        self._active_threads.clear()
        super().closeEvent(event)
