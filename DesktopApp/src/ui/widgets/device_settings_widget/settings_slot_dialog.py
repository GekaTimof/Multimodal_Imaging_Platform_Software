"""
Settings Slot Dialog
Dialog for selecting and managing camera settings slots (0-10).
"""

import logging

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import QDialog, QDialogButtonBox, QLabel, QListWidget, QListWidgetItem, QVBoxLayout

from config.api_config import ENDPOINTS
from core.constants.camera_constants import (
    DEFAULT_RESOLUTION_PHOTO, DEFAULT_RESOLUTION_VIDEO, MAX_CAMERA_SLOTS
)
from core.constants.ui_strings import DialogStrings
from .api_client_thread import APIClientThread

logger = logging.getLogger(__name__)


class SettingsSlotDialog(QDialog):
    """Dialog for selecting and managing camera settings slots (0-10).

    Slot 0: Current Session (runtime settings applied to camera)
    Slots 1-10: Saved presets (persistent storage)
    """

    slot_selected = pyqtSignal(int)

    def __init__(self, parent=None, exclude_slot_0=False):
        super().__init__(parent)
        self.setWindowTitle(DialogStrings.CAMERA_SETTINGS_SLOTS)
        self.setModal(True)
        self.resize(800, 900)
        self.slots_data = {}
        self.active_threads = []
        self.exclude_slot_0 = exclude_slot_0
        self._build_ui()

    def showEvent(self, event):
        """Override showEvent to reload slots data each time dialog is shown."""
        super().showEvent(event)
        self._load_slots()

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel(DialogStrings.SELECT_SETTINGS_SLOT)
        title.setStyleSheet("QLabel { font-weight: bold; font-size: 14px; }")
        layout.addWidget(title)

        self.slots_list = QListWidget()
        self.slots_list.itemDoubleClicked.connect(self._on_slot_selected)
        layout.addWidget(self.slots_list)

        button_box = QDialogButtonBox(QDialogButtonBox.Ok | QDialogButtonBox.Cancel)
        button_box.accepted.connect(self._on_ok_clicked)
        button_box.rejected.connect(self.reject)
        layout.addWidget(button_box)

    def _load_slots(self) -> None:
        """Load all settings slots from API."""
        try:
            api_url = ENDPOINTS["camera_settings_slots"]
            thread = APIClientThread('GET', api_url)
            thread.response_received.connect(self._on_slots_loaded)
            thread.finished.connect(lambda: self._cleanup_thread(thread))
            self.active_threads.append(thread)
            thread.start()
        except Exception as e:
            logger.error(f"Error loading slots from API: {e}")
            self._create_fallback_slots()

    def _on_slots_loaded(self, success, message, data):
        """Handle slots loaded response from API."""
        try:
            if success and data.get('success') and 'data' in data:
                self.slots_data = data['data']
                self.slots_list.clear()
                self._load_individual_slot_details(0)
            else:
                logger.warning(f"API error loading slots: {message}")
                self._create_fallback_slots()
        except Exception as e:
            logger.error(f"Error processing slots data: {e}")
            self._create_fallback_slots()

    def _load_individual_slot_details(self, slot_id):
        """Load details for a specific slot via API."""
        if slot_id == 0 and self.exclude_slot_0:
            self._load_individual_slot_details(slot_id + 1)
            return

        if slot_id >= MAX_CAMERA_SLOTS:
            return

        try:
            api_url = ENDPOINTS["camera_settings_slot"].format(slot_id=slot_id)
            thread = APIClientThread('GET', api_url)
            thread.response_received.connect(lambda success, message, data:
                self._on_slot_details_loaded(success, message, data, slot_id))
            thread.finished.connect(lambda: self._cleanup_thread(thread))
            self.active_threads.append(thread)
            thread.start()
        except Exception as e:
            logger.error(f"Error loading slot {slot_id} details: {e}")
            self._load_individual_slot_details(slot_id + 1)

    def _on_slot_details_loaded(self, success, message, data, slot_id):
        """Handle individual slot details loaded from API."""
        try:
            if success and 'id' in data:
                settings = data
                name = settings.get('SettingsName', f"Slot {slot_id}")
                photo_res = settings.get('PhotoResolution', DEFAULT_RESOLUTION_PHOTO)
                video_res = settings.get('VideoResolution', DEFAULT_RESOLUTION_VIDEO)
                exp_time = settings.get('ExposureTime', 0)
                ae_enable = settings.get('AeEnable', True)

                if slot_id == 0:
                    display_text = (f"[CURRENT SESSION] {name}\n"
                                    f"  Photo: {photo_res} | Video: {video_res}\n"
                                    f"  Exposure: {exp_time}μs | Auto-Exp: {'On' if ae_enable else 'Off'}")
                else:
                    display_text = (f"Slot {slot_id} - {name}\n"
                                    f"  Photo: {photo_res} | Video: {video_res}\n"
                                    f"  Exposure: {exp_time}μs | Auto-Exp: {'On' if ae_enable else 'Off'}")

                item = QListWidgetItem(display_text)
                item.setData(Qt.UserRole, slot_id)
                self.slots_list.addItem(item)
            else:
                if slot_id == 0 and self.exclude_slot_0:
                    pass
                elif slot_id == 0:
                    display_text = (f"[CURRENT SESSION] Current Session\n"
                                    f"  Photo: {DEFAULT_RESOLUTION_PHOTO} | Video: {DEFAULT_RESOLUTION_VIDEO}\n"
                                    f"  Active camera settings")
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, slot_id)
                    self.slots_list.addItem(item)
                else:
                    display_text = (f"Slot {slot_id}\n"
                                    f"  Photo: {DEFAULT_RESOLUTION_PHOTO} | Video: {DEFAULT_RESOLUTION_VIDEO}\n"
                                    f"  Empty slot")
                    item = QListWidgetItem(display_text)
                    item.setData(Qt.UserRole, slot_id)
                    self.slots_list.addItem(item)

            last_slot = 10 if self.exclude_slot_0 else 9
            if slot_id < last_slot:
                self._add_separator()

            self._load_individual_slot_details(slot_id + 1)

        except Exception as e:
            logger.error(f"Error processing slot {slot_id} details: {e}")
            self._load_individual_slot_details(slot_id + 1)

    def _add_separator(self):
        """Add a visual separator line to the list."""
        separator = QListWidgetItem("─" * 40)
        separator.setFlags(Qt.NoItemFlags)
        self.slots_list.addItem(separator)

    def _create_fallback_slots(self) -> None:
        """Create fallback slots when API fails."""
        self.slots_list.clear()
        start_slot = 1 if self.exclude_slot_0 else 0
        for slot_id in range(start_slot, MAX_CAMERA_SLOTS):
            display_text = (f"Slot {slot_id}\n"
                            f"  Photo: {DEFAULT_RESOLUTION_PHOTO} | Video: {DEFAULT_RESOLUTION_VIDEO}")
            item = QListWidgetItem(display_text)
            item.setData(Qt.UserRole, slot_id)
            self.slots_list.addItem(item)
            if slot_id < MAX_CAMERA_SLOTS - 1:
                self._add_separator()

    def _on_slot_selected(self, item):
        """Handle slot double-click selection."""
        slot_id = item.data(Qt.UserRole)
        if slot_id is not None:
            self.slot_selected.emit(slot_id)
            self.accept()

    def _on_ok_clicked(self):
        """Handle OK button click."""
        current_item = self.slots_list.currentItem()
        if current_item:
            slot_id = current_item.data(Qt.UserRole)
            if slot_id is not None:
                self.slot_selected.emit(slot_id)
                self.accept()

    def get_selected_slot(self):
        """Get the selected slot ID."""
        current_item = self.slots_list.currentItem()
        if current_item:
            return current_item.data(Qt.UserRole)
        return None

    def _cleanup_thread(self, thread):
        """Remove thread from active threads list when finished."""
        if hasattr(self, 'active_threads') and thread in self.active_threads:
            self.active_threads.remove(thread)
