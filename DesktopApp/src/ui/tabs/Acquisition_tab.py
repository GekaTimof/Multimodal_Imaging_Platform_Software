"""
Acquisition Tab
Combines camera feed with positioner controls.

Layout:
  Left:  camera video display (same pattern as CameraTab)
  Right: camera start/stop/capture + PositionerSettingsWidget (scrollable)
"""

import logging
import os
from typing import Optional

from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QPixmap, QImage
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel,
    QScrollArea, QSizePolicy, QPushButton, QProgressBar, QMessageBox,
)

from config.api_config import CAMERA_STREAM_URL, API_BASE_URL
from config import interface_config
from config.theme_manager import ThemeManager
from models.interface_text import Interface_text
from ui.ui_utils import get_relative_margin
from core.threads.camera_thread import CameraThread
from core.threads.photo_capture_thread import PhotoCaptureThread
from core.constants.camera_constants import (
    DEFAULT_CAMERA_SLOT,
    PHOTO_CAPTURE_PAUSE_OVERHEAD_S,
    PHOTO_CAPTURE_RESUME_OVERHEAD_S,
    PHOTO_CAPTURE_SAFETY_MARGIN_S,
    PHOTO_CAPTURE_FALLBACK_DURATION_MS,
    PHOTO_CAPTURE_FALLBACK_TIMEOUT_S,
    EXPOSURE_THRESHOLD_EXTREME,
    EXPOSURE_THRESHOLD_VERY_LONG,
    EXPOSURE_THRESHOLD_LONG,
    EXPOSURE_THRESHOLD_MEDIUM,
    PHOTO_TIMEOUT_ADDITIONS,
    PHOTO_EXPECTED_ADDITIONS,
)
from services.save_photo import save_photo
from ui.widgets.device_settings_widget.positioner_settings_widget import PositionerSettingsWidget

logger = logging.getLogger(__name__)


