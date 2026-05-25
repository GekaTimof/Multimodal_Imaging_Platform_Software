"""
Spectrometer Widget
Pure spectrum graph display widget. Controls and file operations are managed by SpectrometerTab.
"""

import numpy as np
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMutex
import pyqtgraph as pg
from PyQt5.QtGui import QPen, QFont

from services.spectrometer_service import SpectrometerService
from models.interface_text import Interface_text
from core.constants.spectrometer_constants import (
    DEFAULT_STREAM_INTERVAL_MS, SPECTRUM_THREAD_SLEEP_MS
)


class SpectrumDataThread(QThread):
    """Thread for handling spectrum data streaming."""
    
    new_data = pyqtSignal(np.ndarray, np.ndarray)
    connection_status = pyqtSignal(bool)
    error_occurred = pyqtSignal(str)
    
    def __init__(self, spectrometer_service: SpectrometerService):
        super().__init__()
        self.service = spectrometer_service
        self.running = False
        self.mutex = QMutex()
        
        self.service.spectrum_received.connect(self.on_spectrum_received)
        self.service.connection_status_changed.connect(self.on_connection_changed)
        self.service.error_occurred.connect(self.on_error)
    
    def start_streaming(self):
        """Start spectrum streaming."""
        self.mutex.lock()
        self.running = True
        self.mutex.unlock()
        self.start()
    
    def stop_streaming(self):
        """Stop spectrum streaming."""
        self.mutex.lock()
        self.running = False
        self.mutex.unlock()
        self.service.stop_spectrum_stream()
        self.quit()
        self.wait()
    
    def on_spectrum_received(self, x_data, y_data):
        self.new_data.emit(x_data, y_data)
    
    def on_connection_changed(self, connected):
        self.connection_status.emit(connected)
    
    def on_error(self, error_msg):
        self.error_occurred.emit(error_msg)
    
    def run(self):
        """Main thread loop."""
        if self.service.check_connection():
            self.service.start_spectrum_stream()
        else:
            self.service.connect_spectrometer()
            if self.service.check_connection():
                self.service.start_spectrum_stream()
        
        while self.running:
            self.msleep(SPECTRUM_THREAD_SLEEP_MS)


