from PyQt5.QtWidgets import QWidget, QHBoxLayout
from models.objects.Interface_text import Interface_text
from ui.widgets.device_settings_widget.device_settings_widgets import DeviceSettingsWidget
from ui.widgets.spectrometer_widget import SpectrometerWidget


class SpectrometerTab(QWidget):
    def __init__(self, interface_text: Interface_text):
        super().__init__()
        
        # Main layout
        main_layout = QHBoxLayout(self)
        
        # Left side - Spectrometer widget (comprehensive interface)
        self.spectrometer_widget = SpectrometerWidget(interface_text)
        
        # Right side - Device settings
        self.device_settings_widget = DeviceSettingsWidget(interface_text)
        
        # Add to main layout with 4:1 ratio
        main_layout.addWidget(self.spectrometer_widget, 4)
        main_layout.addWidget(self.device_settings_widget, 1)
    
    def closeEvent(self, event):
        """Handle tab close event."""
        if hasattr(self, 'spectrometer_widget'):
            self.spectrometer_widget.closeEvent(event)
        super().closeEvent(event)