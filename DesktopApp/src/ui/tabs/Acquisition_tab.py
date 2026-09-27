"""
Acquisition Tab
Layout mirrors CameraTab / SpectrometerTab:
  - Left:  acquisition display area (placeholder)
  - Right (upper): controls — start/stop, capture, status
  - Right (lower): device settings panel (PositionerSettingsWidget inside DeviceSettingsWidget)
"""

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QSizePolicy, QPushButton, QProgressBar,
)
from config import interface_config
from config.theme_manager import ThemeManager
from models.interface_text import Interface_text
from ui.ui_utils import get_relative_margin
from ui.widgets.device_settings_widget import DeviceSettingsWidget


class AcquisitionTab(QWidget):
    """Acquisition tab with the same column structure as CameraTab."""

    def __init__(self, interface_text: Interface_text, theme_manager: ThemeManager = None):
        super().__init__()
        self.interface_text = interface_text

        # ---- Left side: acquisition display area ----
        self.acquisition_display = QLabel(interface_text.Acquisition())
        self.acquisition_display.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.acquisition_display.setAlignment(Qt.AlignCenter)
        self.acquisition_display.setStyleSheet("QLabel { background-color: black; color: white; }")
        self.acquisition_display.setMinimumSize(0, 0)
        self.acquisition_display.setScaledContents(False)

        # ---- Right upper: acquisition controls (like camera) ----
        upper_control_layout = QVBoxLayout()
        upper_control_layout.setContentsMargins(
            get_relative_margin(0.4), get_relative_margin(0.4),
            get_relative_margin(2.5), get_relative_margin(0.4)
        )  # Use relative margins to prevent scrollbar overlap

        # Control buttons (similar to camera)
        self.start_button = QPushButton(interface_text.start_camera())
        self.stop_button = QPushButton(interface_text.stop_camera())
        self.capture_button = QPushButton(interface_text.save_image())

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        self.status_label.setMinimumWidth(200)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)

        upper_control_layout.addWidget(self.start_button)
        upper_control_layout.addWidget(self.stop_button)
        upper_control_layout.addWidget(self.capture_button)
        upper_control_layout.addWidget(self.progress_bar)
        upper_control_layout.addWidget(self.status_label)
        upper_control_layout.addStretch()

        upper_scroll = QScrollArea()
        upper_scroll.setWidgetResizable(True)
        upper_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        upper_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        upper_widget = QWidget()
        upper_widget.setLayout(upper_control_layout)
        upper_scroll.setWidget(upper_widget)

        # ---- Right lower: device settings ----
        self.device_settings_widget = DeviceSettingsWidget(self.interface_text, theme_manager)

        # Switch dropdown to Positioner by default
        if hasattr(interface_text, 'positioner'):
            idx = self.device_settings_widget.settings_type_combo.findText(interface_text.positioner())
        else:
            idx = self.device_settings_widget.settings_type_combo.findText("Positioner")
        if idx >= 0:
            self.device_settings_widget.settings_type_combo.setCurrentIndex(idx)

        lower_scroll = QScrollArea()
        lower_scroll.setWidgetResizable(True)
        lower_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lower_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        lower_scroll.setWidget(self.device_settings_widget)

        # ---- Right panel layout (split into upper and lower parts with 2:3 ratio) ----
        right_panel_layout = QVBoxLayout()
        right_panel_layout.setContentsMargins(
            get_relative_margin(0.6), get_relative_margin(0.6),
            get_relative_margin(0.6), get_relative_margin(0.6)
        )  # Use relative margins to prevent cutoff
        right_panel_layout.addWidget(upper_scroll, 2)
        right_panel_layout.addWidget(lower_scroll, 3)

        # Right panel wrapper widget with fixed minimum width (same as camera)
        right_panel_widget = QWidget()
        right_panel_widget.setLayout(right_panel_layout)
        right_panel_widget.setMinimumWidth(interface_config.get('ui_scaling.side_panel_min_width', 320))
        right_panel_widget.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # ---- Main horizontal layout ----
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.acquisition_display, 1)
        main_layout.addWidget(right_panel_widget)

    # ------------------------------------------------------------------
    # Resize — same constraint as CameraTab / SpectrometerTab
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        """Limit acquisition display to 4/5 width and 95% height of the tab."""
        super().resizeEvent(event)
        w = self.width()
        h = self.height()
        max_w = int(w * 4 / 5)
        max_h = int(h * 0.95)
        self.acquisition_display.setMaximumSize(max_w, max_h)

    # ------------------------------------------------------------------
    # Language
    # ------------------------------------------------------------------

    def update_language(self, interface_text: Interface_text):
        """Update all UI text when language changes."""
        self.interface_text = interface_text
        self.acquisition_display.setText(interface_text.Acquisition())
        self.start_button.setText(interface_text.start_camera())
        self.stop_button.setText(interface_text.stop_camera())
        self.capture_button.setText(interface_text.save_image())