class SpectrometerWidget(QWidget):
    """
    Pure spectrum graph display widget.
    Manages the spectrometer service and data thread.
    All UI controls live in SpectrometerTab (upper-right tools panel).
    """

    def __init__(self, interface_text: Interface_text):
        super().__init__()
        self.interface_text = interface_text
        self.spectrometer_service = SpectrometerService()
        self.data_thread = SpectrumDataThread(self.spectrometer_service)

        self.is_dark_theme = False
        self.loaded_spectra = {}
        self.color_counter = 0
        self.start_graph_reset = True

        self._init_graph()

        self.data_thread.new_data.connect(self._update_graph)
        self.data_thread.connection_status.connect(self._on_connection_changed)

        self.data_thread.start_streaming()

    def _init_graph(self):
        """Build the plot widget."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)

        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground("w")
        self.graph_widget.showGrid(x=True, y=True, alpha=0.75)
        self.graph_widget.setLabel("left", self.interface_text.spectrum())
        self.graph_widget.setLabel("bottom", "Wavelength (nm)")
        self.graph_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # Disable autoRange and set a stable initial view so the empty plot
        # does not enter an undefined state that makes the grid follow the cursor.
        vb = self.graph_widget.getViewBox()
        vb.disableAutoRange()
        vb.setMouseMode(pg.ViewBox.PanMode)
        from core.constants.spectrometer_constants import (
            WAVELENGTH_MIN, WAVELENGTH_MAX, SPECTRUM_Y_MAX, GRAPH_PADDING,
            OVERILLUMINATION_TEXT, OVERILLUMINATION_COLOR, OVERILLUMINATION_FONT, OVERILLUMINATION_FONT_SIZE
        )
        self.graph_widget.setXRange(WAVELENGTH_MIN, WAVELENGTH_MAX, padding=GRAPH_PADDING)
        self.graph_widget.setYRange(0, SPECTRUM_Y_MAX, padding=GRAPH_PADDING)

        self.light_theme_pen = QPen(Qt.blue)
        self.light_theme_pen.setWidth(2)
        self.dark_theme_pen = QPen(Qt.yellow)
        self.dark_theme_pen.setWidth(2)

        self.curve = self.graph_widget.plot(pen=self.light_theme_pen)

        self.overillumination_label = pg.TextItem(
            self.interface_text.overillumination_warning() if self.interface_text else OVERILLUMINATION_TEXT, 
            color=OVERILLUMINATION_COLOR, anchor=(0.5, 0)
        )
        self.overillumination_label.setFont(QFont(OVERILLUMINATION_FONT, OVERILLUMINATION_FONT_SIZE))
        self.overillumination_label.setZValue(2)
        self.overillumination_label.hide()
        self.graph_widget.addItem(self.overillumination_label)

        self.coord_label = pg.TextItem("", anchor=(0, 1), color='k')
        from core.constants.spectrometer_constants import COORD_FONT, COORD_FONT_SIZE, COORD_COLOR
        self.coord_label.setFont(QFont(COORD_FONT, COORD_FONT_SIZE))
        self.coord_label.setFlag(self.coord_label.GraphicsItemFlag.ItemIsMovable, False)
        self.graph_widget.addItem(self.coord_label)
        self.coord_label.hide()

        self.graph_widget.scene().sigMouseMoved.connect(self._on_mouse_move)

        layout.addWidget(self.graph_widget)

    # ------------------------------------------------------------------
    # Public API called by SpectrometerTab
    # ------------------------------------------------------------------

    def stop_spectrometer(self):
        """Stop the data thread."""
        self.data_thread.stop_streaming()

    def reset_graph_view(self):
        """Fit all visible data into the view."""
        all_x, all_y = [], []
        x_data, y_data = self.curve.getData()
        if x_data is not None and len(x_data) > 0:
            all_x.extend(x_data)
            all_y.extend(y_data)
        for curve in self.loaded_spectra.values():
            x_data, y_data = curve.getData()
            if x_data is not None and len(x_data) > 0:
                all_x.extend(x_data)
                all_y.extend(y_data)
        if all_x and all_y:
            self.graph_widget.setXRange(min(all_x), max(all_x))
            self.graph_widget.setYRange(min(all_y), max(all_y))

    def add_spectrum_curve(self, file_path, x_data, y_data):
        """Add a loaded spectrum curve. Returns the color used."""
        color = pg.intColor(self.color_counter)
        self.color_counter += 1
        import os
        curve = self.graph_widget.plot(x_data, y_data, pen=color,
                                       name=os.path.basename(file_path))
        self.loaded_spectra[file_path] = curve
        self.reset_graph_view()
        return color

    def remove_spectrum_curve(self, file_path):
        """Remove a loaded spectrum curve by file path."""
        if file_path in self.loaded_spectra:
            curve = self.loaded_spectra.pop(file_path)
            self.graph_widget.removeItem(curve)
        self.reset_graph_view()

    def set_dark_theme(self):
        """Apply dark theme to graph."""
        self.coord_label.setColor("w")
        self.graph_widget.setBackground('k')
        self.curve.setPen(self.dark_theme_pen)
        self.is_dark_theme = True

    def set_light_theme(self):
        """Apply light theme to graph."""
        self.coord_label.setColor("k")
        self.graph_widget.setBackground('w')
        self.curve.setPen(self.light_theme_pen)
        self.is_dark_theme = False

    # ------------------------------------------------------------------
    # Internal slots
    # ------------------------------------------------------------------

    def _update_graph(self, x_data, y_data):
        self.curve.setData(x_data, y_data)
        self._update_overillumination(x_data, y_data)
        if self.start_graph_reset:
            self.reset_graph_view()
            self.start_graph_reset = False

    def _update_overillumination(self, x_data, y_data):
        if len(y_data) > 0 and np.max(y_data) > 0.95 * np.iinfo(np.uint16).max:
            x_center = np.mean(x_data)
            y_center = (np.min(y_data) + np.max(y_data)) / 2
            self.overillumination_label.setPos(x_center, y_center)
            self.overillumination_label.show()
        else:
            self.overillumination_label.hide()

    def _on_connection_changed(self, connected):
        pass  # forwarded to SpectrometerTab via data_thread signal

    def _on_mouse_move(self, pos):
        from PyQt5.QtWidgets import QApplication
        # Do not update coord label while any mouse button is held (avoids
        # interfering with ViewBox pan/zoom drag state).
        if QApplication.mouseButtons() != Qt.NoButton:
            return
        vb = self.graph_widget.getViewBox()
        if vb.sceneBoundingRect().contains(pos):
            mouse_point = vb.mapSceneToView(pos)
            x, y = mouse_point.x(), mouse_point.y()
            view_rect = vb.viewRect()
            margin_x = (view_rect.right() - view_rect.left()) * 0.04
            margin_y = (view_rect.bottom() - view_rect.top()) * 0.05
            if (view_rect.left() + margin_x <= x <= view_rect.right() - margin_x and
                    view_rect.top() + margin_y <= y <= view_rect.bottom() - margin_y):
                self.coord_label.setText(f"x={int(x)} y={int(y)}")
                self.coord_label.setPos(x, y)
                self.coord_label.show()
            else:
                self.coord_label.hide()
        else:
            self.coord_label.hide()

    def closeEvent(self, event):
        self.stop_spectrometer()
        super().closeEvent(event)
