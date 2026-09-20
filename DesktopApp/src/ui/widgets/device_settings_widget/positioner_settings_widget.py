import logging

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QDoubleValidator
from PyQt5.QtWidgets import (
    QComboBox,
    QDoubleSpinBox,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QVBoxLayout,
    QWidget,
)

from config.api_config import ENDPOINTS
from core.constants.camera_constants import THREAD_TIMEOUT_MS
from ui.ui_utils import get_relative_margin

from .api_client_thread import APIClientThread

logger = logging.getLogger(__name__)


class PositionerSettingsWidget(QWidget):
    settings_updated = pyqtSignal()

    def __init__(self, interface_text=None):
        super().__init__()
        self.interface_text = interface_text
        self.active_threads = []
        self.position_inputs = {}
        self.step_buttons = []
        self._build_ui()
        self.load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        margin = get_relative_margin(0.9)
        layout.setContentsMargins(margin, margin, margin, margin)
        layout.setSpacing(margin)

        self.connection_label = QLabel("Positioner: checking connection...")
        self.connection_label.setStyleSheet("QLabel { font-weight: bold; }")
        layout.addWidget(self.connection_label)

        grid = QGridLayout()
        grid.addWidget(QLabel("Axis"), 0, 0)
        grid.addWidget(QLabel("Target position (mm)"), 0, 1)
        grid.addWidget(QLabel("Step"), 0, 2, 1, 2)
        for row, axis in enumerate(("X", "Y", "Z"), 1):
            grid.addWidget(QLabel(axis), row, 0)
            position = QDoubleSpinBox()
            position.setDecimals(3)
            position.setRange(0.0, 0.0)
            position.setSingleStep(0.1)
            self.position_inputs[axis] = position
            grid.addWidget(position, row, 1)
            minus = QPushButton(f"{axis} −")
            plus = QPushButton(f"{axis} +")
            minus.clicked.connect(lambda _, a=axis: self.step_axis(a, -1))
            plus.clicked.connect(lambda _, a=axis: self.step_axis(a, 1))
            self.step_buttons.extend((minus, plus))
            grid.addWidget(minus, row, 2)
            grid.addWidget(plus, row, 3)
        layout.addLayout(grid)

        step_layout = QHBoxLayout()
        step_layout.addWidget(QLabel("Step size (mm):"))
        self.step_size = QComboBox()
        self.step_size.setEditable(True)
        self.step_size.addItems(["0.01", "0.1", "1", "10"])
        self.step_size.setCurrentText("0.1")
        self.step_size.lineEdit().setValidator(QDoubleValidator(0.01, 100.0, 3, self.step_size))
        step_layout.addWidget(self.step_size)
        layout.addLayout(step_layout)

        buttons = QHBoxLayout()
        self.btn_refresh = QPushButton("Refresh")
        self.btn_connect = QPushButton("Connect")
        self.btn_calibrate = QPushButton("Calibrate")
        self.btn_move = QPushButton("Move To")
        buttons.addWidget(self.btn_refresh)
        buttons.addWidget(self.btn_connect)
        buttons.addWidget(self.btn_calibrate)
        buttons.addWidget(self.btn_move)
        layout.addLayout(buttons)

        self.status_label = QLabel("Ready")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        layout.addStretch()

        self.btn_refresh.clicked.connect(self.load_settings)
        self.btn_connect.clicked.connect(self.connect_positioner)
        self.btn_calibrate.clicked.connect(self.calibrate)
        self.btn_move.clicked.connect(self.move_to_position)

    def load_settings(self):
        self._request("GET", ENDPOINTS["positioner_status"], None, self._on_status)

    def connect_positioner(self):
        self._set_busy("Connecting to positioner...")
        self._request("POST", ENDPOINTS["positioner_connect"], {}, self._on_action, 15)

    def calibrate(self):
        self._set_busy("Calibrating X, Y and Z...")
        self._request("POST", ENDPOINTS["positioner_calibrate"], {}, self._on_action, 3600)

    def move_to_position(self):
        payload = {axis.lower(): control.value() for axis, control in self.position_inputs.items()}
        self._set_busy("Moving to target position...")
        self._request("POST", ENDPOINTS["positioner_move"], payload, self._on_action, 180)

    def step_axis(self, axis, direction):
        try:
            distance = float(self.step_size.currentText())
        except ValueError:
            self._show_error("Step must be between 0.01 and 100 mm")
            return
        if not 0.01 <= distance <= 100.0:
            self._show_error("Step must be between 0.01 and 100 mm")
            return
        self._set_busy(f"Moving {axis} by {direction * distance:g} mm...")
        payload = {"axis": axis, "distance": direction * distance}
        self._request("POST", ENDPOINTS["positioner_step"], payload, self._on_action, 180)

    def _request(self, method, url, payload, callback, timeout=None):
        thread = APIClientThread(method, url, payload, timeout)
        thread.response_received.connect(callback)
        thread.finished.connect(lambda: self._cleanup_thread(thread))
        self.active_threads.append(thread)
        thread.start()

    def _on_action(self, success, message, response):
        self._set_controls_enabled(True)
        if success:
            self._apply_status(response.get("data", {}))
            self.status_label.setText(response.get("message", message))
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            self.settings_updated.emit()
        else:
            self._show_error(message)

    def _on_status(self, success, message, response):
        if success:
            self._apply_status(response.get("data", {}))
            self.status_label.setText("Positioner status loaded")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        else:
            self._show_error(message)
            self.connection_label.setText("Positioner: unavailable")

    def _apply_status(self, status):
        connected = status.get("connected", False)
        calibrated = status.get("calibrated", False)
        busy = status.get("busy", False)
        state = "busy" if busy else "connected" if connected else "disconnected"
        calibration = "calibrated" if calibrated else "not calibrated"
        self.connection_label.setText(f"Positioner: {state}, {calibration}")
        positions = status.get("position", {})
        limits = status.get("limits", {})
        for axis, control in self.position_inputs.items():
            travel = limits.get(axis, {}).get("travel")
            position = positions.get(axis)
            control.setRange(0.0, float(travel) if travel is not None else 0.0)
            if position is not None:
                control.setValue(float(position))
        self.btn_move.setEnabled(connected and calibrated and not busy)
        self.btn_calibrate.setEnabled(connected and not busy)
        for button in self.step_buttons:
            button.setEnabled(connected and calibrated and not busy)

    def _set_busy(self, text):
        self.status_label.setText(text)
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        self._set_controls_enabled(False)

    def _set_controls_enabled(self, enabled):
        self.btn_refresh.setEnabled(enabled)
        self.btn_connect.setEnabled(enabled)
        self.btn_calibrate.setEnabled(enabled)
        self.btn_move.setEnabled(enabled)
        for button in self.step_buttons:
            button.setEnabled(enabled)

    def _show_error(self, message):
        self.status_label.setText(message)
        self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def _cleanup_thread(self, thread):
        if thread in self.active_threads:
            self.active_threads.remove(thread)

    def closeEvent(self, event):
        for thread in self.active_threads:
            if thread.isRunning():
                thread.requestInterruption()
                thread.wait(THREAD_TIMEOUT_MS)
        self.active_threads.clear()
        super().closeEvent(event)
