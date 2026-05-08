from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel
from DesktopApp.objects.Interface_text import Interface_text
from DesktopApp.widgets.device_settings_widget.device_settings_widgets import DeviceSettingsWidget

class SpectrometerTab(QWidget):
    def __init__(self, interface_text: Interface_text):
        super().__init__()
        
        # Main layout
        main_layout = QHBoxLayout(self)
        
        # Left side - Spectrometer content (placeholder for now)
        left_layout = QVBoxLayout()
        left_layout.addWidget(QLabel(interface_text.spectrometer()))
        left_layout.addStretch()
        
        # Right side - Device settings
        self.device_settings_widget = DeviceSettingsWidget(interface_text)
        
        # Add to main layout with 4:1 ratio
        main_layout.addLayout(left_layout, 4)
        main_layout.addWidget(self.device_settings_widget, 1)

    # TODO добавить получение и отображение спектров из потока с Raspberry Pi

    # TODO заменить комадны на отправку команды на API для управления спектрометром на Raspberry Pi, а не управление спектрометром напрямую из приложения