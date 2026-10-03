"""Camera backend implementations.

Provides a pluggable backend layer for the camera service so that
rpicam-apps, OpenCV/V4L2 and test-pattern sources can be swapped without
changing the rest of the application.
"""

import abc
import glob
import logging
import subprocess
import threading
import time
from typing import TYPE_CHECKING, Optional, Tuple, Union

import cv2
import numpy as np

from src.config.settings import config

if TYPE_CHECKING:
    from .camera_service import CameraService

logger = logging.getLogger(__name__)


class CameraBackendError(Exception):
    """Raised when a real camera backend fails and a fallback is needed."""


class CameraBackend(abc.ABC):
    """Abstract base class for camera backends."""

    name: str = "abstract"
    is_real: bool = False

    def __init__(self, service: "CameraService"):
        self.service = service

    @abc.abstractmethod
    def initialize(self) -> None:
        """Prepare the backend. Raises CameraBackendError on failure."""
        ...

    @abc.abstractmethod
    def start(self) -> None:
        """Start producing frames."""
        ...

    @abc.abstractmethod
    def stop(self) -> None:
        """Stop producing frames and release hardware."""
        ...

    @abc.abstractmethod
    def is_running(self) -> bool:
        """Return True if the backend is currently producing frames."""
        ...

    @abc.abstractmethod
    def read_frame(
        self, pause_event: Optional[threading.Event] = None
    ) -> Optional[bytes]:
        """Return one JPEG-encoded frame, or None if none is available."""
        ...

    def pause_stream(self) -> None:
        """Pause streaming, releasing any exclusive hardware."""
        self.stop()

    def resume_stream(self) -> None:
        """Resume streaming after a pause."""
        self.start()

    def capture_photo(
        self, output_path: Optional[str] = None
    ) -> Tuple[bool, Union[np.ndarray, str]]:
        """Capture a high-quality still frame.

        Returns:
            (success, result) where result is a file path, numpy array, or error message.
        """
        raise NotImplementedError(
            f"Backend {self.name} does not implement still capture"
        )


