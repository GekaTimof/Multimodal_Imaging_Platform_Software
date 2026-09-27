"""
Positioner Settings Widget
Widget for controlling the GRBL positioner in Acquisition mode.

Layout (top to bottom):
1. Current XYZ coordinates (3 rows) — each with left/right arrow buttons + slider
2. Speed selection: 3 presets (slow/medium/fast) + custom field with warning >4500
3. Save / Load position (name + XYZ + speed persisted via API)
4. Calibrate button
5. Emergency stop button
6. Status label (minimum height to prevent squishing)
"""

import logging

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton,
    QSlider, QSizePolicy, QLineEdit,
)
from PyQt5.QtCore import pyqtSignal, Qt

from config.api_config import ENDPOINTS
from core.constants.camera_constants import THREAD_TIMEOUT_MS
from ui.ui_utils import get_relative_margin
from .api_client_thread import APIClientThread

logger = logging.getLogger(__name__)

_POSITIONER_TIMEOUT = 600.0
_AXIS_MIN = -5000.0
_AXIS_MAX = 15000.0
_SLIDER_SCALE = 100  # slider uses int, we multiply by this for 0.01 precision
_SPEED_WARNING_THRESHOLD = 4500
_SPEED_PRESETS = {"slow": 500, "medium": 2000, "fast": 5000}


def _t(interface_text, method_name: str, fallback: str) -> str:
    if interface_text is None:
        return fallback
    fn = getattr(interface_text, method_name, None)
    return fn() if fn else fallback


