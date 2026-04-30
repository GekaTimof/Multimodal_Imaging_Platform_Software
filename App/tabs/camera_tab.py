from PyQt5.QtWidgets import QWidget, QLabel, QPushButton, QVBoxLayout, QHBoxLayout, QFileDialog, QMessageBox
from PyQt5.QtGui import QPixmap
from App.threads.camera_thread import CameraThread
from App.obects.Interface_text import Interface_text
from App.services.save_photo import save_photo
from App.services.directory_control import is_directory_allowed, get_home_directory
import os
import json

class CameraTab(QWidget):
    def __init__(self, interface_text: Interface_text):
        super().__init__()

        self.interface_text = interface_text  # Store reference to interface_text

        # Video label (left side)
        self.video_label = QLabel(interface_text.no_video())
        self.video_label.setMinimumSize(640, 480)

        # Control panel (right side)
        self.start_button = QPushButton(interface_text.start_camera())
        self.stop_button = QPushButton(interface_text.stop_camera())
        self.select_folder_button = QPushButton(interface_text.select_save_directory())
        self.save_image_button = QPushButton(interface_text.save_image())
        self.save_folder_label = QLabel(interface_text.no_folder_selected())

        # Right panel layout
        control_layout = QVBoxLayout()
        control_layout.addWidget(self.start_button)
        control_layout.addWidget(self.stop_button)
        control_layout.addWidget(self.select_folder_button)
        control_layout.addWidget(self.save_folder_label)
        control_layout.addWidget(self.save_image_button)
        control_layout.addStretch()  # Push buttons to top

        # Main horizontal layout (4:1 ratio)
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.video_label, 4)  # Stretch factor 4
        main_layout.addLayout(control_layout, 1)    # Stretch factor 1

        # Camera thread
        self.thread = CameraThread()
        self.thread.frame_ready.connect(self.update_frame)

        # Current frame storage
        self.current_frame = None

        # Load initial save folder from settings
        self.load_save_folder()

        # Connect signals
        self.start_button.clicked.connect(self.thread.start)
        self.stop_button.clicked.connect(self.stop_camera)
        self.select_folder_button.clicked.connect(self.select_save_folder)
        self.save_image_button.clicked.connect(self.save_current_image)

    def update_frame(self, image):
        self.current_frame = image
        self.video_label.setPixmap(QPixmap.fromImage(image))

    def stop_camera(self):
        self.thread.stop()
        self.thread.wait()

    def select_save_folder(self):
        # get home directory of user in whose directory the program is located
        home_dir = get_home_directory()

        options = QFileDialog.Option.DontUseNativeDialog
        options |= QFileDialog.Option.ReadOnly

        # if user already select directory we will set it to selection field, if not select, we will set home directory
        current_directory = self.save_folder_label.text() if os.path.isdir(self.save_folder_label.text()) else home_dir

        directory = QFileDialog.getExistingDirectory(self, self.interface_text.select_save_directory(),
                                                     current_directory, options)
        if directory:
            # check that user try to select folder in home directory
            if not directory.startswith(home_dir):
                QMessageBox.warning(self, self.interface_text.warning_title(),
                                    self.interface_text.warning_select_out_of_home())
                return

            self.save_folder_label.setText(directory)
            self.save_settings({"photo": {"save_directory": directory}})

    def save_current_image(self):
        if self.current_frame is None:
            return  # No frame to save
        try:
            saved_path = save_photo(self.current_frame)
            print(f"Image saved to: {saved_path}")
        except Exception as e:
            print(f"Error saving image: {e}")

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

    def save_settings(self, updates):
        settings_path = os.path.join(os.path.dirname(__file__), '..', 'settings.json')
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError):
            settings = {}

        # Deep merge updates
        def merge_dict(target, source):
            for key, value in source.items():
                if isinstance(value, dict) and key in target and isinstance(target[key], dict):
                    merge_dict(target[key], value)
                else:
                    target[key] = value

        merge_dict(settings, updates)

        with open(settings_path, 'w', encoding='utf-8') as f:
            json.dump(settings, f, indent=4)