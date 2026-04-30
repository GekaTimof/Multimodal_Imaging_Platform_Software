from PyQt5.QtWidgets import QMainWindow, QTabWidget
from App.tabs.spectrometer_tab import SpectrometerTab
from App.tabs.camera_tab import CameraTab
from App.tabs.wells_tab import WellsTab
from App.obects.Interface_text import Interface_text

class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.interface_text = Interface_text("English")
        self.setWindowTitle("Lab App")
        self.resize(1400, 800)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)

        self.spectrometer_tab = SpectrometerTab(self.interface_text)
        self.camera_tab = CameraTab(self.interface_text)
        self.wells_tab = WellsTab(self.interface_text)


        self.tabs.addTab(self.spectrometer_tab, self.interface_text.spectrometer())
        self.tabs.addTab(self.camera_tab, self.interface_text.camera())
        self.tabs.addTab(self.wells_tab, self.interface_text.wells())