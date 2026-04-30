from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel
from DesktopApp.objects.Interface_text import Interface_text

class SpectrometerTab(QWidget):
    def __init__(self, interface_text: Interface_text):
        super().__init__()
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel(interface_text.spectrometer()))

    # TODO добавить получение и отображение спектров из потока с Raspberry Pi

    # TODO заменить комадны на отправку команды на API для управления спектрометром на Raspberry Pi, а не управление спектрометром напрямую из приложения