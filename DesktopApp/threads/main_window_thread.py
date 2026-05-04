"""
Main Window Controller
Manages the main application window with tabbed interface for different device modes.

The application provides three main tabs:
- Spectrometer: For spectrometer device control
- Camera: For camera device control and imaging
- Wells: For wells analysis functionality
"""

from PyQt5.QtWidgets import QMainWindow, QTabWidget
from DesktopApp.tabs.spectrometer_tab import SpectrometerTab
from DesktopApp.tabs.camera_tab import CameraTab
from DesktopApp.tabs.wells_tab import WellsTab
from DesktopApp.objects.Interface_text import Interface_text
from DesktopApp.services.raspberry_mode import (
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
        """Initialize main window with default English language."""
        super().__init__()
        self.interface_text = Interface_text("English")
        self.setWindowTitle("Lab App")
        self.resize(1400, 800)
        self.showMaximized()  # Start in fullscreen mode

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

    def handle_tab_change(self, index):
        """
        Handle tab switching by activating appropriate device mode.
        
        Args:
            index (int): Index of selected tab (0=Spectrometer, 1=Camera, 2=Wells)
        """
        if index == 0:
            switch_to_spectrometer_mode()
        elif index == 1:
            switch_to_camera_mode()
        elif index == 2:
            switch_to_wells_mode()