class RpicamBackend(CameraBackend):
    """Backend using rpicam-apps (rpicam-vid / rpicam-still)."""

    name = "rpicam"
    is_real = True

    def __init__(self, service: "CameraService"):
        super().__init__(service)
        self.process: Optional[subprocess.Popen] = None
        self._mjpeg_buffer = b""
        self._mjpeg_lock = threading.Lock()
        self._consecutive_errors = 0

    def initialize(self) -> None:
        test_result = subprocess.run(
            ["rpicam-vid", "--list-cameras"],
            capture_output=True,
            timeout=5,
        )
        if (
            test_result.returncode != 0
            and b"Available cameras"
            not in test_result.stdout + test_result.stderr
        ):
            raise CameraBackendError("No cameras found by rpicam-vid")
        logger.info("rpicam-apps backend selected")

    def _start_rpicam_vid(self) -> None:
        effective_fps = self.service.fps
        if not self.service.ae_enable and self.service.exposure_time > 0:
            max_fps_for_shutter = 1_000_000 / self.service.exposure_time
            if max_fps_for_shutter < self.service.fps:
                effective_fps = max(1, round(max_fps_for_shutter, 2))

        cmd = [
            "rpicam-vid",
            "-t", "0",
            "--width", str(self.service.width),
            "--height", str(self.service.height),
            "--framerate", str(effective_fps),
            "--codec", "mjpeg",
            "--quality", "70",
            "--flush",
            "-o", "-",
        ]
        cmd.extend(self.service._build_exposure_args())
        cmd.extend(self.service._build_awb_args())

        self.process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0,
        )
        logger.info(
            "rpicam-vid started (PID %s): %s",
            self.process.pid,
            " ".join(cmd),
        )

    def start(self) -> None:
        if self.process is None or self.process.poll() is not None:
            self._start_rpicam_vid()

    def stop(self) -> None:
        process = self.process
        self.process = None
        if process is not None:
            try:
                process.terminate()
                try:
                    process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    process.kill()
                    process.wait(timeout=1)
            except Exception:
                pass

    def is_running(self) -> bool:
        return self.process is not None and self.process.poll() is None

    def _kill_stray_processes(self) -> None:
        """Kill any leftover rpicam-vid / rpicam-still processes."""
        for pattern in ["rpicam-vid", "rpicam-still"]:
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

    def read_frame(
        self, pause_event: Optional[threading.Event] = None
    ) -> Optional[bytes]:
        SOI = b"\xff\xd8"
        EOI = b"\xff\xd9"

        try:
            if self.process is None or self.process.poll() is not None:
                if pause_event is not None and pause_event.is_set():
                    time.sleep(0.1)
                    return None
                logger.info("rpicam-vid process died, restarting...")
                self._start_rpicam_vid()
                with self._mjpeg_lock:
                    self._mjpeg_buffer = b""

            chunk = self.process.stdout.read(65536)
            if not chunk:
                time.sleep(0.01)
                return None

            with self._mjpeg_lock:
                self._mjpeg_buffer += chunk
                self._consecutive_errors = 0
                buf = self._mjpeg_buffer

            while True:
                start = buf.find(SOI)
                if start == -1:
                    buf = b""
                    break
                end = buf.find(EOI, start + 2)
                if end == -1:
                    buf = buf[start:]
                    break
                jpeg_bytes = buf[start : end + 2]
                buf = buf[end + 2 :]
                with self._mjpeg_lock:
                    self._mjpeg_buffer = buf
                return jpeg_bytes

            with self._mjpeg_lock:
                self._mjpeg_buffer = buf
            return None

        except Exception as e:
            self._consecutive_errors += 1
            logger.error(
                "rpicam-vid read error (%s/%s): %s",
                self._consecutive_errors,
                10,
                e,
            )
            if self._consecutive_errors > 10:
                logger.error("Too many rpicam-vid errors, falling back to test pattern")
                raise CameraBackendError(str(e))
            time.sleep(0.1)
            return None

    def capture_photo(
        self, output_path: Optional[str] = None
    ) -> Tuple[bool, Union[np.ndarray, str]]:
        exposure_sec = self.service.exposure_time / 1_000_000

        cmd = [
            "rpicam-still",
            "-n",
            "--width", str(self.service.photo_width),
            "--height", str(self.service.photo_height),
            "--quality", "95",
        ]
        if self.service.ae_enable and exposure_sec < 1.0:
            cmd.append("--zsl")
        cmd.extend(self.service._build_exposure_args())
        cmd.extend(self.service._build_awb_args())

        if exposure_sec >= 60:
            timeout_seconds = exposure_sec + 30
        elif exposure_sec >= 10:
            timeout_seconds = exposure_sec + 15
        elif exposure_sec >= 3:
            timeout_seconds = exposure_sec + 15
        elif exposure_sec >= 1:
            timeout_seconds = exposure_sec + 8
        else:
            timeout_seconds = 10

        logger.info(
            "rpicam-still command: %s, timeout=%ss",
            " ".join(cmd),
            timeout_seconds,
        )

        max_retries = 3
        retry_delay = min(2.0, max(0.5, exposure_sec * 0.2))

        for attempt in range(max_retries):
            if attempt > 0:
                logger.info(
                    "Retry attempt %s/%s after %ss...",
                    attempt,
                    max_retries,
                    retry_delay,
                )
                time.sleep(retry_delay)

            out_arg = ["-o", output_path] if output_path else ["-o", "-"]
            result = subprocess.run(
                cmd + out_arg,
                capture_output=True,
                timeout=timeout_seconds,
            )

            if result.returncode == 0:
                if output_path:
                    return True, output_path
                frame_array = np.frombuffer(result.stdout, dtype=np.uint8)
                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                if frame is not None:
                    return True, frame
                error_msg = "Failed to decode captured image"
            else:
                error_msg = (
                    result.stderr.decode("utf-8", errors="ignore")
                    if result.stderr
                    else "Unknown error"
                )

            logger.error("rpicam-still attempt %s failed: %s", attempt + 1, error_msg[:200])
            if "in use by another process" in error_msg or "failed to acquire" in error_msg:
                if attempt < max_retries - 1:
                    continue

            return False, f"rpicam-still failed: {error_msg}"

        return False, f"rpicam-still failed after {max_retries} attempts - camera may be busy"


