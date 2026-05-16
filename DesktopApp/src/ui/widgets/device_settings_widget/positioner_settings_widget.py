"""
Positioner Settings Widget
Widget for configuring positioner device parameters for wells analysis mode.

This widget provides controls for:
- Position coordinates (X, Y, Z)
- Movement speed
- Position presets
- Home/zero positioning
"""

import requests
import json
from config.api_config import API_BASE_URL
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, 
    QLabel, QSpinBox, QDoubleSpinBox, QPushButton, 
    QGridLayout, QComboBox, QLineEdit, QGroupBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont



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
        
        # Set margins and spacing for better layout
        layout.setContentsMargins(10, 10, 10, 10)  # Add padding around the widget
        layout.setSpacing(10)  # Add spacing between elements
        
        # Position Settings Group
        position_group = QGroupBox("Position Settings")
        position_layout = QGridLayout(position_group)
        position_layout.setContentsMargins(5, 5, 5, 5)  # Add padding inside group
        position_layout.setHorizontalSpacing(10)
        position_layout.setVerticalSpacing(8)
        
        # X Position
        x_label = QLabel("X Position (mm):")
        x_label.setStyleSheet("QLabel { font-weight: bold; }")
        position_layout.addWidget(x_label, 0, 0)
        
        self.x_position = QDoubleSpinBox()
        self.x_position.setRange(-1000.0, 1000.0)
        self.x_position.setValue(0.0)
        self.x_position.setDecimals(2)
        position_layout.addWidget(self.x_position, 0, 1)
        
        # Y Position
        y_label = QLabel("Y Position (mm):")
        y_label.setStyleSheet("QLabel { font-weight: bold; }")
        position_layout.addWidget(y_label, 1, 0)
        
        self.y_position = QDoubleSpinBox()
        self.y_position.setRange(-1000.0, 1000.0)
        self.y_position.setValue(0.0)
        self.y_position.setDecimals(2)
        position_layout.addWidget(self.y_position, 1, 1)
        
        # Z Position
        z_label = QLabel("Z Position (mm):")
        z_label.setStyleSheet("QLabel { font-weight: bold; }")
        position_layout.addWidget(z_label, 2, 0)
        
        self.z_position = QDoubleSpinBox()
        self.z_position.setRange(-1000.0, 1000.0)
        self.z_position.setValue(0.0)
        self.z_position.setDecimals(2)
        position_layout.addWidget(self.z_position, 2, 1)
        
        layout.addWidget(position_group)
        
        # Movement Settings Group
        movement_group = QGroupBox("Movement Settings")
        movement_layout = QGridLayout(movement_group)
        movement_layout.setContentsMargins(5, 5, 5, 5)  # Add padding inside group
        movement_layout.setHorizontalSpacing(10)
        movement_layout.setVerticalSpacing(8)
        
        # Movement Speed
        speed_label = QLabel("Speed (mm/s):")
        speed_label.setStyleSheet("QLabel { font-weight: bold; }")
        movement_layout.addWidget(speed_label, 0, 0)
        
        self.movement_speed = QDoubleSpinBox()
        self.movement_speed.setRange(0.1, 100.0)
        self.movement_speed.setValue(10.0)
        self.movement_speed.setDecimals(1)
        movement_layout.addWidget(self.movement_speed, 0, 1)
        
        # Acceleration
        accel_label = QLabel("Acceleration (mm/s²):")
        accel_label.setStyleSheet("QLabel { font-weight: bold; }")
        movement_layout.addWidget(accel_label, 1, 0)
        
        self.acceleration = QDoubleSpinBox()
        self.acceleration.setRange(0.1, 1000.0)
        self.acceleration.setValue(100.0)
        self.acceleration.setDecimals(1)
        movement_layout.addWidget(self.acceleration, 1, 1)
        
        layout.addWidget(movement_group)
        
        # Position Presets
        presets_group = QGroupBox("Position Presets")
        presets_layout = QGridLayout(presets_group)
        presets_layout.setContentsMargins(5, 5, 5, 5)  # Add padding inside group
        presets_layout.setHorizontalSpacing(10)
        presets_layout.setVerticalSpacing(8)
        
        # Preset selection
        preset_label = QLabel("Presets:")
        preset_label.setStyleSheet("QLabel { font-weight: bold; }")
        presets_layout.addWidget(preset_label, 0, 0)
        
        self.preset_combo = QComboBox()
        self.preset_combo.addItems([
            'Home Position',
            'Well A1',
            'Well H12',
            'Focus Point',
            'Custom 1',
            'Custom 2'
        ])
        presets_layout.addWidget(self.preset_combo, 0, 1)
        
        layout.addWidget(presets_group)
        
        # Control Buttons - organize in rows with max 3 buttons per row
        button_row1_layout = QHBoxLayout()
        button_row2_layout = QHBoxLayout()
        
        self.btn_refresh = QPushButton(self.interface_text.refresh() if self.interface_text else "Refresh")
        self.btn_home = QPushButton("Go Home")
        self.btn_move_to = QPushButton("Move To")
        self.btn_save_preset = QPushButton("Save Preset")
        self.btn_apply = QPushButton(self.interface_text.apply() if self.interface_text else "Apply")
        
        # First row: Refresh, Go Home, Move To (3 buttons)
        button_row1_layout.addWidget(self.btn_refresh)
        button_row1_layout.addWidget(self.btn_home)
        button_row1_layout.addWidget(self.btn_move_to)
        button_row1_layout.addStretch()  # Push buttons to left
        
        # Second row: Save Preset, Apply (2 buttons)
        button_row2_layout.addWidget(self.btn_save_preset)
        button_row2_layout.addWidget(self.btn_apply)
        button_row2_layout.addStretch()  # Push buttons to left
        
        layout.addLayout(button_row1_layout)
        layout.addLayout(button_row2_layout)
        
        # Status label
        self.status_label = QLabel("Ready")
        self.status_label.setStyleSheet("QLabel { color: green; font-weight: bold; }")
        self.status_label.setWordWrap(True)
        self.status_label.setMaximumWidth(300)  # Prevent screen stretching
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
        self.status_label.setText("Loading positioner settings...")
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
        
        self.status_label.setText("Positioner settings loaded (placeholder)")
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
        self.status_label.setText("Applying positioner settings...")
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
        self.status_label.setText("Positioner settings applied locally")
        self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
        
        # Emit signal that settings were updated
        self.settings_updated.emit()
    
    def go_home(self):
        """Move positioner to home position."""
        self.status_label.setText("Moving to home position...")
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        
        # Reset all positions to zero
        self.x_position.setValue(0.0)
        self.y_position.setValue(0.0)
        self.z_position.setValue(0.0)
        
        self.status_label.setText("Positioner moved to home (simulated)")
        self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
    
    def move_to_position(self):
        """Move positioner to current target position."""
        self.status_label.setText("Moving to position...")
        self.status_label.setStyleSheet("QLabel { color: blue; font-weight: bold; }")
        
        x = self.x_position.value()
        y = self.y_position.value()
        z = self.z_position.value()
        
        self.status_label.setText(f"Moved to position: X={x:.2f}, Y={y:.2f}, Z={z:.2f} (simulated)")
        self.status_label.setStyleSheet("QLabel { color: orange; font-weight: bold; }")
    
    def save_preset(self):
        """Save current position as a preset."""
        preset_name = self.preset_combo.currentText()
        
        # For now, just show status message
        self.status_label.setText(f"Position saved as preset: {preset_name} (simulated)")
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
                thread.wait(1000)  # Wait up to 1 second for thread to finish
        self.active_threads.clear()
        super().closeEvent(event)
