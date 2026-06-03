"""
Positioner Settings Widget
Widget for configuring positioner device parameters for Acquisition analysis mode.

This widget provides controls for:
- Position coordinates (X, Y, Z)
- Movement speed
- Position presets
- Home/zero positioning
"""

import logging

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout,
    QLabel, QDoubleSpinBox, QPushButton,
    QGridLayout, QComboBox
)
from PyQt5.QtCore import pyqtSignal

from config.api_config import API_BASE_URL
from core.constants.camera_constants import THREAD_TIMEOUT_MS
from ui.ui_utils import get_relative_margin

logger = logging.getLogger(__name__)


class PositionerSettingsWidget(QWidget):
    """Widget for positioner settings configuration."""
    
    # Signal emitted when settings are updated
    settings_updated = pyqtSignal()
    
    def __init__(self, interface_text=None):
        super().__init__()
        self.interface_text = interface_text
        self.api_base_url = API_BASE_URL
        self.current_settings = {}
        self.active_threads = []  # Track active threads
        self._build_ui()
        # Load default settings on startup
        self.load_settings()
    
    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(
            get_relative_margin(0.9), get_relative_margin(0.9),
            get_relative_margin(0.9), get_relative_margin(0.9)
        )
        layout.setSpacing(get_relative_margin(0.9))

        settings_layout = QGridLayout()
        settings_layout.setContentsMargins(
            get_relative_margin(0.5), get_relative_margin(0.5),
            get_relative_margin(0.5), get_relative_margin(0.5)
        )
        settings_layout.setHorizontalSpacing(get_relative_margin(0.9))
        settings_layout.setVerticalSpacing(get_relative_margin(0.7))

        row = 0

        # X Position
        x_label = QLabel(self.interface_text.x_position() if self.interface_text else "X Position (mm):")
        x_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(x_label, row, 0, 1, 2)
        row += 1
        self.x_position = QDoubleSpinBox()
        self.x_position.setRange(-1000.0, 1000.0)
        self.x_position.setValue(0.0)
        self.x_position.setDecimals(2)
        settings_layout.addWidget(self.x_position, row, 0, 1, 2)
        row += 1

        # Y Position
        y_label = QLabel(self.interface_text.y_position() if self.interface_text else "Y Position (mm):")
        y_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(y_label, row, 0, 1, 2)
        row += 1
        self.y_position = QDoubleSpinBox()
        self.y_position.setRange(-1000.0, 1000.0)
        self.y_position.setValue(0.0)
        self.y_position.setDecimals(2)
        settings_layout.addWidget(self.y_position, row, 0, 1, 2)
        row += 1

        # Z Position
        z_label = QLabel(self.interface_text.z_position() if self.interface_text else "Z Position (mm):")
        z_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(z_label, row, 0, 1, 2)
        row += 1
        self.z_position = QDoubleSpinBox()
        self.z_position.setRange(-1000.0, 1000.0)
        self.z_position.setValue(0.0)
        self.z_position.setDecimals(2)
        settings_layout.addWidget(self.z_position, row, 0, 1, 2)
        row += 1

        # Movement Speed
        speed_label = QLabel(self.interface_text.speed() if self.interface_text else "Speed (mm/s):")
        speed_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(speed_label, row, 0, 1, 2)
        row += 1
        self.movement_speed = QDoubleSpinBox()
        self.movement_speed.setRange(0.1, 100.0)
        self.movement_speed.setValue(10.0)
        self.movement_speed.setDecimals(1)
        settings_layout.addWidget(self.movement_speed, row, 0, 1, 2)
        row += 1

        # Acceleration
        accel_label = QLabel(self.interface_text.acceleration() if self.interface_text else "Acceleration (mm/s²):")
        accel_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(accel_label, row, 0, 1, 2)
        row += 1
        self.acceleration = QDoubleSpinBox()
        self.acceleration.setRange(0.1, 1000.0)
        self.acceleration.setValue(100.0)
        self.acceleration.setDecimals(1)
        settings_layout.addWidget(self.acceleration, row, 0, 1, 2)
        row += 1

        # Presets
        preset_label = QLabel(self.interface_text.presets() if self.interface_text else "Presets:")
        preset_label.setStyleSheet("QLabel { font-weight: bold; }")
        settings_layout.addWidget(preset_label, row, 0, 1, 2)
        row += 1
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            'Home Position',
            'Well A1',
            'Well H12',
            'Focus Point',
            'Custom 1',
            'Custom 2'
        ])
        settings_layout.addWidget(self.preset_combo, row, 0, 1, 2)
        row += 1

        layout.addLayout(settings_layout)

        # Buttons
        button_row1_layout = QHBoxLayout()
        button_row2_layout = QHBoxLayout()

        self.btn_refresh = QPushButton(self.interface_text.refresh() if self.interface_text else "Refresh")
        self.btn_home = QPushButton(self.interface_text.go_home() if self.interface_text else "Go Home")
        self.btn_move_to = QPushButton(self.interface_text.move_to() if self.interface_text else "Move To")
        self.btn_save_preset = QPushButton(self.interface_text.save_preset() if self.interface_text else "Save Preset")
        self.btn_apply = QPushButton(self.interface_text.apply() if self.interface_text else "Apply")

        button_row1_layout.addWidget(self.btn_refresh)
        button_row1_layout.addWidget(self.btn_home)
        button_row1_layout.addWidget(self.btn_move_to)
        button_row1_layout.addStretch()

        button_row2_layout.addWidget(self.btn_save_preset)
        button_row2_layout.addWidget(self.btn_apply)
        button_row2_layout.addStretch()

        layout.addLayout(button_row1_layout)
        layout.addLayout(button_row2_layout)

        # Status label
        self.status_label = QLabel(self.interface_text.ready() if self.interface_text else "Ready")
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        self.status_label.setWordWrap(True)
        self.status_label.setMaximumWidth(300)
        layout.addWidget(self.status_label)

        layout.addStretch()

        # Connect signals
        self.btn_refresh.clicked.connect(self.load_settings)
        self.btn_home.clicked.connect(self.go_home)
        self.btn_move_to.clicked.connect(self.move_to_position)
        self.btn_save_preset.clicked.connect(self.save_preset)
        self.btn_apply.clicked.connect(self.apply_settings)
    
    def load_settings(self):
        """Load current positioner settings from API."""
        self.status_label.setText(self.interface_text.loading_positioner_settings() if self.interface_text else "Loading positioner settings...")
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        
        # For now, use placeholder logic since positioner API might not exist yet
        self._load_placeholder_settings()
    
    def _load_placeholder_settings(self):
        """Load placeholder settings until positioner API is implemented."""
        # Simulate loading with placeholder values
        placeholder_settings = {
            'XPosition': 0.0,
            'YPosition': 0.0,
            'ZPosition': 0.0,
            'MovementSpeed': 10.0,
            'Acceleration': 100.0
        }
        
        self.current_settings = placeholder_settings
        self._update_ui_from_settings(placeholder_settings)
        
        status = self.interface_text.positioner_settings_loaded() if self.interface_text else "Positioner settings loaded (placeholder)"
        self.status_label.setText(status)
        self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
    
    def _update_ui_from_settings(self, settings):
        """Update UI controls from settings dictionary."""
        try:
            self.x_position.setValue(float(settings.get('XPosition', 0.0)))
            self.y_position.setValue(float(settings.get('YPosition', 0.0)))
            self.z_position.setValue(float(settings.get('ZPosition', 0.0)))
            self.movement_speed.setValue(float(settings.get('MovementSpeed', 10.0)))
            self.acceleration.setValue(float(settings.get('Acceleration', 100.0)))
            
        except Exception as e:
            self.status_label.setText(f"Error updating UI: {str(e)}")
            self.status_label.setStyleSheet("QLabel { color: red; font-weight: bold; }")
    
    def apply_settings(self):
        """Apply current positioner settings."""
        status = self.interface_text.applying_positioner_settings() if self.interface_text else "Applying positioner settings..."
        self.status_label.setText(status)
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        
        # Collect current settings
        settings = {
            'XPosition': self.x_position.value(),
            'YPosition': self.y_position.value(),
            'ZPosition': self.z_position.value(),
            'MovementSpeed': self.movement_speed.value(),
            'Acceleration': self.acceleration.value()
        }
        
        # For now, just update locally since positioner API might not exist
        self.current_settings = settings
        status = self.interface_text.positioner_settings_applied() if self.interface_text else "Positioner settings applied locally"
        self.status_label.setText(status)
        self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
        
        # Emit signal that settings were updated
        self.settings_updated.emit()
    
    def go_home(self):
        """Move positioner to home position."""
        status = self.interface_text.moving_to_home() if self.interface_text else "Moving to home position..."
        self.status_label.setText(status)
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        
        self.x_position.setValue(0.0)
        self.y_position.setValue(0.0)
        self.z_position.setValue(0.0)
        
        status = self.interface_text.positioner_moved_home() if self.interface_text else "Positioner moved to home (simulated)"
        self.status_label.setText(status)
        self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
    
    def move_to_position(self):
        """Move positioner to current target position."""
        status = self.interface_text.moving_to_position() if self.interface_text else "Moving to position..."
        self.status_label.setText(status)
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        
        x = self.x_position.value()
        y = self.y_position.value()
        z = self.z_position.value()
        
        if self.interface_text:
            status = self.interface_text.moved_to_position().format(x=x, y=y, z=z)
        else:
            status = f"Moved to position: X={x:.2f}, Y={y:.2f}, Z={z:.2f} (simulated)"
        self.status_label.setText(status)
        self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
    
    def save_preset(self):
        """Save current position as a preset."""
        preset_name = self.preset_combo.currentText()
        
        # For now, just show status message
        if self.interface_text:
            status = self.interface_text.position_saved().format(preset_name=preset_name)
        else:
            status = f"Position saved as preset: {preset_name} (simulated)"
        self.status_label.setText(status)
        self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
    
    def _cleanup_thread(self, thread):
        """Remove thread from active threads list when finished."""
        if thread in self.active_threads:
            self.active_threads.remove(thread)
    
    def closeEvent(self, event):
        """Clean up active threads when widget is destroyed."""
        # Terminate all active threads
        for thread in self.active_threads:
            if thread.isRunning():
                thread.terminate()
                thread.wait(THREAD_TIMEOUT_MS)
        self.active_threads.clear()
        super().closeEvent(event)
