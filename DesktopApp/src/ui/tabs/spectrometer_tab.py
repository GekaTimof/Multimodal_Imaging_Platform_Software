"""
Spectrometer Tab
Layout mirrors CameraTab:
  - Left:  spectrum graph (SpectrometerWidget)
  - Right (upper): tools — start/stop, file ops, spectrum list, navigation controls
  - Right (lower): device settings panel (SpectrometerSettingsWidget inside DeviceSettingsWidget)
"""

import logging
import os
import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QProgressBar,
    QMessageBox, QScrollArea, QSizePolicy,
)
import pyqtgraph as pg

from config.api_config import SPECTRUM_STREAM_URL
from config import interface_config
from config.theme_manager import ThemeManager
from models.interface_text import Interface_text
from ui.widgets.device_settings_widget import DeviceSettingsWidget
from ui.widgets.spectrometer_widget import SpectrometerWidget

logger = logging.getLogger(__name__)


class SpectrometerTab(QWidget):
    """
    Spectrometer tab with the same column structure as CameraTab.
    """

    def __init__(self, interface_text: Interface_text, theme_manager: ThemeManager = None):
        super().__init__()
        self.interface_text = interface_text
        self._theme_manager = theme_manager

        # ---- Left: graph widget ----
        self.spectrometer_widget = SpectrometerWidget(interface_text)
        self.spectrometer_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ---- Right upper: tools panel ----
        upper_tools_layout = QVBoxLayout()
        upper_tools_layout.setSpacing(6)

        # Start / Stop buttons (mirrors CameraTab)
        self.start_button = QPushButton(interface_text.start_spectrometer())
        self.stop_button = QPushButton(interface_text.stop_spectrometer())
        self.start_button.clicked.connect(self.start_spectrometer)
        self.stop_button.clicked.connect(self.stop_spectrometer)
        upper_tools_layout.addWidget(self.start_button)
        upper_tools_layout.addWidget(self.stop_button)

        upper_tools_layout.addWidget(QLabel(f"Stream URL: {SPECTRUM_STREAM_URL}"))

        # Save & load buttons
        self.save_button = QPushButton(interface_text.save_spectrum())
        self.save_button.clicked.connect(self._save_spectrum)
        upper_tools_layout.addWidget(self.save_button)

        self.load_button = QPushButton(interface_text.select_spectrum_file())
        self.load_button.clicked.connect(self._load_spectrum_file)
        upper_tools_layout.addWidget(self.load_button)

        # Spectrum list
        upper_tools_layout.addWidget(QLabel(interface_text.loaded_spectra() if interface_text else "Loaded Spectra:"))
        self.spectrum_list = QListWidget()
        self.spectrum_list.setSelectionMode(QListWidget.MultiSelection)
        upper_tools_layout.addWidget(self.spectrum_list)

        # Remove button
        self.remove_button = QPushButton(interface_text.remove_selected_spectrum())
        self.remove_button.clicked.connect(self._remove_selected_spectrum)
        upper_tools_layout.addWidget(self.remove_button)

        # Dark spectrum: label + two buttons
        self.dark_spectrum_label = QLabel(interface_text.dark_spectrum())
        self.dark_spectrum_label.setStyleSheet("QLabel { font-weight: bold; }")
        upper_tools_layout.addWidget(self.dark_spectrum_label)

        dark_row = QHBoxLayout()
        self.set_dark_button = QPushButton(interface_text.set_dark_spectrum())
        self.set_dark_button.clicked.connect(self._set_dark_spectrum)
        dark_row.addWidget(self.set_dark_button)

        self.clear_dark_button = QPushButton(interface_text.clear_dark_spectrum())
        self.clear_dark_button.clicked.connect(self._clear_dark_spectrum)
        dark_row.addWidget(self.clear_dark_button)
        upper_tools_layout.addLayout(dark_row)

        # Navigation / view controls
        self.reset_zoom_button = QPushButton(interface_text.reset_zoom())
        self.reset_zoom_button.clicked.connect(self.spectrometer_widget.reset_graph_view)
        upper_tools_layout.addWidget(self.reset_zoom_button)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        upper_tools_layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)
        upper_tools_layout.addWidget(self.status_label)

        upper_tools_layout.addStretch()

        upper_scroll = QScrollArea()
        upper_scroll.setWidgetResizable(True)
        upper_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        upper_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        upper_tools_widget = QWidget()
        upper_tools_widget.setLayout(upper_tools_layout)
        upper_scroll.setWidget(upper_tools_widget)

        # ---- Right lower: device settings ----
        self.device_settings_widget = DeviceSettingsWidget(interface_text, theme_manager, self.spectrometer_widget.spectrometer_service)

        # Switch dropdown to Spectrometer by default
        if hasattr(interface_text, 'spectrometer'):
            idx = self.device_settings_widget.settings_type_combo.findText(interface_text.spectrometer())
        else:
            idx = self.device_settings_widget.settings_type_combo.findText("Spectrometer")
        if idx >= 0:
            self.device_settings_widget.settings_type_combo.setCurrentIndex(idx)

        lower_scroll = QScrollArea()
        lower_scroll.setWidgetResizable(True)
        lower_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lower_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        lower_scroll.setWidget(self.device_settings_widget)

        # ---- Right panel (upper + lower, 2:3) ----
        right_layout = QVBoxLayout()
        right_layout.addWidget(upper_scroll, 2)
        right_layout.addWidget(lower_scroll, 3)

        right_panel = QWidget()
        right_panel.setLayout(right_layout)
        right_panel.setMinimumWidth(interface_config.get('ui_scaling.side_panel_min_width', 320))
        right_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # ---- Main horizontal layout ----
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.spectrometer_widget, 1)
        main_layout.addWidget(right_panel)

        # ---- Wire spectrometer settings signals ----
        spec_settings = self.device_settings_widget.spectrometer_tab
        spec_settings.integral_time_changed.connect(
            self.spectrometer_widget.spectrometer_service.set_integral_time
        )
        spec_settings.set_dark_requested.connect(self._set_dark_spectrum)
        spec_settings.clear_dark_requested.connect(self._clear_dark_spectrum)
        spec_settings.settings_changed.connect(self._on_settings_changed)

        # Forward errors from service
        self.spectrometer_widget.spectrometer_service.error_occurred.connect(self._on_error)

        # Theme: connect ThemeManager (global)
        if theme_manager is not None:
            theme_manager.theme_changed.connect(self._toggle_theme)
            self._toggle_theme(theme_manager.is_dark)

    # ------------------------------------------------------------------
    # Spectrometer start / stop (mirrors CameraTab.start_camera / stop_camera)
    # ------------------------------------------------------------------

    def start_spectrometer(self):
        """Start spectrum streaming."""
        self.spectrometer_widget.start_spectrometer()

        # Connect thread status signal to our status label
        thread = self.spectrometer_widget.thread
        if thread is not None:
            thread.status_ready.connect(self._on_spectrometer_status)

        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def stop_spectrometer(self):
        """Stop spectrum streaming."""
        self.status_label.setText("Stopping spectrometer...")
        self.spectrometer_widget.stop_spectrometer()
        self.status_label.setText("Spectrometer stopped")

        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def _on_spectrometer_status(self, message: str):
        """Handle status messages from the spectrum thread."""
        self.status_label.setText(message)
        logger.info(f"Spectrometer status: {message}")

        # Update connection status in settings widget
        spec_settings = self.device_settings_widget.spectrometer_tab
        if "started" in message.lower():
            spec_settings.status_label.setText("Connected")
            spec_settings.status_label.setStyleSheet("color: green; font-weight: bold;")
        elif "stopped" in message.lower() or "failed" in message.lower() or "error" in message.lower():
            spec_settings.status_label.setText("Disconnected")
            spec_settings.status_label.setStyleSheet("color: red; font-weight: bold;")

    # ------------------------------------------------------------------
    # File operations
    # ------------------------------------------------------------------

    def _save_spectrum(self):
        directory = self.device_settings_widget.file_tab.get_spectrum_save_directory()
        if not directory:
            QMessageBox.warning(self, self.interface_text.warning_title(),
                                "Please set a spectrum save directory in File Settings")
            return
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        svc = self.spectrometer_widget.spectrometer_service
        if svc.save_spectrum(directory):
            self.progress_bar.setValue(100)
            QMessageBox.information(self, "Success", "Spectrum saved successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to save spectrum")
        self.progress_bar.setVisible(False)

    def _load_spectrum_file(self):
        from PyQt5.QtWidgets import QFileDialog
        initial_dir = self.device_settings_widget.file_tab.get_spectrum_save_directory() or ""
        files, _ = QFileDialog.getOpenFileNames(
            self,
            self.interface_text.select_spectrum_file(),
            initial_dir,
            "Text Files (*.txt *.csv);;All Files (*)",
        )
        for file_path in files:
            if file_path in self.spectrometer_widget.loaded_spectra:
                continue
            try:
                data = np.loadtxt(file_path)
                if data.ndim == 2 and data.shape[1] >= 2:
                    x_data, y_data = data[:, 0], data[:, 1]
                    color = self.spectrometer_widget.add_spectrum_curve(file_path, x_data, y_data)
                    item = QListWidgetItem(os.path.basename(file_path))
                    item.setData(Qt.UserRole, file_path)
                    item.setForeground(pg.mkColor(color))
                    self.spectrum_list.addItem(item)
                else:
                    QMessageBox.warning(self, "Error", f"Invalid spectrum file format: {file_path}")
            except Exception as e:
                QMessageBox.warning(self, "Error", f"Failed to load file {file_path}: {e}")

    def _remove_selected_spectrum(self):
        for item in self.spectrum_list.selectedItems():
            file_path = item.data(Qt.UserRole)
            self.spectrometer_widget.remove_spectrum_curve(file_path)
            self.spectrum_list.takeItem(self.spectrum_list.row(item))

    # ------------------------------------------------------------------
    # Spectrometer device controls
    # ------------------------------------------------------------------

    def _set_dark_spectrum(self):
        svc = self.spectrometer_widget.spectrometer_service
        if svc.set_dark_spectrum():
            QMessageBox.information(self, "Success", "Dark spectrum set successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to set dark spectrum")

    def _clear_dark_spectrum(self):
        svc = self.spectrometer_widget.spectrometer_service
        if svc.clear_dark_spectrum():
            QMessageBox.information(self, "Success", "Dark spectrum cleared successfully")
        else:
            QMessageBox.warning(self, "Error", "Failed to clear dark spectrum")

    def _on_settings_changed(self, settings: dict):
        """Handle settings changes from spectrometer settings widget."""
        logger.info(f"Spectrometer settings changed: {settings}")
        # Could update status or other UI elements here if needed

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _toggle_theme(self, dark: bool):
        if dark:
            self.spectrometer_widget.set_dark_theme()
        else:
            self.spectrometer_widget.set_light_theme()

    # ------------------------------------------------------------------
    # Error handling
    # ------------------------------------------------------------------

    def _on_error(self, error_msg):
        QMessageBox.warning(self, self.interface_text.warning_title(), error_msg)

    # ------------------------------------------------------------------
    # Resize
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        h = self.height()
        max_graph_w = int(w * 4 / 5)
        max_graph_h = int(h * 0.95)
        self.spectrometer_widget.setMaximumSize(max_graph_w, max_graph_h)

    # ------------------------------------------------------------------
    # Dark spectrum
    # ------------------------------------------------------------------

    def _set_dark_spectrum(self):
        """Capture dark spectrum and show status in the upper panel."""
        spec_settings = self.device_settings_widget.spectrometer_tab
        spec_settings.set_dark_requested.emit()
        self.status_label.setText("Capturing dark spectrum...")
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")

    def _clear_dark_spectrum(self):
        """Clear dark spectrum and show status in the upper panel."""
        spec_settings = self.device_settings_widget.spectrometer_tab
        spec_settings.clear_dark_requested.emit()
        spec_settings.current_settings['UseDarkSpectrum'] = False
        spec_settings._update_dark_status()
        self.status_label.setText("Dark spectrum cleared")
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")

    # ------------------------------------------------------------------
    # Language
    # ------------------------------------------------------------------

    def update_language(self, interface_text: Interface_text):
        """Update all UI text when language changes."""
        self.interface_text = interface_text
        self.start_button.setText(interface_text.start_spectrometer())
        self.stop_button.setText(interface_text.stop_spectrometer())
        self.save_button.setText(interface_text.save_spectrum())
        self.load_button.setText(interface_text.select_spectrum_file())
        self.remove_button.setText(interface_text.remove_selected_spectrum())
        self.dark_spectrum_label.setText(interface_text.dark_spectrum())
        self.set_dark_button.setText(interface_text.set_dark_spectrum())
        self.clear_dark_button.setText(interface_text.clear_dark_spectrum())
        self.reset_zoom_button.setText(interface_text.reset_zoom())

    def closeEvent(self, event):
        """Handle tab close event."""
        if hasattr(self, 'spectrometer_widget'):
            self.spectrometer_widget.closeEvent(event)
        super().closeEvent(event)