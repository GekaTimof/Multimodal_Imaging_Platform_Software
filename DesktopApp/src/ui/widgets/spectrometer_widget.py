"""
Spectrometer Widget
Comprehensive spectrometer interface with real-time spectrum display, controls, and file operations.
"""

import os
import numpy as np
from PyQt5.QtWidgets import (QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, 
                             QSpinBox, QLineEdit, QFileDialog, QListWidget, QListWidgetItem,
                             QProgressBar, QMessageBox, QSplitter)
from PyQt5.QtCore import Qt, QThread, pyqtSignal, QMutex
import pyqtgraph as pg
from PyQt5.QtGui import QPen, QFont

from ...services.spectrometer_service import SpectrometerService
from ...models.objects.Interface_text import Interface_text


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
        
        # Connect service signals
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
        """Handle received spectrum data."""
        self.new_data.emit(x_data, y_data)
    
    def on_connection_changed(self, connected):
        """Handle connection status changes."""
        self.connection_status.emit(connected)
    
    def on_error(self, error_msg):
        """Handle errors."""
        self.error_occurred.emit(error_msg)
    
    def run(self):
        """Main thread loop."""
        if self.service.check_connection():
            self.service.start_spectrum_stream()
        else:
            self.service.connect_spectrometer()
            if self.service.check_connection():
                self.service.start_spectrum_stream()
        
        # Keep thread alive while streaming
        while self.running:
            self.msleep(100)


