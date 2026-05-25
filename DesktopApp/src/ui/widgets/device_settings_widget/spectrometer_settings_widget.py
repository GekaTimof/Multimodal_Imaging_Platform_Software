"""
Spectrometer Settings Widget
Widget for configuring spectrometer parameters (integral time, dark spectrum).
"""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import QLabel, QPushButton, QSpinBox, QVBoxLayout, QWidget


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

        # Connection status
        self.connection_label = QLabel(
            self.interface_text.status_disconnected() if self.interface_text else "Status: Disconnected"
        )
        self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        self.connection_label.setWordWrap(True)
        layout.addWidget(self.connection_label)

        # Integral time
        it_label = QLabel(
            self.interface_text.integral_time() if self.interface_text else "Integral Time (ms):"
        )
        it_label.setStyleSheet("QLabel { font-weight: bold; }")
        it_label.setWordWrap(True)
        layout.addWidget(it_label)

        self.integral_time_input = QSpinBox()
        self.integral_time_input.setRange(1, 10000)
        self.integral_time_input.setValue(100)
        self.integral_time_input.setButtonSymbols(QSpinBox.NoButtons)
        self.integral_time_input.valueChanged.connect(self.integral_time_changed.emit)
        layout.addWidget(self.integral_time_input)

        # Dark spectrum buttons
        self.set_dark_button = QPushButton(
            self.interface_text.set_dark_spectrum() if self.interface_text else "Set Dark Spectrum"
        )
        self.set_dark_button.clicked.connect(self.set_dark_requested.emit)
        layout.addWidget(self.set_dark_button)

        self.clear_dark_button = QPushButton(
            self.interface_text.clear_dark_spectrum() if self.interface_text else "Clear Dark Spectrum"
        )
        self.clear_dark_button.clicked.connect(self.clear_dark_requested.emit)
        layout.addWidget(self.clear_dark_button)

        layout.addStretch()

    def set_connection_status(self, connected: bool):
        """Update connection status label."""
        if connected:
            status_text = self.interface_text.status_connected() if self.interface_text else "Status: Connected"
            self.connection_label.setText(status_text)
            self.connection_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            status_text = self.interface_text.status_disconnected() if self.interface_text else "Status: Disconnected"
            self.connection_label.setText(status_text)
            self.connection_label.setStyleSheet("color: red; font-weight: bold;")
