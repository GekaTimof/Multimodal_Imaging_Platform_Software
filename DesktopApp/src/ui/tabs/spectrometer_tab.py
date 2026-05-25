"""
Spectrometer Tab
Layout mirrors CameraTab:
  - Left:  spectrum graph (SpectrometerWidget)
  - Right (upper): tools — file ops, spectrum list, navigation controls
  - Right (lower): device settings panel (SpectrometerSettingsWidget inside DeviceSettingsWidget)
"""

import os
import numpy as np

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QWidget, QHBoxLayout, QVBoxLayout, QLabel, QPushButton,
    QListWidget, QListWidgetItem, QProgressBar,
    QMessageBox, QScrollArea, QSizePolicy,
)
import pyqtgraph as pg

from models.interface_text import Interface_text
from ui.widgets.device_settings_widget import DeviceSettingsWidget
from ui.widgets.spectrometer_widget import SpectrometerWidget


class SpectrometerTab(QWidget):
    """
    Spectrometer tab with the same column structure as CameraTab.
    """

    def __init__(self, interface_text: Interface_text):
        super().__init__()
        self.interface_text = interface_text

        # ---- Left: graph widget ----
        self.spectrometer_widget = SpectrometerWidget(interface_text)
        self.spectrometer_widget.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

        # ---- Right upper: tools panel ----
        upper_tools_layout = QVBoxLayout()
        upper_tools_layout.setSpacing(6)

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

        # Navigation / view controls
        self.reset_zoom_button = QPushButton(interface_text.reset_zoom())
        self.reset_zoom_button.clicked.connect(self.spectrometer_widget.reset_graph_view)
        upper_tools_layout.addWidget(self.reset_zoom_button)

        self.theme_button = QPushButton(interface_text.switch_to_dark_theme())
        self.theme_button.setCheckable(True)
        self.theme_button.toggled.connect(self._toggle_theme)
        upper_tools_layout.addWidget(self.theme_button)

        # Progress bar (hidden by default)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        upper_tools_layout.addWidget(self.progress_bar)

        upper_tools_layout.addStretch()

        upper_scroll = QScrollArea()
        upper_scroll.setWidgetResizable(True)
        upper_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        upper_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        upper_tools_widget = QWidget()
        upper_tools_widget.setLayout(upper_tools_layout)
        upper_scroll.setWidget(upper_tools_widget)

        # ---- Right lower: device settings ----
        self.device_settings_widget = DeviceSettingsWidget(interface_text)

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
        right_panel.setMinimumWidth(260)
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

        # Forward connection status from data thread to settings widget
        self.spectrometer_widget.data_thread.connection_status.connect(
            spec_settings.set_connection_status
        )
        # Forward errors
        self.spectrometer_widget.data_thread.error_occurred.connect(self._on_error)

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

    # ------------------------------------------------------------------
    # Theme
    # ------------------------------------------------------------------

    def _toggle_theme(self, checked):
        if checked:
            self.spectrometer_widget.set_dark_theme()
            self.theme_button.setText(self.interface_text.switch_to_light_theme())
        else:
            self.spectrometer_widget.set_light_theme()
            self.theme_button.setText(self.interface_text.switch_to_dark_theme())

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

    def closeEvent(self, event):
        """Handle tab close event."""
        if hasattr(self, 'spectrometer_widget'):
            self.spectrometer_widget.closeEvent(event)
        super().closeEvent(event)