class SpectrometerWidget(QWidget):
    """Main spectrometer interface widget."""
    
    def __init__(self, interface_text: Interface_text):
        super().__init__()
        self.interface_text = interface_text
        self.spectrometer_service = SpectrometerService()
        self.data_thread = SpectrumDataThread(self.spectrometer_service)
        
        # UI state
        self.is_dark_theme = False
        self.loaded_spectra = {}
        self.color_counter = 0
        self.start_graph_reset = True
        
        # Initialize UI
        self.init_ui()
        self.connect_signals()
        
        # Start spectrometer connection
        self.start_spectrometer()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main layout
        main_layout = QHBoxLayout(self)
        
        # Create splitter for resizable panels
        splitter = QSplitter(Qt.Horizontal)
        
        # Left panel - Graph
        self.init_graph_panel()
        splitter.addWidget(self.graph_container)
        
        # Right panel - Controls
        self.init_control_panel()
        splitter.addWidget(self.control_container)
        
        # Set splitter proportions (4:1 ratio)
        splitter.setSizes([800, 200])
        
        main_layout.addWidget(splitter)
        self.setLayout(main_layout)
    
    def init_graph_panel(self):
        """Initialize the graph panel."""
        self.graph_container = QWidget()
        graph_layout = QVBoxLayout(self.graph_container)
        
        # Graph widget
        self.graph_widget = pg.PlotWidget()
        self.graph_widget.setBackground("w")
        self.graph_widget.showGrid(x=True, y=True, alpha=0.75)
        self.graph_widget.setLabel("left", self.interface_text.spectrum())
        self.graph_widget.setLabel("bottom", "Wavelength (nm)")
        
        # Main spectrum curve
        self.light_theme_pen = QPen(Qt.blue)
        self.light_theme_pen.setWidth(2)
        self.dark_theme_pen = QPen(Qt.yellow)
        self.dark_theme_pen.setWidth(2)
        
        self.curve = self.graph_widget.plot(pen=self.light_theme_pen)
        
        # Overillumination warning
        self.overillumination_label = pg.TextItem("OVERILLUMINATION WARNING", color='r', anchor=(0.5, 0))
        self.overillumination_label.setFont(QFont("Arial", 12))
        self.overillumination_label.setZValue(2)
        self.overillumination_label.hide()
        self.graph_widget.addItem(self.overillumination_label)
        
        # Coordinates display
        self.coord_label = pg.TextItem("", anchor=(0, 1), color='k')
        self.coord_label.setFont(QFont("Arial", 8))
        self.graph_widget.addItem(self.coord_label)
        self.coord_label.hide()
        
        # Mouse tracking
        self.graph_widget.scene().sigMouseMoved.connect(self.on_mouse_move)
        
        graph_layout.addWidget(self.graph_widget)
    
    def init_control_panel(self):
        """Initialize the control panel."""
        self.control_container = QWidget()
        control_layout = QVBoxLayout(self.control_container)
        
        # Connection status
        self.connection_label = QLabel("Status: Disconnected")
        self.connection_label.setStyleSheet("color: red; font-weight: bold;")
        control_layout.addWidget(self.connection_label)
        
        # Integral time control
        control_layout.addWidget(QLabel(self.interface_text.integral_time()))
        self.integral_time_input = QSpinBox()
        self.integral_time_input.setRange(1, 10000)
        self.integral_time_input.setValue(100)
        self.integral_time_input.setButtonSymbols(QSpinBox.NoButtons)
        self.integral_time_input.valueChanged.connect(self.on_integral_time_changed)
        control_layout.addWidget(self.integral_time_input)
        
        # Dark spectrum controls
        self.set_dark_button = QPushButton(self.interface_text.set_dark_spectrum())
        self.set_dark_button.clicked.connect(self.set_dark_spectrum)
        control_layout.addWidget(self.set_dark_button)
        
        self.clear_dark_button = QPushButton(self.interface_text.clear_dark_spectrum())
        self.clear_dark_button.clicked.connect(self.clear_dark_spectrum)
        control_layout.addWidget(self.clear_dark_button)
        
        # File operations
        control_layout.addWidget(QLabel(self.interface_text.save_directory()))
        
        dir_layout = QHBoxLayout()
        self.dir_input = QLineEdit()
        self.dir_input.setPlaceholderText(self.interface_text.no_folder_selected())
        self.dir_input.setReadOnly(True)
        
        self.dir_button = QPushButton(self.interface_text.select())
        self.dir_button.clicked.connect(self.select_directory)
        
        dir_layout.addWidget(self.dir_input)
        dir_layout.addWidget(self.dir_button)
        control_layout.addLayout(dir_layout)
        
        self.save_button = QPushButton(self.interface_text.save_spectrum())
        self.save_button.clicked.connect(self.save_spectrum)
        control_layout.addWidget(self.save_button)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        control_layout.addWidget(self.progress_bar)
        
        # Spectrum management
        control_layout.addWidget(QLabel("Loaded Spectra:"))
        
        self.load_button = QPushButton(self.interface_text.select_spectrum_file())
        self.load_button.clicked.connect(self.load_spectrum_file)
        control_layout.addWidget(self.load_button)
        
        self.remove_button = QPushButton(self.interface_text.remove_selected_spectrum())
        self.remove_button.clicked.connect(self.remove_selected_spectrum)
        control_layout.addWidget(self.remove_button)
        
        self.spectrum_list = QListWidget()
        self.spectrum_list.setSelectionMode(QListWidget.MultiSelection)
        control_layout.addWidget(self.spectrum_list)
        
        # View controls
        control_layout.addWidget(QLabel("View Controls:"))
        
        self.reset_zoom_button = QPushButton(self.interface_text.reset_zoom())
        self.reset_zoom_button.clicked.connect(self.reset_graph_view)
        control_layout.addWidget(self.reset_zoom_button)
        
        self.theme_button = QPushButton(self.interface_text.switch_to_dark_theme())
        self.theme_button.setCheckable(True)
        self.theme_button.toggled.connect(self.toggle_theme)
        control_layout.addWidget(self.theme_button)
        
        control_layout.addStretch()
    
    def connect_signals(self):
        """Connect signals and slots."""
        self.data_thread.new_data.connect(self.update_graph)
        self.data_thread.connection_status.connect(self.on_connection_status_changed)
        self.data_thread.error_occurred.connect(self.on_error_occurred)
    
    def start_spectrometer(self):
        """Start spectrometer connection and data streaming."""
        self.data_thread.start_streaming()
    
    def stop_spectrometer(self):
        """Stop spectrometer connection and data streaming."""
        self.data_thread.stop_streaming()
    
    def on_connection_status_changed(self, connected):
        """Handle connection status changes."""
        if connected:
            self.connection_label.setText("Status: Connected")
            self.connection_label.setStyleSheet("color: green; font-weight: bold;")
        else:
            self.connection_label.setText("Status: Disconnected")
            self.connection_label.setStyleSheet("color: red; font-weight: bold;")
    
    def on_error_occurred(self, error_msg):
        """Handle errors."""
        QMessageBox.warning(self, self.interface_text.warning_title(), error_msg)
    
    def on_integral_time_changed(self, value):
        """Handle integral time change."""
        self.spectrometer_service.set_integral_time(value)
    
    def update_graph(self, x_data, y_data):
        """Update the spectrum graph."""
        self.curve.setData(x_data, y_data)
        self.update_overillumination_warning(x_data, y_data)
        
        # Reset graph view on first data
        if self.start_graph_reset:
            self.reset_graph_view()
            self.start_graph_reset = False
    
    def update_overillumination_warning(self, x_data, y_data):
        """Update overillumination warning."""
        # Check for saturation (simplified check)
        if len(y_data) > 0 and np.max(y_data) > 0.95 * np.iinfo(np.uint16).max:
            x_center = np.mean(x_data)
            y_center = (np.min(y_data) + np.max(y_data)) / 2
            self.overillumination_label.setPos(x_center, y_center)
            self.overillumination_label.show()
        else:
            self.overillumination_label.hide()
    
    def on_mouse_move(self, pos):
        """Handle mouse movement over graph."""
        vb = self.graph_widget.getViewBox()
        if vb.sceneBoundingRect().contains(pos):
            mouse_point = vb.mapSceneToView(pos)
            x, y = mouse_point.x(), mouse_point.y()
            
            view_rect = vb.viewRect()
            margin_x = (view_rect.right() - view_rect.left()) * 0.04
            margin_y = (view_rect.bottom() - view_rect.top()) * 0.05
            
            if (view_rect.left() + margin_x <= x <= view_rect.right() - margin_x and
                view_rect.top() + margin_y <= y <= view_rect.bottom() - margin_y):
                
                text = f"x={int(x)} y={int(y)}"
                self.coord_label.setText(text)
                self.coord_label.setPos(x, y)
                self.coord_label.show()
            else:
                self.coord_label.hide()
        else:
            self.coord_label.hide()
    
    def set_dark_spectrum(self):
        """Set dark spectrum."""
        if self.spectrometer_service.set_dark_spectrum():
            QMessageBox.information(self, "Success", "Dark spectrum set successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to set dark spectrum")
    
    def clear_dark_spectrum(self):
        """Clear dark spectrum."""
        if self.spectrometer_service.clear_dark_spectrum():
            QMessageBox.information(self, "Success", "Dark spectrum cleared successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to clear dark spectrum")
    
    def select_directory(self):
        """Select save directory."""
        home_dir = os.path.expanduser("~")
        directory = QFileDialog.getExistingDirectory(
            self, 
            "Select Directory",
            self.dir_input.text() if os.path.isdir(self.dir_input.text()) else home_dir
        )
        if directory:
            if not directory.startswith(home_dir):
                QMessageBox.warning(self, self.interface_text.warning_title(),
                                  self.interface_text.warning_select_out_of_home())
                return
            self.dir_input.setText(directory)
    
    def save_spectrum(self):
        """Save current spectrum."""
        directory = self.dir_input.text()
        if not directory or not os.path.isdir(directory):
            QMessageBox.warning(self, self.interface_text.warning_title(),
                              "Please select a valid directory")
            return
        
        home_dir = os.path.expanduser("~")
        if not directory.startswith(home_dir):
            QMessageBox.warning(self, self.interface_text.warning_title(),
                              self.interface_text.warning_saving_out_of_home())
            return
        
        # Show progress
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        
        # Save spectrum
        if self.spectrometer_service.save_spectrum(directory):
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Success", "Spectrum saved successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to save spectrum")
        
        self.progress_bar.setVisible(False)
    
    def load_spectrum_file(self):
        """Load spectrum from file."""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.interface_text.select_spectrum_file(),
            self.dir_input.text() if os.path.isdir(self.dir_input.text()) else "",
            "Text Files (*.txt *.csv);;All Files (*)"
        )
        
        for file_path in files:
            if file_path not in self.loaded_spectra:
                try:
                    # Simple spectrum file loading (assuming two-column format)
                    data = np.loadtxt(file_path)
                    if data.ndim == 2 and data.shape[1] >= 2:
                        x_data = data[:, 0]
                        y_data = data[:, 1]
                        
                        # Generate color
                        color = pg.intColor(self.color_counter)
                        self.color_counter += 1
                        
                        # Plot spectrum
                        curve = self.graph_widget.plot(x_data, y_data, pen=color, 
                                                     name=os.path.basename(file_path))
                        self.loaded_spectra[file_path] = curve
                        
                        # Add to list
                        item = QListWidgetItem(os.path.basename(file_path))
                        item.setData(Qt.UserRole, file_path)
                        
                        q_color = pg.mkColor(color)
                        item.setForeground(q_color)
                        
                        self.spectrum_list.addItem(item)
                    else:
                        QMessageBox.warning(self, "Error", f"Invalid spectrum file format: {file_path}")
                        
                except Exception as e:
                    QMessageBox.warning(self, "Error", f"Failed to load file {file_path}: {e}")
        
        # Reset view
        self.reset_graph_view()
    
    def remove_selected_spectrum(self):
        """Remove selected spectra."""
        selected_items = self.spectrum_list.selectedItems()
        for item in selected_items:
            file_path = item.data(Qt.UserRole)
            if file_path in self.loaded_spectra:
                curve = self.loaded_spectra.pop(file_path)
                self.graph_widget.removeItem(curve)
                self.spectrum_list.takeItem(self.spectrum_list.row(item))
        
        self.reset_graph_view()
    
    def reset_graph_view(self):
        """Reset graph view to show all data."""
        all_x = []
        all_y = []
        
        # Add current spectrum
        if self.curve is not None:
            x_data, y_data = self.curve.getData()
            if len(x_data) > 0:
                all_x.extend(x_data)
                all_y.extend(y_data)
        
        # Add loaded spectra
        for curve in self.loaded_spectra.values():
            x_data, y_data = curve.getData()
            if len(x_data) > 0:
                all_x.extend(x_data)
                all_y.extend(y_data)
        
        if all_x and all_y:
            min_x, max_x = min(all_x), max(all_x)
            min_y, max_y = min(all_y), max(all_y)
            
            self.graph_widget.setXRange(min_x, max_x)
            self.graph_widget.setYRange(min_y, max_y)
    
    def toggle_theme(self, checked):
        """Toggle between light and dark theme."""
        if checked:
            self.set_dark_theme()
            self.theme_button.setText(self.interface_text.switch_to_light_theme())
        else:
            self.set_light_theme()
            self.theme_button.setText(self.interface_text.switch_to_dark_theme())
    
    def set_dark_theme(self):
        """Set dark theme."""
        self.setStyleSheet("""
            QWidget {
                background-color: #2b2b2b;
                color: white;
            }
            QPushButton {
                background-color: #404040;
                color: white;
                border: 1px solid #555;
                padding: 5px;
                border-radius: 3px;
            }
            QPushButton:hover {
                background-color: #505050;
            }
            QLineEdit, QSpinBox {
                background-color: #404040;
                color: white;
                border: 1px solid #555;
                padding: 3px;
            }
            QListWidget {
                background-color: #404040;
                color: white;
                border: 1px solid #555;
            }
        """)
        
        self.coord_label.setColor("w")
        self.graph_widget.setBackground('k')
        self.curve.setPen(self.dark_theme_pen)
        self.is_dark_theme = True
    
    def set_light_theme(self):
        """Set light theme."""
        self.setStyleSheet("")
        self.coord_label.setColor("k")
        self.graph_widget.setBackground('w')
        self.curve.setPen(self.light_theme_pen)
        self.is_dark_theme = False
    
    def closeEvent(self, event):
        """Handle widget close event."""
        self.stop_spectrometer()
        super().closeEvent(event)
