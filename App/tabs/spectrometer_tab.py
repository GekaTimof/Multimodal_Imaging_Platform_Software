from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from App.obects.Interface_text import Interface_text

class SpectrometerTab(QWidget):
    def __init__(self, interface_text: Interface_text):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(interface_text.spectrometer()))