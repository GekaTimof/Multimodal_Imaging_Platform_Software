"""
Main Window Controller
Manages the main application window with tabbed interface for different device modes.

The application provides three main tabs:
- Spectrometer: For spectrometer device control
- Camera: For camera device control and imaging
- Wells: For wells analysis functionality
"""

from PyQt5.QtWidgets import QMainWindow, QTabWidget
from ui.tabs.spectrometer_tab import SpectrometerTab
from ui.tabs.camera_tab import CameraTab
from ui.tabs.wells_tab import WellsTab
from models.objects.Interface_text import Interface_text
from config import interface_config
from services.raspberry_mode import (
    switch_to_camera_mode,
    switch_to_spectrometer_mode,
    switch_to_wells_mode,
)


class MainWindow(QMainWindow):
    """
    Main application window with tabbed interface.
    
    Manages three device tabs and handles mode switching when tabs are changed.
    """
    
    def __init__(self):
        """Initialize main window with configuration-based settings."""
        super().__init__()
        
        # Load language from config
        default_language = interface_config.get('language.default', 'English')
        self.interface_text = Interface_text(default_language)
        
        # Configure window from config
        window_config = interface_config.get_window_config()
        self.setWindowTitle(window_config.get('title', 'Lab App'))
        self.resize(window_config.get('width', 1400), window_config.get('height', 800))
        
        if window_config.get('start_maximized', True):
            self.showMaximized()
        
        # Set resizable property
        if not window_config.get('resizable', True):
            self.setFixedSize(self.size())

        # Create tab widget
        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        # Initialize device tabs
        self.spectrometer_tab = SpectrometerTab(self.interface_text)
        self.camera_tab = CameraTab(self.interface_text)
        self.wells_tab = WellsTab(self.interface_text)

        # Connect tab change handler
        self.tabs.currentChanged.connect(self.handle_tab_change)

        # Add tabs to interface
        self.tabs.addTab(self.spectrometer_tab, self.interface_text.spectrometer())
        self.tabs.addTab(self.camera_tab, self.interface_text.camera())
        self.tabs.addTab(self.wells_tab, self.interface_text.wells())
        
        # Set default tab from config
        tabs_config = interface_config.get_tabs_config()
        default_tab = tabs_config.get('default_tab', 0)
        self.tabs.setCurrentIndex(default_tab)

    def handle_tab_change(self, index):
        """
        Handle tab switching by activating appropriate device mode
        and switching device settings to the corresponding type.
        
        Args:
            index (int): Index of selected tab (0=Spectrometer, 1=Camera, 2=Wells)
        """
        if index == 0:
            switch_to_spectrometer_mode()
            # Switch device settings to Spectrometer
            self.spectrometer_tab.device_settings_widget.switch_to_settings(self.interface_text.spectrometer())
        elif index == 1:
            switch_to_camera_mode()
            # Switch device settings to Camera (this will trigger refresh)
            self.camera_tab.device_settings_widget.switch_to_settings(self.interface_text.camera())
        elif index == 2:
            switch_to_wells_mode()
            # Switch device settings to Positioner for wells
            self.wells_tab.device_settings_widget.switch_to_settings(self.interface_text.positioner())
