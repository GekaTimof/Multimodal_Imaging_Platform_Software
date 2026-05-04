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

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap
from DesktopApp.threads.camera_thread import CameraThread
from DesktopApp.objects.Interface_text import Interface_text
from DesktopApp.services.save_photo import save_photo
from DesktopApp.services.directory_control import get_home_directory
from DesktopApp.widgets.device_settings_widget.device_settings_widgets import DeviceSettingsWidget
import os
import json


class CameraTab(QWidget):
    """
    Camera control tab with video streaming and image capture capabilities.
    
    Provides interface for:
    - Video stream display
    - Camera start/stop controls
    - Image capture and saving
    - Camera parameter settings
    """
    
    DEFAULT_STREAM_URL = "http://10.43.70.189:8080/video"

    def __init__(self, interface_text: Interface_text):
        """
        Initialize camera tab with interface text.
        
        Args:
            interface_text (Interface_text): Text manager for UI labels
        """
        super().__init__()

        self.interface_text = interface_text  # Store reference to interface_text

        # Video label (left side)
        self.video_label = QLabel(interface_text.no_video())
        self.video_label.setMinimumSize(640, 480)
        self.video_label.setAlignment(Qt.AlignCenter)

        # Control panel (right side)
        self.start_button = QPushButton(interface_text.start_camera())
        self.stop_button = QPushButton(interface_text.stop_camera())
        self.select_folder_button = QPushButton(interface_text.select_save_directory())
        self.save_image_button = QPushButton(interface_text.save_image())
        self.save_folder_label = QLabel(interface_text.no_folder_selected())
        self.status_label = QLabel("")
        self.status_label.setWordWrap(True)

        # Load initial settings
        self.camera_source = self.load_camera_source()
        self.current_frame = None
        self.thread = None

        # Upper control panel (basic camera controls)
        upper_control_layout = QVBoxLayout()
        upper_control_layout.addWidget(self.start_button)
        upper_control_layout.addWidget(self.stop_button)
        upper_control_layout.addWidget(QLabel(f"Stream URL: {self.camera_source}"))
        upper_control_layout.addWidget(self.select_folder_button)
        upper_control_layout.addWidget(self.save_folder_label)
        upper_control_layout.addWidget(self.save_image_button)
        upper_control_layout.addWidget(self.status_label)
        upper_control_layout.addStretch()  # Push buttons to top

        # Lower panel with device settings (tabbed interface)
        self.device_settings_widget = DeviceSettingsWidget()

        # Right panel layout (split into upper and lower parts)
        right_panel_layout = QVBoxLayout()
        right_panel_layout.addLayout(upper_control_layout, 1)  # Upper part takes 1/3 space
        right_panel_layout.addWidget(self.device_settings_widget, 2)  # Lower part takes 2/3 space

        # Main horizontal layout (4:1 ratio)
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.video_label, 4)  # Stretch factor 4 for video
        main_layout.addLayout(right_panel_layout, 1)    # Stretch factor 1 for controls

        # Connect settings updated signal
        self.device_settings_widget.settings_updated.connect(self.on_settings_updated)

        # Connect signals
        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)
        self.select_folder_button.clicked.connect(self.select_save_folder)
        self.save_image_button.clicked.connect(self.save_current_image)

    def start_camera(self):
        if self.thread is not None and self.thread.isRunning():
            return

        self.thread = CameraThread(self.camera_source)
        self.thread.frame_ready.connect(self.update_frame)
        self.thread.status_ready.connect(self.on_camera_status)
        self.thread.start()
        
        # Load and apply database settings after camera starts
        def apply_db_settings():
            if self.thread and self.thread.cap:
                settings = self.thread.load_camera_settings()
                if settings:
                    self.thread.apply_camera_settings(settings)
        
        # Wait a moment for camera to initialize, then apply settings
        from PyQt5.QtCore import QTimer
        QTimer.singleShot(1000, apply_db_settings)
        
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def on_camera_status(self, message):
        """Handle camera status messages."""
        self.status_label.setText(message)
        print(f"Camera status: {message}")

    def on_camera_stopped(self):
        self.thread = None

    def update_frame(self, image):
        self.current_frame = image
        self.video_label.setPixmap(QPixmap.fromImage(image))

    def stop_camera(self):
        if self.thread is None:
            return
        
        self.status_label.setText("Stopping camera...")
        
        # Stop the thread
        self.thread.stop()
        
        # Wait for thread to finish
        if self.thread.isRunning():
            if not self.thread.wait(3000):  # Wait up to 3 seconds
                self.status_label.setText("Force terminating camera...")
                self.thread.terminate()  # Force terminate if not stopping
                self.thread.wait(1000)   # Additional wait for termination
        
        self.thread = None
        self.status_label.setText("Camera stopped")
        
        # Re-enable start button and disable stop button
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def select_save_folder(self):
        home_dir = get_home_directory()

        options = QFileDialog.Option.DontUseNativeDialog
        options |= QFileDialog.Option.ReadOnly

        current_directory = self.save_folder_label.text() if os.path.isdir(self.save_folder_label.text()) else home_dir

        directory = QFileDialog.getExistingDirectory(self, self.interface_text.select_save_directory(),
                                                     current_directory, options)
        if directory:
            if not directory.startswith(home_dir):
                QMessageBox.warning(self, self.interface_text.warning_title(),
                                    self.interface_text.warning_select_out_of_home())
                return

            self.save_folder_label.setText(directory)
            self.save_settings({"photo": {"save_directory": directory}})

    def save_current_image(self):
        if self.current_frame is None:
            return
        try:
            saved_path = save_photo(self.current_frame)
            print(f"Image saved to: {saved_path}")
        except Exception as e:
            print(f"Error saving image: {e}")

    def on_settings_updated(self):
        """Handle settings updated event - restart camera with new settings from database."""
        print("Settings updated, restarting camera with new database settings...")
        
        # Stop current camera if running
        if self.thread is not None and self.thread.isRunning():
            self.stop_camera()
        
        # Wait a moment for camera to stop
        import time
        time.sleep(0.5)
        
        # Restart camera - it will load settings from database automatically
        self.start_camera()

    def load_save_folder(self):
        settings_path = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            save_dir = settings.get('photo', {}).get('save_directory', '')
            if save_dir:
                self.save_folder_label.setText(save_dir)
        except (FileNotFoundError, json.JSONDecodeError):
            pass

    def load_camera_source(self):
        settings_path = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            return settings.get('camera', {}).get('stream_url', self.DEFAULT_STREAM_URL)
        except (FileNotFoundError, json.JSONDecodeError):
            return self.DEFAULT_STREAM_URL

    def save_settings(self, updates):
        settings_path = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            settings = {}

        def merge_dict(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    merge_dict(target[key], value)
                else:
                    target[key] = value

        merge_dict(settings, updates)

        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)


    # TODO добавить получение и отображение видео из потока с Raspberry Pi

    # TODO заменить комадны на отправку команды на API для управления камерой на Raspberry Pi, а не управление камерой напрямую из приложения