class PositionerSettingsWidget(QWidget):
    """Compact positioner control panel for the Acquisition tab."""

    settings_updated = pyqtSignal()

    def __init__(self, interface_text=None):
        super().__init__()
        self.interface_text = interface_text
        self.current_settings = {}
        self._active_threads: list = []
        self._build_ui()
        self.refresh_status()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        m = get_relative_margin(0.5)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(m)

        # ---- 1. XYZ axis rows ----
        self._axis_widgets = {}
        for axis in ("X", "Y", "Z"):
            row_widget = self._build_axis_row(axis)
            layout.addWidget(row_widget)

        # ---- 2. Speed selection ----
        layout.addWidget(self._build_speed_section())

        # ---- 3. Save / Load position ----
        layout.addWidget(self._build_save_load_section())

        # ---- 4. Calibrate button ----
        self.btn_calibrate = QPushButton(_t(self.interface_text, 'calibrate', 'Calibrate'))
        self.btn_calibrate.clicked.connect(self.calibrate_all)
        layout.addWidget(self.btn_calibrate)

        # ---- 5. Emergency stop ----
        self.btn_estop = QPushButton(_t(self.interface_text, 'emergency_stop', 'EMERGENCY STOP'))
        self.btn_estop.setMinimumHeight(get_relative_margin(3))
        self.btn_estop.setStyleSheet(
            "QPushButton { background-color: #d32f2f; color: white; font-weight: bold; font-size: 14pt; border-radius: 6px; }"
            "QPushButton:hover { background-color: #b71c1c; }"
            "QPushButton:pressed { background-color: #ff1744; }"
        )
        self.btn_estop.clicked.connect(self.stop_positioner)
        layout.addWidget(self.btn_estop)

        # ---- 6. Status label ----
        self.status_label = QLabel(_t(self.interface_text, 'ready', 'Ready'))
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumHeight(get_relative_margin(3))
        self.status_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Minimum)
        layout.addWidget(self.status_label)

        layout.addStretch()

    # ---- Axis row builder ----

    def _build_axis_row(self, axis: str) -> QWidget:
        """Build a single axis control: label + value, [<] slider [>]."""
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)

        # Top: axis label + current value spinbox
        top = QHBoxLayout()
        label = QLabel(f"{axis}:")
        label.setStyleSheet("QLabel { font-weight: bold; }")
        label.setFixedWidth(get_relative_margin(2))
        top.addWidget(label)

        spinbox = QDoubleSpinBox()
        spinbox.setRange(_AXIS_MIN, _AXIS_MAX)
        spinbox.setValue(0.0)
        spinbox.setDecimals(2)
        spinbox.setSuffix(" mm")
        spinbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        spinbox.valueChanged.connect(lambda val, a=axis: self._on_spinbox_changed(a, val))
        top.addWidget(spinbox)

        btn_move = QPushButton(_t(self.interface_text, 'move_to', 'Move To'))
        btn_move.clicked.connect(lambda _, a=axis: self._move_single_axis(a))
        top.addWidget(btn_move)
        vbox.addLayout(top)

        # Bottom: [<] slider [>]
        bottom = QHBoxLayout()
        btn_left = QPushButton("\u25C0")  # left arrow
        btn_left.setFixedWidth(get_relative_margin(2.5))
        btn_left.clicked.connect(lambda _, a=axis: self._nudge_axis(a, -1))
        bottom.addWidget(btn_left)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(int(_AXIS_MIN * _SLIDER_SCALE), int(_AXIS_MAX * _SLIDER_SCALE))
        slider.setValue(0)
        slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        slider.valueChanged.connect(lambda val, a=axis: self._on_slider_changed(a, val))
        slider.sliderReleased.connect(lambda a=axis: self._on_slider_released(a))
        bottom.addWidget(slider)

        btn_right = QPushButton("\u25B6")  # right arrow
        btn_right.setFixedWidth(get_relative_margin(2.5))
        btn_right.clicked.connect(lambda _, a=axis: self._nudge_axis(a, +1))
        bottom.addWidget(btn_right)
        vbox.addLayout(bottom)

        self._axis_widgets[axis] = {
            "spinbox": spinbox,
            "slider": slider,
            "btn_left": btn_left,
            "btn_right": btn_right,
            "btn_move": btn_move,
        }
        return container

    # ---- Speed section builder ----

    def _build_speed_section(self) -> QWidget:
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)

        speed_label = QLabel(_t(self.interface_text, 'speed', 'Speed (mm/s):'))
        speed_label.setStyleSheet("QLabel { font-weight: bold; }")
        vbox.addWidget(speed_label)

        # Preset buttons row
        preset_row = QHBoxLayout()
        self.btn_slow = QPushButton(_t(self.interface_text, 'speed_slow', 'Slow'))
        self.btn_medium = QPushButton(_t(self.interface_text, 'speed_medium', 'Medium'))
        self.btn_fast = QPushButton(_t(self.interface_text, 'speed_fast', 'Fast'))
        self.btn_slow.clicked.connect(lambda: self._set_speed(_SPEED_PRESETS["slow"]))
        self.btn_medium.clicked.connect(lambda: self._set_speed(_SPEED_PRESETS["medium"]))
        self.btn_fast.clicked.connect(lambda: self._set_speed(_SPEED_PRESETS["fast"]))
        preset_row.addWidget(self.btn_slow)
        preset_row.addWidget(self.btn_medium)
        preset_row.addWidget(self.btn_fast)
        preset_row.addStretch()
        vbox.addLayout(preset_row)

        # Custom speed spinbox
        self.speed_spinbox = QDoubleSpinBox()
        self.speed_spinbox.setRange(1, 10000)
        self.speed_spinbox.setValue(_SPEED_PRESETS["medium"])
        self.speed_spinbox.setDecimals(0)
        self.speed_spinbox.setSuffix(" mm/s")
        self.speed_spinbox.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.speed_spinbox.valueChanged.connect(self._on_speed_changed)
        vbox.addWidget(self.speed_spinbox)

        # Warning label (hidden by default)
        self.speed_warning_label = QLabel(
            _t(self.interface_text, 'speed_warning',
               'Speed above 4500: motor may skip steps, accuracy will be lost')
        )
        self.speed_warning_label.setStyleSheet("QLabel { color: #b8860b; font-weight: bold; }")
        self.speed_warning_label.setWordWrap(True)
        self.speed_warning_label.setVisible(False)
        vbox.addWidget(self.speed_warning_label)

        return container

    # ---- Save / Load section builder ----

    def _build_save_load_section(self) -> QWidget:
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)

        save_label = QLabel(_t(self.interface_text, 'position_presets', 'Position Presets'))
        save_label.setStyleSheet("QLabel { font-weight: bold; }")
        vbox.addWidget(save_label)

        # Settings name field
        name_row = QHBoxLayout()
        name_label = QLabel(_t(self.interface_text, 'settings_name', 'Settings Name:'))
        name_row.addWidget(name_label)
        self.settings_name_edit = QLineEdit()
        self.settings_name_edit.setPlaceholderText("Basic")
        self.settings_name_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        name_row.addWidget(self.settings_name_edit)
        vbox.addLayout(name_row)

        # Save / Load buttons
        btn_row = QHBoxLayout()
        self.btn_save = QPushButton(_t(self.interface_text, 'save', 'Save'))
        self.btn_load = QPushButton(_t(self.interface_text, 'load', 'Load'))
        self.btn_save.setToolTip("Save current XYZ + speed to Raspberry Pi database")
        self.btn_load.setToolTip("Load saved XYZ + speed from Raspberry Pi database")
        self.btn_save.clicked.connect(self.save_position)
        self.btn_load.clicked.connect(self.load_position)
        btn_row.addWidget(self.btn_save)
        btn_row.addWidget(self.btn_load)
        btn_row.addStretch()
        vbox.addLayout(btn_row)

        return container

    # ------------------------------------------------------------------
    # Axis interaction
    # ------------------------------------------------------------------

    def _on_spinbox_changed(self, axis: str, value: float):
        """Sync slider when spinbox changes."""
        w = self._axis_widgets[axis]
        w["slider"].blockSignals(True)
        w["slider"].setValue(int(value * _SLIDER_SCALE))
        w["slider"].blockSignals(False)

    def _on_slider_changed(self, axis: str, int_value: int):
        """Sync spinbox when slider is being dragged (live preview)."""
        w = self._axis_widgets[axis]
        value = int_value / _SLIDER_SCALE
        w["spinbox"].blockSignals(True)
        w["spinbox"].setValue(value)
        w["spinbox"].blockSignals(False)

    def _on_slider_released(self, axis: str):
        """When user releases slider, move the axis to the new position."""
        # Position is already synced via _on_slider_changed
        pass

    def _nudge_axis(self, axis: str, direction: int):
        """Move axis by a small step (1mm * direction), then send move command."""
        w = self._axis_widgets[axis]
        current = w["spinbox"].value()
        new_val = max(_AXIS_MIN, min(_AXIS_MAX, current + direction * 1.0))
        w["spinbox"].setValue(new_val)
        self._move_single_axis(axis)

    def _move_single_axis(self, axis: str):
        """Send move command for the current XYZ values."""
        self._set_status(
            _t(self.interface_text, 'moving_to_position', 'Moving to position...'), 'blue'
        )
        self._set_motion_enabled(False)
        payload = {
            'x': self._axis_widgets["X"]["spinbox"].value(),
            'y': self._axis_widgets["Y"]["spinbox"].value(),
            'z': self._axis_widgets["Z"]["spinbox"].value(),
            'speed': self.speed_spinbox.value(),
        }
        self._request('POST', ENDPOINTS['positioner_move'], payload,
                       self._motion_completed, timeout=_POSITIONER_TIMEOUT)

    # ------------------------------------------------------------------
    # Speed
    # ------------------------------------------------------------------

    def _set_speed(self, value: float):
        self.speed_spinbox.setValue(value)

    def _on_speed_changed(self, value: float):
        if value > _SPEED_WARNING_THRESHOLD:
            self.speed_warning_label.setVisible(True)
            self.speed_spinbox.setStyleSheet(
                "QDoubleSpinBox { background-color: #fff3cd; border: 2px solid #b8860b; }"
            )
        else:
            self.speed_warning_label.setVisible(False)
            self.speed_spinbox.setStyleSheet("")

    # ------------------------------------------------------------------
    # API helpers
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

    def _set_motion_enabled(self, enabled: bool):
        for axis_w in self._axis_widgets.values():
            axis_w["btn_left"].setEnabled(enabled)
            axis_w["btn_right"].setEnabled(enabled)
            axis_w["btn_move"].setEnabled(enabled)
            axis_w["slider"].setEnabled(enabled)
        self.btn_calibrate.setEnabled(enabled)

    def _update_position_from_response(self, data: dict):
        position = data.get('work_position') or data.get('position', {})
        if position:
            for axis_key, axis_name in [('x', 'X'), ('y', 'Y'), ('z', 'Z')]:
                val = float(position.get(axis_key, 0.0))
                w = self._axis_widgets[axis_name]
                w["spinbox"].blockSignals(True)
                w["spinbox"].setValue(val)
                w["spinbox"].blockSignals(False)
                w["slider"].blockSignals(True)
                w["slider"].setValue(int(val * _SLIDER_SCALE))
                w["slider"].blockSignals(False)

    # ------------------------------------------------------------------
    # Status / refresh
    # ------------------------------------------------------------------

    def refresh_status(self):
        self._set_status(
            _t(self.interface_text, 'loading_positioner_settings', 'Loading...'), 'blue'
        )
        self._request('GET', ENDPOINTS['positioner_status'], None, self._on_status)

    def _on_status(self, success: bool, message: str, response: dict):
        if not success:
            self._set_status(message, 'red')
            return
        data = response.get('data', {})
        self._update_position_from_response(data)
        connected = data.get('connected', False)
        state = data.get('state', '?')
        colour = 'green' if connected else 'red'
        self._set_status(f"State: {state}", colour)

    # ------------------------------------------------------------------
    # Emergency stop
    # ------------------------------------------------------------------

    def stop_positioner(self):
        self._request('POST', ENDPOINTS['positioner_stop'], {}, self._on_stopped)

    def _on_stopped(self, success: bool, message: str, response: dict):
        self._set_motion_enabled(True)
        if not success:
            self._set_status(f"Stop: {message}", 'red')
            return
        self._set_status(
            _t(self.interface_text, 'positioner_stopped', 'Positioner stopped'), 'orange'
        )

    # ------------------------------------------------------------------
    # Motion
    # ------------------------------------------------------------------

    def _motion_completed(self, success: bool, message: str, response: dict):
        self._set_motion_enabled(True)
        if not success:
            self._set_status(message, 'red')
            return
        data = response.get('data', {})
        self._update_position_from_response(data)
        self._set_status(response.get('message', 'Movement completed'))

    # ------------------------------------------------------------------
    # Calibration
    # ------------------------------------------------------------------

    def calibrate_all(self):
        self._set_status(
            _t(self.interface_text, 'calibrating_all', 'Calibrating all axes...'), 'blue'
        )
        self._set_motion_enabled(False)
        self._request('POST', ENDPOINTS['positioner_calibrate'], {},
                       self._on_calibration_done, timeout=_POSITIONER_TIMEOUT)

    def _on_calibration_done(self, success: bool, message: str, response: dict):
        self._set_motion_enabled(True)
        if not success:
            self._set_status(message, 'red')
            return
        self._set_status(
            _t(self.interface_text, 'calibration_complete', 'Calibration complete')
        )

    # ------------------------------------------------------------------
    # Save / Load position
    # ------------------------------------------------------------------

    def save_position(self):
        name = self.settings_name_edit.text().strip() or "Basic"
        settings = {
            'SettingsName': name,
            'XPosition': self._axis_widgets["X"]["spinbox"].value(),
            'YPosition': self._axis_widgets["Y"]["spinbox"].value(),
            'ZPosition': self._axis_widgets["Z"]["spinbox"].value(),
            'MovementSpeed': self.speed_spinbox.value(),
            'Acceleration': 100.0,
        }
        self._set_status(
            _t(self.interface_text, 'applying_positioner_settings', 'Saving position...'), 'blue'
        )
        self._request('POST', ENDPOINTS['positioner_settings'], settings, self._on_position_saved)

    def _on_position_saved(self, success: bool, message: str, response: dict):
        if not success:
            self._set_status(f"Save failed: {message}", 'red')
            return
        name = self.settings_name_edit.text().strip() or "Basic"
        self._set_status(
            _t(self.interface_text, 'position_saved', 'Position saved as preset: {preset_name}').format(preset_name=name)
        )

    def load_position(self):
        self._set_status(
            _t(self.interface_text, 'loading_positioner_settings', 'Loading saved position...'), 'blue'
        )
        self._request('GET', ENDPOINTS['positioner_settings'], None, self._on_position_loaded)

    def _on_position_loaded(self, success: bool, message: str, response: dict):
        if not success:
            self._set_status(f"Load failed: {message}", 'red')
            return
        self.settings_name_edit.setText(response.get('SettingsName', 'Basic'))
        speed = float(response.get('MovementSpeed', 2000))
        for axis_name in ('X', 'Y', 'Z'):
            val = float(response.get(f'{axis_name}Position', 0.0))
            w = self._axis_widgets[axis_name]
            w["spinbox"].blockSignals(True)
            w["spinbox"].setValue(val)
            w["spinbox"].blockSignals(False)
            w["slider"].blockSignals(True)
            w["slider"].setValue(int(val * _SLIDER_SCALE))
            w["slider"].blockSignals(False)
        self.speed_spinbox.setValue(speed)
        name = response.get('SettingsName', 'Basic')
        self._set_status(
            _t(self.interface_text, 'positioner_settings_loaded', 'Positioner settings loaded') + f": {name}"
        )

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
