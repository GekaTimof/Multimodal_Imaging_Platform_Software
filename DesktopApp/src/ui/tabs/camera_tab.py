"""
Camera Tab Interface
Provides camera control functionality including video streaming, image capture, and device settings.

Features:
- Video stream display from IP camera
- Start/stop camera controls
- Image capture and saving
- Camera parameter configuration
- Save directory management
"""

import json
import logging
import os
import time
from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton, QScrollArea, QVBoxLayout, QWidget

from config.api_config import CAMERA_STREAM_URL
from core.constants.camera_constants import DEFAULT_CAMERA_SLOT
from core.constants.ui_strings import CameraTabStrings
from models.objects.Interface_text import Interface_text
from services.save_photo import save_photo
from core.threads.camera_thread import CameraThread
from ui.widgets.device_settings_widget.device_settings_widgets import DeviceSettingsWidget

logger = logging.getLogger(__name__)


class CameraTab(QWidget):
    """
    Camera control tab with video streaming and image capture capabilities.
    
    Provides interface for:
    - Video stream display
    - Camera start/stop controls
    - Image capture and saving
    - Camera parameter settings
    """

    def __init__(self, interface_text: Interface_text):
        """
        Initialize camera tab with interface text.
        
        Args:
            interface_text (Interface_text): Text manager for UI labels
        """
        super().__init__()

        self.interface_text = interface_text  # Store reference to interface_text
        self.camera_source = self.load_camera_source()
        self.current_frame = None
        self.thread: Optional[CameraThread] = None
        self.current_settings_slot = DEFAULT_CAMERA_SLOT  # Default to slot 0 (Basic)
        
        # Video label (left side)
        self.video_label = QLabel(interface_text.no_video())
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("QLabel { background-color: black; color: white; }")

        # Control panel (right side)
        self.start_button = QPushButton(interface_text.start_camera())
        self.stop_button = QPushButton(interface_text.stop_camera())
        self.save_image_button = QPushButton(interface_text.save_image())
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

        # Upper control panel (basic camera controls) with scroll
        upper_control_layout = QVBoxLayout()
        upper_control_layout.addWidget(self.start_button)
        upper_control_layout.addWidget(self.stop_button)
        upper_control_layout.addWidget(QLabel(f"Stream URL: {self.camera_source}"))
        upper_control_layout.addWidget(self.save_image_button)
        upper_control_layout.addWidget(self.status_label)
        upper_control_layout.addStretch()  # Push buttons to top
        
        # Create scroll area for upper controls
        upper_scroll_area = QScrollArea()
        upper_scroll_area.setWidgetResizable(True)
        upper_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        upper_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        
        upper_widget = QWidget()
        upper_widget.setLayout(upper_control_layout)
        upper_scroll_area.setWidget(upper_widget)

        # Lower panel with device settings (tabbed interface) with scroll
        self.device_settings_widget = DeviceSettingsWidget(self.interface_text)
        
        # Create scroll area for device settings
        lower_scroll_area = QScrollArea()
        lower_scroll_area.setWidgetResizable(True)
        lower_scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        lower_scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        lower_scroll_area.setWidget(self.device_settings_widget)

        # Right panel layout (split into upper and lower parts with 2:3 ratio)
        right_panel_layout = QVBoxLayout()
        right_panel_layout.addWidget(upper_scroll_area, 2)  # Upper part takes 2/5 space
        right_panel_layout.addWidget(lower_scroll_area, 3)  # Lower part takes 3/5 space

        # Main horizontal layout (3:1 ratio - more space for video)
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.video_label, 3)  # Stretch factor 3 for video
        main_layout.addLayout(right_panel_layout, 1)    # Stretch factor 1 for controls

        # Connect settings updated signal
        self.device_settings_widget.settings_updated.connect(self.on_settings_updated)
        
        # Connect slot changed signal
        self.device_settings_widget.camera_tab.slot_changed.connect(self.set_current_settings_slot)

        # Connect signals
        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)
        self.save_image_button.clicked.connect(self.save_current_image)

    def start_camera(self):
        if self.thread is not None and self.thread.isRunning():
            return

        self.thread = CameraThread(self.camera_source)
        self.thread.frame_ready.connect(self.update_frame)
        self.thread.status_ready.connect(self.on_camera_status)
        self.thread.start()
        
        # Load and apply camera settings after camera starts
        def apply_camera_settings():
            if self.thread and self.thread.cap:
                settings = self.thread.load_camera_settings(self.current_settings_slot)
                if settings:
                    self.thread.apply_camera_settings(settings)
        
        # Wait a moment for camera to initialize, then apply settings
        QTimer.singleShot(1000, apply_camera_settings)
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def on_camera_status(self, message: str) -> None:
        """Handle camera status messages."""
        self.status_label.setText(message)
        logger.info(f"Camera status: {message}")

    def on_camera_stopped(self) -> None:
        """Handle camera stopped event."""
        self.thread = None

    def update_frame(self, image) -> None:
        """Update video display with new frame."""
        self.current_frame = image
        # Scale image to fit the video label size while maintaining aspect ratio
        pixmap = QPixmap.fromImage(image)
        scaled_pixmap = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled_pixmap)

    def stop_camera(self) -> None:
        """Stop the camera thread and clean up resources."""
        if self.thread is None:
            return
        
        self.status_label.setText(CameraTabStrings.STOPPING_CAMERA)
        
        # Stop the thread
        self.thread.stop()
        
        # Wait for thread to finish
        if self.thread.isRunning():
            if not self.thread.wait(3000):  # Wait up to 3 seconds
                self.status_label.setText(CameraTabStrings.FORCE_TERMINATING)
                logger.warning("Force terminating camera thread")
                self.thread.terminate()  # Force terminate if not stopping
                self.thread.wait(1000)   # Additional wait for termination
        
        self.thread = None
        self.status_label.setText(CameraTabStrings.CAMERA_STOPPED)
        
        # Re-enable start button and disable stop button
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def save_current_image(self) -> None:
        """Save the current camera frame to disk."""
        if self.current_frame is None:
            return
        try:
            # Get save directory from FileSettingsWidget
            photo_dir = self.device_settings_widget.file_tab.get_photo_save_directory()
            if photo_dir:
                saved_path = save_photo(self.current_frame, photo_dir)
            else:
                saved_path = save_photo(self.current_frame)  # Fallback to default
            logger.info(f"Image saved to: {saved_path}")
            self.status_label.setText(CameraTabStrings.IMAGE_SAVED.format(os.path.basename(saved_path)))
        except Exception as e:
            logger.error(f"Error saving image: {e}")
            self.status_label.setText(CameraTabStrings.ERROR_SAVING_IMAGE.format(str(e)))

    def on_settings_updated(self) -> None:
        """Handle settings updated event - restart camera with new settings from API."""
        logger.info("Settings updated, restarting camera with new settings...")
        
        # Stop current camera if running
        if self.thread is not None and self.thread.isRunning():
            self.stop_camera()
        
        # Wait a moment for camera to stop
        time.sleep(0.5)
        
        # Restart camera - it will load settings from API automatically
        self.start_camera()
    
    def set_current_settings_slot(self, slot_id: int) -> None:
        """Set the current settings slot and restart camera if needed."""
        self.current_settings_slot = slot_id
        logger.info(f"Switched to settings slot {slot_id}")
        
        # If camera is running, restart it with new slot settings
        if self.thread is not None and self.thread.isRunning():
            self.stop_camera()
            time.sleep(0.5)
            self.start_camera()

    def load_camera_source(self) -> str:
        """Load camera stream URL from settings file."""
        settings_path = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            return settings.get('camera', {}).get('stream_url', CAMERA_STREAM_URL)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            logger.warning(f"Could not load settings from {settings_path}: {e}")
            return CAMERA_STREAM_URL


    # Future enhancement: Add video stream reception from Raspberry Pi
    # Future enhancement: Replace direct camera control with API commands to Raspberry Pi
