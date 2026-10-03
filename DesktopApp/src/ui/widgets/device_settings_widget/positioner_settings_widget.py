"""
Positioner Settings Widget
Widget for controlling the GRBL positioner in Acquisition mode.

Layout (top to bottom):
1. Speed selection: 3 presets (slow/medium/fast) + custom field with warning >4500
2. Current XYZ coordinates (3 rows) — each with step buttons + slider
3. Save / Load position (name + XYZ + speed persisted via API)
4. Calibrate button
5. Emergency stop button
6. Status label (minimum height to prevent squishing)
"""

import logging

from PyQt5.QtCore import QEvent, QTimer, Qt, pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (
    QApplication,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QPushButton,
    QSizePolicy,
    QSlider,
    QVBoxLayout,
    QWidget,
)

from config.api_config import ENDPOINTS
from core.constants.camera_constants import THREAD_TIMEOUT_MS, MAX_POSITIONER_SLOTS
from ui.ui_utils import get_relative_margin
from .api_client_thread import APIClientThread
from .positioner_slot_dialog import PositionerSlotDialog

logger = logging.getLogger(__name__)

_POSITIONER_TIMEOUT = 600.0  # Up to 5+ minutes for calibration and long moves
_STATUS_TIMEOUT = 15.0  # Status request should return quickly
_AXIS_MIN_DEFAULT = -5000.0
_AXIS_MAX_DEFAULT = 15000.0
_SLIDER_SCALE = 100  # slider uses int, we multiply by this for 0.01 precision
_SPEED_WARNING_THRESHOLD = 4500
_SPEED_PRESETS = {"slow": 100, "medium": 2000, "fast": 4000}
# Work coordinate minimum is always 0 after calibration.
_AXIS_MIN = 0.0


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
        self._busy_timer: QTimer | None = None
        self._axis_values: dict = {}
        self._axis_ranges: dict = {}
        self._build_ui()
        QApplication.instance().installEventFilter(self)

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        m = get_relative_margin(0.5)
        layout = QVBoxLayout(self)
        layout.setContentsMargins(m, m, m, m)
        layout.setSpacing(m)

        # ---- 1. Speed selection ----
        layout.addWidget(self._build_speed_section())

        # ---- 2. XYZ axis rows ----
        self._axis_widgets = {}
        for axis in ("X", "Y", "Z"):
            row_widget = self._build_axis_row(axis)
            layout.addWidget(row_widget)

        self.btn_move = QPushButton(_t(self.interface_text, 'move_to', 'Move To'))
        self.btn_move.clicked.connect(self._move_to_position)
        layout.addWidget(self.btn_move)

        # ---- Get current position button ----
        self.btn_get_position = QPushButton(
            _t(self.interface_text, 'current_position', 'Current position')
        )
        self.btn_get_position.clicked.connect(self.refresh_status)
        layout.addWidget(self.btn_get_position)

        # ---- 3. Save / Load position ----
        layout.addWidget(self._build_save_load_section())

        # ---- 4. Calibrate button ----
        # TODO: Add an explicit Connect/Disconnect button for the positioner.
        # Currently refresh_status and move implicitly trigger a serial connect,
        # which can block the UI for several seconds. The API already exposes
        # /positioner/connect and /positioner/disconnect endpoints.
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

    def _shortcut_context_active(self, watched) -> bool:
        return (
            isinstance(watched, QWidget)
            and watched.window() is self.window()
            and self.isVisible()
            and self.isEnabled()
        )

    def eventFilter(self, watched, event):
        if event.type() != QEvent.KeyPress or event.isAutoRepeat():
            return super().eventFilter(watched, event)
        if not self._shortcut_context_active(watched):
            return super().eventFilter(watched, event)

        key = event.key()
        modifiers = event.modifiers()
        if modifiers & (Qt.AltModifier | Qt.MetaModifier):
            return super().eventFilter(watched, event)
        if modifiers & Qt.ShiftModifier:
            return super().eventFilter(watched, event)

        control_pressed = bool(modifiers & Qt.ControlModifier)
        if key == Qt.Key_S and control_pressed:
            self.stop_positioner()
            return True
        if not self.btn_move.isEnabled():
            return super().eventFilter(watched, event)
        if key == Qt.Key_M and control_pressed:
            self._move_to_position()
            return True

        bindings = {
            Qt.Key_Left: ("X", -1.0),
            Qt.Key_Right: ("X", 1.0),
            Qt.Key_Down: ("Y", -1.0),
            Qt.Key_Up: ("Y", 1.0),
            Qt.Key_Minus: ("Z", 1.0),
            Qt.Key_Equal: ("Z", -1.0),
        }
        binding = bindings.get(key)
        if binding is None:
            return super().eventFilter(watched, event)

        axis, direction = binding
        self._nudge_axis(axis, direction * (10.0 if control_pressed else 1.0))
        return True

    # ---- Axis row builder ----

    def _build_axis_row(self, axis: str) -> QWidget:
        """Build a single axis control: label + value, [-10][-1] slider [+1][+10]."""
        container = QWidget()
        vbox = QVBoxLayout(container)
        vbox.setContentsMargins(0, 0, 0, 0)
        vbox.setSpacing(2)

        # Top: axis label + current value field
        top = QHBoxLayout()
        label = QLabel(f"{axis}:")
        label.setStyleSheet("QLabel { font-weight: bold; }")
        label.setFixedWidth(get_relative_margin(2))
        top.addWidget(label)

        line_edit = QLineEdit("0.00")
        line_edit.setValidator(QDoubleValidator(_AXIS_MIN, _AXIS_MAX_DEFAULT, 2, line_edit))
        line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        line_edit.editingFinished.connect(lambda a=axis: self._clamp_line_edit(a))
        line_edit.returnPressed.connect(lambda a=axis: self._on_line_edit_return(a))
        top.addWidget(line_edit)

        # Store current value/range for this axis
        self._axis_values[axis] = 0.0
        self._axis_ranges[axis] = (_AXIS_MIN, _AXIS_MAX_DEFAULT)
        vbox.addLayout(top)

        # Bottom: [<<][<] slider [>][>>]
        bottom = QHBoxLayout()
        btn_minus_10 = QPushButton("\u00AB")  # << (fast -10)
        btn_minus_10.setMinimumWidth(get_relative_margin(3))
        btn_minus_10.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        btn_minus_10.setToolTip("-10 mm (fast)")
        btn_minus_10.clicked.connect(lambda _, a=axis: self._nudge_axis(a, -10.0))
        bottom.addWidget(btn_minus_10)

        btn_minus_1 = QPushButton("\u25C4")  # < (slow -1)
        btn_minus_1.setMinimumWidth(get_relative_margin(3))
        btn_minus_1.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        btn_minus_1.setToolTip("-1 mm (slow)")
        btn_minus_1.clicked.connect(lambda _, a=axis: self._nudge_axis(a, -1.0))
        bottom.addWidget(btn_minus_1)

        slider = QSlider(Qt.Horizontal)
        slider.setRange(int(_AXIS_MIN * _SLIDER_SCALE), int(_AXIS_MAX_DEFAULT * _SLIDER_SCALE))
        slider.setValue(0)
        slider.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        slider.valueChanged.connect(lambda val, a=axis: self._on_slider_changed(a, val))
        bottom.addWidget(slider)

        btn_plus_1 = QPushButton("\u25BA")  # > (slow +1)
        btn_plus_1.setMinimumWidth(get_relative_margin(3))
        btn_plus_1.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        btn_plus_1.setToolTip("+1 mm (slow)")
        btn_plus_1.clicked.connect(lambda _, a=axis: self._nudge_axis(a, +1.0))
        bottom.addWidget(btn_plus_1)

        btn_plus_10 = QPushButton("\u00BB")  # >> (fast +10)
        btn_plus_10.setMinimumWidth(get_relative_margin(3))
        btn_plus_10.setSizePolicy(QSizePolicy.Minimum, QSizePolicy.Fixed)
        btn_plus_10.setToolTip("+10 mm (fast)")
        btn_plus_10.clicked.connect(lambda _, a=axis: self._nudge_axis(a, +10.0))
        bottom.addWidget(btn_plus_10)
        vbox.addLayout(bottom)

        self._axis_widgets[axis] = {
            "line_edit": line_edit,
            "slider": slider,
            "btn_minus_10": btn_minus_10,
            "btn_minus_1": btn_minus_1,
            "btn_plus_1": btn_plus_1,
            "btn_plus_10": btn_plus_10,
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
        preset_row.addWidget(self.btn_slow, 1)
        preset_row.addWidget(self.btn_medium, 1)
        preset_row.addWidget(self.btn_fast, 1)
        vbox.addLayout(preset_row)

        # Custom speed field, clamped to the supported range after editing
        self.speed_line_edit = QLineEdit(str(int(_SPEED_PRESETS["medium"])))
        self.speed_line_edit.setValidator(QDoubleValidator(1.0, 10000.0, 2, self.speed_line_edit))
        self.speed_line_edit.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.speed_line_edit.editingFinished.connect(self._clamp_speed_line_edit)
        self.speed_line_edit.returnPressed.connect(self._on_speed_line_edit_return)
        vbox.addWidget(self.speed_line_edit)
        self._speed_value = float(_SPEED_PRESETS["medium"])

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
        self.btn_save.setToolTip("Save current XYZ + speed to a position slot")
        self.btn_load.setToolTip("Load XYZ + speed from a position slot")
        self.btn_save.clicked.connect(self._open_save_slot_dialog)
        self.btn_load.clicked.connect(self._open_load_slot_dialog)
        btn_row.addWidget(self.btn_save, 1)
        btn_row.addWidget(self.btn_load, 1)
        vbox.addLayout(btn_row)

        return container

    # ------------------------------------------------------------------
    # Axis interaction
    # ------------------------------------------------------------------

    def _on_slider_changed(self, axis: str, int_value: int):
        """Sync line edit when slider is being dragged (live preview)."""
        value = int_value / _SLIDER_SCALE
        self._axis_values[axis] = value
        w = self._axis_widgets[axis]
        w["line_edit"].blockSignals(True)
        w["line_edit"].setText(f"{value:.2f}")
        w["line_edit"].blockSignals(False)

    def _parse_line_edit(self, axis: str) -> float:
        """Parse axis line edit text, clamp to current range and update UI."""
        w = self._axis_widgets[axis]
        text = w["line_edit"].text().strip().replace(',', '.')
        try:
            value = float(text)
        except ValueError:
            value = self._axis_values.get(axis, 0.0)
        axis_min, axis_max = self._axis_ranges.get(axis, (_AXIS_MIN, _AXIS_MAX_DEFAULT))
        value = max(axis_min, min(axis_max, value))
        return value

    def _set_axis_value(self, axis: str, value: float, sync_slider: bool = True):
        """Store, display and optionally sync slider for an axis value."""
        axis_min, axis_max = self._axis_ranges.get(axis, (_AXIS_MIN, _AXIS_MAX_DEFAULT))
        value = max(axis_min, min(axis_max, value))
        self._axis_values[axis] = value
        w = self._axis_widgets[axis]
        w["line_edit"].blockSignals(True)
        w["line_edit"].setText(f"{value:.2f}")
        w["line_edit"].blockSignals(False)
        if sync_slider:
            w["slider"].blockSignals(True)
            w["slider"].setValue(int(value * _SLIDER_SCALE))
            w["slider"].blockSignals(False)

    def _clamp_line_edit(self, axis: str):
        """Clamp line edit value to its current range and sync slider."""
        value = self._parse_line_edit(axis)
        self._set_axis_value(axis, value)

    def _on_line_edit_return(self, axis: str):
        """Clamp the entered axis value without starting a move."""
        self._clamp_line_edit(axis)

    def _get_axis_value(self, axis: str) -> float:
        """Get current clamped axis value from stored state."""
        return self._axis_values.get(axis, 0.0)

    def _nudge_axis(self, axis: str, step: float):
        """Move axis by the given step (mm), clamp to range, then send move command."""
        current = self._get_axis_value(axis)
        axis_min, axis_max = self._axis_ranges.get(axis, (_AXIS_MIN, _AXIS_MAX_DEFAULT))
        new_val = max(axis_min, min(axis_max, current + step))
        self._set_axis_value(axis, new_val)
        self._move_to_position()

    def _move_to_position(self):
        """Send move command for the current XYZ values."""
        self._set_status(
            _t(self.interface_text, 'moving_to_position', 'Moving to position...'), 'blue'
        )
        self._set_motion_enabled(False)
        payload = {
            'x': self._get_axis_value('X'),
            'y': self._get_axis_value('Y'),
            'z': self._get_axis_value('Z'),
            'speed': self._get_speed_value(),
        }
        self._request('POST', ENDPOINTS['positioner_move'], payload,
                       self._motion_completed, timeout=_POSITIONER_TIMEOUT)

    # ------------------------------------------------------------------
    # Speed
    # ------------------------------------------------------------------

    def _get_speed_value(self) -> float:
        """Return current clamped speed value."""
        return self._speed_value

    def _set_speed(self, value: float):
        value = max(1.0, min(10000.0, float(value)))
        self._speed_value = value
        self.speed_line_edit.setText(f"{value:g}")
        self._update_speed_warning(value)

    def _update_speed_warning(self, value: float):
        if value > _SPEED_WARNING_THRESHOLD:
            self.speed_warning_label.setVisible(True)
            self.speed_line_edit.setStyleSheet(
                "QLineEdit { background-color: #fff3cd; border: 2px solid #b8860b; }"
            )
        else:
            self.speed_warning_label.setVisible(False)
            self.speed_line_edit.setStyleSheet("")

    def _clamp_speed_line_edit(self):
        """Parse speed line edit, clamp to 1..10000 and update warning."""
        text = self.speed_line_edit.text().strip().replace(',', '.')
        try:
            value = float(text)
        except ValueError:
            value = self._speed_value
        value = max(1.0, min(10000.0, value))
        self._set_speed(value)

    def _on_speed_line_edit_return(self):
        """On Enter in speed line edit: clamp and keep focus."""
        self._clamp_speed_line_edit()

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
            axis_w["btn_minus_10"].setEnabled(enabled)
            axis_w["btn_minus_1"].setEnabled(enabled)
            axis_w["btn_plus_1"].setEnabled(enabled)
            axis_w["btn_plus_10"].setEnabled(enabled)
            axis_w["slider"].setEnabled(enabled)
            axis_w["line_edit"].setEnabled(enabled)
        self.btn_move.setEnabled(enabled)
        self.btn_calibrate.setEnabled(enabled)
        self.btn_save.setEnabled(enabled)
        self.btn_load.setEnabled(enabled)
        self.btn_get_position.setEnabled(enabled)
        self.speed_line_edit.setEnabled(enabled)
        self.settings_name_edit.setEnabled(enabled)

    def _update_axis_limits_from_calibration(self, data: dict):
        """Update axis ranges from calibration data returned by status API.

        After calibration, work coordinates go from 0 to travel (mm) per axis.
        If calibration data is absent, ranges stay at defaults.
        """
        calibration = data.get('calibration', {})
        if not calibration:
            return
        for axis_key, axis_name in [('x', 'X'), ('y', 'Y'), ('z', 'Z')]:
            cal = calibration.get(axis_key)
            if not cal:
                continue
            travel = float(cal.get('travel', 0.0))
            if travel <= 0:
                continue
            self._axis_ranges[axis_name] = (0.0, travel)
            w = self._axis_widgets[axis_name]
            w["line_edit"].validator().setRange(0.0, travel, 2)
            w["slider"].blockSignals(True)
            w["slider"].setRange(0, int(travel * _SLIDER_SCALE))
            w["slider"].blockSignals(False)
            # Re-clamp current value to new range
            self._set_axis_value(axis_name, self._axis_values.get(axis_name, 0.0))

    def _update_position_from_response(self, data: dict):
        self._update_axis_limits_from_calibration(data)
        position = data.get('work_position') or data.get('position', {})
        if position:
            for axis_key, axis_name in [('x', 'X'), ('y', 'Y'), ('z', 'Z')]:
                val = float(position.get(axis_key, 0.0))
                self._set_axis_value(axis_name, val)

    # ------------------------------------------------------------------
    # Status / refresh
    # ------------------------------------------------------------------

    def refresh_status(self):
        self._set_status(
            _t(self.interface_text, 'loading_positioner_settings', 'Loading...'), 'blue'
        )
        self._request('GET', ENDPOINTS['positioner_busy'], None, self._on_busy_checked,
                      timeout=_STATUS_TIMEOUT)

    def _on_busy_checked(self, success: bool, message: str, response: dict):
        """After checking busy state: block UI if calibrating, then fetch position."""
        busy = False
        if success and response.get('success'):
            busy = response.get('data', {}).get('busy', False)
        if busy:
            self._set_motion_enabled(False)
            self._set_status(
                _t(self.interface_text, 'positioner_calibrating', 'Positioner is calibrating...'), 'orange'
            )
            self._start_busy_polling()
            return
        self._stop_busy_polling()
        self._request('GET', ENDPOINTS['positioner_status'], None, self._on_status,
                      timeout=_STATUS_TIMEOUT)

    def _start_busy_polling(self):
        """Poll /positioner/busy every second until calibration finishes."""
        if self._busy_timer is None:
            self._busy_timer = QTimer(self)
            self._busy_timer.timeout.connect(self._poll_busy)
        if not self._busy_timer.isActive():
            self._busy_timer.start(1000)

    def _stop_busy_polling(self):
        if self._busy_timer is not None and self._busy_timer.isActive():
            self._busy_timer.stop()

    def _poll_busy(self):
        self._request('GET', ENDPOINTS['positioner_busy'], None, self._on_busy_poll_result,
                      timeout=_STATUS_TIMEOUT)

    def _on_busy_poll_result(self, success: bool, message: str, response: dict):
        busy = False
        if success and response.get('success'):
            busy = response.get('data', {}).get('busy', False)
        if not busy:
            self._stop_busy_polling()
            self._set_motion_enabled(True)
            self.refresh_status()

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
        # Refresh coordinates after emergency stop to show actual halted position.
        self.refresh_status()

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
        self.refresh_status()

    # ------------------------------------------------------------------
    # Save / Load position slots
    # ------------------------------------------------------------------

    def _open_save_slot_dialog(self):
        """Open dialog for selecting slot to save current position into."""
        dialog = PositionerSlotDialog(self, exclude_slot_0=True)
        dialog.setWindowTitle(_t(self.interface_text, 'save_to_slot', 'Save Position to Slot'))
        dialog.slot_selected.connect(self.save_position_to_slot)
        dialog.exec_()

    def save_position_to_slot(self, slot_id: int):
        """Save current XYZ + speed to the selected position slot via API."""
        if slot_id < 1 or slot_id >= MAX_POSITIONER_SLOTS:
            self._set_status(f"Invalid slot {slot_id}", 'red')
            return
        name = self.settings_name_edit.text().strip() or f"Slot {slot_id}"
        # TODO: Acceleration is hard-coded to 100.0. Add an acceleration
        # spinbox or fetch the current value from /positioner/settings so the
        # saved preset actually reflects the user's configuration.
        settings = {
            'SettingsName': name,
            'XPosition': self._get_axis_value('X'),
            'YPosition': self._get_axis_value('Y'),
            'ZPosition': self._get_axis_value('Z'),
            'MovementSpeed': self._get_speed_value(),
            'Acceleration': 100.0,
        }
        self._set_status(
            _t(self.interface_text, 'applying_positioner_settings', 'Saving position...'), 'blue'
        )
        url = ENDPOINTS['positioner_settings_slot'].format(slot_id=slot_id)
        self._request('POST', url, settings, self._on_position_saved)

    def _on_position_saved(self, success: bool, message: str, response: dict):
        if not success:
            self._set_status(f"Save failed: {message}", 'red')
            return
        self._set_status(
            _t(self.interface_text, 'position_saved', 'Position saved to slot')
        )

    def _open_load_slot_dialog(self):
        """Open dialog for selecting slot to load position from."""
        dialog = PositionerSlotDialog(self, exclude_slot_0=True)
        dialog.setWindowTitle(_t(self.interface_text, 'load_from_slot', 'Load Position from Slot'))
        dialog.slot_selected.connect(self.load_position_from_slot)
        dialog.exec_()

    def load_position_from_slot(self, slot_id: int):
        """Load position from saved slot (1-10) into the UI."""
        if slot_id < 1 or slot_id >= MAX_POSITIONER_SLOTS:
            self._set_status(f"Invalid slot {slot_id}", 'red')
            return
        self._set_status(
            _t(self.interface_text, 'loading_positioner_settings', 'Loading saved position...'), 'blue'
        )
        url = ENDPOINTS['positioner_settings_slot'].format(slot_id=slot_id)
        self._request('GET', url, None, self._on_position_loaded)

    def _on_position_loaded(self, success: bool, message: str, response: dict):
        if not success:
            self._set_status(f"Load failed: {message}", 'red')
            return
        self.settings_name_edit.setText(response.get('SettingsName', 'Basic'))
        speed = float(response.get('MovementSpeed', 2000))
        self._set_speed(speed)
        for axis_name in ('X', 'Y', 'Z'):
            val = float(response.get(f'{axis_name}Position', 0.0))
            self._set_axis_value(axis_name, val)
        name = response.get('SettingsName', 'Basic')
        self._set_status(
            _t(self.interface_text, 'positioner_settings_loaded', 'Positioner position loaded') + f": {name}"
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