class AcquisitionTab(QWidget):
    """Acquisition tab: camera video + positioner controls."""

    def __init__(self, interface_text: Interface_text, theme_manager: ThemeManager = None):
        super().__init__()
        self.interface_text = interface_text
        self.camera_source = CAMERA_STREAM_URL
        self.current_frame: Optional[QImage] = None
        self.thread: Optional[CameraThread] = None
        self.photo_thread: Optional[PhotoCaptureThread] = None
        self._progress_timer: Optional[QTimer] = None
        self._progress_elapsed_ms: int = 0
        self._progress_total_ms: int = 1000

        # ---- Left: camera display ----
        self.video_label = QLabel(interface_text.no_video())
        self.video_label.setAlignment(Qt.AlignCenter)
        self.video_label.setStyleSheet("QLabel { background-color: black; color: white; }")
        self.video_label.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.video_label.setMinimumSize(0, 0)
        self.video_label.setScaledContents(False)

        # ---- Right: camera buttons + positioner ----
        right_inner = QVBoxLayout()
        right_inner.setContentsMargins(
            get_relative_margin(0.4), get_relative_margin(0.4),
            get_relative_margin(2.5), get_relative_margin(0.4),
        )

        # Camera control buttons
        cam_row = QHBoxLayout()
        self.start_button = QPushButton(interface_text.start_camera())
        self.stop_button = QPushButton(interface_text.stop_camera())
        self.capture_button = QPushButton(interface_text.capture_photo())
        cam_row.addWidget(self.start_button)
        cam_row.addWidget(self.stop_button)
        cam_row.addWidget(self.capture_button)
        right_inner.addLayout(cam_row)

        # Progress bar (hidden)
        self.progress_bar = QProgressBar()
        self.progress_bar.setVisible(False)
        right_inner.addWidget(self.progress_bar)

        # Camera status
        self.camera_status = QLabel("")
        self.camera_status.setWordWrap(True)
        right_inner.addWidget(self.camera_status)

        # Positioner controls (takes remaining space)
        self.positioner_widget = PositionerSettingsWidget(interface_text)
        right_inner.addWidget(self.positioner_widget, stretch=1)

        # Wrap in scroll area
        right_widget = QWidget()
        right_widget.setLayout(right_inner)
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        right_scroll.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        right_scroll.setWidget(right_widget)

        right_panel = QWidget()
        right_panel_layout = QVBoxLayout(right_panel)
        right_panel_layout.setContentsMargins(0, 0, 0, 0)
        right_panel_layout.addWidget(right_scroll)
        right_panel.setMinimumWidth(interface_config.get('ui_scaling.side_panel_min_width', 320))
        right_panel.setSizePolicy(QSizePolicy.Fixed, QSizePolicy.Expanding)

        # ---- Main layout ----
        main_layout = QHBoxLayout(self)
        main_layout.addWidget(self.video_label, 1)
        main_layout.addWidget(right_panel)

        # ---- Signals ----
        self.start_button.clicked.connect(self.start_camera)
        self.stop_button.clicked.connect(self.stop_camera)
        self.capture_button.clicked.connect(self.save_current_image)

    # ------------------------------------------------------------------
    # Camera
    # ------------------------------------------------------------------

    def start_camera(self):
        if self.thread is not None and self.thread.isRunning():
            return
        self.thread = CameraThread(self.camera_source)
        self.thread.frame_ready.connect(self.update_frame)
        self.thread.status_ready.connect(self._on_camera_status)
        self.thread.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)

    def _on_camera_status(self, message: str):
        self.camera_status.setText(message)

    def update_frame(self, image: QImage):
        self.current_frame = image
        pixmap = QPixmap.fromImage(image)
        scaled = pixmap.scaled(self.video_label.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.video_label.setPixmap(scaled)

    def stop_camera(self):
        if self.thread is None:
            return
        self.camera_status.setText("Stopping camera...")
        self.thread.stop()
        if self.thread.isRunning():
            if not self.thread.wait(3000):
                self.thread.terminate()
                self.thread.wait(1000)
        self.thread = None
        self.camera_status.setText("Camera stopped")
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)

    def clear_display(self):
        self.video_label.clear()
        self.video_label.setText(self.interface_text.no_video() if self.interface_text else "No video")

    # ------------------------------------------------------------------
    # Photo capture (mirrors CameraTab logic)
    # ------------------------------------------------------------------

    _PAUSE_OVERHEAD_S: float = PHOTO_CAPTURE_PAUSE_OVERHEAD_S
    _RESUME_OVERHEAD_S: float = PHOTO_CAPTURE_RESUME_OVERHEAD_S

    @staticmethod
    def _rpicam_still_timeout(exposure_us: int) -> float:
        exposure_sec = exposure_us / 1_000_000
        if exposure_sec >= EXPOSURE_THRESHOLD_EXTREME:
            return exposure_sec + PHOTO_TIMEOUT_ADDITIONS['extreme']
        elif exposure_sec >= EXPOSURE_THRESHOLD_VERY_LONG:
            return exposure_sec + PHOTO_TIMEOUT_ADDITIONS['very_long']
        elif exposure_sec >= EXPOSURE_THRESHOLD_LONG:
            return exposure_sec + PHOTO_TIMEOUT_ADDITIONS['long']
        elif exposure_sec >= EXPOSURE_THRESHOLD_MEDIUM:
            return exposure_sec + PHOTO_TIMEOUT_ADDITIONS['medium']
        else:
            return PHOTO_TIMEOUT_ADDITIONS['short']

    @staticmethod
    def _rpicam_still_expected(exposure_us: int) -> float:
        exposure_sec = exposure_us / 1_000_000
        if exposure_sec >= EXPOSURE_THRESHOLD_EXTREME:
            return exposure_sec + PHOTO_EXPECTED_ADDITIONS['extreme']
        elif exposure_sec >= EXPOSURE_THRESHOLD_VERY_LONG:
            return exposure_sec + PHOTO_EXPECTED_ADDITIONS['very_long']
        elif exposure_sec >= EXPOSURE_THRESHOLD_LONG:
            return exposure_sec + PHOTO_EXPECTED_ADDITIONS['long']
        elif exposure_sec >= EXPOSURE_THRESHOLD_MEDIUM:
            return exposure_sec + PHOTO_EXPECTED_ADDITIONS['medium']
        else:
            return PHOTO_EXPECTED_ADDITIONS['short']

    def _get_expected_capture_duration_ms(self) -> tuple:
        import requests
        try:
            api_url = f"{API_BASE_URL}/settings/camera"
            response = requests.get(api_url, timeout=5)
            if response.status_code == 200:
                settings = response.json()
                from core.constants.camera_constants import DEFAULT_EXPOSURE_TIME
                exposure_us = int(settings.get("ExposureTime", DEFAULT_EXPOSURE_TIME))
                ae_enable = settings.get("AeEnable", True)
                if ae_enable:
                    exposure_us = DEFAULT_EXPOSURE_TIME
                still_expected_s = self._rpicam_still_expected(exposure_us)
                still_timeout_s = self._rpicam_still_timeout(exposure_us)
                total_s = self._PAUSE_OVERHEAD_S + still_expected_s + self._RESUME_OVERHEAD_S
                http_timeout_s = (
                    self._PAUSE_OVERHEAD_S + still_timeout_s + self._RESUME_OVERHEAD_S
                    + PHOTO_CAPTURE_SAFETY_MARGIN_S
                )
                return int(total_s * 1000), http_timeout_s
        except Exception as e:
            logger.warning(f"Could not fetch exposure for progress estimate: {e}")
        return PHOTO_CAPTURE_FALLBACK_DURATION_MS, PHOTO_CAPTURE_FALLBACK_TIMEOUT_S

    def save_current_image(self):
        if self.photo_thread is not None and self.photo_thread.isRunning():
            return
        self._progress_total_ms, http_timeout_s = self._get_expected_capture_duration_ms()
        self._progress_elapsed_ms = 0
        self.capture_button.setEnabled(False)
        self.progress_bar.setVisible(True)
        self.progress_bar.setValue(0)
        self.camera_status.setText("Capturing photo...")
        self._progress_timer = QTimer(self)
        self._progress_timer.setInterval(200)
        self._progress_timer.timeout.connect(self._advance_progress)
        self._progress_timer.start()
        self.photo_thread = PhotoCaptureThread(timeout=http_timeout_s)
        self.photo_thread.finished.connect(self._on_photo_captured)
        self.photo_thread.failed.connect(self._on_photo_failed)
        self.photo_thread.start()

    def _advance_progress(self):
        self._progress_elapsed_ms += 200
        pct = min(95, int(self._progress_elapsed_ms * 95 / self._progress_total_ms))
        self.progress_bar.setValue(pct)

    def _stop_progress_timer(self):
        if self._progress_timer is not None:
            self._progress_timer.stop()
            self._progress_timer.deleteLater()
            self._progress_timer = None

    def _on_photo_captured(self, image: QImage, photo_info: dict):
        self._stop_progress_timer()
        # Save to default pictures folder
        photo_dir = os.path.expanduser("~/Pictures")
        os.makedirs(photo_dir, exist_ok=True)
        try:
            saved_path = save_photo(image, photo_dir)
        except (ValueError, RuntimeError) as e:
            logger.error(f"Failed to save photo: {e}")
            self.camera_status.setText(f"Error: {e}")
            self.progress_bar.setVisible(False)
            self.capture_button.setEnabled(True)
            return
        self.progress_bar.setValue(100)
        resolution = photo_info.get("resolution", "unknown")
        self.camera_status.setText(f"Photo saved: {os.path.basename(saved_path)} ({resolution})")
        self.progress_bar.setVisible(False)
        self.capture_button.setEnabled(True)
        self.photo_thread = None

    def _on_photo_failed(self, error_message: str):
        self._stop_progress_timer()
        self.camera_status.setText(f"Error: {error_message}")
        self.progress_bar.setVisible(False)
        self.capture_button.setEnabled(True)
        self.photo_thread = None

    # ------------------------------------------------------------------
    # Layout
    # ------------------------------------------------------------------

    def resizeEvent(self, event):
        super().resizeEvent(event)
        w = self.width()
        h = self.height()
        self.video_label.setMaximumSize(int(w * 4 / 5), int(h * 0.95))

    def update_language(self, interface_text: Interface_text):
        self.interface_text = interface_text
        self.start_button.setText(interface_text.start_camera())
        self.stop_button.setText(interface_text.stop_camera())
        self.capture_button.setText(interface_text.capture_photo())

    def closeEvent(self, event):
        self.stop_camera()
        if hasattr(self, 'positioner_widget'):
            self.positioner_widget.closeEvent(event)
        super().closeEvent(event)
