"""
File Settings Widget
Widget for configuring file save directories for photos and spectra.
"""

import logging
import os

from PyQt5.QtCore import pyqtSignal
from PyQt5.QtWidgets import (
    QFileDialog, QHBoxLayout, QLabel, QMessageBox,
    QProgressBar, QPushButton, QVBoxLayout, QWidget
)

from ui.ui_utils import get_relative_margin

logger = logging.getLogger(__name__)


class FileSettingsWidget(QWidget):
    """Widget for file saving settings configuration."""

    settings_updated = pyqtSignal()

    def __init__(self, interface_text=None):
        super().__init__()
        self.interface_text = interface_text
        self._build_ui()
        self._load_settings()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            get_relative_margin(0.9), get_relative_margin(0.9), 
            get_relative_margin(0.9), get_relative_margin(0.9)
        )
        layout.setSpacing(get_relative_margin(0.9))

        # Photo save directory
        photo_dir_label = QLabel(
            self.interface_text.photo_save_directory() if self.interface_text else "Photo Save Directory:"
        )
        photo_dir_label.setStyleSheet("QLabel { font-weight: bold; }")
        photo_dir_label.setWordWrap(True)
        layout.addWidget(photo_dir_label)

        self.photo_dir_label = QLabel(
            self.interface_text.no_folder_selected() if self.interface_text else "No folder selected"
        )
        self.photo_dir_label.setWordWrap(True)
        layout.addWidget(self.photo_dir_label)

        photo_btn_row = QHBoxLayout()
        self.photo_dir_button = QPushButton(
            self.interface_text.select() if self.interface_text else "Select"
        )
        photo_btn_row.addWidget(self.photo_dir_button)
        photo_btn_row.addStretch()
        layout.addLayout(photo_btn_row)

        # Spectrum save directory
        spectrum_dir_label = QLabel(
            self.interface_text.spectrum_save_directory() if self.interface_text else "Spectrum Save Directory:"
        )
        spectrum_dir_label.setStyleSheet("QLabel { font-weight: bold; }")
        spectrum_dir_label.setWordWrap(True)
        layout.addWidget(spectrum_dir_label)

        self.spectrum_dir_label = QLabel(
            self.interface_text.no_folder_selected() if self.interface_text else "No folder selected"
        )
        self.spectrum_dir_label.setWordWrap(True)
        layout.addWidget(self.spectrum_dir_label)

        spectrum_btn_row = QHBoxLayout()
        self.spectrum_dir_button = QPushButton(
            self.interface_text.select() if self.interface_text else "Select"
        )
        spectrum_btn_row.addWidget(self.spectrum_dir_button)
        spectrum_btn_row.addStretch()
        layout.addLayout(spectrum_btn_row)

        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        layout.addWidget(self.progress_bar)

        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)

        layout.addStretch()

        self.photo_dir_button.clicked.connect(self._select_photo_directory)
        self.spectrum_dir_button.clicked.connect(self._select_spectrum_directory)

    def _pick_directory(self, current_label_text) -> str:
        """Open a directory picker and validate the selected path."""
        from services.directory_control import get_home_directory
        from config import path_manager
        home_dir = get_home_directory()
        options = QFileDialog.Option.DontUseNativeDialog | QFileDialog.Option.ReadOnly
        current = current_label_text if os.path.isdir(current_label_text) else home_dir
        directory = QFileDialog.getExistingDirectory(
            self,
            self.interface_text.select_save_directory() if self.interface_text else "Select Save Directory",
            current, options
        )
        if not directory:
            return ""
        is_valid, reason = path_manager.validate_directory(directory)
        if not is_valid:
            QMessageBox.warning(
                self,
                self.interface_text.warning_title() if self.interface_text else "Invalid Directory",
                reason
            )
            return ""
        return directory

    def _select_photo_directory(self):
        directory = self._pick_directory(self.photo_dir_label.text())
        if directory:
            self._save_photo_directory(directory)

    def _select_spectrum_directory(self):
        directory = self._pick_directory(self.spectrum_dir_label.text())
        if directory:
            self._save_spectrum_directory(directory)

    def _update_progress(self, value, maximum=100):
        self.progress_bar.setMaximum(maximum)
        self.progress_bar.setValue(value)
        self.progress_bar.setVisible(value < maximum)

    def _save_photo_directory(self, directory):
        from config import path_manager
        is_valid, reason = path_manager.validate_directory(directory)
        if not is_valid:
            self.status_label.setText(f"Invalid path: {reason}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            return
        try:
            path_manager.set_save_directory('photo', directory)
            self.photo_dir_label.setText(directory)
            self.status_label.setText(f"Photo directory saved: {directory}")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
            self.settings_updated.emit()
        except Exception as e:
            self.status_label.setText(f"Error saving directory: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def _save_spectrum_directory(self, directory):
        from config import path_manager
        is_valid, reason = path_manager.validate_directory(directory)
        if not is_valid:
            self.status_label.setText(f"Invalid path: {reason}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
            return
        try:
            path_manager.set_save_directory('spectrum', directory)
            self.spectrum_dir_label.setText(directory)
            self.status_label.setText(f"Spectrum directory set: {directory}")
            self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        except Exception as e:
            self.status_label.setText(f"Error saving directory: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")

    def _load_settings(self):
        try:
            from config import path_manager
            photo_dir = path_manager.get_configured_save_directory('photo')
            if photo_dir:
                self.photo_dir_label.setText(photo_dir)

            spectrum_dir = path_manager.get_configured_save_directory('spectrum')
            if spectrum_dir:
                self.spectrum_dir_label.setText(spectrum_dir)
        except Exception as e:
            logger.error(f"Error loading file settings: {e}")

    def get_photo_save_directory(self):
        dir_text = self.photo_dir_label.text()
        return dir_text if os.path.isdir(dir_text) else None

    def get_spectrum_save_directory(self):
        dir_text = self.spectrum_dir_label.text()
        return dir_text if os.path.isdir(dir_text) else None
