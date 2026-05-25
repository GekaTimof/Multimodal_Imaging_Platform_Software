from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from config.theme_manager import ThemeManager
from models.interface_text import Interface_text
from ui.widgets.device_settings_widget import DeviceSettingsWidget

class AcquisitionTab(QWidget):
    def __init__(self, interface_text: Interface_text, theme_manager: ThemeManager = None):
        super().__init__()
        
        # Main layout
        main_layout = QHBoxLayout(self)
        
        # Left side - Acquisition content (placeholder for now)
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel(interface_text.Acquisition()))
        left_layout.addStretch()
        
        # Right side - Device settings
        self.device_settings_widget = DeviceSettingsWidget(interface_text, theme_manager)
        
        # Add to main layout with 4:1 ratio
        main_layout.addLayout(left_layout, 4)
        main_layout.addWidget(self.device_settings_widget, 1)
