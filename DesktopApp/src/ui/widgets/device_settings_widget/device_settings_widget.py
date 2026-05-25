"""
Device Settings Widget
Main widget with a dropdown selector that switches between Camera, Spectrometer,
Positioner and File Settings panels using a QStackedWidget.
"""

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtGui import QFont
from PyQt5.QtWidgets import QComboBox, QStackedWidget, QVBoxLayout, QWidget

from .camera_settings_widget import CameraSettingsWidget
from .spectrometer_settings_widget import SpectrometerSettingsWidget
from .positioner_settings_widget import PositionerSettingsWidget
from .file_settings_widget import FileSettingsWidget


class DeviceSettingsWidget(QWidget):
    """Main device settings widget with dropdown selector."""

    settings_updated = pyqtSignal()

    def __init__(self, interface_text=None, parent=None):
        super().__init__(parent)
        self.interface_text = interface_text
        self._build_ui()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(10, 10, 10, 10)
        layout.setSpacing(10)

        # Dropdown for settings type
        self.settings_type_combo = QComboBox()
        if self.interface_text:
            self.settings_type_combo.addItems([
                self.interface_text.camera(),
                self.interface_text.spectrometer(),
                self.interface_text.positioner(),
                self.interface_text.file_settings(),
            ])
        else:
            self.settings_type_combo.addItems(["Camera", "Spectrometer", "Positioner", "File Settings"])
        self.settings_type_combo.currentTextChanged.connect(self._on_settings_type_changed)
        self.settings_type_combo.setMaximumWidth(200)
        layout.addWidget(self.settings_type_combo)

        # Stacked widget
        self.stacked_widget = QStackedWidget()
        self.camera_tab = CameraSettingsWidget(self.interface_text)
        self.spectrometer_tab = SpectrometerSettingsWidget(self.interface_text)
        self.positioner_tab = PositionerSettingsWidget(self.interface_text)
        self.file_tab = FileSettingsWidget(self.interface_text)

        self.stacked_widget.addWidget(self.camera_tab)
        self.stacked_widget.addWidget(self.spectrometer_tab)
        self.stacked_widget.addWidget(self.positioner_tab)
        self.stacked_widget.addWidget(self.file_tab)
        layout.addWidget(self.stacked_widget)

        font = QFont()
        font.setPointSize(10)
        self.setFont(font)

        self.camera_tab.settings_updated.connect(self.settings_updated.emit)

    def _on_settings_type_changed(self, text):
        """Switch stacked widget page based on dropdown selection."""
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
            self.camera_tab.load_settings()
        elif text == spectrometer_text:
            self.stacked_widget.setCurrentWidget(self.spectrometer_tab)
        elif text == positioner_text:
            self.stacked_widget.setCurrentWidget(self.positioner_tab)
            self.positioner_tab.load_settings()
        elif text == file_settings_text:
            self.stacked_widget.setCurrentWidget(self.file_tab)

    def switch_to_settings(self, settings_type: str):
        """Switch to a specific settings panel by its localized name."""
        index = self.settings_type_combo.findText(settings_type)
        if index >= 0:
            if self.settings_type_combo.currentIndex() != index:
                self.settings_type_combo.setCurrentIndex(index)
            else:
                camera_text = self.interface_text.camera() if self.interface_text else "Camera"
                if settings_type == camera_text:
                    self.camera_tab.load_settings()
