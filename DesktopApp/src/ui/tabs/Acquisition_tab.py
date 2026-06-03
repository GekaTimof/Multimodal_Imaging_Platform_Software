from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QSizePolicy,
)
from config import interface_config
from config.theme_manager import ThemeManager
from models.interface_text import Interface_text
from ui.widgets.device_settings_widget import DeviceSettingsWidget


class AcquisitionTab(QWidget):
    def __init__(self, interface_text: Interface_text, theme_manager: ThemeManager = None):
        super().__init__()
        self.interface_text = interface_text

        # ---- Left side: placeholder content ----
        self._title_label = QLabel(interface_text.Acquisition())
        self._title_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self._title_label.setAlignment(Qt.AlignCenter)

        # ---- Right upper: tools panel (placeholder) ----
        upper_tools_layout = QVBoxLayout()
        upper_tools_layout.setSpacing(6)
        upper_tools_layout.setContentsMargins(4, 4, 25, 4)  # Add large right margin to prevent scrollbar overlap
        upper_tools_layout.addWidget(QLabel(interface_text.Acquisition()))
        upper_tools_layout.addStretch()

        upper_scroll = QScrollArea()
        upper_scroll.setWidgetResizable(True)
        upper_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        upper_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        upper_widget = QWidget()
        upper_widget.setLayout(upper_tools_layout)
        upper_scroll.setWidget(upper_widget)

        # ---- Right lower: device settings ----
        self.device_settings_widget = DeviceSettingsWidget(interface_text, theme_manager)

        lower_scroll = QScrollArea()
        lower_scroll.setWidgetResizable(True)
        lower_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lower_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        lower_scroll.setWidget(self.device_settings_widget)

        # ---- Right panel (upper + lower, 2:3 ratio) ----
        right_layout = QVBoxLayout()
        right_layout.setContentsMargins(6, 6, 6, 6)  # Add margins to prevent cutoff
        right_layout.addWidget(upper_scroll, 2)
        right_layout.addWidget(lower_scroll, 3)

        right_panel = QWidget()
        right_panel.setLayout(right_layout)
        right_panel.setMinimumWidth(interface_config.get('ui_scaling.side_panel_min_width', 320) + 40)  # Add 40px for DeviceSettingsWidget internal margins
        right_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # ---- Main horizontal layout ----
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self._title_label, 1)
        main_layout.addWidget(right_panel)

    def update_language(self, interface_text: Interface_text):
        """Update all UI text when language changes."""
        self.interface_text = interface_text
        self._title_label.setText(interface_text.Acquisition())