class OpenCVBackend(CameraBackend):
    """Backend using OpenCV / V4L2 video devices."""

    name = "opencv"
    is_real = True

    def __init__(self, service: "CameraService"):
        super().__init__(service)
        self.cap: Optional[cv2.VideoCapture] = None
        self._device: Optional[str] = None
        self._backend: Optional[int] = None

    def initialize(self) -> None:
        video_devices = glob.glob("/dev/video*")
        logger.info("Trying video devices: %s", video_devices)

        for device in video_devices:
            try:
                cap = cv2.VideoCapture(device)
                if not cap.isOpened():
                    cap.release()
                    continue

                for backend in (cv2.CAP_V4L2, cv2.CAP_ANY):
                    try:
                        cap_backend = cv2.VideoCapture(device, backend)
                        if cap_backend.isOpened():
                            cap_backend.set(
                                cv2.CAP_PROP_FRAME_WIDTH, self.service.width
                            )
                            cap_backend.set(
                                cv2.CAP_PROP_FRAME_HEIGHT, self.service.height
                            )
                            cap_backend.set(cv2.CAP_PROP_FPS, self.service.fps)
                            ret, frame = cap_backend.read()
                            if ret and frame is not None:
                                self.cap = cap_backend
                                self._device = device
                                self._backend = backend
                                self.service.width = int(
                                    cap_backend.get(cv2.CAP_PROP_FRAME_WIDTH)
                                )
                                self.service.height = int(
                                    cap_backend.get(cv2.CAP_PROP_FRAME_HEIGHT)
                                )
                                logger.info(
                                    "OpenCV camera working with %s (backend %s): %sx%s",
                                    device,
                                    backend,
                                    self.service.width,
                                    self.service.height,
                                )
                                return
                            cap_backend.release()
                    except Exception as e:
                        logger.warning("Backend %s failed for %s: %s", backend, device, e)
                        continue
                cap.release()
            except Exception as e:
                logger.warning("Failed to open %s: %s", device, e)
                continue

        raise CameraBackendError("No working OpenCV camera device found")

    def start(self) -> None:
        if self.cap is None or not self.cap.isOpened():
            self.initialize()

    def stop(self) -> None:
        if self.cap is not None:
            try:
                self.cap.release()
            except Exception:
                pass
            self.cap = None

    def is_running(self) -> bool:
        return self.cap is not None and self.cap.isOpened()

    def read_frame(
        self, pause_event: Optional[threading.Event] = None
    ) -> Optional[bytes]:
        if self.cap is None or not self.cap.isOpened():
            raise CameraBackendError("OpenCV camera is not open")
        ret, frame = self.cap.read()
        if not ret or frame is None:
            raise CameraBackendError("Failed to read frame from OpenCV camera")
        ret, jpeg = cv2.imencode(".jpg", frame)
        if not ret:
            raise CameraBackendError("Failed to encode OpenCV frame")
        return jpeg.tobytes()

    def capture_photo(
        self, output_path: Optional[str] = None
    ) -> Tuple[bool, Union[np.ndarray, str]]:
        try:
            if self.cap is not None:
                self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.service.photo_width)
                self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.service.photo_height)
                time.sleep(0.5)
            ret, frame = self.cap.read() if self.cap else (False, None)
            if not ret or frame is None:
                return False, "Failed to capture frame from OpenCV camera"
            if output_path:
                cv2.imwrite(output_path, frame)
                return True, output_path
            return True, frame
        except Exception as e:
            return False, f"OpenCV capture error: {e}"


class TestBackend(CameraBackend):
    """Backend that produces a synthetic test pattern."""

    name = "test"
    is_real = False

    def initialize(self) -> None:
        logger.info("Test pattern backend selected")

    def start(self) -> None:
        pass

    def stop(self) -> None:
        pass

    def is_running(self) -> bool:
        return True

    def _generate_pattern(self, width: int, height: int) -> np.ndarray:
        x = np.linspace(0, 255, width)
        y = np.linspace(0, 255, height)
        X, Y = np.meshgrid(x, y)
        R = np.uint8(X)
        G = np.uint8(Y)
        B = np.uint8(255 - X)
        frame = np.stack([R, G, B], axis=2)
        text = f"Camera Test Pattern {width}x{height}"
        cv2.putText(
            frame,
            text,
            (50, height // 2),
            cv2.FONT_HERSHEY_SIMPLEX,
            1,
            (255, 255, 255),
            2,
        )
        cv2.putText(
            frame,
            "Real Camera: False",
            (50, height // 2 + 40),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.7,
            (255, 255, 255),
            2,
        )
        return frame

    def read_frame(
        self, pause_event: Optional[threading.Event] = None
    ) -> Optional[bytes]:
        frame = self._generate_pattern(self.service.width, self.service.height)
        ret, jpeg = cv2.imencode(".jpg", frame)
        return jpeg.tobytes() if ret else None

    def capture_photo(
        self, output_path: Optional[str] = None
    ) -> Tuple[bool, Union[np.ndarray, str]]:
        frame = self._generate_pattern(
            self.service.photo_width, self.service.photo_height
        )
        if output_path:
            cv2.imwrite(output_path, frame)
            return True, output_path
        return True, frame
