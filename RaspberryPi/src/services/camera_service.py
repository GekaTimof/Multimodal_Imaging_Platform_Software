import time
import threading
import glob
import numpy as np
import cv2
import sys
import os
import signal
import subprocess
import logging
from typing import Optional, Dict, Any, Tuple, Union

# Import config
from src.config.settings import config
from .database_service import db_service

# Setup logging
logger = logging.getLogger(__name__)

# Global flag to prevent auto-restart of rpicam-vid during photo capture
# Must be module-level to be shared across all CameraService instances
_pause_for_photo_global = threading.Event()

# Camera backend options
OPENCV_AVAILABLE = True
RPICAM_AVAILABLE = True  # Use rpicam-apps as subprocess


class CameraService:
    """Service responsible for capturing frames from the Raspberry Pi camera."""

    def __init__(self, fps: int = config.DEFAULT_FPS):
        self.fps: int = fps
        self.frame_lock = threading.Lock()
        self.current_frame: Optional[np.ndarray] = None
        self.running: bool = False
        self.use_real_camera: bool = False
        self.camera_backend: Optional[str] = None
        # Note: _pause_for_photo_global is module-level, shared across all instances
        
        # Load settings from database
        self._load_settings()
        
        # Try to initialize real camera with different backends
        self._initialize_camera()
    
    def _initialize_camera(self):
        """Try different camera backends to find a working one."""
        
        # Try rpicam-apps first (most reliable for IMX477)
        if RPICAM_AVAILABLE:
            try:
                self._init_rpicam_app()
                self.use_real_camera = True
                self.camera_backend = "rpicam"
                print("rpicam-apps camera initialized successfully")
                return
            except Exception as e:
                print(f"rpicam-apps camera failed: {e}")
        
        # Try OpenCV + V4L2
        if OPENCV_AVAILABLE:
            try:
                self._init_opencv_camera()
                self.use_real_camera = True
                self.camera_backend = "opencv"
                print("OpenCV + V4L2 camera initialized successfully")
                return
            except Exception as e:
                print(f"OpenCV camera failed: {e}")
        
        # If all fail, use test pattern
        print("All camera backends failed, using test pattern")
        self.use_real_camera = False
        self.camera_backend = "test"
    
    def _init_opencv_camera(self):
        """Initialize camera using OpenCV + V4L2."""
        video_devices = glob.glob('/dev/video*')
        
        print(f"Trying video devices: {video_devices}")
        
        for device in video_devices:
            try:
                print(f"Testing {device}...")
                cap = cv2.VideoCapture(device)
                if cap.isOpened():
                    print(f"Device {device} opened successfully")
                    
                    # Try different backend indices
                    backends = [cv2.CAP_V4L2, cv2.CAP_ANY]
                    for backend in backends:
                        try:
                            cap_with_backend = cv2.VideoCapture(device, backend)
                            if cap_with_backend.isOpened():
                                # Set resolution
                                cap_with_backend.set(cv2.CAP_PROP_FRAME_WIDTH, self.width)
                                cap_with_backend.set(cv2.CAP_PROP_FRAME_HEIGHT, self.height)
                                cap_with_backend.set(cv2.CAP_PROP_FPS, self.fps)
                                
                                # Test if we can read a frame
                                ret, frame = cap_with_backend.read()
                                if ret and frame is not None:
                                    self.cap = cap_with_backend
                                    # Update actual resolution
                                    actual_width = int(cap_with_backend.get(cv2.CAP_PROP_FRAME_WIDTH))
                                    actual_height = int(cap_with_backend.get(cv2.CAP_PROP_FRAME_HEIGHT))
                                    self.width = actual_width
                                    self.height = actual_height
                                    print(f"OpenCV camera working with {device} (backend {backend}): {actual_width}x{actual_height}")
                                    return
                                else:
                                    cap_with_backend.release()
                        except Exception as e:
                            print(f"Backend {backend} failed for {device}: {e}")
                            continue
                    
                    cap.release()
                else:
                    print(f"Could not open {device}")
            except Exception as e:
                print(f"Failed to open {device}: {e}")
                continue
        
        raise Exception("No working OpenCV camera device found")
    
    def _init_rpicam_app(self):
        """Initialize camera using rpicam-vid continuous MJPEG stream."""
        self.rpicam_process = None
        self._mjpeg_buffer = b''
        self._mjpeg_lock = threading.Lock()

        # Verify camera is accessible by doing a quick test
        test_result = subprocess.run(
            ['rpicam-vid', '--list-cameras'],
            capture_output=True, timeout=5
        )
        if test_result.returncode != 0 and b'Available cameras' not in test_result.stdout + test_result.stderr:
            raise Exception("No cameras found by rpicam-vid")

        print("rpicam-apps backend selected")
        
    def _load_settings(self):
        """Load camera settings from database."""
        try:
            settings = db_service.get_camera_settings()
            self._apply_settings_to_attributes(settings)
        except Exception as e:
            print(f"Error loading camera settings: {e}")
            # Fallback to safe default settings
            self._set_default_settings()

    def _apply_settings_to_attributes(self, settings: Dict[str, Any]):
        """Apply settings dictionary to instance attributes."""
        if settings:
            # Parse video resolution from database (format: "1920x1080")
            video_resolution = settings.get('VideoResolution', '1280x720')
            if 'x' in video_resolution:
                width_str, height_str = video_resolution.split('x')
                width = int(width_str)
                height = int(height_str)
                # Accept any resolution from the known config list; fallback for truly unknown ones
                known_resolutions = [
                    (int(r.split('x')[0]), int(r.split('x')[1]))
                    for r in config.AVAILABLE_RESOLUTIONS
                ]
                if (width, height) in known_resolutions:
                    self.width, self.height = width, height
                else:
                    self.width, self.height = 1280, 720  # Safe fallback
            else:
                self.width, self.height = 1280, 720

            # Parse photo resolution from database
            photo_resolution = settings.get('PhotoResolution', '3280x2464')
            if 'x' in photo_resolution:
                width_str, height_str = photo_resolution.split('x')
                self.photo_width = int(width_str)
                self.photo_height = int(height_str)
            else:
                self.photo_width, self.photo_height = 3280, 2464

            # Load other camera settings
            self.ae_enable = bool(settings.get('AeEnable', True))
            self.awb_enable = bool(settings.get('AwbEnable', True))
            self.exposure_time = settings.get('ExposureTime', 10000)
            self.analogue_gain = settings.get('AnalogueGain', 1.0)
            self.exposure_value = settings.get('ExposureValue', 0.0)
            self.red_gain = float(settings.get('RedGain', 2.0))
            self.blue_gain = float(settings.get('BlueGain', 2.0))
        else:
            # Default settings if database is empty - use safe defaults
            self._set_default_settings()

    def _set_default_settings(self):
        """Set default camera settings."""
        self.width, self.height = 1280, 720
        self.photo_width, self.photo_height = 3280, 2464
        self.ae_enable = True
        self.awb_enable = True
        self.exposure_time = 10000
        self.analogue_gain = 1.0
        self.exposure_value = 0.0
        self.red_gain = 2.0
        self.blue_gain = 2.0

    def apply_session_settings(self, settings: Dict[str, Any]) -> bool:
        """Apply session settings to camera and save to slot 0 (current session).

        This updates the camera's current operational parameters, saves them to
        slot 0 (current session) in the database, and restarts the camera stream
        to apply the new settings immediately.

        Args:
            settings: Dictionary containing camera settings to apply

        Returns:
            True if settings were applied successfully, False otherwise
        """
        try:
            print(f"Applying session settings: {settings}")

            # Store old resolution to check if camera needs reinitialization
            old_resolution = (self.width, self.height)

            # Apply settings to instance attributes
            self._apply_settings_to_attributes(settings)

            # Save to slot 0 (current session) in database
            success, message = db_service.save_camera_settings_to_slot(0, settings)
            if not success:
                logger.warning(f"Failed to save session settings to slot 0: {message}")
                # Continue anyway - camera settings are still applied

            # Check if resolution changed
            new_resolution = (self.width, self.height)
            resolution_changed = old_resolution != new_resolution

            # Restart camera to apply new settings
            if self.camera_backend == "rpicam" and self.use_real_camera:
                print("Restarting rpicam-vid with session settings...")
                self._restart_rpicam_vid()
            elif resolution_changed and self.use_real_camera:
                print("Resolution changed, reinitializing camera...")
                self._reinitialize_camera()
            else:
                print("Settings applied to camera session")

            return True

        except Exception as e:
            print(f"Error applying session settings: {e}")
            logger.error(f"Failed to apply session settings: {e}")
            return False

    def _build_awb_args(self) -> list:
        """Build rpicam AWB command-line arguments."""
        if not self.awb_enable and self.red_gain > 0 and self.blue_gain > 0:
            return ['--awb', 'custom', '--awbgains', f"{self.red_gain:.4f},{self.blue_gain:.4f}"]
        return ['--awb', 'auto']

    def _build_exposure_args(self) -> list:
        """Build rpicam manual exposure command-line arguments (empty when AE is on)."""
        args = []
        if not self.ae_enable:
            args.extend(['--shutter', str(int(self.exposure_time))])
            args.extend(['--gain', str(float(self.analogue_gain))])
        if self.exposure_value is not None and self.exposure_value != 0.0:
            args.extend(['--ev', str(float(self.exposure_value))])
        return args

    def _start_rpicam_vid(self):
        """Start rpicam-vid process for continuous MJPEG streaming."""
        # When manual shutter exceeds 1/fps the sensor caps exposure at 1/fps.
        # Lower the framerate so the requested shutter time is actually achievable.
        effective_fps = self.fps
        if not self.ae_enable and self.exposure_time > 0:
            max_fps_for_shutter = 1_000_000 / self.exposure_time  # e.g. 200000us → 5fps
            if max_fps_for_shutter < self.fps:
                effective_fps = max(1, round(max_fps_for_shutter, 2))

        cmd = [
            'rpicam-vid',
            '-t', '0',
            '--width', str(self.width),
            '--height', str(self.height),
            '--framerate', str(effective_fps),
            '--codec', 'mjpeg',
            '--quality', '70',
            '--flush',
            '-o', '-',
        ]
        cmd.extend(self._build_exposure_args())
        cmd.extend(self._build_awb_args())

        self.rpicam_process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.DEVNULL,
            bufsize=0
        )
        print(f"rpicam-vid started (PID {self.rpicam_process.pid}): {' '.join(cmd)}")

    def start(self):
        if self.running:
            return
        self.running = True
        if self.camera_backend == "rpicam":
            self._start_rpicam_vid()
        self.thread = threading.Thread(target=self._capture_loop, daemon=True)
        self.thread.start()

    def _capture_loop(self):
        if self.camera_backend == "rpicam" and self.use_real_camera:
            self._capture_loop_rpicam_vid()
        else:
            self._capture_loop_generic()

    def _capture_loop_rpicam_vid(self):
        """Read MJPEG frames from rpicam-vid stdout."""
        SOI = b'\xff\xd8'
        EOI = b'\xff\xd9'
        buf = b''
        consecutive_errors = 0

        while self.running:
            try:
                if self.rpicam_process is None or self.rpicam_process.poll() is not None:
                    # Don't auto-restart if we're paused for photo capture (global flag)
                    if _pause_for_photo_global.is_set():
                        print("rpicam-vid process ended (paused for photo), waiting...")
                        time.sleep(0.5)
                        continue
                    print("rpicam-vid process died, restarting...")
                    self._start_rpicam_vid()
                    buf = b''

                chunk = self.rpicam_process.stdout.read(65536)
                if not chunk:
                    time.sleep(0.01)
                    continue

                buf += chunk
                consecutive_errors = 0

                while True:
                    start = buf.find(SOI)
                    if start == -1:
                        buf = b''
                        break
                    end = buf.find(EOI, start + 2)
                    if end == -1:
                        buf = buf[start:]
                        break
                    jpeg_bytes = buf[start:end + 2]
                    buf = buf[end + 2:]
                    with self.frame_lock:
                        self.current_frame = jpeg_bytes

            except Exception as e:
                consecutive_errors += 1
                print(f"rpicam-vid read error ({consecutive_errors}): {e}")
                if consecutive_errors > 10:
                    print("Too many errors, falling back to test pattern")
                    self.use_real_camera = False
                    self.camera_backend = "test"
                    self._capture_loop_generic()
                    return
                time.sleep(0.1)

    def _capture_loop_generic(self):
        """Capture loop for OpenCV/test backends."""
        while self.running:
            if self.use_real_camera and self.camera_backend == "opencv":
                try:
                    ret, frame = self.cap.read()
                    if not ret or frame is None:
                        raise Exception("Failed to read frame from OpenCV camera")
                except Exception as e:
                    print(f"Camera capture error: {e}")
                    self.use_real_camera = False
                    self.camera_backend = "test"
                    frame = self._generate_test_pattern()
            else:
                frame = self._generate_test_pattern()

            ret, jpeg = cv2.imencode('.jpg', frame)
            if ret:
                with self.frame_lock:
                    self.current_frame = jpeg.tobytes()
            time.sleep(1 / self.fps)

    def _generate_test_pattern(self):
        """Generate a test pattern with the configured resolution."""
        # Create a colorful test pattern
        height, width = self.height, self.width

        # Create gradient background
        x = np.linspace(0, 255, width)
        y = np.linspace(0, 255, height)
        X, Y = np.meshgrid(x, y)

        # Create RGB channels with different patterns
        R = np.uint8(X)
        G = np.uint8(Y)
        B = np.uint8(255 - X)

        # Stack channels to create RGB image
        frame = np.stack([R, G, B], axis=2)

        # Add some text overlay
        text = f"Camera Test Pattern {width}x{height}"
        cv2.putText(frame, text, (50, height//2), cv2.FONT_HERSHEY_SIMPLEX, 1, (255, 255, 255), 2)
        cv2.putText(frame, f"Real Camera: {self.use_real_camera}", (50, height//2 + 40), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        return frame

    def _pause_video_stream(self):
        """Pause video stream by stopping rpicam-vid process."""
        # Set flag FIRST to prevent auto-restart by capture loop (race condition guard)
        _pause_for_photo_global.set()
        print("Pausing video stream for photo capture")

        # Give capture loop one iteration to notice the flag (~10ms)
        time.sleep(0.02)

        # Stop our own rpicam-vid process
        if hasattr(self, 'rpicam_process') and self.rpicam_process is not None:
            try:
                self.rpicam_process.terminate()
                try:
                    self.rpicam_process.wait(timeout=1.0)
                except subprocess.TimeoutExpired:
                    self.rpicam_process.kill()
                    self.rpicam_process.wait(timeout=1.0)
            except Exception as e:
                print(f"Warning: error stopping video stream: {e}")
            finally:
                self.rpicam_process = None

        # Kill any stray rpicam-vid / rpicam-still processes (NOT libcamera-ipa — it's a system daemon)
        try:
            stray_pids = set()
            for pattern in ['rpicam-vid', 'rpicam-still']:
                result = subprocess.run(['pgrep', '-f', pattern],
                                        capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and result.stdout.strip():
                    for pid in result.stdout.strip().split('\n'):
                        if pid.strip():
                            stray_pids.add(pid.strip())
            if stray_pids:
                print(f"Killing stray camera processes: {sorted(stray_pids)}")
                for pid in sorted(stray_pids):
                    try:
                        subprocess.run(['kill', '-9', pid], check=False, timeout=2)
                    except Exception:
                        pass
        except Exception as e:
            print(f"Warning: could not check for stray camera processes: {e}")

        # Wait until no rpicam processes are running (camera device will then be free)
        self._wait_for_camera_release(max_wait_time=10.0, check_interval=0.05)
        print("Video stream paused, camera is free")

    def _wait_for_camera_release(self, max_wait_time=10.0, check_interval=0.05):
        """Poll until no rpicam-vid / rpicam-still processes are running.

        libcamera-ipa is intentionally excluded — it is a persistent system
        daemon that always holds /dev/media0 and does NOT block rpicam-still.
        """
        start_time = time.time()
        last_log_time = 0.0

        while time.time() - start_time < max_wait_time:
            elapsed = time.time() - start_time
            camera_processes = self._get_camera_processes()
            if not camera_processes:
                print(f"Camera ready after {elapsed:.2f}s")
                return True
            if elapsed - last_log_time >= 1.0:
                print(f"[{elapsed:.1f}s] Waiting for camera processes: {camera_processes}")
                last_log_time = elapsed
            time.sleep(check_interval)

        elapsed = time.time() - start_time
        print(f"Warning: Camera wait timeout after {elapsed:.1f}s — proceeding anyway")
        return False
    
    def _is_rpicam_vid_running(self):
        """Check if rpicam-vid process is actually running (may be started by streaming server)."""
        try:
            result = subprocess.run(['pgrep', '-f', 'rpicam-vid'], 
                                  capture_output=True, text=True, timeout=2)
            return result.returncode == 0 and bool(result.stdout.strip())
        except Exception:
            return False

    def _get_camera_processes(self):
        """Get list of PIDs of processes that might be holding the camera."""
        pids = []
        for pattern in ['rpicam-vid', 'rpicam-still', 'libcamera-vid', 'libcamera-still']:
            try:
                result = subprocess.run(['pgrep', '-f', pattern], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and result.stdout.strip():
                    pids.extend(result.stdout.strip().split('\n'))
            except Exception:
                pass
        return [p for p in pids if p.strip()]
    
    def _resume_video_stream(self):
        """Resume video stream by clearing the pause flag.

        The capture loop will restart rpicam-vid automatically once the flag is
        cleared. We must NOT call _start_rpicam_vid() here — doing so would race
        with the capture loop and produce two conflicting rpicam-vid processes.
        """
        _pause_for_photo_global.clear()
        print("Video stream resume flag cleared — capture loop will restart rpicam-vid")

    def capture_photo(self, output_path: Optional[str] = None) -> Tuple[bool, Union[np.ndarray, str]]:
        """Capture a high-quality photo using PhotoResolution and all camera settings.

        Args:
            output_path: Optional path to save the photo. If None, returns the frame as numpy array.

        Returns:
            Tuple of (success: bool, result: Union[np.ndarray, str])
            - If output_path is None: returns (True, numpy_array) or (False, error_message)
            - If output_path is provided: returns (True, file_path) or (False, error_message)
        """
        try:
            # Reload settings to get current values
            self._load_settings()
            
            if self.use_real_camera and self.camera_backend == "rpicam":
                # Pause video stream to free camera for still capture
                # Camera cannot be used by rpicam-vid and rpicam-still simultaneously
                video_was_running = self.running or self._is_rpicam_vid_running()
                if video_was_running:
                    self._pause_video_stream()

                try:
                    exposure_sec = self.exposure_time / 1_000_000
                    
                    # Build rpicam-still command with photo resolution and full quality
                    cmd = [
                        'rpicam-still',
                        '-n',  # No preview
                        '--width', str(self.photo_width),
                        '--height', str(self.photo_height),
                        '--quality', '95',  # High quality for photos
                    ]
                    
                    # ZSL only in auto-AE mode for short exposures — in manual mode ZSL
                    # captures from the preview buffer (which used AE settings) and ignores --shutter
                    if self.ae_enable and exposure_sec < 1.0:
                        cmd.append('--zsl')

                    cmd.extend(self._build_exposure_args())
                    cmd.extend(self._build_awb_args())

                    # Calculate timeout based on exposure time + buffer
                    # Camera init takes ~3-5s, then actual exposure, then processing
                    if exposure_sec >= 60:
                        # Extreme long exposure (60s+): exposure + 30s buffer
                        # Must exceed CAMERA_TIMEOUT_SECONDS (340s) at max exposure (300s)
                        timeout_seconds = exposure_sec + 30
                    elif exposure_sec >= 10:
                        # Very long exposure (10-60s): exposure + 15s buffer
                        timeout_seconds = exposure_sec + 15
                    elif exposure_sec >= 3:
                        # Long exposure (3-10s): exposure + 15s buffer
                        # Need extra time for camera init with long shutter settings
                        timeout_seconds = exposure_sec + 15
                    elif exposure_sec >= 1:
                        # Medium exposure (1-3s): exposure + 8s buffer
                        timeout_seconds = exposure_sec + 8
                    else:
                        # Short exposure (<1s): 10s total (fast init + ZSL)
                        timeout_seconds = 10
                    print(f"rpicam-still command: {' '.join(cmd)}, timeout={timeout_seconds}s")

                    # Retry logic for camera acquisition race condition
                    max_retries = 3
                    # Fast retry for short exposures, longer for long exposures
                    retry_delay = min(2.0, max(0.5, exposure_sec * 0.2))  # 0.5s to 2s based on exposure
                    
                    for attempt in range(max_retries):
                        if attempt > 0:
                            print(f"Retry attempt {attempt}/{max_retries} after {retry_delay}s...")
                            time.sleep(retry_delay)
                        
                        if output_path:
                            # Save to file
                            cmd_with_output = cmd + ['-o', output_path]
                            result = subprocess.run(cmd_with_output, capture_output=True, timeout=timeout_seconds)
                            if result.returncode == 0:
                                print(f"Photo captured successfully on attempt {attempt + 1}")
                                return True, output_path
                            else:
                                error_msg = result.stderr.decode('utf-8', errors='ignore') if result.stderr else "Unknown error"
                                print(f"rpicam-still attempt {attempt + 1} failed: {error_msg[:200]}")
                                # Check if it's a camera busy error - retry if so
                                if 'in use by another process' in error_msg or 'failed to acquire' in error_msg:
                                    if attempt < max_retries - 1:
                                        continue
                                # Other error - don't retry
                                return False, f"rpicam-still failed: {error_msg}"
                        else:
                            # Return as numpy array
                            cmd_with_output = cmd + ['-o', '-']
                            result = subprocess.run(cmd_with_output, capture_output=True, timeout=timeout_seconds)
                            if result.returncode == 0:
                                frame_array = np.frombuffer(result.stdout, dtype=np.uint8)
                                frame = cv2.imdecode(frame_array, cv2.IMREAD_COLOR)
                                if frame is not None:
                                    print(f"Photo captured successfully on attempt {attempt + 1}")
                                    return True, frame
                                else:
                                    print("Failed to decode captured image from rpicam-still output")
                                    if attempt < max_retries - 1:
                                        continue
                                    return False, "Failed to decode captured image"
                            else:
                                error_msg = result.stderr.decode('utf-8', errors='ignore') if result.stderr else "Unknown error"
                                print(f"rpicam-still attempt {attempt + 1} failed: {error_msg[:200]}")
                                # Check if it's a camera busy error - retry if so
                                if 'in use by another process' in error_msg or 'failed to acquire' in error_msg:
                                    if attempt < max_retries - 1:
                                        continue
                                # Other error - don't retry
                                return False, f"rpicam-still failed: {error_msg}"
                    
                    # All retries exhausted
                    return False, f"rpicam-still failed after {max_retries} attempts - camera may be busy"

                finally:
                    if video_was_running:
                        self._resume_video_stream()

            elif self.use_real_camera and self.camera_backend == "opencv":
                # For OpenCV backend, capture frame at photo resolution if possible
                try:
                    # Try to set photo resolution temporarily
                    if hasattr(self, 'cap'):
                        self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, self.photo_width)
                        self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, self.photo_height)
                        time.sleep(0.5)  # Wait for resolution change

                    ret, frame = self.cap.read()
                    if ret and frame is not None:
                        if output_path:
                            cv2.imwrite(output_path, frame)
                            return True, output_path
                        else:
                            return True, frame
                    else:
                        return False, "Failed to capture frame from OpenCV camera"
                except Exception as e:
                    return False, f"OpenCV capture error: {e}"

            else:
                # Test pattern - generate at photo resolution
                # Temporarily set resolution for test pattern
                orig_width, orig_height = self.width, self.height
                self.width, self.height = self.photo_width, self.photo_height
                frame = self._generate_test_pattern()
                self.width, self.height = orig_width, orig_height

                if output_path:
                    cv2.imwrite(output_path, frame)
                    return True, output_path
                else:
                    return True, frame

        except subprocess.TimeoutExpired:
            return False, f"Photo capture timeout (exposure={self.exposure_time}us)"
        except Exception as e:
            return False, f"Photo capture error: {e}"

    def get_frame(self):
        with self.frame_lock:
            return self.current_frame

    def reload_settings(self):
        """Reload camera settings from database and reinitialize if needed."""
        old_resolution = (self.width, self.height)

        # Reload settings from database
        self._load_settings()

        # Check if resolution changed
        new_resolution = (self.width, self.height)
        if old_resolution != new_resolution and self.use_real_camera:
            print(f"Resolution changed from {old_resolution} to {new_resolution}, reinitializing camera...")
            self._reinitialize_camera()
        elif self.camera_backend == "rpicam" and self.use_real_camera:
            # Restart rpicam-vid to apply new settings (exposure, AWB, etc.)
            print("Restarting rpicam-vid with updated settings...")
            self._restart_rpicam_vid()

    def _restart_rpicam_vid(self):
        """Terminate current rpicam-vid and start a new one with updated settings."""
        # Set pause flag so capture loop doesn't race-restart the process
        _pause_for_photo_global.set()
        time.sleep(0.05)  # Let capture loop notice the flag
        try:
            if hasattr(self, 'rpicam_process') and self.rpicam_process is not None:
                saved_pid = self.rpicam_process.pid
                try:
                    self.rpicam_process.terminate()
                    # Close stdout so the capture loop's blocking read() returns immediately
                    try:
                        self.rpicam_process.stdout.close()
                    except Exception:
                        pass
                    self.rpicam_process.wait(timeout=3)
                except subprocess.TimeoutExpired:
                    self.rpicam_process.kill()
                    self.rpicam_process.wait(timeout=1)
                except Exception:
                    pass
                self.rpicam_process = None
                # Force kill by PID in case process is still alive
                try:
                    subprocess.run(['kill', '-9', str(saved_pid)], check=False, timeout=2)
                except Exception:
                    pass
            # Kill any other stray rpicam-vid processes (NOT libcamera-ipa)
            try:
                result = subprocess.run(['pgrep', '-f', 'rpicam-vid'],
                                        capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and result.stdout.strip():
                    for pid in result.stdout.strip().split('\n'):
                        if pid.strip():
                            subprocess.run(['kill', '-9', pid.strip()], check=False, timeout=2)
            except Exception:
                pass
            # Wait for camera to be released before starting new process
            self._wait_for_camera_release(max_wait_time=5.0, check_interval=0.05)
            self._start_rpicam_vid()
        finally:
            _pause_for_photo_global.clear()

    def _reinitialize_camera(self):
        """Reinitialize camera with new settings."""
        if self.camera_backend == "rpicam":
            self._restart_rpicam_vid()
            return
        # Stop current camera
        if self.camera_backend == "opencv" and hasattr(self, 'cap'):
            try:
                self.cap.release()
            except Exception:
                pass
        # Reinitialize with new settings
        self._initialize_camera()

    def stop(self):
        self.running = False
        if hasattr(self, 'thread'):
            self.thread.join(timeout=2.0)

        if hasattr(self, 'rpicam_process') and self.rpicam_process is not None:
            try:
                self.rpicam_process.terminate()
                self.rpicam_process.wait(timeout=3)
            except Exception:
                pass
            self.rpicam_process = None

        if self.use_real_camera:
            if self.camera_backend == "opencv" and hasattr(self, 'cap'):
                try:
                    self.cap.release()
                except Exception:
                    pass
