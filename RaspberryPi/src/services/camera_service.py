import time
import threading
import subprocess
import logging
from typing import Optional, Dict, Any, Tuple, Union

import numpy as np

from src.config.settings import config
from .database_service import db_service
from .camera_backends import (
    CameraBackend,
    CameraBackendError,
    RpicamBackend,
    OpenCVBackend,
    TestBackend,
)

logger = logging.getLogger(__name__)

# Global flag to prevent auto-restart of the video backend during still capture.
# Module-level so it is shared across any CameraService instance in this process.
_pause_for_photo_global = threading.Event()


class CameraService:
    """High-level camera service that delegates to a pluggable backend."""

    def __init__(self, fps: int = config.DEFAULT_FPS):
        self.fps: int = fps
        self.frame_lock = threading.Lock()
        self.current_frame: Optional[bytes] = None
        self.running: bool = False
        self.use_real_camera: bool = False
        self.camera_backend: Optional[str] = None
        self._backend: Optional[CameraBackend] = None
        self.thread: Optional[threading.Thread] = None

        self._load_settings()
        self._initialize_camera()

    def _initialize_camera(self):
        """Probe backends in order of preference until one works."""
        candidates = [
            ("rpicam", RpicamBackend),
            ("opencv", OpenCVBackend),
        ]

        for name, backend_cls in candidates:
            try:
                backend = backend_cls(self)
                backend.initialize()
                self._backend = backend
                self.camera_backend = name
                self.use_real_camera = backend.is_real
                logger.info("%s backend initialized successfully", name)
                return
            except Exception as e:
                logger.warning("%s backend failed: %s", name, e)

        logger.warning("All real camera backends failed, using test pattern")
        self._backend = TestBackend(self)
        self._backend.initialize()
        self.camera_backend = self._backend.name
        self.use_real_camera = self._backend.is_real

    def _load_settings(self):
        """Load camera settings from the database."""
        try:
            settings = db_service.get_camera_settings()
            self._apply_settings_to_attributes(settings)
        except Exception as e:
            logger.error("Error loading camera settings: %s", e)
            self._set_default_settings()

    def _apply_settings_to_attributes(self, settings: Dict[str, Any]):
        """Apply a settings dictionary to instance attributes."""
        if not settings:
            self._set_default_settings()
            return

        video_resolution = settings.get("VideoResolution", "1280x720")
        known_resolutions = [
            (int(r.split("x")[0]), int(r.split("x")[1]))
            for r in config.AVAILABLE_RESOLUTIONS
        ]
        if "x" in video_resolution:
            width, height = map(int, video_resolution.split("x"))
            if (width, height) in known_resolutions:
                self.width, self.height = width, height
            else:
                self.width, self.height = 1280, 720
        else:
            self.width, self.height = 1280, 720

        photo_resolution = settings.get("PhotoResolution", "3280x2464")
        if "x" in photo_resolution:
            self.photo_width, self.photo_height = map(int, photo_resolution.split("x"))
        else:
            self.photo_width, self.photo_height = 3280, 2464

        self.ae_enable = bool(settings.get("AeEnable", True))
        self.awb_enable = bool(settings.get("AwbEnable", True))
        self.exposure_time = settings.get("ExposureTime", 10000)
        self.analogue_gain = settings.get("AnalogueGain", 1.0)
        self.exposure_value = settings.get("ExposureValue", 0.0)
        self.red_gain = float(settings.get("RedGain", 2.0))
        self.blue_gain = float(settings.get("BlueGain", 2.0))

    def _set_default_settings(self):
        """Set safe default camera settings."""
        self.width, self.height = 1280, 720
        self.photo_width, self.photo_height = 3280, 2464
        self.ae_enable = True
        self.awb_enable = True
        self.exposure_time = 10000
        self.analogue_gain = 1.0
        self.exposure_value = 0.0
        self.red_gain = 2.0
        self.blue_gain = 2.0

    def _build_awb_args(self) -> list:
        """Build rpicam AWB command-line arguments."""
        if not self.awb_enable and self.red_gain > 0 and self.blue_gain > 0:
            return [
                "--awb",
                "custom",
                "--awbgains",
                f"{self.red_gain:.4f},{self.blue_gain:.4f}",
            ]
        return ["--awb", "auto"]

    def _build_exposure_args(self) -> list:
        """Build rpicam manual exposure command-line arguments (empty when AE is on)."""
        args = []
        if not self.ae_enable:
            args.extend(["--shutter", str(int(self.exposure_time))])
            args.extend(["--gain", str(float(self.analogue_gain))])
        if self.exposure_value is not None and self.exposure_value != 0.0:
            args.extend(["--ev", str(float(self.exposure_value))])
        return args

    def apply_session_settings(self, settings: Dict[str, Any]) -> bool:
        """Apply session settings and persist them to slot 0.

        Args:
            settings: Dictionary containing camera settings to apply.

        Returns:
            True if settings were applied successfully, False otherwise.
        """
        try:
            logger.info("Applying session settings: %s", settings)
            old_resolution = (self.width, self.height)
            self._apply_settings_to_attributes(settings)

            success, message = db_service.save_camera_settings_to_slot(0, settings)
            if not success:
                logger.warning("Failed to save session settings to slot 0: %s", message)

            new_resolution = (self.width, self.height)
            resolution_changed = old_resolution != new_resolution

            if self.camera_backend == "rpicam" and self.use_real_camera:
                logger.info("Restarting rpicam-vid with session settings...")
                self._restart_rpicam_vid()
            elif resolution_changed and self.use_real_camera:
                logger.info("Resolution changed, reinitializing camera...")
                self._reinitialize_camera()
            else:
                logger.info("Settings applied to camera session")

            return True
        except Exception as e:
            logger.error("Failed to apply session settings: %s", e)
            return False

    def start(self):
        """Start the camera backend and capture thread."""
        if self.running:
            return
        self.running = True
        if self._backend is not None:
            self._backend.start()
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        """Continuously read frames from the active backend."""
        while self.running:
            try:
                frame = self._backend.read_frame(pause_event=_pause_for_photo_global)
            except CameraBackendError as e:
                logger.error(
                    "Camera backend failed (%s), falling back to test pattern: %s",
                    self.camera_backend,
                    e,
                )
                self._backend.stop()
                self._backend = TestBackend(self)
                self._backend.start()
                self.camera_backend = self._backend.name
                self.use_real_camera = self._backend.is_real
                continue

            if frame is not None:
                with self.frame_lock:
                    self.current_frame = frame
            time.sleep(1 / self.fps)

    def _pause_video_stream(self):
        """Pause video streaming so the camera can be used for still capture."""
        _pause_for_photo_global.set()
        logger.info("Pausing video stream for photo capture")
        time.sleep(0.02)

        if self._backend is not None:
            self._backend.pause_stream()

        if self.camera_backend == "rpicam":
            self._kill_stray_camera_processes()
            self._wait_for_camera_release(max_wait_time=10.0, check_interval=0.05)

        logger.info("Video stream paused, camera is free")

    def _resume_video_stream(self):
        """Resume video streaming after a still capture."""
        if self._backend is not None:
            self._backend.resume_stream()
        _pause_for_photo_global.clear()
        logger.info("Video stream resumed")

    def capture_photo(
        self, output_path: Optional[str] = None
    ) -> Tuple[bool, Union[np.ndarray, str]]:
        """Capture a high-quality still frame using the active backend.

        Args:
            output_path: Optional path to save the JPEG. If None, the raw
                BGR numpy array is returned.

        Returns:
            (success, result) where result is a file path, numpy array, or
            an error message.
        """
        try:
            self._load_settings()
            video_was_running = self.running or self._is_rpicam_vid_running()

            needs_pause = self.camera_backend == "rpicam" and self.use_real_camera
            if needs_pause and video_was_running:
                self._pause_video_stream()

            try:
                success, result = self._backend.capture_photo(output_path)
                return success, result
            finally:
                if needs_pause and video_was_running:
                    self._resume_video_stream()

        except subprocess.TimeoutExpired:
            return False, f"Photo capture timeout (exposure={self.exposure_time}us)"
        except Exception as e:
            return False, f"Photo capture error: {e}"

    def get_frame(self):
        with self.frame_lock:
            return self.current_frame

    def _is_rpicam_vid_running(self) -> bool:
        """Check whether an rpicam-vid process is running on the host."""
        try:
            result = subprocess.run(
                ["pgrep", "-f", "rpicam-vid"],
                capture_output=True,
                text=True,
                timeout=2,
            )
            return result.returncode == 0 and bool(result.stdout.strip())
        except Exception:
            return False

    def _kill_stray_camera_processes(self):
        """Kill any rpicam-vid / rpicam-still processes that may hold the camera."""
        for pattern in ["rpicam-vid", "rpicam-still", "libcamera-vid", "libcamera-still"]:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", pattern],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0 and result.stdout.strip():
                    for pid in result.stdout.strip().split("\n"):
                        pid = pid.strip()
                        if pid:
                            subprocess.run(
                                ["kill", "-9", pid], check=False, timeout=2
                            )
            except Exception:
                pass

    def _wait_for_camera_release(
        self, max_wait_time: float = 10.0, check_interval: float = 0.05
    ) -> bool:
        """Wait until no rpicam/libcamera capture processes are running."""
        start_time = time.time()
        last_log_time = 0.0

        while time.time() - start_time < max_wait_time:
            elapsed = time.time() - start_time
            camera_processes = self._get_camera_processes()
            if not camera_processes:
                logger.info("Camera ready after %.2fs", elapsed)
                return True
            if elapsed - last_log_time >= 1.0:
                logger.info(
                    "[%.1fs] Waiting for camera processes: %s",
                    elapsed,
                    camera_processes,
                )
                last_log_time = elapsed
            time.sleep(check_interval)

        elapsed = time.time() - start_time
        logger.warning("Camera wait timeout after %.1fs - proceeding anyway", elapsed)
        return False

    def _get_camera_processes(self):
        """Return PIDs of processes that may hold the camera."""
        pids = []
        for pattern in ["rpicam-vid", "rpicam-still", "libcamera-vid", "libcamera-still"]:
            try:
                result = subprocess.run(
                    ["pgrep", "-f", pattern],
                    capture_output=True,
                    text=True,
                    timeout=2,
                )
                if result.returncode == 0 and result.stdout.strip():
                    pids.extend(result.stdout.strip().split("\n"))
            except Exception:
                pass
        return [p for p in pids if p.strip()]

    def _restart_rpicam_vid(self):
        """Restart the rpicam-vid process with current settings."""
        _pause_for_photo_global.set()
        time.sleep(0.05)
        try:
            if self._backend is not None:
                self._backend.stop()
            self._kill_stray_camera_processes()
            self._wait_for_camera_release(max_wait_time=5.0, check_interval=0.05)
            if self._backend is not None:
                self._backend.start()
        finally:
            _pause_for_photo_global.clear()

    def _reinitialize_camera(self):
        """Reinitialize the active camera backend (e.g. after a resolution change)."""
        if self._backend is not None:
            self._backend.stop()
        self._initialize_camera()
        if self.running and self._backend is not None:
            self._backend.start()

    def stop(self):
        """Stop the capture thread and release the camera backend."""
        self.running = False
        if self.thread is not None:
            self.thread.join(timeout=2.0)
        if self._backend is not None:
            self._backend.stop()
